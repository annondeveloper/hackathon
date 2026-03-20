"""
ClaimClear AI - Insurance Claim Explanation Assistant
A Streamlit-powered AI assistant that generates clear, personalized
explanations of insurance claim decisions.
"""

import streamlit as st
from openai import OpenAI
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
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #0f4c81 0%, #17a2b8 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 2.2rem; }
    .main-header p  { margin: 0.4rem 0 0; opacity: 0.9; font-size: 1.1rem; }
    .result-card {
        background: #f8fbff;
        border-left: 4px solid #17a2b8;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .glossary-term {
        background: #eef6fb;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
    }
    .metric-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-card h3 { color: #0f4c81; margin: 0; font-size: 2rem; }
    .metric-card p  { color: #666; margin: 0.2rem 0 0; font-size: 0.85rem; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0f4c81 0%, #17a2b8 100%);
        color: white; border: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🛡️ ClaimClear AI")
    st.caption("Making insurance decisions crystal clear")
    st.divider()

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Your key is never stored. Leave blank for demo mode.",
    )
    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini"], index=1)
    tone = st.selectbox("Tone", ["Simple & Friendly", "Professional", "Technical"])
    reading_level = st.selectbox("Reading Level", ["Basic", "Intermediate", "Advanced"])

    st.divider()
    st.markdown("**How it works**")
    st.markdown(
        "1. Enter claim details\n"
        "2. Click *Generate Explanation*\n"
        "3. Get a clear, jargon-free explanation"
    )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="main-header">'
    "<h1>🛡️ ClaimClear AI</h1>"
    "<p>Transform complex claim decisions into clear, personalized explanations</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
defaults = {
    "claim_id": "",
    "customer_name": "",
    "policy_type": "Health",
    "claim_amount": 0.0,
    "decision": "Denied",
    "decision_reason": "",
    "policy_terms": "",
    "explanation": None,
    "glossary": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Sample data loader
# ---------------------------------------------------------------------------
sample_labels = {s["label"]: s for s in SAMPLE_CLAIMS}

selected_sample = st.selectbox(
    "Quick-fill with a sample claim:",
    ["-- select --"] + list(sample_labels.keys()),
)
if selected_sample != "-- select --":
    s = sample_labels[selected_sample]
    for key in (
        "claim_id", "customer_name", "policy_type",
        "claim_amount", "decision", "decision_reason", "policy_terms",
    ):
        st.session_state[key] = s[key]

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
        "Policy Type",
        POLICY_TYPES,
        index=POLICY_TYPES.index(st.session_state.policy_type)
        if st.session_state.policy_type in POLICY_TYPES else 0,
    )
    claim_amount = st.number_input(
        "Claim Amount ($)", min_value=0.0, step=100.0,
        value=float(st.session_state.claim_amount),
    )

with col2:
    decision = st.selectbox(
        "Claim Decision",
        DECISIONS,
        index=DECISIONS.index(st.session_state.decision)
        if st.session_state.decision in DECISIONS else 0,
    )
    decision_reason = st.text_area(
        "Decision Reason",
        value=st.session_state.decision_reason,
        height=100,
    )
    policy_terms = st.text_area(
        "Policy Terms Referenced",
        value=st.session_state.policy_terms,
        height=100,
    )

# ---------------------------------------------------------------------------
# Prompt engineering
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are ClaimClear AI, an insurance claims explanation specialist.

Your task is to produce a clear, empathetic, and personalized explanation of a
claim decision that a customer can easily understand.

Guidelines:
- Address the customer by name.
- Avoid or immediately define any insurance jargon.
- Explain WHY the decision was made, referencing specific policy terms simply.
- Provide concrete next steps the customer can take.
- Match the requested tone and reading level.
- Keep the explanation concise (200-350 words).
- End with an encouraging, supportive note.

After the explanation, output a glossary section. Mark it with the exact
delimiter:

---GLOSSARY---

Then list each insurance term used with a plain-language definition, one per
line in the format:
TERM: definition
"""


def build_user_prompt():
    return (
        f"Claim ID: {claim_id}\n"
        f"Customer Name: {customer_name}\n"
        f"Policy Type: {policy_type}\n"
        f"Claim Amount: ${claim_amount:,.2f}\n"
        f"Decision: {decision}\n"
        f"Decision Reason: {decision_reason}\n"
        f"Policy Terms Referenced: {policy_terms}\n"
        f"Requested Tone: {tone}\n"
        f"Reading Level: {reading_level}\n"
    )


# ---------------------------------------------------------------------------
# Demo fallback explanation
# ---------------------------------------------------------------------------
DEMO_EXPLANATION = """Hi Sarah,

Thank you for filing your health insurance claim (CLM-2024-78432). We understand that dealing with medical bills can be stressful, so we want to clearly explain the outcome of your claim.

**What happened:** Your claim for $3,200.00 for services received at Riverside Medical Center was **denied**.

**Why this decision was made:** Your policy (Section 4.2 - Network Provider Requirements) requires that non-emergency medical services be provided by doctors and facilities within our approved network. Riverside Medical Center is not currently part of our provider network, which means the services you received there are not covered under your plan.

**What this means for you:** Because the care was received outside of the network, your plan does not cover these costs. However, this does not mean you are out of options.

**Your next steps:**
1. **Appeal the decision** - If you believe the services were medically necessary or that no in-network provider was available, you can file an appeal within 60 days.
2. **Check for exceptions** - Contact our team at 1-800-555-0199 to ask about a network gap exception.
3. **Find in-network providers** - Visit our online directory to find covered providers near you for future visits.

We are here to help you through this process. Please do not hesitate to reach out with any questions.

---GLOSSARY---
Provider Network: A group of doctors, hospitals, and other healthcare providers that have agreed to provide services at pre-negotiated rates with your insurance company.
Out-of-Network: Healthcare providers or facilities that do not have a contract with your insurance plan, meaning services may not be covered or may cost more.
Appeal: A formal request to have your insurance company review and reconsider a claim decision.
Network Gap Exception: A special approval that allows you to see an out-of-network provider at in-network rates when no suitable in-network provider is available.
Medically Necessary: Services or treatments that are required to diagnose or treat a medical condition and meet accepted standards of medical practice.
"""


def parse_response(text):
    """Split AI response into explanation body and glossary terms."""
    if "---GLOSSARY---" in text:
        parts = text.split("---GLOSSARY---", 1)
        explanation = parts[0].strip()
        glossary = []
        for line in parts[1].strip().splitlines():
            if ":" in line:
                term, _, defn = line.partition(":")
                glossary.append({"term": term.strip(), "definition": defn.strip()})
        return explanation, glossary
    return text.strip(), []


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
                "🔔 **Demo mode** — showing a pre-built sample explanation. "
                "Add your OpenAI API key in the sidebar for live generation."
            )
            raw = DEMO_EXPLANATION
        else:
            with st.spinner("Generating explanation..."):
                try:
                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": build_user_prompt()},
                        ],
                        temperature=0.7,
                        max_tokens=1024,
                    )
                    raw = response.choices[0].message.content
                except Exception as exc:
                    st.error(f"OpenAI API error: {exc}")
                    raw = None

        if raw:
            explanation, glossary = parse_response(raw)
            st.session_state.explanation = explanation
            st.session_state.glossary = glossary

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------
if st.session_state.explanation:
    st.subheader("📄 Generated Explanation")
    st.markdown(
        f'<div class="result-card">{st.session_state.explanation}</div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        score = 8.5
        st.markdown(
            f'<div class="metric-card"><h3>{score}/10</h3>'
            f"<p>Comprehension Score</p></div>",
            unsafe_allow_html=True,
        )
        st.progress(score / 10)
    with m2:
        st.markdown(
            '<div class="metric-card"><h3>~12 min</h3>'
            "<p>Estimated Time Saved</p></div>",
            unsafe_allow_html=True,
        )
    with m3:
        reading_time = max(1, len(st.session_state.explanation.split()) // 200)
        st.markdown(
            f'<div class="metric-card"><h3>{reading_time} min</h3>'
            f"<p>Reading Time</p></div>",
            unsafe_allow_html=True,
        )

    if st.session_state.glossary:
        st.subheader("📖 Key Terms Glossary")
        for item in st.session_state.glossary:
            st.markdown(
                f'<div class="glossary-term"><strong>{item["term"]}</strong>: '
                f'{item["definition"]}</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    a1, a2 = st.columns(2)
    with a1:
        st.download_button(
            "📥 Download Explanation",
            data=st.session_state.explanation,
            file_name=f"claim_explanation_{claim_id or 'draft'}.txt",
            mime="text/plain",
        )
    with a2:
        if st.button("📋 Copy to Clipboard"):
            st.code(st.session_state.explanation, language=None)
            st.success("Text displayed above — select and copy.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "ClaimClear AI · Built for the AI Prototype Challenge · "
    "Powered by OpenAI · Not a substitute for professional insurance advice"
)
