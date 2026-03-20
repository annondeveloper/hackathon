# ClaimClear AI — Design Decisions

## 1. Dual Implementation Strategy

**Decision**: Build the same product twice — a rapid Streamlit prototype and a production-grade Rust + React version.

**Rationale**:
- The Streamlit version proves the concept fast and is immediately demonstrable
- The Rust + React version shows production readiness and engineering depth
- Having both demonstrates versatility and pragmatic decision-making
- The AI prompt engineering is shared between both, validating it independently

---

## 2. OpenAI GPT-4o as the AI Engine

**Decision**: Use OpenAI's GPT-4o (with GPT-4o-mini as a cost-effective fallback).

**Alternatives considered**:
- Claude (Anthropic) — excellent but less ubiquitous SDK support
- Llama 3 (local) — no API costs but requires GPU infrastructure
- Fine-tuned model — better accuracy but high upfront cost

**Rationale**:
- GPT-4o excels at instruction-following and structured output
- Widely available, well-documented SDK
- Cost-effective at ~$2.50/1M input tokens
- GPT-4o-mini option reduces cost 10x for high-volume use

---

## 3. Delimiter-Based Output Parsing

**Decision**: Use `---GLOSSARY---` as a text delimiter rather than JSON output.

**Alternatives considered**:
- JSON mode — structured but harder for the model to produce natural text
- Function calling — adds complexity for a text-generation task
- Multiple API calls — one for explanation, one for glossary

**Rationale**:
- Natural text generation produces better explanations
- Single delimiter is simple, reliable, and easy to parse
- One API call instead of two reduces latency and cost
- The model consistently produces this format with clear instructions

---

## 4. Demo Mode Without API Key

**Decision**: Include a fully functional demo mode with pre-built sample explanations.

**Rationale**:
- Enables demonstration without exposing API keys
- Judges/reviewers can immediately try the app
- Reduces friction for first-time users
- Sample explanations showcase the quality of output

---

## 5. Rust for Backend (Cutting-Edge Version)

**Decision**: Use Rust with Axum instead of Node.js, Go, or Python FastAPI.

**Alternatives considered**:
- Node.js + Express — familiar but single-threaded, high memory
- Go + Gin — fast but less type-safe than Rust
- Python + FastAPI — easy but slower, higher memory usage

**Rationale**:
- **Performance**: Rust's zero-cost abstractions and no garbage collector mean consistently low latency (~1ms overhead per request vs ~5-15ms for Node/Python)
- **Memory**: ~10MB footprint vs ~100MB+ for Node/Python
- **Safety**: Compiler catches entire classes of bugs (null pointer, data races)
- **Axum**: Built on Tokio (battle-tested async runtime), excellent middleware ecosystem
- **Signal**: Using Rust signals engineering sophistication in a hackathon context

---

## 6. React + Tailwind for Frontend

**Decision**: React 18 with TypeScript and Tailwind CSS via Vite.

**Alternatives considered**:
- SvelteKit — smaller bundle but smaller ecosystem
- Vue 3 — good but React has broader adoption
- Vanilla HTML/CSS — simpler but slower to build complex UI

**Rationale**:
- **React**: Component model perfect for form → result flow
- **TypeScript**: Type safety catches bugs before runtime, matches Rust's philosophy
- **Tailwind**: Utility-first CSS enables rapid, consistent styling without CSS files
- **Vite**: Sub-100ms HMR, optimized production builds

---

## 7. Tone and Reading Level as Parameters

**Decision**: Let users control explanation tone (Simple/Professional/Technical) and reading level (Basic/Intermediate/Advanced).

**Rationale**:
- Different customers have different comprehension levels
- Customer service reps can tailor output per customer
- A single prompt handles all variations (no separate prompts per tone)
- Demonstrates personalization capability

---

## 8. Comprehension Score as a Metric

**Decision**: Display a comprehension score (currently simulated, production would use readability algorithms).

**Rationale**:
- Directly maps to the success metric (customer comprehension score)
- Provides quantifiable evidence of explanation quality
- Production version would use Flesch-Kincaid, Gunning Fog, or similar
- Visual progress bar makes the metric immediately understandable

---

## 9. No Database Layer

**Decision**: Stateless architecture with no persistent storage.

**Rationale**:
- Claim data comes from existing systems (ERP, claims management)
- Generated explanations are transient (can be regenerated)
- Avoids PII storage compliance issues
- Simplifies deployment and reduces attack surface
- In production, logging/analytics would go to existing data infrastructure

---

## 10. Glossary Auto-Extraction

**Decision**: Have the AI model both generate the explanation AND extract key terms with definitions.

**Alternatives considered**:
- Separate NLP pipeline for term extraction
- Pre-built glossary database
- Manual term tagging

**Rationale**:
- AI naturally identifies which terms need explanation in context
- No separate infrastructure needed
- Definitions are contextual, not generic dictionary entries
- Single API call handles both tasks efficiently
