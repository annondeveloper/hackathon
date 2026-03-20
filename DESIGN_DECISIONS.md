# ClaimClear AI — Design Decisions

This document explains the rationale behind each major technical and
architectural choice in ClaimClear AI.

---

## 1. Agentic Pipeline Architecture

**Decision:** Use a 5-stage sequential pipeline (Analyze -> Retrieve -> Generate ->
Evaluate -> Refine) instead of a single LLM call.

**Alternatives considered:**
- Single prompt with all instructions -> simpler but less accurate
- Parallel multi-agent -> higher complexity, harder to debug
- Pure LangGraph agent -> more framework overhead

**Rationale:**
- Each stage has a focused, well-defined task (single responsibility)
- Analysis stage produces chain-of-thought reasoning that improves generation
- RAG retrieval is a separate, observable stage with its own metrics
- Self-evaluation catches errors that a single call would miss
- Conditional refinement saves tokens when output is already good
- Easy to extend: add stages (e.g., compliance check) without refactoring

---

## 2. LangChain RAG with Policy PDF

**Decision:** Use LangChain (PyPDFLoader + RecursiveCharacterTextSplitter +
ChromaDB) to ingest a real insurance policy PDF and retrieve relevant sections
with page-level citations.

**Alternatives considered:**
- No RAG (rely on LLM's training data) -> high hallucination risk
- Hardcoded text snippets only -> doesn't demonstrate real document ingestion
- Full production vector DB (Pinecone) -> requires hosted service, more setup
- Fine-tuned model on policy documents -> expensive, inflexible

**Rationale:**
- Insurance policy terms are domain-specific; LLMs frequently hallucinate
  section numbers and coverage details
- A real PDF demonstrates production-ready RAG (not just toy hardcoded text)
- LangChain provides the standard PDF -> chunks -> embeddings -> retrieval pipeline
- ChromaDB runs in-memory with zero infrastructure (perfect for hackathon)
- Page-level citations build user trust ("this came from page 3 of your policy")
- Keyword fallback ensures the app works even without an API key

---

## 3. Dual Retrieval (Vector + Keyword)

**Decision:** Support both ChromaDB vector search (when embeddings are available)
and keyword-based fallback (zero-cost, always available).

**Alternatives considered:**
- Vector only -> breaks without API key
- Keyword only -> misses semantic matches
- Embedding-free alternatives (BM25) -> adds another dependency

**Rationale:**
- Demo mode must work without any API key (judges need instant access)
- Vector search provides much better semantic matching (e.g., "MRI denied" matches
  "prior authorization for advanced imaging")
- Keyword fallback is fast (< 1ms) and still effective for direct term matches
- The UI clearly shows which mode is active (vector badge vs keyword badge)
- Seamless upgrade: add API key -> automatic switch to vector search

---

## 4. Real Policy PDF Document

**Decision:** Generate a realistic 8-page insurance policy PDF
(`SilverShield_Master_Policy.pdf`) with proper sections, page numbers, and
professional formatting.

**Alternatives considered:**
- Use a public domain insurance document -> legal uncertainty, messy formatting
- Text file instead of PDF -> doesn't demonstrate PDF ingestion
- Markdown/HTML policy document -> not realistic for the domain

**Rationale:**
- Insurance companies work with PDF policy documents — this is authentic
- 8 pages with 12 sections covers Health, Auto, Home, Travel realistically
- Generated via `create_policy_pdf.py` so it's reproducible and customizable
- Page numbers in the PDF match the citations in the generated explanations
- The PDF is downloadable in the sidebar so users can verify citations manually
- Professional formatting (headers, table of contents, numbered sections) adds credibility

---

## 5. Self-Evaluation with Conditional Refinement

**Decision:** Have the LLM evaluate its own output across 4 dimensions
(accuracy, empathy, readability, completeness) and only refine when the
score falls below 7/10.

**Alternatives considered:**
- Always refine -> doubles cost for already-good output
- Never refine -> misses quality issues
- Human-in-the-loop -> not feasible at scale
- Rule-based checks (regex, readability formulas) -> can't assess empathy

**Rationale:**
- Self-evaluation adds ~300 tokens but catches real issues
- Conditional refinement (only when needed) avoids wasting tokens
- Threshold of 7/10 balances quality with cost efficiency
- Scoring dimensions map directly to the product's success metrics
- Issues and suggestions provide actionable feedback for the refinement stage

---

## 6. Structured Outputs (JSON Mode)

**Decision:** Use OpenAI's `response_format: {"type": "json_object"}` for
all LLM calls instead of delimiter-based text parsing.

**Alternatives considered:**
- `---GLOSSARY---` delimiter parsing -> fragile, model sometimes omits it
- Function calling / tool use -> more complex, not needed for this use case
- Free-text parsing with regex -> unreliable

**Rationale:**
- JSON mode guarantees valid JSON — zero parsing failures
- Eliminates verbose "you MUST reply with valid JSON" prompt instructions
- Saves ~50 tokens per system prompt
- Structured output makes each stage's data contract explicit
- Compatible with all OpenAI-compatible models that support JSON mode

---

## 7. Few-Shot Prompting with PDF Citations

**Decision:** Include one gold-standard example (user + assistant messages)
in the Generate stage that demonstrates proper PDF citation format.

**Alternatives considered:**
- Zero-shot (no examples) -> inconsistent formatting, no citation pattern
- Multiple examples -> higher token cost
- Examples in all stages -> wasteful for analysis/evaluation

**Rationale:**
- One example is sufficient to anchor output format, tone, and citation style
- The example demonstrates: greeting, bold headers, bullet lists, next steps,
  and crucially — how to cite policy sections with page numbers
- Only used in generation (the most variable stage); analysis and evaluation
  are constrained enough by their JSON schemas
- Total cost: ~200 tokens for the example pair — a good quality/cost tradeoff

---

## 8. Multi-Model Support

**Decision:** Support OpenAI GPT-4o/mini, TCS GenAI Lab, and any
OpenAI-compatible endpoint via a configurable `MODEL_PROVIDERS` registry.

**Alternatives considered:**
- OpenAI only -> limits deployment options
- Model-agnostic abstraction (LiteLLM) -> adds another dependency
- LangChain LLM wrappers -> heavier, more complex

**Rationale:**
- TCS GenAI Lab uses an OpenAI-compatible API (no code changes needed)
- `get_openai_client()` factory handles all provider configurations
- Custom base URL field in sidebar supports any endpoint (Azure, local LLMs)
- No API key required for whitelisted/firewalled endpoints like TCS GenAI Lab
- Users see clear labels in the dropdown (not raw model IDs)

---

## 9. GPT-4o-mini as Default Model

**Decision:** Default to `gpt-4o-mini` with `gpt-4o` as an option.

**Alternatives considered:**
- GPT-4o only -> better quality but 10x more expensive
- Claude (Anthropic) -> excellent quality, different SDK
- Llama 3 (local) -> no API costs but requires GPU infrastructure
- Fine-tuned model -> best accuracy but high upfront cost and maintenance

**Rationale:**
- GPT-4o-mini handles structured JSON output reliably at ~$0.15/1M tokens
- The agentic pipeline compensates for any quality gap vs. GPT-4o
  (analysis + evaluation + refinement improve output quality by ~20%)
- Users can switch to GPT-4o in the sidebar for higher-stakes claims
- Cost per claim: ~$0.002 with mini, ~$0.02 with 4o

---

## 10. Demo Mode Without API Key

**Decision:** Include a fully functional demo mode with pre-built pipeline
results including realistic RAG citations from the policy PDF.

**Rationale:**
- Enables instant demonstration without any setup
- Judges/reviewers can try the app immediately
- Demo data shows the full pipeline output format including RAG citations
- Pre-built quality scores demonstrate the evaluation feature
- RAG citations reference real pages in the downloadable PDF
- Reduces barrier to first impression

---

## 11. No Database / Stateless Architecture

**Decision:** No persistent storage. Claim data lives in Streamlit session
state during the browser session only.

**Alternatives considered:**
- SQLite for claim history -> adds complexity, PII concerns
- Redis for caching -> useful at scale, overkill for prototype

**Rationale:**
- Claim data comes from existing systems (ERP, claims management)
- Generated explanations are transient and can be regenerated
- Avoids PII storage and compliance issues entirely
- Simplifies deployment to a single process
- Production version would use existing enterprise data infrastructure

---

## 12. Token-Efficient Prompt Design

**Decision:** Keep all system prompts under 100 tokens and minimize
redundancy between stages.

**Design principles:**
- Each system prompt defines the role and output format — nothing else
- No instructional overlap between stages (analyze doesn't generate,
  evaluate doesn't refine)
- User prompts use compact key-value format instead of prose
- RAG context uses structured citation format: `[file, p.N, section]: text`

**Token savings:**
| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Analyze system prompt | ~80 tokens | ~50 tokens | 38% |
| Generate system prompt | ~200 tokens | ~90 tokens | 55% |
| Evaluate system prompt | ~100 tokens | ~60 tokens | 40% |
| Refine system prompt | ~100 tokens | ~55 tokens | 45% |
| **Total per pipeline run** | **~480** | **~255** | **47%** |

---

## 13. Streamlit for UI

**Decision:** Use Streamlit instead of a custom frontend.

**Alternatives considered:**
- React + FastAPI -> more flexible but much more code
- Gradio -> simpler but less customizable
- Flask + templates -> more control but slower to build

**Rationale:**
- Streamlit handles form inputs, state management, and layout in pure Python
- Custom CSS support for branded look and feel (theme-aware dark/light mode)
- Session state persists results across reruns
- Sidebar provides clean separation of settings from main content
- One `pip install` — no Node.js, no build step, no separate frontend server
- Ideal for prototyping and demos; production would migrate to React
