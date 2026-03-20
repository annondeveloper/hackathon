"""
ClaimClear AI - Insurance Claim Explanation Assistant
Powered by a multi-step agentic pipeline with RAG and self-evaluation.
"""

import streamlit as st
from pipeline import ClaimExplanationPipeline, ClaimInput
from policy_store import PolicyStore
from sample_data import SAMPLE_CLAIMS

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ClaimClear AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #0f4c81 0%, #17a2b8 100%);
    padding: 2rem 2.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;
}
.main-header h1 { margin: 0; font-size: 2.2rem; }
.main-header p  { margin: 0.4rem 0 0; opacity: 0.9; font-size: 1.1rem; }
.result-card {
    background: #f8fbff; border-left: 4px solid #17a2b8;
    padding: 1.5rem; border-radius: 8px; margin: 1rem 0;
}
.glossary-term {
    background: #eef6fb; padding: 0.6rem 1rem;
    border-radius: 6px; margin: 0.4rem 0;
}
.metric-card {
    background: white; border: 1px solid #e0e0e0;
    border-radius: 10px; padding: 1.2rem; text-align: center;
}
.metric-card h3 { color: #0f4c81; margin: 0; font-size: 2rem; }
.metric-card p  { color: #666; margin: 0.2rem 0 0; font-size: 0.85rem; }
.stage-badge {
    display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px;
    font-size: 0.75rem; font-weight: 600; margin: 0.1rem;
}
.stage-done { background: #d4edda; color: #155724; }
.stage-active { background: #fff3cd; color: #856404; }
.pipeline-info {
    background: #f0f7ff; border: 1px solid #b8d4f0;
    border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🛡️ ClaimClear AI")
    st.caption("Agentic AI · RAG · Self-Evaluation")
    st.divider()

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Your key is used in-memory only, never stored to disk.",
    )
    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)
    tone = st.selectbox("Tone", ["Simple & Friendly", "Professional", "Technical"])
    reading_level = st.selectbox("Reading Level", ["Basic", "Intermediate", "Advanced"])

    st.divider()
    st.markdown("**AI Pipeline Stages**")
    st.markdown(
        "1. 🔍 **Analyze** — Extract key factors & complexity\n"
        "2. 📝 **Generate** — RAG-grounded explanation\n"
        "3. ✅ **Evaluate** — Self-critique for quality\n"
        "4. 🔄 **Refine** — Fix issues if score < 7/10"
    )
    st.divider()
    show_pipeline = st.checkbox("Show pipeline details", value=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="main-header">'
    "<h1>🛡️ ClaimClear AI</h1>"
    "<p>Agentic AI pipeline with RAG grounding and self-evaluation</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
defaults = {
    "claim_id": "", "customer_name": "", "policy_type": "Health",
    "claim_amount": 0.0, "decision": "Denied", "decision_reason": "",
    "policy_terms": "", "pipeline_result": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Sample claim loader
# ---------------------------------------------------------------------------
sample_labels = {s.get("label", s["claim_id"]): s for s in SAMPLE_CLAIMS}

selected_sample = st.selectbox(
    "Quick-fill with a sample claim:",
    ["-- select --"] + list(sample_labels.keys()),
)
if selected_sample != "-- select --":
    s = sample_labels[selected_sample]
    for key in ("claim_id", "customer_name", "policy_type",
                "claim_amount", "decision", "decision_reason", "policy_terms"):
        # Handle both "decision" and "claim_decision" field names
        src_key = key if key in s else f"claim_{key}" if f"claim_{key}" in s else key
        if src_key in s:
            st.session_state[key] = s[src_key]

# ---------------------------------------------------------------------------
# Claim input form
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Demo fallback
# ---------------------------------------------------------------------------
DEMO_EXPLANATION = """Dear Maria,

Thank you for filing your health insurance claim (CLM-2024-78432). We understand dealing with medical expenses is stressful, and we want to clearly explain this decision.

**Your claim for $4,750.00 has been denied.**

**Why:** Your MRI and consultation at Lakewood Imaging Center were performed by an out-of-network provider. Your Silver PPO 3000 plan (Section 5.2) requires non-emergency diagnostic imaging to be done at in-network facilities. Additionally, no prior authorization was obtained before the procedure, which is required under Section 8.4 for advanced imaging like MRIs.

**Your next steps:**
1. **File an appeal** within 180 days if you believe no in-network provider was available within 50 miles
2. **Request a network gap exception** by calling 1-800-555-0199
3. **Get prior authorization** for any future imaging — submit requests at least 5 business days ahead

We're here to help. Please don't hesitate to reach out with questions."""

DEMO_GLOSSARY = [
    {"term": "Out-of-Network", "definition": "A healthcare provider not contracted with your insurance plan, meaning services may not be covered."},
    {"term": "Prior Authorization", "definition": "Approval your insurance requires before certain medical services to confirm they're covered."},
    {"term": "Network Gap Exception", "definition": "Special approval to see an out-of-network provider at in-network rates when no in-network option is nearby."},
    {"term": "Deductible", "definition": "The amount you pay for covered services before your insurance starts paying."},
]

# ---------------------------------------------------------------------------
# Generate button
# ---------------------------------------------------------------------------
st.divider()
generate = st.button("🚀 Generate Explanation", use_container_width=True, type="primary")

if generate:
    if not customer_name or not decision_reason:
        st.warning("Please fill in at least the customer name and decision reason.")
    else:
        demo_mode = not api_key

        if demo_mode:
            st.info(
                "🔔 **Demo mode** — showing a pre-built explanation. "
                "Add your OpenAI API key in the sidebar for the full agentic pipeline."
            )
            from pipeline import PipelineResult, AnalysisResult, EvaluationResult, GlossaryTerm

            st.session_state.pipeline_result = PipelineResult(
                explanation=DEMO_EXPLANATION,
                glossary=[GlossaryTerm(**g) for g in DEMO_GLOSSARY],
                analysis=AnalysisResult(
                    complexity="medium",
                    key_factors=["out-of-network provider", "no prior authorization", "policy section 5.2 & 8.4"],
                    jargon_terms=["out-of-network", "prior authorization", "network gap exception", "deductible"],
                    customer_impact="Claim denied; customer must pay $4,750 out of pocket unless appeal succeeds.",
                    missing_info=[],
                ),
                evaluation=EvaluationResult(
                    accuracy_score=9, empathy_score=8, readability_score=9,
                    completeness_score=9, overall_score=9,
                    issues=[], suggestions=[],
                ),
                was_refined=False,
                total_tokens_used=0,
                processing_time_ms=0,
                stages_completed=["analyze", "generate", "evaluate"],
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
            pipeline = ClaimExplanationPipeline(
                api_key=api_key,
                model=model,
                policy_store=policy_store,
            )

            stage_placeholder = st.empty()
            stage_names = {
                "analyzing": "🔍 Analyzing claim...",
                "generating": "📝 Generating explanation (RAG-grounded)...",
                "evaluating": "✅ Self-evaluating quality...",
                "refining": "🔄 Refining based on feedback...",
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

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------
result = st.session_state.pipeline_result

if result:
    st.subheader("📄 Generated Explanation")
    st.markdown(
        f'<div class="result-card">{result.explanation}</div>',
        unsafe_allow_html=True,
    )

    # --- Quality metrics ---
    ev = result.evaluation
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card"><h3>{ev.overall_score}/10</h3>'
            f"<p>Overall Quality</p></div>", unsafe_allow_html=True,
        )
        st.progress(ev.overall_score / 10)
    with m2:
        st.markdown(
            f'<div class="metric-card"><h3>{ev.accuracy_score}/10</h3>'
            f"<p>Accuracy</p></div>", unsafe_allow_html=True,
        )
        st.progress(ev.accuracy_score / 10)
    with m3:
        st.markdown(
            f'<div class="metric-card"><h3>{ev.empathy_score}/10</h3>'
            f"<p>Empathy</p></div>", unsafe_allow_html=True,
        )
        st.progress(ev.empathy_score / 10)
    with m4:
        st.markdown(
            f'<div class="metric-card"><h3>{ev.readability_score}/10</h3>'
            f"<p>Readability</p></div>", unsafe_allow_html=True,
        )
        st.progress(ev.readability_score / 10)

    # --- Glossary ---
    if result.glossary:
        st.subheader("📖 Key Terms Glossary")
        for item in result.glossary:
            term = item.term if hasattr(item, 'term') else item.get('term', '')
            defn = item.definition if hasattr(item, 'definition') else item.get('definition', '')
            st.markdown(
                f'<div class="glossary-term"><strong>{term}</strong>: {defn}</div>',
                unsafe_allow_html=True,
            )

    # --- Pipeline transparency ---
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
            st.markdown("- **Policy knowledge store** — relevant sections retrieved by keyword matching")
            st.markdown("- **Few-shot example** — high-quality reference anchoring output style")
            st.markdown("- **Structured output** — JSON schema enforcement via OpenAI response_format")

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
                for s in ev.suggestions:
                    st.markdown(f"- {s}")

        if result.was_refined:
            with st.expander("Stage 4: Refinement", expanded=False):
                st.success("Explanation was refined based on evaluation feedback.")

        # --- Token usage ---
        st.markdown(
            f'<div class="pipeline-info">'
            f"<strong>Pipeline stats:</strong> "
            f"{'→'.join(result.stages_completed)} | "
            f"{'Refined' if result.was_refined else 'No refinement needed'} | "
            f"{result.total_tokens_used:,} tokens used | "
            f"{result.processing_time_ms:,}ms"
            f"</div>",
            unsafe_allow_html=True,
        )

    # --- Actions ---
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
            st.success("Text displayed above — select and copy.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "ClaimClear AI · Agentic Pipeline with RAG & Self-Evaluation · "
    "Powered by OpenAI · Not a substitute for professional insurance advice"
)
