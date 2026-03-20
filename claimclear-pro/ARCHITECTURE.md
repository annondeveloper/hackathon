# ClaimClear AI Pro — Architecture Document

## System Design

### Why Rust?

1. **Performance**: No garbage collector, zero-cost abstractions. API handler overhead ~1ms vs ~10-15ms for Node.js/Python.
2. **Memory Safety**: The compiler eliminates null pointer dereferences, data races, and buffer overflows at compile time.
3. **Concurrency**: Tokio async runtime handles thousands of concurrent connections with minimal memory (~10MB baseline vs ~100MB+ for Node/Python).
4. **Type System**: Rich enum types model domain errors precisely. `Result<T, E>` forces error handling at every call site.

### Backend Architecture (Axum)

```
main.rs           → Server setup, routing, middleware, CORS
├── models.rs     → Request/response types (serde Serialize/Deserialize)
├── handlers.rs   → Route handlers (validation, orchestration)
├── openai.rs     → OpenAI API integration (prompt engineering, HTTP calls)
└── error.rs      → Custom AppError enum, IntoResponse impl
```

**Key patterns:**
- **Shared state** via `Arc<AppState>` containing the reqwest client and API key
- **Custom error type** with `IntoResponse` for consistent error responses
- **Structured logging** via `tracing` + `tracing-subscriber`

### Frontend Architecture (React + TypeScript)

```
App.tsx
├── Header.tsx              → Branding, gradient banner
├── ClaimForm.tsx           → Input form, validation, sample loading
├── ExplanationResult.tsx   → Results display, glossary, metrics
└── Footer.tsx              → Attribution

api/client.ts               → Axios wrapper, type-safe API calls
types/index.ts              → Shared TypeScript interfaces
```

**Key patterns:**
- **Demo mode fallback**: Works without backend using embedded sample data
- **Optimistic UI**: Loading states, error boundaries, smooth animations
- **Tailwind utility classes**: No separate CSS files, consistent design system

### Data Flow

```
1. User fills form → ClaimForm component state
2. Submit → ClaimRequest object → POST /api/explain
3. Axum handler validates → calls openai::generate_explanation()
4. Prompt assembled → reqwest POST to OpenAI API
5. Response parsed → explanation + glossary extracted
6. Comprehension score calculated (text complexity heuristic)
7. ClaimResponse returned → ExplanationResult renders
```

### Scalability Path

- **Horizontal**: Stateless backend → deploy N instances behind load balancer
- **Caching**: Add Redis for repeat claim patterns (same reason + policy type)
- **CDN**: React build served via CloudFront/Cloudflare
- **Rate limiting**: Tower middleware (already in middleware stack)
- **Estimated capacity**: ~10,000 req/s per instance (excluding OpenAI latency)

### Security Model

- API keys: Runtime env vars only, never in code
- CORS: Strict origin whitelist
- Input validation: Serde deserialization rejects malformed requests
- No PII storage: Stateless, in-memory only
- XSS: React auto-escapes all rendered content
