# ClaimClear AI — Architecture

## 1. System Overview

ClaimClear AI is a Python application that uses a multi-step agentic AI
pipeline to generate clear, personalized explanations of insurance claim
decisions. It combines LangChain RAG (PDF document grounding), self-evaluation,
and conditional refinement to produce high-quality output.

```
┌─────────────────────────────────────────────────────────────┐
│                   User (Browser)                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (localhost:8501)
┌──────────────────────────▼──────────────────────────────────┐
│                  Streamlit Process                            │
│                                                              │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│   │  Claim Form   │   │  Sidebar     │   │  Results     │   │
│   │  (input)      │   │  (settings)  │   │  + RAG Cites │   │
│   └──────┬───────┘   └──────────────┘   └──────▲───────┘   │
│          │                                      │            │
│   ┌──────▼──────────────────────────────────────┴───────┐   │
│   │              ClaimExplanationPipeline                 │   │
│   │                                                      │   │
│   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────┐      │   │
│   │  │Analyze │─▶│Retrieve│─▶│Generate│─▶│Eval. │──┐   │   │
│   │  └────────┘  └───┬────┘  └────────┘  └──────┘  │   │   │
│   │                   │                        ┌────▼─┐ │   │
│   │            ┌──────▼──────┐                 │Refine│ │   │
│   │            │ PolicyStore  │                 └──────┘ │   │
│   │            │ (LangChain)  │                          │   │
│   │            └──────┬──────┘                          │   │
│   │                   │                                  │   │
│   │            ┌──────▼──────┐                          │   │
│   │            │ ChromaDB /   │                          │   │
│   │            │ Keyword      │                          │   │
│   │            └──────┬──────┘                          │   │
│   │                   │                                  │   │
│   │            ┌──────▼──────┐                          │   │
│   │            │ Policy PDF   │                          │   │
│   │            │ (8 pages)    │                          │   │
│   │            └─────────────┘                          │   │
│   └──────────────────────────────────────────────────────┘   │
│          │                                                    │
└──────────┼────────────────────────────────────────────────────┘
           │ HTTPS
┌──────────▼──────────┐
│   LLM Provider       │
│   - OpenAI API       │
│   - TCS GenAI Lab    │
│   - Custom Endpoint  │
└─────────────────────┘
```

---

## 2. Component Details

### 2.1 Streamlit UI (`app.py`)

| Responsibility | Details |
|---------------|---------|
| Claim input | Two-column form: ID, name, type, amount, decision, reason, terms |
| Sidebar settings | Model selector, API key, custom URL, tone, reading level |
| Model selection | OpenAI GPT-4o-mini, GPT-4o, TCS GenAI Lab, or custom endpoint |
| Sample loading | Dropdown with 4 pre-built claims for quick testing |
| Pipeline execution | Calls `ClaimExplanationPipeline.run()` with stage callbacks |
| Results display | Explanation card, 4 quality metric gauges, glossary accordion |
| RAG citations | Source badges showing PDF name, page number, section, excerpt text |
| RAG method badge | Shows whether vector search or keyword fallback was used |
| Policy PDF | Download button in sidebar for the source policy document |
| Pipeline transparency | Expandable sections showing each stage's output |
| Export | Download as `.txt`, copy to clipboard |
| Demo mode | Pre-built response with sample RAG citations when no API key |

### 2.2 Agentic Pipeline (`pipeline.py`)

The pipeline is a sequential chain of specialized LLM calls with RAG retrieval:

| Stage | Input | Output | Purpose |
|-------|-------|--------|---------|
| **Analyze** | Claim data | `AnalysisResult` (complexity, key factors, jargon) | Chain-of-thought reasoning before generation |
| **Retrieve** | Claim query | `RAGContext` (top-3 chunks with page numbers) | LangChain RAG from policy PDF |
| **Generate** | Claim + Analysis + RAG context + Few-shot | Explanation + glossary | Core explanation with PDF citations |
| **Evaluate** | Claim + Explanation | `EvaluationResult` (4 scores + issues) | Quality gate |
| **Refine** | Explanation + Evaluation feedback | Improved explanation | Only runs if score < 7/10 |

