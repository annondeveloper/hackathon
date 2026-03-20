"""
sample_data.py - Sample insurance claims for ClaimClear AI demo and testing.

Each sample claim is a dictionary matching the input fields of the application.
These provide realistic scenarios across different policy types and decisions.
"""

SAMPLE_CLAIMS = [
    {
        "label": "Denied Health — Out-of-Network",
        "claim_id": "CLM-2024-78432",
        "customer_name": "Maria Santos",
        "policy_type": "Health",
        "claim_amount": 4750.00,
        "decision": "Denied",
        "decision_reason": (
            "The claim for an MRI and consultation at Lakewood Imaging Center "
            "has been denied because the provider is out-of-network. The "
            "member's current plan (Silver PPO 3000) requires the use of "
            "in-network providers for diagnostic imaging services. "
            "Additionally, no prior authorization was obtained before the "
            "procedure, which is required for all advanced imaging under "
            "Section 8.4 of the policy agreement."
        ),
        "policy_terms": (
            "Section 5.2 - Network Provider Requirements: All non-emergency "
            "diagnostic imaging must be performed by in-network providers.\n"
            "Section 8.4 - Prior Authorization: Advanced imaging (MRI, CT, "
            "PET) requires prior authorization submitted at least 5 business "
            "days before the scheduled procedure.\n"
            "Section 12.1 - Out-of-Network Exceptions: Emergency situations "
            "or when no in-network provider is available within 50 miles."
        ),
    },
    {
        "label": "Partial Auto — Aftermarket Excluded",
        "claim_id": "CLM-2024-91205",
        "customer_name": "James Whitfield",
        "policy_type": "Auto",
        "claim_amount": 12300.00,
        "decision": "Partially Approved",
        "decision_reason": (
            "The collision claim has been partially approved. The repair costs "
            "for the 2022 Honda Accord have been assessed at $12,300. After "
            "applying the $1,000 deductible, the approved payout is $11,300. "
            "However, $2,100 of the claimed amount for aftermarket spoiler "
            "and custom rims is excluded as these modifications were not "
            "declared on the policy and are not covered under the standard "
            "collision coverage."
        ),
        "policy_terms": (
            "Section 3.1 - Collision Coverage: Covers damage to the insured "
            "vehicle resulting from collision, subject to the stated deductible.\n"
            "Section 3.5 - Aftermarket Modifications: Custom parts and "
            "equipment are only covered if declared and added to the policy "
            "with supplemental coverage.\n"
            "Section 7.2 - Deductible Application: The deductible is applied "
            "per incident before benefit calculation."
        ),
    },
    {
        "label": "Approved Home — Water Damage",
        "claim_id": "CLM-2024-63318",
        "customer_name": "Patricia Nguyen",
        "policy_type": "Home",
        "claim_amount": 28500.00,
        "decision": "Approved",
        "decision_reason": (
            "The claim for water damage resulting from a burst pipe during "
            "the January freeze has been approved in full. The adjuster's "
            "inspection confirmed sudden and accidental water discharge from "
            "the second-floor bathroom, causing damage to flooring, drywall, "
            "and personal belongings. The total approved amount of $28,500 "
            "covers structural repairs ($18,200), personal property "
            "replacement ($7,800), and temporary housing costs ($2,500) for "
            "the estimated 3-week repair period."
        ),
        "policy_terms": (
            "Section 4.1 - Water Damage: Sudden and accidental discharge of "
            "water from household plumbing systems is a covered peril.\n"
            "Section 6.3 - Additional Living Expenses: Reasonable costs for "
            "temporary housing when the home is uninhabitable due to a "
            "covered loss, up to 20% of dwelling coverage.\n"
            "Section 9.1 - Personal Property: Replacement cost coverage for "
            "personal belongings damaged by a covered peril."
        ),
    },
    {
        "label": "Under Review Travel — Trip Cancellation",
        "claim_id": "CLM-2024-44890",
        "customer_name": "Robert Chen",
        "policy_type": "Travel",
        "claim_amount": 3200.00,
        "decision": "Under Review",
        "decision_reason": (
            "The trip cancellation claim is currently under review. The "
            "claimant canceled a non-refundable trip to Tokyo due to a "
            "reported medical emergency. We have received the cancellation "
            "receipts ($3,200 in non-refundable costs) but are awaiting "
            "the attending physician's statement confirming the medical "
            "condition prevented travel. The 30-day documentation deadline "
            "is March 15, 2025."
        ),
        "policy_terms": (
            "Section 2.1 - Trip Cancellation: Covers non-refundable trip "
            "costs when cancellation is due to covered reasons including "
            "illness, injury, or death of the insured or immediate family.\n"
            "Section 2.4 - Documentation Requirements: Medical claims "
            "require a signed physician's statement within 30 days.\n"
            "Section 10.1 - Claim Filing Deadline: All claims must be "
            "filed within 90 days of the covered event."
        ),
    },
]

# The default sample loaded by the "Load Sample Claim" button
DEFAULT_SAMPLE_INDEX = 0
