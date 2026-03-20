# ClaimClear AI Pro — Rust + React Implementation

High-performance, production-ready insurance claim explanation assistant.

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Rust + Axum | Zero-cost abstractions, ~10x faster than Python, memory-safe |
| Frontend | React 18 + TypeScript + Tailwind CSS | Modern component model, type-safe, utility-first styling |
| Build | Vite | Sub-100ms HMR, optimized production bundles |
| AI | OpenAI GPT-4o via reqwest | Industry-standard LLM with structured output |

## Quick Start

### Backend
```bash
cd backend
cp .env.example .env   # Add your OPENAI_API_KEY
cargo run              # Starts on http://localhost:3001
```

### Frontend
```bash
cd frontend
npm install
npm run dev            # Starts on http://localhost:5173
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/explain` | Generate claim explanation |
| GET | `/api/health` | Health check |
| GET | `/api/samples` | Get sample claims |

### POST /api/explain

**Request:**
```json
{
  "claim_id": "CLM-2024-78432",
  "customer_name": "Sarah Johnson",
  "policy_type": "Health",
  "claim_amount": 3200.0,
  "decision": "Denied",
  "decision_reason": "Out-of-network provider",
  "policy_terms": "Section 4.2",
  "tone": "Simple & Friendly",
  "reading_level": "Basic"
}
```

**Response:**
```json
{
  "explanation": "Hi Sarah, ...",
  "glossary": [{"term": "Provider Network", "definition": "..."}],
  "comprehension_score": 8.5,
  "processing_time_ms": 1250,
  "request_id": "uuid-here"
}
```

## Architecture

```
React (Vite)  ──HTTP──▶  Axum (Rust)  ──HTTPS──▶  OpenAI API
     │                       │
  Tailwind CSS         reqwest client
  lucide-react         serde (de)serialization
  axios                tower-http (CORS, tracing)
```