Each LLM stage uses:
- **Structured Output** — `response_format: {"type": "json_object"}`
- **Low temperature** — `0.3` for deterministic, consistent results
- **Token cap** — `max_tokens: 800` to prevent verbose responses

### 2.3 Policy Store (`policy_store.py`) — LangChain RAG

The PolicyStore implements a full RAG pipeline with dual retrieval:

| Aspect | Details |
|--------|---------|
| Document Source | `docs/SilverShield_Master_Policy.pdf` (8 pages, 12 sections) |
| PDF Ingestion | LangChain `PyPDFLoader` extracts text page by page |
| Text Splitting | `RecursiveCharacterTextSplitter` (500 chars, 80 overlap) |
| Vector Store | ChromaDB in-memory collection with OpenAI `text-embedding-3-small` |
| Keyword Fallback | TF-IDF keyword matching when no API key (zero-cost) |
| Policy Type Boost | 2x score boost when chunk matches the claim's policy type |
| Citation Data | Every chunk carries: section name, page number, source filename |
| Output | `RAGContext` with structured citations for UI display |

**Retrieval modes:**

| Mode | When Used | How It Works |
|------|-----------|-------------|
| **Vector** | API key available | ChromaDB similarity search with OpenAI embeddings |
| **Keyword** | No API key / fallback | Token overlap scoring with policy-type boosting |

### 2.4 Policy PDF (`create_policy_pdf.py`)

The `SilverShield_Master_Policy.pdf` is a realistic 8-page insurance policy:

| Section | Page | Content |
|---------|------|---------|
| Definitions and Key Terms | 2 | Deductible, coinsurance, copayment, OOP max, etc. |
| Coverage Overview | 2 | Health plan tiers (Silver/Gold/Platinum), multi-line discount |
| Network and Provider Requirements | 3 | In-network, out-of-network, gap exceptions, emergency |
| Covered Perils and Services | 3 | Health services, home perils |
| Prior Authorization | 4 | Required services, process, consequences |
| Cost Sharing and Deductibles | 4 | Annual deductible, coinsurance rates by plan |
| Exclusions and Limitations | 5 | General, homeowners, auto exclusions |
| Claims Filing Procedures | 5 | How to file, documentation, timeline |
| Appeals and Grievance Process | 6 | Internal appeals (Level 1/2), external review |
| Auto Insurance Provisions | 6 | Collision, comprehensive, aftermarket mods |
| Homeowners Insurance Provisions | 7 | Dwelling, water damage, ALE, personal property |
| Travel Insurance Provisions | 7 | Trip cancellation, documentation, interruption |

### 2.5 Sample Data (`sample_data.py`)

Four realistic insurance claim scenarios:

| Sample | Type | Decision | Amount |
|--------|------|----------|--------|
| Denied Health | Health | Denied | $4,750 |
| Partial Auto | Auto | Partially Approved | $12,300 |
| Approved Home | Home | Approved | $28,500 |
| Under Review Travel | Travel | Under Review | $3,200 |

---

## 3. Data Flow

```
User fills form
    │
    ▼
ClaimInput dataclass created
    │
    ▼
Stage 1: _analyze(claim) ────────────────────────► LLM API
    │                                                    │
    ▼                                                    ▼
AnalysisResult (complexity, key_factors, jargon)   ~200 tokens
    │
    ▼
Stage 2: _retrieve_policy_context(claim)
    │
    ├── LangChain PyPDFLoader ──► Parse PDF pages
    ├── RecursiveCharacterTextSplitter ──► 500-char chunks
    ├── ChromaDB (if embeddings available)
    │   └── similarity_search_with_score(query, k=3)
    │
    └── Keyword fallback (if no embeddings)
        └── TF-IDF overlap + policy_type boost
    │
    ▼
RAGContext (top-3 chunks with page numbers + scores)
    │
    ▼
Stage 3: _generate(claim, analysis, rag_context) ─► LLM API
    │   + Few-shot example injected                      │
    │   + RAG citations with page refs                   │
    ▼                                                    ▼
(explanation, glossary)                            ~600 tokens
    │
    ▼
Stage 4: _evaluate(claim, explanation) ───────────► LLM API
    │                                                    │
    ▼                                                    ▼
EvaluationResult (4 scores, issues, suggestions)   ~300 tokens
    │
    ▼
overall_score < 7? ──── No ──► Return PipelineResult
    │
    Yes
    │
    ▼
Stage 5: _refine(claim, explanation, evaluation) ──► LLM API
    │                                                     │
    ▼                                                     ▼
Improved (explanation, glossary)                    ~500 tokens
    │
    ▼
Return PipelineResult (with RAGContext for UI citations)
```

