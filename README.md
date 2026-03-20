# 🛡️ ClaimClear AI

**AI-Powered Insurance Claim Explanation Assistant**

> Transform complex insurance claim decisions into clear, personalized explanations that customers can actually understand.

## Problem Statement

Insurance customers often find claim decisions confusing due to complex policy language and technical jargon. Customer service teams spend significant time explaining claim outcomes, leading to increased operational costs and customer dissatisfaction.

**ClaimClear AI** solves this by generating clear, personalized, jargon-free explanations of claim decisions — improving transparency and reducing support workload.

---

## 🏗️ Project Structure

This repository contains **two implementations** of the same solution:

```
hackathon/
├── app.py                  # Streamlit prototype (Python)
├── sample_data.py          # Sample insurance claims
├── requirements.txt        # Python dependencies
├── .env.example            # Environment config template
├── README.md               # This file
├── ARCHITECTURE.md         # Detailed architecture document
├── DEPLOYMENT.md           # Deployment guide
├── DESIGN_DECISIONS.md     # Design decisions rationale
├── VIDEO_PROMPT.md         # Gemini video generation prompt
│
└── claimclear-pro/         # Cutting-edge implementation
    ├── backend/            # Rust (Axum) API server
    │   ├── Cargo.toml
    │   └── src/
    │       ├── main.rs
    │       ├── models.rs
    │       ├── handlers.rs
    │       ├── openai.rs
    │       └── error.rs
    ├── frontend/           # React + TypeScript + Tailwind
    │   ├── package.json
    │   ├── vite.config.ts
    │   ├── index.html
    │   └── src/
    │       ├── main.tsx
    │       ├── App.tsx
    │       ├── index.css
    │       ├── api/client.ts
    │       ├── types/index.ts
    │       └── components/
    │           ├── Header.tsx
    │           ├── ClaimForm.tsx
    │           ├── ExplanationResult.tsx
    │           └── Footer.tsx
    ├── README.md
    └── ARCHITECTURE.md
```

---

## 🚀 Approach 1: Streamlit Prototype (Fast & Familiar)

### Tech Stack
- **UI**: Streamlit 1.41
- **Language**: Python 3.11+
- **AI**: OpenAI SDK (GPT-4o / GPT-4o-mini)

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key (optional — demo mode works without it)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the app
streamlit run app.py
```

### Features
- **Demo Mode**: Works without an API key using pre-built sample explanations
- **Sample Claims**: Quick-fill buttons with realistic insurance scenarios
- **Tone Control**: Simple & Friendly, Professional, or Technical
- **Reading Level**: Basic, Intermediate, or Advanced
- **Glossary**: Auto-extracted key terms with plain-language definitions
- **Metrics**: Comprehension score, time saved estimate, reading time
- **Export**: Download explanation as text file

---

## 🚀 Approach 2: Cutting-Edge (Rust + React)

### Tech Stack
- **Backend**: Rust with Axum (blazing-fast async web framework)
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Vite
- **AI**: OpenAI API via reqwest (Rust HTTP client)

### Quick Start

```bash
# Backend
cd claimclear-pro/backend
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
cargo run

# Frontend (in a separate terminal)
cd claimclear-pro/frontend
npm install
npm run dev
```

### Why This Stack?
- **Rust**: Memory safety, zero-cost abstractions, ~10x faster than Python for API handling
- **Axum**: Tokio-based async runtime, excellent middleware ecosystem
- **React + Tailwind**: Modern component architecture, utility-first CSS, rapid UI development
- **Vite**: Sub-second HMR, optimized production builds

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Customer / User                 │
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│  Streamlit UI    │    │  React + Tailwind UI │
│  (Python)        │    │  (TypeScript)        │
└────────┬─────────┘    └──────────┬───────────┘
         │                         │
         ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│  OpenAI SDK      │    │  Axum REST API       │
│  (Direct call)   │    │  (Rust backend)      │
└────────┬─────────┘    └──────────┬───────────┘
         │                         │
         └────────────┬────────────┘
                      ▼
            ┌──────────────────┐
            │   OpenAI GPT-4o  │
            │   (LLM Engine)   │
            └──────────────────┘
```

---

## 📏 Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Customer Comprehension Score | ≥ 8/10 | Post-explanation survey / readability analysis |
| Support Interaction Reduction | ≥ 30% | Before/after comparison of support tickets |
| Explanation Generation Time | < 5 seconds | API response time tracking |
| Customer Satisfaction (CSAT) | ≥ 4.5/5 | Customer feedback ratings |

---

## 📦 Deliverables

- [x] Generated explanation text (AI-powered)
- [x] Working prototype UI (Streamlit)
- [x] Cutting-edge production-ready architecture (Rust + React)
- [x] Usage documentation (this README)
- [x] Architecture document (ARCHITECTURE.md)
- [x] Design decisions (DESIGN_DECISIONS.md)
- [x] Deployment guide (DEPLOYMENT.md)
- [x] Demo video generation prompt (VIDEO_PROMPT.md)

---

## 📄 License

Built for the AI Prototype Challenge. Internal use only.
