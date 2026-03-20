# ClaimClear AI

**AI-Powered Insurance Claim Explanation Assistant**

> Transform complex insurance claim decisions into clear, personalized
> explanations that customers can actually understand.

---

## The Problem

Insurance customers receive claim decisions written in dense policy language
full of jargon like "subrogation", "contestability period", and "deductible
aggregate". This leads to:

- Confused customers who don't understand why their claim was denied
- High call volumes to customer service for explanation
- Low customer satisfaction and trust erosion

**ClaimClear AI** solves this with an agentic AI pipeline that generates
clear, empathetic, personalized explanations — grounded in actual policy
documents via LangChain RAG and quality-checked before delivery.

---

## Modern AI Techniques

| Technique | What It Does | Why It Matters |
|-----------|-------------|----------------|
| **Agentic Pipeline** | 5-stage pipeline (Analyze → Retrieve → Generate → Evaluate → Refine) | Each stage has a focused role; errors are caught before delivery |
| **LangChain RAG** | PyPDFLoader + RecursiveCharacterTextSplitter + ChromaDB vector store | Retrieves exact policy sections from a real PDF with page citations |
| **PDF Document Grounding** | 8-page SilverShield Master Policy PDF is the RAG source | Real document ingestion, not hardcoded text — demonstrates production RAG |
| **Dual Retrieval** | ChromaDB vector search (with embeddings) or keyword fallback (zero-cost) | Works with or without an API key; seamless upgrade path |
| **Self-Evaluation** | LLM scores its own output (accuracy, empathy, readability, completeness) | Catches tone/accuracy issues automatically |
| **Conditional Refinement** | Re-generates only when quality score < 7/10 | Saves tokens when output is already good |
| **Structured Outputs** | OpenAI JSON mode (`response_format: json_object`) | Zero parsing failures, guaranteed valid responses |
| **Few-Shot Prompting** | One gold-standard example with PDF page citations | Consistent formatting and citation style across all generations |
| **Chain-of-Thought** | Analysis stage reasons about complexity before generation | Better explanations for complex multi-factor decisions |
| **Multi-Model Support** | OpenAI, TCS GenAI Lab, or any OpenAI-compatible endpoint | Flexible deployment across different AI providers |

---

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key (optional — demo mode works without one)

### Install & Run

```bash
# Clone the repository and switch to the correct branch
git clone https://github.com/annondeveloper/hackathon.git
cd hackathon
git checkout claude/python-version-oTxa2

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate the policy PDF (RAG source document)
python create_policy_pdf.py

# Run the app
streamlit run app.py
# Opens at http://localhost:8501
```

### Configure API Key

**Option A — Sidebar (recommended for quick testing):**
Paste your OpenAI API key directly in the sidebar input. It stays in memory
only and is never written to disk.

**Option B — Environment variable:**
```bash
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-your-key-here
```

**Option C — No key (demo mode):**
The app works without an API key using pre-built sample explanations with
RAG citations from the policy PDF.

---

## How It Works

```
┌────────────────────────────────────────────────────────────────┐
│                     Streamlit UI (app.py)                       │
│  Claim Form → Sidebar Settings → Results + RAG Citations       │
└─────────────────────────────┬──────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Pipeline (pipeline.py)                     │
                    │                                             │
                    │  Stage 1: ANALYZE                           │
                    │  └─ Extract complexity, key factors, jargon │
                    │                                             │
                    │  Stage 2: RETRIEVE (RAG)                    │
                    │  └─ LangChain → ChromaDB → Top-3 chunks    │
                    │                     ▲                       │
                    │                     │                       │
                    │            ┌────────┴────────┐              │
                    │            │  PolicyStore     │              │
                    │            │  (LangChain RAG) │              │
                    │            │                  │              │
                    │            │  PyPDFLoader     │              │
                    │            │  TextSplitter    │              │
                    │            │  ChromaDB Vector │              │
                    │            │  Keyword Fallback│              │
                    │            └────────┬────────┘              │
                    │                     │                       │
                    │            ┌────────┴────────┐              │
                    │            │  Policy PDF      │              │
                    │            │  (8 pages,       │              │
                    │            │  12 sections)    │              │
                    │            └─────────────────┘              │
                    │                                             │
                    │  Stage 3: GENERATE                          │
                    │  └─ Explanation + glossary (few-shot + RAG) │
                    │                                             │
                    │  Stage 4: EVALUATE                          │
                    │  └─ Score: accuracy, empathy, readability   │
                    │                                             │
                    │  Stage 5: REFINE (if score < 7/10)          │
                    │  └─ Fix issues from evaluation              │
                    └─────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   LLM Provider      │
                    │   OpenAI / TCS /    │
                    │   Custom Endpoint   │
                    └────────────────────┘
```

---

## Project Structure