**Typical token usage:** ~1,100 tokens (4 stages, no refinement needed)
**With refinement:** ~1,600 tokens (5 stages)

---

## 4. LLM Integration

### Multi-Model Support

| Provider | Model ID | Base URL | API Key Required |
|----------|----------|----------|-----------------|
| OpenAI | `gpt-4o-mini` | Default | Yes |
| OpenAI | `gpt-4o` | Default | Yes |
| TCS GenAI Lab | `azure/genailab-maas-gpt-4o` | `https://genailab.tcs.in` | No |
| Custom | Any | User-provided | Depends |

### Request Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `model` | Configurable | User selects in sidebar |
| `temperature` | `0.3` | Deterministic, consistent responses |
| `max_tokens` | `800` | Prevents verbose output |
| `response_format` | `{"type": "json_object"}` | Guaranteed valid JSON |

### Prompt Strategy

- **System prompts** are compact (< 100 tokens each)
- **User prompts** include only essential data
- **Few-shot example** is injected only in the Generate stage, includes PDF page citations
- **RAG context** is appended with source format: `[filename, p.N, Section X.Y]: text`
- Each stage has a dedicated system prompt focused on one task

---

## 5. RAG Architecture

```
┌────────────────────────────────────────────────┐
│ SilverShield_Master_Policy.pdf (8 pages)        │
│ ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌──┐│
│ │ p1 ││ p2 ││ p3 ││ p4 ││ p5 ││ p6 ││ p7 ││p8││
│ └────┘└────┘└────┘└────┘└────┘└────┘└────┘└──┘│
└────────────────┬───────────────────────────────┘
                 │
          ┌──────▼──────┐
          │ PyPDFLoader  │  LangChain document loader
          └──────┬──────┘
                 │
    ┌────────────▼────────────┐
    │ RecursiveCharacterText  │  500 chars, 80 overlap
    │ Splitter                │
    └────────────┬────────────┘
                 │
          ~18-25 chunks (each with page metadata)
                 │
         ┌───────┴────────┐
         │                │
  ┌──────▼──────┐  ┌──────▼──────┐
  │  ChromaDB    │  │  Keyword     │
  │  + OpenAI    │  │  Fallback    │
  │  Embeddings  │  │  (TF-IDF)   │
  └──────┬──────┘  └──────┬──────┘
         │                │
         └───────┬────────┘
                 │
          ┌──────▼──────┐
          │  RAGContext   │
          │  - chunks[]   │
          │  - citations  │
          │  - method     │
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │  LLM Prompt  │  "[PDF, p.3, Section 3.2]: ..."
          │  Injection   │
          └─────────────┘
```

---

## 6. Security

| Concern | Mitigation |
|---------|-----------|
| API key exposure | Entered via password field; held in memory only; never logged or persisted |
| Prompt injection | System prompts are isolated; user input is structured, not free-text |
| PII handling | No database; claim data is transient in Streamlit session state |
| Output safety | Explanations are text-only; HTML is sanitized by Streamlit |
| PDF handling | Policy PDF is local, not user-uploaded; no path traversal risk |

---

## 7. Production Upgrade Path

| Current (Prototype) | Production |
|--------------------|-----------|
| LangChain + ChromaDB in-memory | Persistent ChromaDB or Pinecone with embeddings |
| PyPDFLoader for single PDF | Multi-document ingestion pipeline |
| Keyword fallback retrieval | Always vector search with embedding cache |
| Streamlit UI | React/Next.js frontend |
| Single process | FastAPI backend + async workers |
| No auth | OAuth 2.0 / SSO |
| No caching | Redis cache for repeated claim patterns |
| No monitoring | OpenTelemetry + LLM observability (LangSmith/Langfuse) |
