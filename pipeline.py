"""
pipeline.py - Agentic multi-step pipeline for claim explanation generation.

Architecture (3-stage agentic pipeline):
  1. ANALYZE  — Extract key factors, determine complexity, identify jargon
  2. GENERATE — Produce structured explanation grounded in policy terms (RAG-enhanced)
  3. EVALUATE & REFINE — Self-critique for accuracy, tone, and readability;
                         conditionally refine if quality score < threshold

Modern AI techniques used:
  - Structured Outputs (JSON schema enforcement)
  - Chain-of-thought reasoning (analysis step before generation)
  - Self-evaluation with conditional refinement loop
  - RAG-style policy grounding via policy_store
  - Few-shot prompting for consistent quality
  - Token-efficient prompt engineering
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

from policy_store import PolicyStore


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ClaimInput:
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
    """Output of Stage 1 — claim analysis."""
    complexity: str          # "low" | "medium" | "high"
    key_factors: list[str]   # most important factors in the decision
    jargon_terms: list[str]  # insurance terms that need explaining
    customer_impact: str     # one-sentence summary of impact on customer
    missing_info: list[str]  # anything unclear from the input


@dataclass
class GlossaryTerm:
    term: str
    definition: str


@dataclass
class EvaluationResult:
    """Output of Stage 3 — self-evaluation."""
    accuracy_score: int       # 1-10: are policy references correct?
    empathy_score: int        # 1-10: is the tone appropriate?
    readability_score: int    # 1-10: matches target reading level?
    completeness_score: int   # 1-10: are next steps included?
    overall_score: int        # 1-10
    issues: list[str]         # specific problems found
    suggestions: list[str]    # concrete improvements


@dataclass
class PipelineResult:
    """Final output from the full pipeline."""
    explanation: str
    glossary: list[GlossaryTerm]
    analysis: AnalysisResult
    evaluation: EvaluationResult
    was_refined: bool = False
    total_tokens_used: int = 0
    processing_time_ms: int = 0
    stages_completed: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompts — compact, token-efficient
# ---------------------------------------------------------------------------

ANALYZE_SYSTEM = """You analyze insurance claims to prepare for explanation generation.
Given claim details, extract structured analysis. Be precise and concise.

Reply as JSON:
{"complexity":"low|medium|high","key_factors":["..."],"jargon_terms":["..."],"customer_impact":"...","missing_info":["..."]}"""

GENERATE_SYSTEM = """You are ClaimClear AI. Write a clear, personalized letter explaining an insurance claim decision.

Rules:
- Address customer by name, reference claim ID
- State decision clearly upfront
- Explain reasoning in plain language, citing ONLY provided policy terms
- Include 2-3 concrete next steps
- Match requested tone and reading level
- Do NOT invent policy terms or sections not in the input
- Keep under 300 words

Context from analysis will help you focus on what matters most.

Reply as JSON:
{"explanation":"<letter with \\n\\n between paragraphs>","glossary":[{"term":"...","definition":"..."}]}
Include 3-5 glossary entries for terms a layperson needs defined."""

EVALUATE_SYSTEM = """You evaluate insurance claim explanations for quality.
Score each dimension 1-10 and identify specific issues.

Reply as JSON:
{"accuracy_score":N,"empathy_score":N,"readability_score":N,"completeness_score":N,"overall_score":N,"issues":["..."],"suggestions":["..."]}"""

REFINE_SYSTEM = """You improve insurance claim explanations based on evaluation feedback.
Fix the specific issues identified. Keep the same structure and format.
Do NOT add content beyond what's needed to fix the issues.