```
hackathon/
├── app.py                # Streamlit UI — form, RAG citations, pipeline transparency
├── pipeline.py           # 5-stage agentic pipeline with LangChain RAG integration
├── policy_store.py       # LangChain RAG store — PDF loader, splitter, ChromaDB, keyword fallback
├── sample_data.py        # 4 sample claims across Health, Auto, Home, Travel
├── create_policy_pdf.py  # Generates the SilverShield Master Policy PDF (RAG source)
├── generate_docs.py      # Script to generate formatted Word (.docx) documents
├── requirements.txt      # Python dependencies (streamlit, openai, langchain, chromadb, etc.)
├── .env.example          # Environment variable template
├── .gitignore            # Standard Python ignores
│
├── README.md             # This file — overview and quick start
├── ARCHITECTURE.md       # Detailed architecture and data flow
├── DEPLOYMENT.md         # Full deployment guide (local, Docker, cloud)
├── DESIGN_DECISIONS.md   # Why each AI technique was chosen
├── VIDEO_PROMPT.md       # Demo video generation prompt
│
└── docs/                 # Generated documents
    ├── SilverShield_Master_Policy.pdf   # 8-page insurance policy (RAG source)
    ├── ClaimClear_AI_README.docx
    ├── ClaimClear_AI_Architecture.docx
    ├── ClaimClear_AI_Architecture_Diagram.docx  # Visual architecture diagram
    ├── ClaimClear_AI_Deployment_Guide.docx
    └── ClaimClear_AI_Design_Decisions.docx
```

---

## Features

- **LangChain RAG Pipeline** — PDF ingestion, text splitting, ChromaDB vector search
- **Real Policy PDF** — 8-page SilverShield Master Policy with 12 sections as RAG source
- **RAG Citations** — Every explanation cites specific PDF pages and sections
- **Dual Retrieval** — Vector search (ChromaDB + OpenAI embeddings) or keyword fallback
- **Agentic Pipeline** — 5-stage AI workflow with full transparency
- **Self-Evaluation** — Quality scores (accuracy, empathy, readability, completeness)
- **Multi-Model** — OpenAI GPT-4o/mini, TCS GenAI Lab, or custom endpoints
- **Demo Mode** — Works instantly without an API key (with sample RAG citations)
- **Sample Claims** — 4 realistic scenarios (denied, approved, partial, under review)
- **Tone & Reading Level Control** — Simple/Professional/Technical + Basic/Intermediate/Advanced
- **Pipeline Transparency** — See every stage including RAG retrieval details
- **PDF Download** — Policy document available for download in the sidebar
- **Token Tracking** — Monitor total tokens used per generation
- **Export** — Download explanations as text files

---

## Sample Output

**Input:** Denied health claim for $4,750 (out-of-network MRI)

**Pipeline produces:**
- Clear explanation letter addressing the customer by name
- References to specific policy sections with page numbers (Section 3.2, p.3)
- RAG citations showing the exact PDF passages that grounded the explanation
- 3 actionable next steps (appeal, network exception, future authorization)
- Glossary defining "out-of-network", "prior authorization", "deductible"
- Quality scores: Accuracy 9/10, Empathy 8/10, Readability 9/10

---

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Explanation Accuracy | >= 8/10 | Self-evaluation accuracy score |
| Customer Readability | >= 8/10 | Self-evaluation readability score |
| Support Call Reduction | >= 30% | Before/after comparison |
| Generation Time | < 10 seconds | Pipeline processing time |
| Token Efficiency | < 3,000 tokens/request | Total tokens tracked per run |

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, data flow, component details |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Local, Docker, and cloud deployment guides |
| [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) | Rationale for each AI technique and design choice |
| [VIDEO_PROMPT.md](VIDEO_PROMPT.md) | Prompt for generating a demo video |
| docs/ClaimClear_AI_Architecture_Diagram.docx | Visual architecture diagram |

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| UI | Streamlit 1.41+ | Rapid prototyping, built-in widgets, zero frontend code |
| Language | Python 3.11+ | Rich AI/ML ecosystem, OpenAI SDK support |
| AI | OpenAI GPT-4o-mini / GPT-4o | Best cost/quality ratio, native JSON mode |
| RAG Framework | LangChain | PyPDFLoader, text splitting, embeddings integration |
| Vector Store | ChromaDB | In-memory vector search, LangChain-native |
| Embeddings | OpenAI text-embedding-3-small | High-quality semantic search at low cost |
| PDF Generation | fpdf2 | Lightweight PDF creation for the policy document |
| PDF Parsing | PyPDF2 | Extract text from policy PDF for RAG ingestion |
| Multi-Model | OpenAI-compatible API | Supports TCS GenAI Lab, Azure, custom endpoints |

---

## License

Built for the AI Prototype Challenge. Internal use only.
