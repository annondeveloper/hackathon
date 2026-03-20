"""
pipeline.py - Agentic multi-step pipeline for claim explanation generation.

Pipeline stages:
    1. ANALYZE   - Extract key factors, complexity, and jargon from the claim.
    2. GENERATE  - Produce a structured explanation grounded in policy terms
                   and augmented with RAG-retrieved policy knowledge.
    3. EVALUATE  - Self-critique the explanation for accuracy, tone, readability,
                   and completeness.
    4. REFINE    - (Conditional) If the evaluation score falls below the quality
                   threshold, refine the explanation using the feedback.

Modern AI techniques:
    - Structured Outputs  - JSON schema enforcement via OpenAI response_format
    - Chain-of-Thought    - analysis step produces reasoning before generation
    - RAG Grounding       - PolicyStore injects relevant policy knowledge
    - Self-Evaluation     - LLM critiques its own output
    - Conditional Refine  - only runs when quality < threshold (saves tokens)
    - Few-Shot Prompting  - one gold-standard example anchors output style
    - Token Efficiency    - compact system prompts, focused user prompts
    - Model-Agnostic      - works with OpenAI, Azure, or custom endpoints
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from openai import OpenAI

from policy_store import PolicyStore, RAGContext

# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ClaimInput:
    """User-submitted claim data."""

    claim_id: str
    customer_name: str
    policy_type: str
    claim_amount: float
    decision: str
    decision_reason: str
    policy_terms: str
    tone: str = "Simple & Friendly"
    reading_level: str = "Basic"


@dataclass
class AnalysisResult:
    """Stage 1 output - structured claim analysis."""

    complexity: str           # "low" | "medium" | "high"
    key_factors: list[str]    # most important decision factors
    jargon_terms: list[str]   # insurance terms needing plain-language definitions
    customer_impact: str      # one-sentence summary
    missing_info: list[str]   # anything unclear from the input


@dataclass
class GlossaryTerm:
    """A single glossary entry."""

    term: str
    definition: str


@dataclass
class EvaluationResult:
    """Stage 3 output - self-evaluation scores and feedback."""

    accuracy_score: int       # 1-10
    empathy_score: int        # 1-10
    readability_score: int    # 1-10
    completeness_score: int   # 1-10
    overall_score: int        # 1-10
    issues: list[str]
    suggestions: list[str]


@dataclass
class PipelineResult:
    """Final output from the full pipeline."""

    explanation: str
    glossary: list[GlossaryTerm]
    analysis: AnalysisResult
    evaluation: EvaluationResult
    rag_context: RAGContext | None = None
    was_refined: bool = False
    total_tokens_used: int = 0
    processing_time_ms: int = 0
    stages_completed: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Model Configuration
# ═══════════════════════════════════════════════════════════════════════════

# Pre-configured model providers
MODEL_PROVIDERS = {
    "gpt-4o-mini": {
        "label": "OpenAI GPT-4o Mini",
        "base_url": None,
        "needs_api_key": True,
    },
    "gpt-4o": {
        "label": "OpenAI GPT-4o",
        "base_url": None,
        "needs_api_key": True,
    },
    "azure/genailab-maas-gpt-4o": {
        "label": "TCS GenAI Lab (GPT-4o)",
        "base_url": "https://genailab.tcs.in",
        "needs_api_key": False,
    },
}


def get_openai_client(
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAI:
    """Create an OpenAI-compatible client for any provider."""
    provider = MODEL_PROVIDERS.get(model, {})
    effective_url = base_url or provider.get("base_url")
    effective_key = api_key or "not-needed"

    kwargs = {"api_key": effective_key}
    if effective_url:
        kwargs["base_url"] = effective_url

    return OpenAI(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# System Prompts
# ═══════════════════════════════════════════════════════════════════════════

ANALYZE_SYSTEM = (
    "You analyze insurance claims to prepare for explanation generation.\n"
    "Given claim details, extract structured analysis. Be precise and concise.\n\n"
    "Reply as JSON:\n"
    '{"complexity":"low|medium|high","key_factors":["..."],'
    '"jargon_terms":["..."],"customer_impact":"...","missing_info":["..."]}'
)

GENERATE_SYSTEM = (
    "You are ClaimClear AI. Write a clear, personalized letter explaining an "
    "insurance claim decision.\n\n"
    "Rules:\n"
    "- Address customer by name, reference claim ID\n"
    "- State decision clearly upfront\n"
    "- Explain reasoning in plain language, citing ONLY provided policy terms\n"
    "- When citing policy sections, include the page number if available\n"
    "- Include 2-3 concrete next steps\n"
    "- Match requested tone and reading level\n"
    "- Do NOT invent policy terms or sections not in the input\n"
    "- Keep under 300 words\n\n"
    "Context from analysis and policy documents will help you focus on what matters.\n\n"
    "Reply as JSON:\n"
    '{"explanation":"<letter with \\\\n\\\\n between paragraphs>",'
    '"glossary":[{"term":"...","definition":"..."}]}\n'
    "Include 3-5 glossary entries for terms a layperson needs defined."
)

EVALUATE_SYSTEM = (
    "You evaluate insurance claim explanations for quality.\n"
    "Score each dimension 1-10 and identify specific issues.\n\n"
    "Reply as JSON:\n"
    '{"accuracy_score":N,"empathy_score":N,"readability_score":N,'
    '"completeness_score":N,"overall_score":N,'
    '"issues":["..."],"suggestions":["..."]}'
)

REFINE_SYSTEM = (
    "You improve insurance claim explanations based on evaluation feedback.\n"
    "Fix the specific issues identified. Keep the same structure and format.\n"
    "Do NOT add content beyond what is needed to fix the issues.\n\n"
    "Reply as JSON:\n"
    '{"explanation":"<improved letter>",'
    '"glossary":[{"term":"...","definition":"..."}]}'
)

# ═══════════════════════════════════════════════════════════════════════════
# Few-Shot Example
# ═══════════════════════════════════════════════════════════════════════════

_FEW_SHOT_USER = {
    "role": "user",
    "content": (
        "Claim ID: CLM-2024-63318\n"
        "Customer: Patricia Nguyen\n"
        "Policy: Home | Amount: $28,500.00\n"
        "Decision: Approved\n"
        "Reason: Burst pipe water damage, approved in full.\n"
        "Policy terms: Section 4.1 Water Damage, Section 6.3 Living Expenses, "
        "Section 9.1 Personal Property\n"
        "Tone: Simple & Friendly | Reading level: Basic\n\n"
        "Analysis - Complexity: low\n"
        "Key factors: burst pipe, sudden damage, full coverage\n"
        "Terms to define: covered peril, adjuster, additional living expenses\n"
        "Customer impact: Full claim approved, customer receives payment.\n\n"
        "Relevant policy knowledge:\n"
        "[SilverShield_Master_Policy.pdf, p.7, Section 11.2 - Water Damage]: "
        "Sudden and accidental water damage from burst pipes is a covered peril."
    ),
}

_FEW_SHOT_ASSISTANT = {
    "role": "assistant",
    "content": json.dumps({
        "explanation": (
            "Dear Patricia,\n\n"
            "Thank you for filing your homeowners claim (CLM-2024-63318). "
            "We're pleased to let you know that your claim has been "
            "**approved in full** for $28,500.\n\n"
            "**What happened:** The burst pipe in your second-floor bathroom "
            "caused water damage to your floors, walls, and personal "
            "belongings. Our adjuster confirmed this was a sudden, accidental "
            "event - which is covered under your policy (Section 4.1, p.3).\n\n"
            "**What's covered:**\n"
            "- Structural repairs: $18,200\n"
            "- Personal property replacement: $7,800\n"
            "- Temporary housing (up to 3 weeks): $2,500\n\n"
            "**Your next steps:**\n"
            "1. You'll receive payment within 10 business days\n"
            "2. Contact our claims team at 1-800-555-0199 to arrange "
            "temporary housing\n"
            "3. Keep all repair receipts for your records\n\n"
            "We're glad we could help during this difficult time. "
            "Please reach out if you have any questions."
        ),
        "glossary": [
            {
                "term": "Covered Peril",
                "definition": "A specific risk or cause of damage that your "
                "insurance policy protects against.",
            },
            {
                "term": "Adjuster",
                "definition": "A professional who inspects damage and determines "
                "how much the insurance company should pay.",
            },
            {
                "term": "Additional Living Expenses",
                "definition": "Money your insurance pays for temporary housing "
                "when your home can't be lived in due to covered damage.",
            },
        ],
    }),
}


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline
# ═══════════════════════════════════════════════════════════════════════════


class ClaimExplanationPipeline:
    """Agentic pipeline: Analyze -> Generate (RAG) -> Evaluate -> Refine.

    Supports OpenAI, Azure, TCS GenAI Lab, or any OpenAI-compatible endpoint.

    Args:
        api_key:      API key (optional for whitelisted endpoints).
        model:        Model identifier.
        base_url:     Custom API endpoint (overrides provider defaults).
        policy_store: Optional pre-built PolicyStore instance.
    """

    QUALITY_THRESHOLD = 7

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        policy_store: PolicyStore | None = None,
    ):
        self.client = get_openai_client(model, api_key, base_url)
        self.model = model
        self.policy_store = policy_store or PolicyStore()
        self._total_tokens = 0

        # Try to build vector index for better RAG
        if api_key:
            provider = MODEL_PROVIDERS.get(model, {})
            embed_url = base_url or provider.get("base_url")
            self.policy_store.build_vector_index(
                api_key=api_key, base_url=embed_url,
            )

    # ── Public API ────────────────────────────────────────────────────

    def run(
        self,
        claim: ClaimInput,
        on_stage: Callable[[str, Any], None] | None = None,
    ) -> PipelineResult:
        """Execute the full pipeline."""
        start = time.time()
        stages: list[str] = []

        def _notify(name: str, data: Any = None) -> None:
            if on_stage:
                on_stage(name, data)

        # Stage 1: Analyze
        _notify("analyzing")
        analysis = self._analyze(claim)
        stages.append("analyze")
        _notify("analyzed", analysis)

        # Stage 2: Generate (with RAG context)
        _notify("retrieving")
        rag_context = self._retrieve_policy_context(claim)
        _notify("retrieved", rag_context)

        _notify("generating")
        explanation, glossary = self._generate(claim, analysis, rag_context)
        stages.append("generate")
        _notify("generated", {"explanation": explanation, "glossary": glossary})

        # Stage 3: Evaluate
        _notify("evaluating")
        evaluation = self._evaluate(claim, explanation)
        stages.append("evaluate")
        _notify("evaluated", evaluation)

        # Stage 4: Conditional Refine
        was_refined = False
        if evaluation.overall_score < self.QUALITY_THRESHOLD and evaluation.issues:
            _notify("refining")
            explanation, glossary = self._refine(
                claim, explanation, glossary, evaluation,
            )
            was_refined = True
            stages.append("refine")
            _notify("refined", {"explanation": explanation, "glossary": glossary})

        elapsed_ms = int((time.time() - start) * 1000)

        return PipelineResult(
            explanation=explanation,
            glossary=[
                GlossaryTerm(**g) if isinstance(g, dict) else g for g in glossary
            ],
            analysis=analysis,
            evaluation=evaluation,
            rag_context=rag_context,
            was_refined=was_refined,
            total_tokens_used=self._total_tokens,
            processing_time_ms=elapsed_ms,
            stages_completed=stages,
        )

    # ── LLM Helper ────────────────────────────────────────────────────

    def _call_llm(
        self,
        system: str,
        user: str,
        extra_messages: list[dict] | None = None,
    ) -> tuple[str, int]:
        """Send a chat-completion request and return (content, tokens)."""
        messages: list[dict] = [{"role": "system", "content": system}]
        if extra_messages:
            messages.extend(extra_messages)
        messages.append({"role": "user", "content": user})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        self._total_tokens += tokens
        return content, tokens

    # ── Stage 1: Analyze ──────────────────────────────────────────────

    def _analyze(self, claim: ClaimInput) -> AnalysisResult:
        user_msg = (
            f"Claim: {claim.claim_id} | {claim.policy_type} "
            f"| ${claim.claim_amount:,.2f}\n"
            f"Decision: {claim.decision}\n"
            f"Reason: {claim.decision_reason}\n"
            f"Terms: {claim.policy_terms}"
        )
        content, _ = self._call_llm(ANALYZE_SYSTEM, user_msg)
        data = json.loads(content)
        return AnalysisResult(
            complexity=data.get("complexity", "medium"),
            key_factors=data.get("key_factors", []),
            jargon_terms=data.get("jargon_terms", []),
            customer_impact=data.get("customer_impact", ""),
            missing_info=data.get("missing_info", []),
        )

    # ── RAG Retrieval ─────────────────────────────────────────────────

    def _retrieve_policy_context(self, claim: ClaimInput) -> RAGContext:
        """Retrieve relevant policy sections from the knowledge store."""
        query = f"{claim.policy_type} {claim.decision} {claim.decision_reason}"
        return self.policy_store.search(query, claim.policy_type, top_k=3)

    # ── Stage 2: Generate ─────────────────────────────────────────────

    def _generate(
        self,
        claim: ClaimInput,
        analysis: AnalysisResult,
        rag_context: RAGContext,
    ) -> tuple[str, list[dict]]:
        parts = [
            f"Claim ID: {claim.claim_id}",
            f"Customer: {claim.customer_name}",
            f"Policy: {claim.policy_type} | Amount: ${claim.claim_amount:,.2f}",
            f"Decision: {claim.decision}",
            f"Reason: {claim.decision_reason}",
            f"Policy terms: {claim.policy_terms}",
            f"Tone: {claim.tone} | Reading level: {claim.reading_level}",
            "",
            f"Analysis - Complexity: {analysis.complexity}",
            f"Key factors: {', '.join(analysis.key_factors)}",
            f"Terms to define: {', '.join(analysis.jargon_terms)}",
            f"Customer impact: {analysis.customer_impact}",
        ]
        if rag_context.context_text:
            parts += ["", rag_context.context_text]

        content, _ = self._call_llm(
            GENERATE_SYSTEM,
            "\n".join(parts),
            extra_messages=[_FEW_SHOT_USER, _FEW_SHOT_ASSISTANT],
        )
        data = json.loads(content)
        return data.get("explanation", ""), data.get("glossary", [])

    # ── Stage 3: Evaluate ─────────────────────────────────────────────

    def _evaluate(self, claim: ClaimInput, explanation: str) -> EvaluationResult:
        user_msg = (
            f"Original claim decision: {claim.decision}\n"
            f"Decision reason: {claim.decision_reason}\n"
            f"Policy terms provided: {claim.policy_terms}\n"
            f"Target tone: {claim.tone} | "
            f"Target reading level: {claim.reading_level}\n\n"
            f"Generated explanation:\n{explanation}"
        )
        content, _ = self._call_llm(EVALUATE_SYSTEM, user_msg)
        data = json.loads(content)
        return EvaluationResult(
            accuracy_score=data.get("accuracy_score", 5),
            empathy_score=data.get("empathy_score", 5),
            readability_score=data.get("readability_score", 5),
            completeness_score=data.get("completeness_score", 5),
            overall_score=data.get("overall_score", 5),
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
        )

    # ── Stage 4: Refine ───────────────────────────────────────────────

    def _refine(
        self,
        claim: ClaimInput,
        explanation: str,
        glossary: list[dict],
        evaluation: EvaluationResult,
    ) -> tuple[str, list[dict]]:
        issues_text = "\n".join(f"- {i}" for i in evaluation.issues)
        suggestions_text = "\n".join(f"- {s}" for s in evaluation.suggestions)
        user_msg = (
            f"Original explanation:\n{explanation}\n\n"
            f"Issues found:\n{issues_text}\n\n"
            f"Suggestions:\n{suggestions_text}\n\n"
            f"Target tone: {claim.tone} | "
            f"Reading level: {claim.reading_level}\n"
            f"Policy terms (ground truth): {claim.policy_terms}"
        )
        content, _ = self._call_llm(REFINE_SYSTEM, user_msg)
        data = json.loads(content)
        return (
            data.get("explanation", explanation),
            data.get("glossary", glossary),
        )
