"""
ClaimClear AI - Insurance Claim Explanation Assistant
Powered by a multi-step agentic pipeline with LangChain RAG and self-evaluation.
"""

import os
import streamlit as st
from pipeline import (
    ClaimExplanationPipeline, ClaimInput, PipelineResult,
    AnalysisResult, EvaluationResult, GlossaryTerm, MODEL_PROVIDERS,
)
from policy_store import PolicyStore, RAGContext, RetrievedChunk, POLICY_PDF_PATH
from sample_data import SAMPLE_CLAIMS

# ═══════════════════════════════════════════════════════════════════════════
# Page Configuration
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ClaimClear AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# Theme-Aware CSS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Header banner (always dark bg, white text) ── */
.main-header {
    background: linear-gradient(135deg, #0f4c81 0%, #17a2b8 100%);
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}
.main-header h1 {
    margin: 0; font-size: 2.2rem;
    color: #ffffff !important;
}
.main-header p {
    margin: 0.4rem 0 0; opacity: 0.9; font-size: 1.1rem;
    color: #f0f0f0 !important;
}

/* ── Result card ── */
.result-card {
    background: var(--secondary-background-color, #f8fbff);
    border-left: 4px solid #17a2b8;
    padding: 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    color: var(--text-color, #333333);
}

/* ── Glossary terms ── */
.glossary-term {
    background: var(--secondary-background-color, #eef6fb);
    padding: 0.6rem 1rem;
    border-radius: 6px;
    margin: 0.4rem 0;
    color: var(--text-color, #333333);
}

/* ── Metric cards ── */
.metric-card {
    background: var(--secondary-background-color, #ffffff);
    border: 1px solid rgba(128, 128, 128, 0.2);
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
}
.metric-card h3 {
    color: #17a2b8 !important;
    margin: 0; font-size: 2rem;
}
.metric-card p {
    color: var(--text-color, #666666);
    margin: 0.2rem 0 0; font-size: 0.85rem; opacity: 0.8;
}

/* ── RAG citation card ── */
.rag-citation {
    background: var(--secondary-background-color, #f0f7ff);
    border: 1px solid rgba(23, 162, 184, 0.3);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    color: var(--text-color, #333333);
    font-size: 0.9rem;
}
.rag-citation .source-badge {
    display: inline-block;
    background: rgba(23, 162, 184, 0.15);
    color: #17a2b8;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

/* ── Pipeline info bar ── */
.pipeline-info {
    background: var(--secondary-background-color, #f0f7ff);
    border: 1px solid rgba(128, 128, 128, 0.2);
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    color: var(--text-color, #333333);
}

/* ── RAG status badge ── */
.rag-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.rag-badge-vector {
    background: rgba(40, 167, 69, 0.15);
    color: #28a745;
}
.rag-badge-keyword {
    background: rgba(255, 193, 7, 0.15);
    color: #d49e00;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("🛡️ ClaimClear AI")
    st.caption("Agentic AI + LangChain RAG + Self-Evaluation")
    st.divider()

    # Model selection
    st.markdown("**Model Configuration**")
    model_options = list(MODEL_PROVIDERS.keys())
    model_labels = [MODEL_PROVIDERS[m]["label"] for m in model_options]
    model_idx = st.selectbox(
        "Model",
        range(len(model_options)),
        format_func=lambda i: model_labels[i],
        index=0,
    )
    model = model_options[model_idx]
    model_info = MODEL_PROVIDERS[model]

    # API key (only if needed)
    api_key = ""
    if model_info["needs_api_key"]:
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-...",
            help="Used in-memory only, never stored to disk.",
        )
    else:
        st.success(f"No API key needed for {model_info['label']}")

    # Custom endpoint override
    custom_url = st.text_input(
        "Custom Base URL (optional)",
        placeholder="https://your-endpoint.com",
        help="Override the API endpoint for custom deployments.",
    )

    st.divider()

    # Explanation settings
    tone = st.selectbox("Tone", ["Simple & Friendly", "Professional", "Technical"])
    reading_level = st.selectbox("Reading Level", ["Basic", "Intermediate", "Advanced"])

    st.divider()

    # Pipeline info
    st.markdown("**Agentic Pipeline**")
    st.markdown(
        "1. 🔍 **Analyze** - Extract key factors\n"
        "2. 📚 **Retrieve** - RAG from policy PDF\n"
        "3. 📝 **Generate** - Grounded explanation\n"
        "4. ✅ **Evaluate** - Self-critique quality\n"
        "5. 🔄 **Refine** - Fix if score < 7/10"
    )

    st.divider()
    show_pipeline = st.checkbox("Show pipeline details", value=True)
    show_rag = st.checkbox("Show RAG citations", value=True)

    # Policy document info
    st.divider()
    st.markdown("**Policy Document**")
    if os.path.exists(POLICY_PDF_PATH):
        st.markdown("📄 `SilverShield_Master_Policy.pdf`")
        with open(POLICY_PDF_PATH, "rb") as f:
            st.download_button(
                "📥 Download Policy PDF",
                data=f,
                file_name="SilverShield_Master_Policy.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    else:
        st.warning("Policy PDF not found. Run `python create_policy_pdf.py`")

# ═══════════════════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="main-header">'
    "<h1>🛡️ ClaimClear AI</h1>"
    "<p>Agentic pipeline with LangChain RAG grounding and self-evaluation</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════════════════════════════════════

defaults = {
    "claim_id": "", "customer_name": "", "policy_type": "Health",
    "claim_amount": 0.0, "decision": "Denied", "decision_reason": "",
    "policy_terms": "", "pipeline_result": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════════════════
# Sample Claim Loader
# ═══════════════════════════════════════════════════════════════════════════

sample_labels = {s.get("label", s["claim_id"]): s for s in SAMPLE_CLAIMS}

selected_sample = st.selectbox(
    "Quick-fill with a sample claim:",
    ["-- select --"] + list(sample_labels.keys()),
)
if selected_sample != "-- select --":
    s = sample_labels[selected_sample]
    for key in ("claim_id", "customer_name", "policy_type",
                "claim_amount", "decision", "decision_reason", "policy_terms"):
        src_key = key if key in s else f"claim_{key}" if f"claim_{key}" in s else key
        if src_key in s:
            st.session_state[key] = s[src_key]

# ═══════════════════════════════════════════════════════════════════════════
# Claim Input Form
# ═══════════════════════════════════════════════════════════════════════════

st.subheader("📋 Claim Details")
col1, col2 = st.columns(2)

POLICY_TYPES = ["Health", "Auto", "Home", "Life", "Travel"]
DECISIONS = ["Approved", "Partially Approved", "Denied", "Under Review"]

with col1:
    claim_id = st.text_input("Claim ID", value=st.session_state.claim_id)
    customer_name = st.text_input("Customer Name", value=st.session_state.customer_name)
    policy_type = st.selectbox(
        "Policy Type", POLICY_TYPES,
        index=POLICY_TYPES.index(st.session_state.policy_type)
        if st.session_state.policy_type in POLICY_TYPES else 0,
    )
    claim_amount = st.number_input(
        "Claim Amount ($)", min_value=0.0, step=100.0,
        value=float(st.session_state.claim_amount),
    )

with col2:
    decision = st.selectbox(
        "Claim Decision", DECISIONS,
        index=DECISIONS.index(st.session_state.decision)
        if st.session_state.decision in DECISIONS else 0,
    )
    decision_reason = st.text_area(
        "Decision Reason", value=st.session_state.decision_reason, height=100,
    )
    policy_terms = st.text_area(
        "Policy Terms Referenced", value=st.session_state.policy_terms, height=100,
    )

# ═══════════════════════════════════════════════════════════════════════════
# Demo Fallback Data
# ═══════════════════════════════════════════════════════════════════════════

DEMO_EXPLANATION = """Dear Maria,

Thank you for filing your health insurance claim (CLM-2024-78432). We understand dealing with medical expenses is stressful, and we want to clearly explain this decision.

**Your claim for $4,750.00 has been denied.**

**Why:** Your MRI and consultation at Lakewood Imaging Center were performed by an out-of-network provider. Your Silver PPO 3000 plan (Section 3.2, p.3) requires non-emergency diagnostic imaging to be done at in-network facilities. Additionally, no prior authorization was obtained before the procedure, which is required under Section 5.1 (p.4) for advanced imaging like MRIs.

**Your next steps:**
1. **File an appeal** within 180 days if you believe no in-network provider was available within 50 miles (see Section 9.1, p.6)
2. **Request a network gap exception** by calling 1-800-555-0199 (Section 3.3, p.3)
3. **Get prior authorization** for any future imaging - submit requests at least 5 business days ahead

We're here to help. Please don't hesitate to reach out with questions."""

DEMO_GLOSSARY = [
    {"term": "Out-of-Network", "definition": "A healthcare provider not contracted with your insurance plan, meaning services may not be covered or cost significantly more."},
    {"term": "Prior Authorization", "definition": "Approval your insurance requires before certain medical services to confirm they're covered under your plan."},
    {"term": "Network Gap Exception", "definition": "Special approval to see an out-of-network provider at in-network rates when no in-network option is available nearby."},
    {"term": "Deductible", "definition": "The amount you pay for covered services before your insurance starts paying. Silver PPO 3000: $3,000/individual."},
]

DEMO_RAG_CONTEXT = RAGContext(
    chunks=[
        RetrievedChunk(
            text="Out-of-network services are covered at a reduced rate under PPO plans (60% vs 80% after deductible). HMO plans do not cover out-of-network except emergencies.",
            section="Section 3.2 - Out-of-Network Services",
            page=3, source_doc="SilverShield_Master_Policy.pdf",
            score=8.0, policy_type="Health",
        ),
        RetrievedChunk(
            text="Required for: advanced imaging (MRI, CT, PET), specialty referrals, elective procedures, outpatient surgery, DME over $500. Submit at least 5 business days before scheduled date.",
            section="Section 5.1 - Prior Authorization",
            page=4, source_doc="SilverShield_Master_Policy.pdf",
            score=6.5, policy_type="Health",
        ),
        RetrievedChunk(
            text="If no in-network provider is available within 50 miles, SilverShield will authorize out-of-network coverage at in-network rates. Call 1-800-555-0199. Valid for 90 days.",
            section="Section 3.3 - Network Gap Exceptions",
            page=3, source_doc="SilverShield_Master_Policy.pdf",
            score=5.0, policy_type="Health",
        ),
    ],
    retrieval_method="keyword",
    total_chunks_in_store=18,
)

# ═══════════════════════════════════════════════════════════════════════════
# Generate Button
# ═══════════════════════════════════════════════════════════════════════════

st.divider()
generate = st.button("🚀 Generate Explanation", use_container_width=True, type="primary")

if generate:
    if not customer_name or not decision_reason:
        st.warning("Please fill in at least the customer name and decision reason.")
    else:
        needs_key = MODEL_PROVIDERS.get(model, {}).get("needs_api_key", True)
        demo_mode = needs_key and not api_key

        if demo_mode:
            st.info(
                "🔔 **Demo mode** - showing a pre-built explanation with sample RAG citations. "
                "Add your API key in the sidebar for the full agentic pipeline."
            )
            st.session_state.pipeline_result = PipelineResult(
                explanation=DEMO_EXPLANATION,
                glossary=[GlossaryTerm(**g) for g in DEMO_GLOSSARY],
                analysis=AnalysisResult(
                    complexity="medium",
                    key_factors=["out-of-network provider", "no prior authorization", "policy section 3.2 & 5.1"],
                    jargon_terms=["out-of-network", "prior authorization", "network gap exception", "deductible"],
                    customer_impact="Claim denied; customer must pay $4,750 out of pocket unless appeal succeeds.",
                    missing_info=[],
                ),
                evaluation=EvaluationResult(
                    accuracy_score=9, empathy_score=8, readability_score=9,
                    completeness_score=9, overall_score=9,
                    issues=[], suggestions=[],
                ),
                rag_context=DEMO_RAG_CONTEXT,
                was_refined=False,
                total_tokens_used=0,
                processing_time_ms=0,
                stages_completed=["analyze", "retrieve", "generate", "evaluate"],
            )
        else:
            # Run the full agentic pipeline
            claim_input = ClaimInput(
                claim_id=claim_id,
                customer_name=customer_name,
                policy_type=policy_type,
                claim_amount=claim_amount,
                decision=decision,
                decision_reason=decision_reason,
                policy_terms=policy_terms,
                tone=tone,
                reading_level=reading_level,
            )

            policy_store = PolicyStore()
            effective_url = custom_url if custom_url else None
            pipeline = ClaimExplanationPipeline(
                api_key=api_key or None,
                model=model,
                base_url=effective_url,
                policy_store=policy_store,
            )

            stage_placeholder = st.empty()
            stage_names = {
                "analyzing": "🔍 Stage 1/4: Analyzing claim...",
                "retrieving": "📚 RAG: Retrieving policy documents...",
                "generating": "📝 Stage 2/4: Generating explanation (RAG-grounded)...",
                "evaluating": "✅ Stage 3/4: Self-evaluating quality...",
                "refining": "🔄 Stage 4/4: Refining based on feedback...",
            }

            def on_stage(name, _data):
                if name in stage_names:
                    stage_placeholder.info(stage_names[name])

            try:
                result = pipeline.run(claim_input, on_stage=on_stage)
                st.session_state.pipeline_result = result
                stage_placeholder.empty()
            except Exception as exc:
                stage_placeholder.empty()
                st.error(f"Pipeline error: {exc}")

# ═══════════════════════════════════════════════════════════════════════════
# Results Display
# ═══════════════════════════════════════════════════════════════════════════

result = st.session_state.pipeline_result

if result:
    # ── Explanation ──
    st.subheader("📄 Generated Explanation")
    with st.container():
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown(result.explanation)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Quality Metrics ──
    ev = result.evaluation
    m1, m2, m3, m4 = st.columns(4)
    for col, (score, label) in zip(
        [m1, m2, m3, m4],
        [
            (ev.overall_score, "Overall Quality"),
            (ev.accuracy_score, "Accuracy"),
            (ev.empathy_score, "Empathy"),
            (ev.readability_score, "Readability"),
        ],
    ):
        with col:
            st.markdown(
                f'<div class="metric-card"><h3>{score}/10</h3>'
                f"<p>{label}</p></div>",
                unsafe_allow_html=True,
            )
            st.progress(score / 10)

    # ── RAG Citations ──
    if show_rag and result.rag_context and result.rag_context.chunks:
        st.subheader("📚 RAG Source Citations")
        rag = result.rag_context

        # RAG method badge
        if rag.retrieval_method == "vector":
            st.markdown(
                '<span class="rag-badge rag-badge-vector">🧠 Vector Search (ChromaDB + OpenAI Embeddings)</span>'
                f" &nbsp; {rag.total_chunks_in_store} chunks indexed from PDF",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="rag-badge rag-badge-keyword">🔤 Keyword Search (TF-IDF)</span>'
                f" &nbsp; {rag.total_chunks_in_store} chunks indexed from PDF",
                unsafe_allow_html=True,
            )

        # Citation cards
        for i, chunk in enumerate(rag.chunks, 1):
            st.markdown(
                f'<div class="rag-citation">'
                f'<span class="source-badge">📄 {chunk.source_doc} &bull; Page {chunk.page}</span>'
                f"<br><strong>{chunk.section}</strong>"
                f"<br>{chunk.text}"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Glossary ──
    if result.glossary:
        st.subheader("📖 Key Terms Glossary")
        for item in result.glossary:
            term = item.term if hasattr(item, "term") else item.get("term", "")
            defn = item.definition if hasattr(item, "definition") else item.get("definition", "")
            st.markdown(
                f'<div class="glossary-term"><strong>{term}</strong>: {defn}</div>',
                unsafe_allow_html=True,
            )

    # ── Pipeline Transparency ──
    if show_pipeline:
        st.divider()
        st.subheader("🔬 Pipeline Details")

        with st.expander("Stage 1: Claim Analysis", expanded=False):
            a = result.analysis
            st.markdown(f"**Complexity:** {a.complexity}")
            st.markdown(f"**Key Factors:** {', '.join(a.key_factors)}")
            st.markdown(f"**Jargon to Define:** {', '.join(a.jargon_terms)}")
            st.markdown(f"**Customer Impact:** {a.customer_impact}")
            if a.missing_info:
                st.markdown(f"**Missing Info:** {', '.join(a.missing_info)}")

        with st.expander("Stage 2: RAG-Grounded Generation", expanded=False):
            st.markdown("The explanation was generated using:")
            st.markdown(f"- **Policy document:** `{POLICY_PDF_PATH}`")
            st.markdown("- **LangChain PDF loader** - PyPDFLoader for document ingestion")
            st.markdown("- **Text splitter** - RecursiveCharacterTextSplitter (500 chars, 80 overlap)")
            if result.rag_context:
                method = result.rag_context.retrieval_method
                if method == "vector":
                    st.markdown("- **Vector store** - ChromaDB with OpenAI text-embedding-3-small")
                else:
                    st.markdown("- **Retrieval** - Keyword matching with TF-IDF scoring")
                st.markdown(f"- **Chunks retrieved:** {len(result.rag_context.chunks)} of {result.rag_context.total_chunks_in_store}")
            st.markdown("- **Few-shot example** - Gold-standard reference anchoring output style")
            st.markdown("- **Structured output** - JSON schema enforcement via response_format")

        with st.expander("Stage 3: Self-Evaluation", expanded=False):
            cols = st.columns(4)
            for col, (label, score) in zip(cols, [
                ("Accuracy", ev.accuracy_score),
                ("Empathy", ev.empathy_score),
                ("Readability", ev.readability_score),
                ("Completeness", ev.completeness_score),
            ]):
                with col:
                    st.metric(label, f"{score}/10")
            if ev.issues:
                st.markdown("**Issues Found:**")
                for issue in ev.issues:
                    st.markdown(f"- {issue}")
            if ev.suggestions:
                st.markdown("**Suggestions:**")
                for sug in ev.suggestions:
                    st.markdown(f"- {sug}")

        if result.was_refined:
            with st.expander("Stage 4: Refinement", expanded=False):
                st.success("Explanation was refined based on evaluation feedback.")

        # ── Pipeline Stats ──
        st.markdown(
            f'<div class="pipeline-info">'
            f"<strong>Pipeline:</strong> "
            f"{'  →  '.join(result.stages_completed)} &nbsp;|&nbsp; "
            f"{'Refined' if result.was_refined else 'No refinement needed'} &nbsp;|&nbsp; "
            f"{result.total_tokens_used:,} tokens &nbsp;|&nbsp; "
            f"{result.processing_time_ms:,}ms &nbsp;|&nbsp; "
            f"Model: {model}"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Actions ──
    st.divider()
    a1, a2 = st.columns(2)
    with a1:
        st.download_button(
            "📥 Download Explanation",
            data=result.explanation,
            file_name=f"claim_explanation_{claim_id or 'draft'}.txt",
            mime="text/plain",
        )
    with a2:
        if st.button("📋 Copy to Clipboard"):
            st.code(result.explanation, language=None)
            st.success("Text displayed above - select and copy.")

# ═══════════════════════════════════════════════════════════════════════════
# Footer
# ═══════════════════════════════════════════════════════════════════════════

st.divider()
st.caption(
    "ClaimClear AI | Agentic Pipeline + LangChain RAG + Self-Evaluation | "
    "Powered by OpenAI / TCS GenAI Lab | Not a substitute for professional insurance advice"
)
