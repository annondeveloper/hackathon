# ClaimClear AI — Architecture

## 1. System Overview

ClaimClear AI is a Python application that uses a multi-step agentic AI
pipeline to generate clear, personalized explanations of insurance claim
decisions. It combines RAG (Retrieval-Augmented Generation), self-evaluation,
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
│   │  (input)      │   │  (settings)  │   │  (output)    │   │
│   └──────┬───────┘   └──────────────┘   └──────▲───────┘   │
│          │                                      │            │
│   ┌──────▼──────────────────────────────────────┴───────┐   │
│   │              ClaimExplanationPipeline                 │   │
│   │                                                      │   │
│   │  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌───────┐ │   │
│   │  │ Analyze │──▶│Generate │──▶│ Evaluate │──▶│Refine │ │   │
│   │  └─────────┘  └────┬────┘  └──────────┘  └───────┘ │   │
│   │                     │                                │   │
│   │              ┌──────▼──────┐                         │   │
│   │              │ PolicyStore  │                         │   │
│   │              │ (RAG)        │                         │   │
│   │              └─────────────┘                         │   │
│   └──────────────────────────────────────────────────────┘   │
│          │                                                    │
└──────────┼────────────────────────────────────────────────────┘
           │ HTTPS
┌──────────▼──────────┐
│   OpenAI API         │
│   (gpt-4o-mini)      │
└─────────────────────┘
```

---

## 2. Component Details

### 2.1 Streamlit UI (`app.py`)

| Responsibility | Details |
|---------------|---------|
| Claim input | Two-column form: ID, name, type, amount, decision, reason, terms |
| Sidebar settings | API key (password field), model selector, tone, reading level |
| Sample loading | Dropdown with 4 pre-built claims for quick testing |
| Pipeline execution | Calls `ClaimExplanationPipeline.run()` with stage callbacks |
| Results display | Explanation card, 4 quality metric gauges, glossary accordion |
| Pipeline transparency | Expandable sections showing each stage's output |
| Export | Download as `.txt`, copy to clipboard |
| Demo mode | Pre-built response when no API key is configured |

### 2.2 Agentic Pipeline (`pipeline.py`)

The pipeline is a sequential chain of four specialized LLM calls:

| Stage | Input | Output | Purpose |
|-------|-------|--------|---------|
| **Analyze** | Claim data | `AnalysisResult` (complexity, key factors, jargon) | Chain-of-thought reasoning before generation |
| **Generate** | Claim + Analysis + RAG context + Few-shot | Explanation + glossary | Core explanation generation |
| **Evaluate** | Claim + Explanation | `EvaluationResult` (4 scores + issues) | Quality gate |
| **Refine** | Explanation + Evaluation feedback | Improved explanation | Only runs if score < 7/10 |

Each stage uses:
- **Structured Output** — `response_format: {"type": "json_object"}`
- **Low temperature** — `0.3` for deterministic, consistent results
- **Token cap** — `max_tokens: 800` to prevent verbose responses

### 2.3 Policy Store (`policy_store.py`)

RAG-style knowledge retrieval:

| Aspect | Details |
|--------|---------|
| Storage | In-memory list of `PolicySection` dataclasses |
| Content | 20 policy sections across 5 insurance types |
| Retrieval | Keyword overlap scoring with policy-type boosting |
| Integration | Called between Analyze and Generate stages |
| Purpose | Ground explanations in real policy knowledge |

### 2.4 Sample Data (`sample_data.py`)

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
Stage 1: _analyze(claim) ────────────────────────► OpenAI API
    │                                                    │
    ▼                                                    ▼
AnalysisResult (complexity, key_factors, jargon)   ~200 tokens
    │
    ▼
_retrieve_policy_context(claim) ──────► PolicyStore
    │                                       │
    ▼                                       ▼
RAG context string                    Top-3 matching sections
    │
    ▼
Stage 2: _generate(claim, analysis, rag_context) ─► OpenAI API
    │   + Few-shot example injected                      │
    ▼                                                    ▼
(explanation, glossary)                            ~600 tokens
    │
    ▼
Stage 3: _evaluate(claim, explanation) ───────────► OpenAI API
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
Stage 4: _refine(claim, explanation, evaluation) ──► OpenAI API
    │                                                     │
    ▼                                                     ▼
Improved (explanation, glossary)                    ~500 tokens
    │
    ▼
Return PipelineResult
```

**Typical token usage:** ~1,100 tokens (3 stages, no refinement needed)
**With refinement:** ~1,600 tokens (4 stages)

---

## 4. LLM Integration

### Request Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `model` | `gpt-4o-mini` | Best cost/quality for structured output |
| `temperature` | `0.3` | Deterministic, consistent responses |
| `max_tokens` | `800` | Prevents verbose output |
| `response_format` | `{"type": "json_object"}` | Guaranteed valid JSON |

### Prompt Strategy

- **System prompts** are compact (< 100 tokens each)
- **User prompts** include only essential data
- **Few-shot example** is injected only in the Generate stage
- **RAG context** is appended to the user prompt when available
- Each stage has a dedicated system prompt focused on one task

---

## 5. Security

| Concern | Mitigation |
|---------|-----------|
| API key exposure | Entered via password field; held in memory only; never logged or persisted |
| Prompt injection | System prompts are isolated; user input is structured, not free-text |
| PII handling | No database; claim data is transient in Streamlit session state |
| Output safety | Explanations are text-only; HTML is sanitized by Streamlit |

---

## 6. Production Upgrade Path

| Current (Prototype) | Production |
|--------------------|-----------|
| In-memory PolicyStore | Vector DB (Pinecone/Chroma) with embeddings |
| Keyword retrieval | Semantic search via `text-embedding-3-small` |
| Streamlit UI | React/Next.js frontend |
| Single process | FastAPI backend + async workers |
| No auth | OAuth 2.0 / SSO |
| No caching | Redis cache for repeated claim patterns |
| No monitoring | OpenTelemetry + LLM observability (LangSmith/Langfuse) |
