"""
policy_store.py - LangChain-powered RAG policy knowledge store.

Uses LangChain for:
    - PDF document loading (PyPDFLoader)
    - Recursive text splitting with overlap
    - ChromaDB vector store for semantic search (with fallback to keyword)
    - Source citation with page numbers

Works in two modes:
    1. With OpenAI API key: Full vector embeddings via text-embedding-3-small
    2. Without API key: Keyword-based retrieval (zero-cost fallback)
"""

from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

POLICY_PDF_PATH = os.path.join(
    os.path.dirname(__file__), "docs", "SilverShield_Master_Policy.pdf",
)
POLICY_PDF_NAME = "SilverShield_Master_Policy.pdf"

_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "or", "and", "not", "no",
    "but", "if", "than", "that", "this", "these", "those", "it", "its",
    "any", "all", "each", "every", "such", "more", "most", "other",
})


# ═══════════════════════════════════════════════════════════════════════════
# Data Model
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RetrievedChunk:
    """A retrieved policy text chunk with source citation."""

    text: str
    section: str
    page: int
    source_doc: str
    score: float = 0.0
    policy_type: str = "General"


@dataclass
class RAGContext:
    """Full RAG context returned to the pipeline."""

    chunks: list[RetrievedChunk] = field(default_factory=list)
    retrieval_method: str = "keyword"  # "vector" or "keyword"
    total_chunks_in_store: int = 0

    @property
    def context_text(self) -> str:
        """Format chunks as context for the LLM prompt."""
        if not self.chunks:
            return ""
        lines = []
        for c in self.chunks:
            lines.append(
                f"[{c.source_doc}, p.{c.page}, {c.section}]: {c.text}"
            )
        return "Relevant policy knowledge (cite these sources):\n" + "\n\n".join(lines)

    @property
    def citations(self) -> list[dict]:
        """Structured citation data for UI display."""
        return [
            {
                "section": c.section,
                "page": c.page,
                "source": c.source_doc,
                "excerpt": c.text[:150] + "..." if len(c.text) > 150 else c.text,
                "score": c.score,
            }
            for c in self.chunks
        ]


# ═══════════════════════════════════════════════════════════════════════════
# Policy Store
# ═══════════════════════════════════════════════════════════════════════════


