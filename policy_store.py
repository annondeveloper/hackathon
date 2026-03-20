"""
policy_store.py - RAG-style policy knowledge store.

Provides relevant policy context to ground LLM explanations in real policy
knowledge, reducing hallucination and improving accuracy.

This is a lightweight in-memory implementation suitable for a prototype.
In production, this would use a vector database (Pinecone, Chroma, etc.)
with OpenAI embeddings for semantic search.

For the prototype, we use keyword-based retrieval with TF-IDF-like scoring,
which is fast, requires no API calls, and demonstrates the RAG pattern.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class PolicySection:
    policy_type: str  # Health, Auto, Home, Life, Travel
    section: str      # e.g., "Section 4.2 - Network Requirements"
    text: str         # full text of the section
    keywords: list[str]  # pre-extracted keywords for fast matching


class PolicyStore:
    """Simple keyword-based policy knowledge retrieval."""

    def __init__(self):
        self._sections: list[PolicySection] = []
        self._load_knowledge_base()

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from text."""
        # Remove common stop words and extract significant terms
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "or", "and", "not", "no",
            "but", "if", "than", "that", "this", "these", "those", "it", "its",
            "any", "all", "each", "every", "such", "more", "most", "other",
        }
        words = re.findall(r"[a-z]+", text.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _add(self, policy_type: str, section: str, text: str):
        keywords = self._extract_keywords(f"{section} {text}")
        self._sections.append(PolicySection(
            policy_type=policy_type,
            section=section,
            text=text,
            keywords=keywords,
        ))

    def search(
        self, query: str, policy_type: str = None, top_k: int = 3
    ) -> list[dict]:
        """Find the most relevant policy sections for a query."""
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return []

        query_counts = Counter(query_keywords)
        scored = []

        for sec in self._sections:
            # Boost score if policy type matches
            type_boost = 2.0 if (policy_type and sec.policy_type == policy_type) else 1.0

            # Count keyword overlaps
            sec_counts = Counter(sec.keywords)
            overlap = sum(
                min(query_counts[k], sec_counts[k])
                for k in query_counts
                if k in sec_counts
            )

            if overlap > 0:
                score = overlap * type_boost
                scored.append((score, sec))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {"section": s.section, "text": s.text, "score": round(score, 2)}
            for score, s in scored[:top_k]
        ]

    def _load_knowledge_base(self):
        """Load comprehensive insurance policy knowledge."""

        # --- Health Insurance ---
        self._add("Health", "Network Provider Requirements",
            "All non-emergency services must be obtained from in-network providers. "
            "Out-of-network services are not covered unless a network gap exception "
            "applies (no in-network provider within 50 miles).")

        self._add("Health", "Prior Authorization",
            "Advanced imaging (MRI, CT, PET scans), specialty referrals, and "
            "elective procedures require prior authorization submitted at least "
            "5 business days before the scheduled date. Failure to obtain prior "
            "authorization may result in claim denial.")

        self._add("Health", "Emergency Services",
            "Emergency room visits are covered at in-network rates regardless of "
            "facility network status. Emergency is defined as a condition that "
            "a prudent layperson would reasonably believe requires immediate "
            "medical attention to prevent serious harm.")

        self._add("Health", "Deductible and Cost Sharing",
            "The annual deductible must be met before the plan pays benefits. "
            "After the deductible, the plan pays a percentage (typically 80%) "
            "and the member pays coinsurance (typically 20%) until the "
            "out-of-pocket maximum is reached.")

        self._add("Health", "Appeals Process",
            "Members have the right to appeal any claim denial. Internal appeals "
            "must be filed within 180 days of the denial notice. The plan must "
            "respond within 30 days for pre-service appeals and 60 days for "
            "post-service appeals. External review is available after internal "
            "appeal is exhausted.")

        # --- Auto Insurance ---
        self._add("Auto", "Collision Coverage",
            "Covers damage to the insured vehicle resulting from collision with "
            "another vehicle or object, regardless of fault. Subject to the "
            "stated deductible. Does not cover mechanical breakdown or wear.")

        self._add("Auto", "Comprehensive Coverage",
            "Covers non-collision damage including theft, vandalism, natural "
            "disasters, falling objects, and animal strikes. Subject to the "
            "stated deductible.")

        self._add("Auto", "Aftermarket Modifications",
            "Custom parts, aftermarket modifications, and non-factory equipment "
            "are only covered if specifically declared on the policy with "
            "supplemental coverage. Undeclared modifications are excluded.")

        self._add("Auto", "Liability Coverage",
            "Covers bodily injury and property damage you cause to others in an "
            "accident. Includes legal defense costs. Minimum limits vary by state.")

        self._add("Auto", "Deductible Application",
            "The deductible is applied per incident before benefit calculation. "
            "Choosing a higher deductible lowers premiums but increases "
            "out-of-pocket costs per claim.")

        # --- Home Insurance ---
        self._add("Home", "Water Damage Coverage",
            "Sudden and accidental water damage from burst pipes, appliance "
            "overflow, or plumbing failures is a covered peril. Gradual water "
            "damage, mold from long-term moisture, and flood damage are excluded.")

        self._add("Home", "Additional Living Expenses",
            "When the home is uninhabitable due to a covered loss, reasonable "
            "costs for temporary housing, meals, and transportation are covered "
            "up to 20% of dwelling coverage for up to 12 months.")

        self._add("Home", "Personal Property Coverage",
            "Replacement cost coverage for personal belongings damaged by a "
            "covered peril. High-value items (jewelry, art, electronics over "
            "$2,500) may require scheduled coverage.")

        self._add("Home", "Exclusions",
            "Standard exclusions include flood, earthquake, normal wear and tear, "
            "pest damage, neglect, and intentional damage. Separate policies or "
            "endorsements are available for some excluded perils.")

        # --- Life Insurance ---
        self._add("Life", "Contestability Period",
            "During the first two years after policy issuance, the insurer may "
            "contest the policy based on material misrepresentations in the "
            "application. After two years, only fraud can void the policy.")

        self._add("Life", "Material Misrepresentation",
            "Failure to disclose pre-existing medical conditions, tobacco use, "
            "hazardous occupations, or other facts that would have affected "
            "underwriting decisions constitutes material misrepresentation.")

        self._add("Life", "Beneficiary Claims",
            "Death benefits are paid to the named beneficiary within 30-60 days "
            "of receiving a valid claim with required documentation (death "
            "certificate, claim form, policy number).")

        # --- Travel Insurance ---
        self._add("Travel", "Trip Cancellation",
            "Covers non-refundable trip costs when cancellation is due to "
            "covered reasons: illness, injury, death of insured or family "
            "member, jury duty, natural disaster at destination, or terrorism.")

        self._add("Travel", "Documentation Requirements",
            "Medical cancellation claims require a signed physician's statement "
            "within 30 days. All claims must be filed within 90 days of the "
            "covered event with original receipts and booking confirmations.")

        self._add("Travel", "Trip Interruption",
            "If a trip is cut short due to a covered reason, covers unused "
            "non-refundable expenses plus reasonable additional transportation "
            "costs to return home.")