Reply as JSON:
{"explanation":"<improved letter>","glossary":[{"term":"...","definition":"..."}]}"""

# ---------------------------------------------------------------------------
# Few-shot example (one high-quality example for consistent output)
# ---------------------------------------------------------------------------

FEW_SHOT_EXAMPLE = {
    "role": "assistant",
    "content": json.dumps({
        "explanation": (
            "Dear Patricia,\n\n"
            "Thank you for filing your homeowners claim (CLM-2024-63318). "
            "We're pleased to let you know that your claim has been **approved in full** "
            "for $28,500.\n\n"
            "**What happened:** The burst pipe in your second-floor bathroom caused water "
            "damage to your floors, walls, and personal belongings. Our adjuster confirmed "
            "this was a sudden, accidental event — which is covered under your policy "
            "(Section 4.1).\n\n"
            "**What's covered:**\n"
            "- Structural repairs: $18,200\n"
            "- Personal property replacement: $7,800\n"
            "- Temporary housing (up to 3 weeks): $2,500\n\n"
            "**Your next steps:**\n"
            "1. You'll receive payment within 10 business days\n"
            "2. Contact our claims team at 1-800-555-0199 to arrange temporary housing\n"
            "3. Keep all repair receipts for your records\n\n"
            "We're glad we could help during this difficult time. Please reach out if you "
            "have any questions."
        ),
        "glossary": [
            {"term": "Covered Peril", "definition": "A specific risk or cause of damage that your insurance policy protects against."},
            {"term": "Adjuster", "definition": "A professional who inspects damage and determines how much the insurance company should pay."},
            {"term": "Additional Living Expenses", "definition": "Money your insurance pays for temporary housing when your home can't be lived in due to covered damage."},
        ]
    })
}


# ---------------------------------------------------------------------------
# Pipeline class
# ---------------------------------------------------------------------------

class ClaimExplanationPipeline:
    """Multi-step agentic pipeline for generating claim explanations."""

    QUALITY_THRESHOLD = 7  # minimum overall_score to skip refinement

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        policy_store: Optional[PolicyStore] = None,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.policy_store = policy_store or PolicyStore()
        self._total_tokens = 0

    def run(self, claim: ClaimInput, on_stage: callable = None) -> PipelineResult:
        """Execute the full pipeline. on_stage(name, data) is called after each stage."""
        start = time.time()
        stages = []

        # --- Stage 1: Analyze ---
        if on_stage:
            on_stage("analyzing", None)
        analysis = self._analyze(claim)
        stages.append("analyze")
        if on_stage:
            on_stage("analyzed", analysis)

        # --- Stage 2: Generate (with RAG context) ---
        if on_stage:
            on_stage("generating", None)
        rag_context = self._retrieve_policy_context(claim)
        explanation, glossary = self._generate(claim, analysis, rag_context)
        stages.append("generate")
        if on_stage:
            on_stage("generated", {"explanation": explanation, "glossary": glossary})

        # --- Stage 3: Evaluate ---
        if on_stage:
            on_stage("evaluating", None)
        evaluation = self._evaluate(claim, explanation)
        stages.append("evaluate")
        if on_stage:
            on_stage("evaluated", evaluation)

        # --- Stage 4: Conditional Refine ---
        was_refined = False
        if evaluation.overall_score < self.QUALITY_THRESHOLD and evaluation.issues:
            if on_stage:
                on_stage("refining", None)
            explanation, glossary = self._refine(claim, explanation, glossary, evaluation)
            was_refined = True
            stages.append("refine")
            if on_stage:
                on_stage("refined", {"explanation": explanation, "glossary": glossary})

        elapsed = int((time.time() - start) * 1000)

        return PipelineResult(
            explanation=explanation,
            glossary=[GlossaryTerm(**g) if isinstance(g, dict) else g for g in glossary],
            analysis=analysis,
            evaluation=evaluation,
            was_refined=was_refined,
            total_tokens_used=self._total_tokens,
            processing_time_ms=elapsed,
            stages_completed=stages,
        )

    # --- Stage implementations ---

    def _call_llm(self, system: str, user: str, extra_messages: list = None) -> tuple[str, int]:
        """Make an LLM call and return (content, tokens_used)."""
        messages = [{"role": "system", "content": system}]
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

    def _analyze(self, claim: ClaimInput) -> AnalysisResult:
        """Stage 1: Analyze the claim to extract key factors and complexity."""
        user_msg = (
            f"Claim: {claim.claim_id} | {claim.policy_type} | ${claim.claim_amount:,.2f}\n"
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

    def _retrieve_policy_context(self, claim: ClaimInput) -> str:
        """RAG: retrieve relevant policy sections based on claim context."""
        query = f"{claim.policy_type} {claim.decision} {claim.decision_reason}"
        results = self.policy_store.search(query, claim.policy_type, top_k=3)
        if not results:
            return ""
        return "Relevant policy knowledge:\n" + "\n".join(
            f"- {r['section']}: {r['text']}" for r in results
        )

    def _generate(
        self,
        claim: ClaimInput,
        analysis: AnalysisResult,
        rag_context: str,
    ) -> tuple[str, list[dict]]:
        """Stage 2: Generate the explanation grounded in analysis + RAG context."""
        # Build a compact user prompt enriched with analysis
        parts = [
            f"Claim ID: {claim.claim_id}",
            f"Customer: {claim.customer_name}",
            f"Policy: {claim.policy_type} | Amount: ${claim.claim_amount:,.2f}",
            f"Decision: {claim.decision}",
            f"Reason: {claim.decision_reason}",
            f"Policy terms: {claim.policy_terms}",
            f"Tone: {claim.tone} | Reading level: {claim.reading_level}",
            "",
            f"Analysis — Complexity: {analysis.complexity}",
            f"Key factors: {', '.join(analysis.key_factors)}",
            f"Terms to define: {', '.join(analysis.jargon_terms)}",
            f"Customer impact: {analysis.customer_impact}",
        ]
        if rag_context:
            parts.append("")
            parts.append(rag_context)

        user_msg = "\n".join(parts)

        # Include few-shot example for quality anchoring
        few_shot_user = {
            "role": "user",
            "content": (
                "Claim ID: CLM-2024-63318\nCustomer: Patricia Nguyen\n"
                "Policy: Home | Amount: $28,500.00\nDecision: Approved\n"
                "Reason: Burst pipe water damage, approved in full.\n"
                "Policy terms: Section 4.1 Water Damage, Section 6.3 Living Expenses, Section 9.1 Personal Property\n"
                "Tone: Simple & Friendly | Reading level: Basic\n\n"
                "Analysis — Complexity: low\nKey factors: burst pipe, sudden damage, full coverage\n"
                "Terms to define: covered peril, adjuster, additional living expenses\n"
                "Customer impact: Full claim approved, customer receives payment."
            ),
        }

        content, _ = self._call_llm(
            GENERATE_SYSTEM,
            user_msg,
            extra_messages=[few_shot_user, FEW_SHOT_EXAMPLE],
        )
        data = json.loads(content)
        return data.get("explanation", ""), data.get("glossary", [])

    def _evaluate(self, claim: ClaimInput, explanation: str) -> EvaluationResult:
        """Stage 3: Self-evaluate the generated explanation."""
        user_msg = (
            f"Original claim decision: {claim.decision}\n"
            f"Decision reason: {claim.decision_reason}\n"
            f"Policy terms provided: {claim.policy_terms}\n"
            f"Target tone: {claim.tone} | Target reading level: {claim.reading_level}\n\n"
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

    def _refine(
        self,
        claim: ClaimInput,
        explanation: str,
        glossary: list[dict],
        evaluation: EvaluationResult,
    ) -> tuple[str, list[dict]]:
        """Stage 4: Refine based on evaluation feedback."""
        user_msg = (
            f"Original explanation:\n{explanation}\n\n"
            f"Issues found:\n" + "\n".join(f"- {i}" for i in evaluation.issues) + "\n\n"
            f"Suggestions:\n" + "\n".join(f"- {s}" for s in evaluation.suggestions) + "\n\n"
            f"Target tone: {claim.tone} | Reading level: {claim.reading_level}\n"
            f"Policy terms (ground truth): {claim.policy_terms}"
        )
        content, _ = self._call_llm(REFINE_SYSTEM, user_msg)
        data = json.loads(content)
        return (
            data.get("explanation", explanation),
            data.get("glossary", glossary),
        )