class PolicyStore:
    """RAG-powered policy retrieval with LangChain + ChromaDB.

    Attempts vector search first (requires API key for embeddings).
    Falls back to keyword search if embeddings are unavailable.

    Usage::

        store = PolicyStore()
        # Without embeddings (keyword mode)
        context = store.search("out-of-network MRI denied", policy_type="Health")

        # With embeddings (vector mode)
        store.build_vector_index(api_key="sk-...", base_url=None)
        context = store.search("out-of-network MRI denied", policy_type="Health")
    """

    def __init__(self) -> None:
        self._chunks: list[RetrievedChunk] = []
        self._vectorstore = None
        self._retrieval_method = "keyword"
        self._load_pdf_chunks()
        if not self._chunks:
            self._load_builtin_chunks()

    # ── Properties ────────────────────────────────────────────────────

    @property
    def source_document(self) -> str:
        return POLICY_PDF_NAME

    @property
    def is_pdf_backed(self) -> bool:
        return os.path.exists(POLICY_PDF_PATH)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def retrieval_method(self) -> str:
        return self._retrieval_method

    @property
    def has_vector_index(self) -> bool:
        return self._vectorstore is not None

    # ── Vector Index ──────────────────────────────────────────────────

    def build_vector_index(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> bool:
        """Build ChromaDB vector index using OpenAI embeddings.

        Returns True if successful, False if fallback to keyword.
        """
        if not api_key and not base_url:
            return False

        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_community.vectorstores import Chroma
            from langchain.schema import Document

            # Build embeddings client
            embed_kwargs = {}
            if api_key:
                embed_kwargs["api_key"] = api_key
            if base_url:
                embed_kwargs["base_url"] = base_url
                embed_kwargs["model"] = "text-embedding-3-small"
            else:
                embed_kwargs["model"] = "text-embedding-3-small"

            embeddings = OpenAIEmbeddings(**embed_kwargs)

            # Convert chunks to LangChain documents
            docs = [
                Document(
                    page_content=c.text,
                    metadata={
                        "section": c.section,
                        "page": c.page,
                        "source_doc": c.source_doc,
                        "policy_type": c.policy_type,
                    },
                )
                for c in self._chunks
            ]

            # Build in-memory ChromaDB
            self._vectorstore = Chroma.from_documents(
                documents=docs,
                embedding=embeddings,
                collection_name="policy_sections",
            )
            self._retrieval_method = "vector"
            return True

        except Exception:
            self._vectorstore = None
            self._retrieval_method = "keyword"
            return False

    # ── Search ────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        policy_type: str | None = None,
        top_k: int = 3,
    ) -> RAGContext:
        """Retrieve relevant policy chunks. Uses vector search if available."""
        if self._vectorstore is not None:
            return self._vector_search(query, policy_type, top_k)
        return self._keyword_search(query, policy_type, top_k)

    def _vector_search(
        self, query: str, policy_type: str | None, top_k: int,
    ) -> RAGContext:
        """Semantic search via ChromaDB + OpenAI embeddings."""
        filter_dict = None
        if policy_type:
            filter_dict = {"policy_type": policy_type}

        try:
            results = self._vectorstore.similarity_search_with_score(
                query, k=top_k, filter=filter_dict,
            )
        except Exception:
            # If filtered search fails (no matches), try without filter
            results = self._vectorstore.similarity_search_with_score(
                query, k=top_k,
            )

        chunks = []
        for doc, score in results:
            chunks.append(RetrievedChunk(
                text=doc.page_content,
                section=doc.metadata.get("section", "Unknown"),
                page=doc.metadata.get("page", 0),
                source_doc=doc.metadata.get("source_doc", POLICY_PDF_NAME),
                score=round(1.0 - score, 3),  # ChromaDB: lower = better
                policy_type=doc.metadata.get("policy_type", "General"),
            ))

        return RAGContext(
            chunks=chunks,
            retrieval_method="vector",
            total_chunks_in_store=len(self._chunks),
        )

    def _keyword_search(
        self, query: str, policy_type: str | None, top_k: int,
    ) -> RAGContext:
        """Keyword overlap search (zero-cost fallback)."""
        query_kw = _extract_keywords(query)
        if not query_kw:
            return RAGContext(retrieval_method="keyword", total_chunks_in_store=len(self._chunks))

        query_counts = Counter(query_kw)
        scored: list[tuple[float, RetrievedChunk]] = []

        for chunk in self._chunks:
            type_boost = 2.0 if (policy_type and chunk.policy_type == policy_type) else 1.0
            chunk_kw = _extract_keywords(f"{chunk.section} {chunk.text}")
            chunk_counts = Counter(chunk_kw)
            overlap = sum(
                min(query_counts[k], chunk_counts[k])
                for k in query_counts if k in chunk_counts
            )
            if overlap > 0:
                scored.append((overlap * type_boost, chunk))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        results = []
        for score, chunk in scored[:top_k]:
            results.append(RetrievedChunk(
                text=chunk.text,
                section=chunk.section,
                page=chunk.page,
                source_doc=chunk.source_doc,
                score=round(score, 2),
                policy_type=chunk.policy_type,
            ))

        return RAGContext(
            chunks=results,
            retrieval_method="keyword",
            total_chunks_in_store=len(self._chunks),
        )

    # ── PDF Loading (LangChain) ───────────────────────────────────────

    def _load_pdf_chunks(self) -> None:
        """Load and split the policy PDF using LangChain."""
        if not os.path.exists(POLICY_PDF_PATH):
            return

        try:
            from langchain_community.document_loaders import PyPDFLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            loader = PyPDFLoader(POLICY_PDF_PATH)
            pages = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=80,
                separators=["\n\n", "\n", ". ", " "],
            )
            docs = splitter.split_documents(pages)

            for doc in docs:
                text = doc.page_content.strip()
                if len(text) < 30:
                    continue

                page = doc.metadata.get("page", 0) + 1  # 0-indexed to 1-indexed
                section = _extract_section_name(text)
                ptype = _infer_policy_type(text)

                self._chunks.append(RetrievedChunk(
                    text=text,
                    section=section,
                    page=page,
                    source_doc=POLICY_PDF_NAME,
                    policy_type=ptype,
                ))

        except Exception:
            self._chunks.clear()

    # ── Built-In Fallback ─────────────────────────────────────────────

    def _load_builtin_chunks(self) -> None:
        """Hardcoded policy chunks (used when PDF is missing)."""
        data = [
            ("Health", "Section 1 - Definitions", 2,
             "Deductible: Amount you pay out-of-pocket before insurance pays. Silver PPO 3000: $3,000 individual / $6,000 family. Coinsurance: Your share after deductible, typically 20% in-network. Out-of-Pocket Maximum: $8,150 individual / $16,300 family."),
            ("Health", "Section 3.1 - In-Network Provider Usage", 3,
             "All non-emergency services must be obtained from in-network providers to receive full coverage benefits. The SilverShield provider directory is updated quarterly."),
            ("Health", "Section 3.2 - Out-of-Network Services", 3,
             "Out-of-network services are covered at a reduced rate under PPO plans (60% vs 80% after deductible). HMO plans do not cover out-of-network except emergencies."),
            ("Health", "Section 3.3 - Network Gap Exceptions", 3,
             "If no in-network provider is available within 50 miles, SilverShield will authorize out-of-network coverage at in-network rates. Call 1-800-555-0199. Valid for 90 days."),
            ("Health", "Section 3.4 - Emergency Services", 3,
             "Emergency room visits covered at in-network rates regardless of facility network status."),
            ("Health", "Section 5.1 - Prior Authorization", 4,
             "Required for: advanced imaging (MRI, CT, PET), specialty referrals, elective procedures, outpatient surgery, DME over $500. Submit at least 5 business days before scheduled date."),
            ("Health", "Section 5.3 - Missing Authorization", 4,
             "Claims missing required prior authorization may be denied in full. Retroactive authorization possible in emergencies within 48 hours."),
            ("Health", "Section 6.1 - Annual Deductible", 4,
             "Resets January 1. All covered services except preventive care count toward deductible."),
            ("Health", "Section 9.1 - Appeals Process", 6,
             "Members may appeal any denial within 180 days. Level 1: senior examiner (30 days). Level 2: Medical Director. External review available after internal appeals."),
            ("Auto", "Section 10.1 - Collision Coverage", 6,
             "Covers damage from collision regardless of fault. Deductible options: $250, $500, $1,000. Excludes mechanical breakdown."),
            ("Auto", "Section 10.2 - Comprehensive Coverage", 6,
             "Covers non-collision damage: theft, vandalism, natural disasters, falling objects, animal strikes."),
            ("Auto", "Section 10.3 - Aftermarket Modifications", 6,
             "Custom parts ONLY covered if declared on policy with endorsement. Undeclared modifications excluded. Must notify within 30 days of install."),
            ("Home", "Section 11.2 - Water Damage", 7,
             "COVERED: Sudden and accidental from burst pipes, failed appliances. EXCLUDED: Gradual leaks, mold, flood, sewer backup (unless endorsed)."),
            ("Home", "Section 11.3 - Additional Living Expenses", 7,
             "Covers temporary housing, meals, transport when home is uninhabitable. Limited to 20% of dwelling coverage, max 12 months."),
            ("Home", "Section 11.4 - Personal Property", 7,
             "Replacement cost for belongings. Sub-limits: jewelry $1,500, electronics $2,500."),
            ("Travel", "Section 12.1 - Trip Cancellation", 7,
             "Covers non-refundable costs for: illness, death in family, natural disaster at destination, terrorism, job loss."),
            ("Travel", "Section 12.2 - Documentation", 7,
             "Medical claims need physician statement within 30 days. File all claims within 90 days with receipts."),
            ("Travel", "Section 12.3 - Trip Interruption", 7,
             "Covers unused expenses pro-rata, additional transport home, up to $200/day accommodation."),
        ]
        for ptype, section, page, text in data:
            self._chunks.append(RetrievedChunk(
                text=text,
                section=section,
                page=page,
                source_doc=POLICY_PDF_NAME,
                policy_type=ptype,
            ))


