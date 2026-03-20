# ClaimClear AI — Architecture Document

## 1. System Overview

ClaimClear AI is a GenAI-powered assistant that generates plain-language explanations of insurance claim decisions. The system accepts structured claim data and produces personalized, jargon-free explanations tailored to individual customers.

Two implementations exist:
1. **Streamlit Prototype** — rapid development, single-process Python app
2. **Rust + React Production** — high-performance, scalable microservice architecture

---

## 2. Streamlit Prototype Architecture

```
┌─────────────────────────────────────────┐
│            Streamlit Process            │
│                                         │
│  ┌──────────┐  ┌────────────────────┐  │
│  │ UI Layer │──│ Session State Mgmt │  │
│  └────┬─────┘  └────────────────────┘  │
│       │                                 │
│  ┌────▼──────────────────────────────┐ │
│  │      Prompt Engineering Layer     │ │
│  │  - System prompt construction     │ │
│  │  - User context assembly          │ │
│  │  - Response parsing (glossary)    │ │
│  └────┬──────────────────────────────┘ │
│       │                                 │
│  ┌────▼──────────────────────────────┐ │
│  │      OpenAI SDK Integration       │ │
│  │  - Chat completions API           │ │
│  │  - Model selection (4o / 4o-mini) │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Data Flow
1. User enters claim details in the form
2. System constructs a structured prompt with claim context + tone/level preferences
3. OpenAI API generates explanation with embedded glossary
4. Response is parsed: explanation body separated from glossary section
5. Results rendered with metrics (comprehension score, time saved)

### Key Design Choices
- **Single-file app**: Minimal complexity for rapid prototyping
- **Demo mode**: Pre-built responses allow demonstration without API keys
- **Delimiter-based parsing**: `---GLOSSARY---` marker enables reliable extraction
- **Session state**: Maintains results across Streamlit reruns

---

## 3. Rust + React Production Architecture

```
┌────────────────────────┐     ┌─────────────────────────┐
│    React Frontend      │     │     Rust Backend         │
│    (Vite + TS)         │     │     (Axum)               │
│                        │     │                           │
│  ┌──────────────────┐  │     │  ┌─────────────────────┐ │
│  │ ClaimForm        │  │     │  │ Route Handlers      │ │
│  │ Component        │──┼─────┼─▶│ - POST /api/explain │ │
│  └──────────────────┘  │     │  │ - GET /api/health   │ │
│                        │ HTTP│  │ - GET /api/samples   │ │
│  ┌──────────────────┐  │     │  └────────┬────────────┘ │
│  │ Explanation      │  │     │           │               │
│  │ Result           │◀─┼─────┼───────────┤               │
│  └──────────────────┘  │     │  ┌────────▼────────────┐ │
│                        │     │  │ OpenAI Integration   │ │
│  ┌──────────────────┐  │     │  │ - Prompt assembly    │ │
│  │ API Client       │  │     │  │ - HTTP via reqwest   │ │
│  │ (Axios)          │  │     │  │ - Response parsing   │ │
│  └──────────────────┘  │     │  └────────┬────────────┘ │
└────────────────────────┘     │           │               │
                               │  ┌────────▼────────────┐ │
                               │  │ Error Handling       │ │
                               │  │ - Custom AppError    │ │
                               │  │ - Typed responses    │ │
                               │  └─────────────────────┘ │
                               └─────────────────────────┘
                                           │
                                    ┌──────▼──────┐
                                    │  OpenAI API │
                                    │  (GPT-4o)   │
                                    └─────────────┘
```

### Backend Layers

| Layer | Responsibility |
|-------|---------------|
| **Router** (main.rs) | Route definitions, CORS, middleware, server binding |
| **Handlers** (handlers.rs) | Request validation, orchestration, response construction |
| **OpenAI** (openai.rs) | Prompt engineering, API communication, response parsing |
| **Models** (models.rs) | Type-safe request/response structures |
| **Error** (error.rs) | Centralized error handling with proper HTTP status codes |

### Frontend Components

| Component | Purpose |
|-----------|---------|
| **Header** | Branding, gradient banner |
| **ClaimForm** | Input form with validation and sample data loading |
| **ExplanationResult** | Animated result display with glossary, metrics, export |
| **Footer** | Attribution and disclaimers |

---

## 4. AI Prompt Engineering Strategy

### System Prompt Design Principles
1. **Role Definition**: Establishes AI as an "insurance claims explanation specialist"
2. **Personalization**: Requires customer name usage and context-specific language
3. **Jargon Elimination**: Explicitly instructs to avoid or define technical terms
4. **Structured Output**: Mandates `---GLOSSARY---` delimiter for reliable parsing
5. **Tone Matching**: Adapts to requested communication style
6. **Action-Oriented**: Always includes concrete next steps

### Prompt Template
```
System: Role + guidelines + output format
User:   Claim ID + Customer Name + Policy Type + Amount + Decision
        + Reason + Terms Referenced + Tone + Reading Level
```

### Why This Approach Works
- **Structured input** → consistent, parseable output
- **Delimiter-based sections** → reliable programmatic extraction
- **Tone/level parameters** → personalization without multiple prompts
- **Next steps requirement** → actionable, not just explanatory

---

## 5. Scalability Considerations

### Streamlit (Prototype)
- Suitable for demos and small teams (1-50 concurrent users)
- Vertical scaling only (bigger server)
- No caching layer — each request hits OpenAI

### Rust + React (Production)
- **Horizontal scaling**: Stateless Axum backend behind a load balancer
- **Connection pooling**: reqwest client with connection reuse
- **Caching potential**: Redis layer for repeat claim patterns
- **CDN**: Static React frontend served via CDN
- **Rate limiting**: Tower middleware for API protection
- **Estimated throughput**: ~10,000 requests/second per instance (excluding OpenAI latency)

### Future Scaling Path
```
                    ┌─────────┐
                    │   CDN   │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │  Load   │
                    │Balancer │
                    └────┬────┘
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │ Axum 1 │ │ Axum 2 │ │ Axum N │
         └───┬────┘ └───┬────┘ └───┬────┘
             └───────────┼─────────┘
                    ┌────▼────┐
                    │  Redis  │
                    │ (Cache) │
                    └────┬────┘
                    ┌────▼────┐
                    │ OpenAI  │
                    │   API   │
                    └─────────┘
```

---

## 6. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| API key exposure | Keys passed at runtime, never stored in code; env vars only |
| Prompt injection | Input sanitization; system prompt is isolated from user content |
| PII in explanations | Customer data stays in-memory; no persistence layer |
| CORS | Strict origin whitelisting (localhost in dev, specific domains in prod) |
| Rate limiting | Tower middleware + API key rotation strategy |
| XSS | React auto-escapes; Streamlit sandboxed rendering |

---

## 7. Technology Comparison

| Aspect | Streamlit (Python) | Rust + React |
|--------|-------------------|-------------|
| **Development Speed** | ⚡ Very fast (hours) | 🔧 Moderate (days) |
| **Performance** | Adequate for demos | Production-grade |
| **Scalability** | Limited | Excellent (horizontal) |
| **Type Safety** | Runtime errors | Compile-time guarantees |
| **Memory Usage** | ~100MB+ | ~10MB |
| **Concurrent Users** | ~50 | ~10,000+ |
| **Deployment** | Single process | Container-ready microservice |
| **Best For** | Prototyping, demos | Production deployment |