# ═══════════════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════════════


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return [w for w in words if w not in _STOP_WORDS and len(w) > 2]


def _extract_section_name(text: str) -> str:
    """Try to extract a section header from chunk text."""
    match = re.match(r"^(?:Section\s+)?(\d+(?:\.\d+)?)\s*[-:]\s*(.+?)(?:\n|$)", text)
    if match:
        return f"Section {match.group(1)} - {match.group(2).strip()}"
    match = re.match(r"^(\d+\.\d+)\s+(.+?)(?:\n|$)", text)
    if match:
        return f"Section {match.group(1)} - {match.group(2).strip()}"
    return "Policy Content"


def _infer_policy_type(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["health", "medical", "imaging", "deductible",
                                 "coinsurance", "copay", "provider", "network",
                                 "authorization", "hmo", "ppo"]):
        return "Health"
    if any(w in lower for w in ["auto", "collision", "vehicle", "comprehensive",
                                 "aftermarket", "liability"]):
        return "Auto"
    if any(w in lower for w in ["home", "dwelling", "water damage", "peril",
                                 "living expenses", "personal property"]):
        return "Home"
    if any(w in lower for w in ["travel", "trip", "cancellation", "interruption"]):
        return "Travel"
    if any(w in lower for w in ["life", "beneficiary", "contestability", "death benefit"]):
        return "Life"
    return "General"
