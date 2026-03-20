"""
create_policy_pdf.py — Generate a realistic sample insurance policy PDF.

Run once to create docs/SilverShield_Master_Policy.pdf which the app
uses for RAG-style retrieval demonstration.

Usage:
    python create_policy_pdf.py
"""

from fpdf import FPDF


def _ascii(text: str) -> str:
    """Replace Unicode punctuation with ASCII equivalents for PDF compat."""
    return text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')


class PolicyPDF(FPDF):
    """Custom PDF with headers and footers."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(15, 76, 129)  # Navy
        self.cell(0, 8, "SilverShield Insurance Co. - Master Policy Document", align="C")
        self.ln(4)
        self.set_draw_color(23, 162, 184)  # Teal
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"SilverShield Master Policy - Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, number: str, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(15, 76, 129)
        self.cell(0, 10, _ascii(f"Section {number} - {title}"), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection_title(self, number: str, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(23, 162, 184)
        self.cell(0, 8, _ascii(f"{number} {title}"), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5.5, _ascii(text))
        self.ln(3)

    def definition_item(self, term: str, definition: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(51, 51, 51)
        self.cell(50, 6, _ascii(f"  {term}:"))
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, _ascii(definition))
        self.ln(1)


def create_policy():
    pdf = PolicyPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Page 1: Cover & Table of Contents ──
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(15, 76, 129)
    pdf.cell(0, 15, "SilverShield Insurance", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(23, 162, 184)
    pdf.cell(0, 10, "Master Policy Document", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Policy Effective Date: January 1, 2024", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Document Version: 3.2", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Applicable Plans: Silver PPO 3000, Gold HMO 1500, Platinum PPO 500", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 76, 129)
    pdf.cell(0, 10, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 51, 51)
    toc = [
        ("1", "Definitions and Key Terms", 2),
        ("2", "Coverage Overview", 2),
        ("3", "Network and Provider Requirements", 3),
        ("4", "Covered Perils and Services", 3),
        ("5", "Prior Authorization Requirements", 4),
        ("6", "Cost Sharing and Deductibles", 4),
        ("7", "Exclusions and Limitations", 5),
        ("8", "Claims Filing Procedures", 5),
        ("9", "Appeals and Grievance Process", 6),
        ("10", "Auto Insurance Provisions", 6),
        ("11", "Homeowners Insurance Provisions", 7),
        ("12", "Travel Insurance Provisions", 7),
    ]
    for num, title, page in toc:
        pdf.cell(0, 6, f"  Section {num}: {title} .............. {page}", new_x="LMARGIN", new_y="NEXT")

    # ── Page 2: Section 1 — Definitions ──
    pdf.add_page()
    pdf.section_title("1", "Definitions & Key Terms")
    pdf.body_text(
        "The following terms have specific meanings throughout this policy document. "
        "Understanding these definitions is essential to interpreting your coverage."
    )
    definitions = [
        ("Deductible", "The amount you must pay out-of-pocket for covered services before the insurance plan begins to pay. For the Silver PPO 3000 plan, the annual deductible is $3,000 for individuals and $6,000 for families."),
        ("Coinsurance", "Your share of costs after you have met your deductible. Typically 20% for in-network services and 40% for out-of-network services."),
        ("Copayment", "A fixed dollar amount you pay for a covered service at the time of receiving care. Primary care visits: $30; Specialist visits: $50; Emergency room: $250."),
        ("Out-of-Pocket Maximum", "The most you will pay during a policy year before the plan covers 100% of allowed charges. Individual: $8,150; Family: $16,300."),
        ("In-Network Provider", "A healthcare provider who has a contract with SilverShield Insurance to provide services at pre-negotiated rates."),
        ("Out-of-Network Provider", "A healthcare provider who does not have a contract with SilverShield Insurance. Services from these providers may not be covered or may be covered at a reduced rate."),
        ("Prior Authorization", "Approval that SilverShield Insurance requires before you receive certain services or medications. Failure to obtain prior authorization may result in denial of the claim."),
        ("Allowed Amount", "The maximum amount SilverShield will recognize for a covered service. Also called 'eligible expense' or 'negotiated rate.'"),
        ("Explanation of Benefits (EOB)", "A statement from SilverShield that explains what was covered for a medical service, what the insurer paid, and what the member owes."),
        ("Network Gap Exception", "A special provision allowing coverage of out-of-network services at in-network rates when no in-network provider is available within 50 miles of the member's residence."),
    ]
    for term, defn in definitions:
        pdf.definition_item(term, defn)

    # ── Section 2 — Coverage Overview ──
    pdf.section_title("2", "Coverage Overview")
    pdf.body_text(
        "SilverShield Insurance provides comprehensive coverage across multiple "
        "insurance lines including health, auto, homeowners, life, and travel insurance. "
        "Each policy type has specific terms and conditions detailed in subsequent sections."
    )
    pdf.subsection_title("2.1", "Health Insurance Plans")
    pdf.body_text(
        "Three health plan tiers are available:\n"
        "- Silver PPO 3000: $3,000 deductible, 80/20 coinsurance, broad network\n"
        "- Gold HMO 1500: $1,500 deductible, 90/10 coinsurance, HMO network\n"
        "- Platinum PPO 500: $500 deductible, 95/5 coinsurance, broadest network\n\n"
        "All plans cover preventive care at 100% with no deductible when using in-network providers."
    )
    pdf.subsection_title("2.2", "Multi-Line Discount")
    pdf.body_text(
        "Members who hold two or more SilverShield policies (e.g., health + auto, "
        "or home + auto) qualify for a 10% multi-line discount on all premiums."
    )

    # ── Page 3: Section 3 — Network Requirements ──
    pdf.add_page()
    pdf.section_title("3", "Network & Provider Requirements")
    pdf.subsection_title("3.1", "In-Network Provider Usage")
    pdf.body_text(
        "All non-emergency services must be obtained from in-network providers to receive "
        "full coverage benefits. Using an in-network provider ensures you pay the lowest "
        "out-of-pocket costs. The SilverShield provider directory is updated quarterly and "
        "available at silvershield.example.com/providers."
    )
    pdf.subsection_title("3.2", "Out-of-Network Services")
    pdf.body_text(
        "Services from out-of-network providers are generally not covered under HMO plans. "
        "Under PPO plans, out-of-network services are covered at a reduced rate (60% vs 80% "
        "after deductible). The member is responsible for any charges exceeding the allowed amount. "
        "Balance billing protections apply in states where mandated."
    )
    pdf.subsection_title("3.3", "Network Gap Exceptions")
    pdf.body_text(
        "If no in-network provider for a required specialty or service is available within "
        "50 miles of the member's primary residence, SilverShield will authorize coverage "
        "of an out-of-network provider at in-network rates. Members must call 1-800-555-0199 "
        "to request a network gap exception before receiving services. Approved exceptions "
        "are valid for 90 days and may be renewed."
    )
    pdf.subsection_title("3.4", "Emergency Services Exception")
    pdf.body_text(
        "Emergency room visits are covered at in-network rates regardless of the facility's "
        "network status. An emergency is defined as a medical condition manifesting itself by "
        "acute symptoms of sufficient severity (including severe pain) such that a prudent "
        "layperson could reasonably expect that the absence of immediate medical attention "
        "would place their health in serious jeopardy."
    )

    # ── Section 4 — Covered Perils ──
    pdf.section_title("4", "Covered Perils & Services")
    pdf.subsection_title("4.1", "Health — Covered Services")
    pdf.body_text(
        "Covered health services include: preventive care, diagnostic imaging, laboratory "
        "services, inpatient and outpatient surgery, maternity care, mental health services, "
        "prescription drugs (formulary), rehabilitation services, and durable medical equipment. "
        "All services are subject to applicable deductibles, coinsurance, and prior authorization."
    )
    pdf.subsection_title("4.2", "Home — Covered Perils")
    pdf.body_text(
        "Standard homeowners coverage includes protection against: fire and lightning, "
        "windstorm and hail, explosion, riot, aircraft and vehicle damage, smoke, vandalism, "
        "theft, volcanic eruption, falling objects, weight of ice/snow/sleet, accidental "
        "discharge of water or steam from household systems, sudden tearing/cracking/bulging "
        "of heating/cooling/plumbing systems, freezing of plumbing, and sudden accidental "
        "damage from artificially generated electrical current."
    )

    # ── Page 4: Section 5 — Prior Authorization ──
    pdf.add_page()
    pdf.section_title("5", "Prior Authorization Requirements")
    pdf.subsection_title("5.1", "Services Requiring Authorization")
    pdf.body_text(
        "The following services require prior authorization:\n"
        "- Advanced diagnostic imaging (MRI, CT scan, PET scan)\n"
        "- Specialty referrals (non-primary care physicians)\n"
        "- Elective inpatient procedures and surgeries\n"
        "- Outpatient surgical procedures\n"
        "- Durable medical equipment over $500\n"
        "- Home health services\n"
        "- Physical, occupational, and speech therapy beyond 20 visits/year\n"
        "- Prescription medications on the specialty tier\n\n"
        "Prior authorization requests must be submitted at least 5 business days before "
        "the scheduled service date. Urgent requests are processed within 72 hours."
    )
    pdf.subsection_title("5.2", "Authorization Process")
    pdf.body_text(
        "To obtain prior authorization: (1) Your physician submits a request to SilverShield "
        "including clinical justification. (2) SilverShield's medical review team evaluates "
        "the request within 5 business days. (3) You and your physician receive written "
        "notification of approval or denial. (4) Approved authorizations are valid for 60 days "
        "from the approval date."
    )
    pdf.subsection_title("5.3", "Consequences of Missing Authorization")
    pdf.body_text(
        "Claims for services that required but did not receive prior authorization may be "
        "denied in full. The member is responsible for the entire cost. Retroactive authorization "
        "may be granted in emergency situations within 48 hours of service."
    )

    # ── Section 6 — Cost Sharing ──
    pdf.section_title("6", "Cost Sharing & Deductibles")
    pdf.subsection_title("6.1", "Annual Deductible")
    pdf.body_text(
        "The annual deductible resets on January 1 of each plan year. All covered services "
        "(except preventive care) count toward the deductible. Once the deductible is met, "
        "the plan pays its share (coinsurance) for covered services.\n\n"
        "Silver PPO 3000: $3,000 individual / $6,000 family\n"
        "Gold HMO 1500: $1,500 individual / $3,000 family\n"
        "Platinum PPO 500: $500 individual / $1,000 family"
    )
    pdf.subsection_title("6.2", "Coinsurance After Deductible")
    pdf.body_text(
        "After meeting the deductible, you pay coinsurance (your percentage of costs) "
        "until you reach the out-of-pocket maximum. In-network coinsurance: 20% (Silver), "
        "10% (Gold), 5% (Platinum). Out-of-network coinsurance: 40% (Silver/Platinum PPO). "
        "HMO plans do not cover out-of-network services except emergencies."
    )

    # ── Page 5: Section 7 — Exclusions ──
    pdf.add_page()
    pdf.section_title("7", "Exclusions & Limitations")
    pdf.subsection_title("7.1", "General Exclusions")
    pdf.body_text(
        "The following are NOT covered under any SilverShield policy:\n"
        "- Cosmetic surgery (unless medically necessary for reconstruction)\n"
        "- Experimental or investigational treatments\n"
        "- Services received outside the United States (except Travel policy)\n"
        "- Workers' compensation claims\n"
        "- Self-inflicted injuries\n"
        "- Services not medically necessary as determined by SilverShield\n"
        "- Long-term custodial care"
    )
    pdf.subsection_title("7.2", "Homeowners Exclusions")
    pdf.body_text(
        "Standard homeowners policies exclude: flood damage, earthquake damage, "
        "normal wear and tear, gradual deterioration, pest/insect/rodent damage, "
        "mold from long-term moisture, neglect or intentional damage, government action, "
        "nuclear hazard, and power failure originating outside the premises. "
        "Flood and earthquake endorsements are available for additional premium."
    )
    pdf.subsection_title("7.3", "Auto Exclusions")
    pdf.body_text(
        "Auto insurance excludes: intentional damage, racing or speed contests, "
        "use of vehicle for hire (without commercial endorsement), mechanical breakdown, "
        "wear and tear, damage while used for illegal purposes, and damage to custom "
        "parts/equipment not declared on the policy."
    )

    # ── Section 8 — Claims Filing ──
    pdf.section_title("8", "Claims Filing Procedures")
    pdf.subsection_title("8.1", "Filing a Claim")
    pdf.body_text(
        "Claims can be filed online at silvershield.example.com/claims, by calling "
        "1-800-555-0199, or by mailing a completed claim form to SilverShield Insurance, "
        "PO Box 12345, Hartford, CT 06101. Health claims from in-network providers are "
        "typically filed automatically by the provider."
    )
    pdf.subsection_title("8.2", "Required Documentation")
    pdf.body_text(
        "All claims require: completed claim form, proof of loss, itemized bills or receipts, "
        "and relevant supporting documentation (police report for theft/accident, physician "
        "statement for medical claims, photos for property damage). Incomplete claims will "
        "be returned with a request for additional information."
    )
    pdf.subsection_title("8.3", "Claims Processing Timeline")
    pdf.body_text(
        "Standard claims are processed within 30 days of receipt of complete documentation. "
        "Health claims: typically 15 business days. Auto claims: 10-20 business days depending "
        "on investigation requirements. Home claims: 15-30 business days. Expedited processing "
        "is available for hardship cases."
    )

    # ── Page 6: Section 9 — Appeals ──
    pdf.add_page()
    pdf.section_title("9", "Appeals & Grievance Process")
    pdf.subsection_title("9.1", "Right to Appeal")
    pdf.body_text(
        "You have the right to appeal any claim denial or adverse benefit determination. "
        "Appeals must be filed in writing within 180 days of receiving the denial notice. "
        "Include your policy number, claim number, explanation of why you disagree with "
        "the decision, and any supporting documentation."
    )
    pdf.subsection_title("9.2", "Internal Appeal Process")
    pdf.body_text(
        "Level 1 Appeal: Reviewed by a senior claims examiner not involved in the original "
        "decision. Response within 30 days for post-service appeals, 15 days for pre-service. "
        "Level 2 Appeal: If Level 1 is upheld, a second appeal is reviewed by the Medical "
        "Director or designee. Response within 30 days."
    )
    pdf.subsection_title("9.3", "External Review")
    pdf.body_text(
        "After exhausting internal appeals, you may request an independent external review "
        "by a certified Independent Review Organization (IRO). External review requests must "
        "be made within 4 months of the final internal appeal decision. The IRO decision "
        "is binding on SilverShield Insurance."
    )

    # ── Section 10 — Auto ──
    pdf.section_title("10", "Auto Insurance Provisions")
    pdf.subsection_title("10.1", "Collision Coverage")
    pdf.body_text(
        "Covers damage to the insured vehicle resulting from collision with another vehicle "
        "or object, regardless of fault. Subject to the selected deductible ($250, $500, or "
        "$1,000). Does not cover mechanical breakdown, wear, or maintenance."
    )
    pdf.subsection_title("10.2", "Comprehensive Coverage")
    pdf.body_text(
        "Covers non-collision damage including theft, vandalism, natural disasters, falling "
        "objects, fire, flood, and animal strikes. Subject to the selected deductible."
    )
    pdf.subsection_title("10.3", "Aftermarket Modifications")
    pdf.body_text(
        "Custom parts, aftermarket modifications, and non-factory equipment are ONLY covered "
        "if specifically declared on the policy with supplemental coverage (Custom Parts and "
        "Equipment endorsement). Undeclared modifications are excluded from all coverage. "
        "Members must notify SilverShield within 30 days of installing modifications valued "
        "over $1,000."
    )

    # ── Page 7: Section 11 — Home ──
    pdf.add_page()
    pdf.section_title("11", "Homeowners Insurance Provisions")
    pdf.subsection_title("11.1", "Dwelling Coverage")
    pdf.body_text(
        "Covers the physical structure of your home against covered perils (see Section 4.2). "
        "Coverage is at replacement cost, meaning the cost to rebuild with similar materials "
        "and quality without deduction for depreciation."
    )
    pdf.subsection_title("11.2", "Water Damage — Covered vs. Excluded")
    pdf.body_text(
        "COVERED: Sudden and accidental water damage from burst pipes, failed appliances, "
        "accidental overflow, and fire suppression systems. "
        "EXCLUDED: Gradual leaks, seepage, condensation, mold from chronic moisture, flood "
        "(rising water from external sources), and sewer/drain backup (unless endorsement added). "
        "Important: To be covered, water damage must be sudden and accidental, not the result "
        "of deferred maintenance or neglect."
    )
    pdf.subsection_title("11.3", "Additional Living Expenses (ALE)")
    pdf.body_text(
        "When the home is uninhabitable due to a covered loss, SilverShield covers reasonable "
        "costs for temporary housing, meals above normal living expenses, and local transportation. "
        "ALE coverage is limited to 20% of dwelling coverage and a maximum duration of 12 months. "
        "Receipts are required for all ALE claims."
    )
    pdf.subsection_title("11.4", "Personal Property")
    pdf.body_text(
        "Replacement cost coverage for personal belongings damaged or destroyed by a covered "
        "peril. Standard limit: 50% of dwelling coverage. Sub-limits apply: jewelry $1,500, "
        "electronics $2,500, firearms $2,500, collectibles $1,000. Higher limits available "
        "with scheduled personal property endorsement."
    )

    # ── Section 12 — Travel ──
    pdf.section_title("12", "Travel Insurance Provisions")
    pdf.subsection_title("12.1", "Trip Cancellation")
    pdf.body_text(
        "Covers non-refundable trip costs when cancellation is due to: illness or injury of "
        "insured or immediate family member, death in the family, jury duty, natural disaster "
        "at destination rendering it uninhabitable, terrorism event at destination within 30 days "
        "of departure, involuntary job loss, or military deployment."
    )
    pdf.subsection_title("12.2", "Documentation Requirements")
    pdf.body_text(
        "Medical cancellation requires a signed attending physician's statement confirming "
        "the condition prevented travel, submitted within 30 days of cancellation. All claims "
        "require original receipts, booking confirmations, and proof of non-refundability. "
        "Claims must be filed within 90 days of the covered event."
    )
    pdf.subsection_title("12.3", "Trip Interruption")
    pdf.body_text(
        "If a trip is cut short due to a covered reason, covers: unused non-refundable "
        "expenses on a pro-rata basis, reasonable additional transportation costs to return "
        "home (economy class equivalent), and up to $200/day for additional accommodation "
        "if stranded due to a covered event."
    )

    # ── Final Page: Contact ──
    pdf.add_page()
    pdf.section_title("13", "Contact Information")
    pdf.body_text(
        "SilverShield Insurance Company\n"
        "PO Box 12345, Hartford, CT 06101\n\n"
        "General Inquiries: 1-800-555-0199\n"
        "Claims Department: 1-800-555-0200\n"
        "Appeals Department: 1-800-555-0201\n"
        "Prior Authorization: 1-800-555-0202\n"
        "Website: silvershield.example.com\n"
        "Member Portal: my.silvershield.example.com\n\n"
        "This policy document is for demonstration purposes. It represents a sample "
        "insurance policy used by ClaimClear AI to showcase RAG-grounded explanation "
        "generation. SilverShield Insurance is a fictional company."
    )

    # Save
    pdf.output("docs/SilverShield_Master_Policy.pdf")
    print("Generated: docs/SilverShield_Master_Policy.pdf")


if __name__ == "__main__":
    create_policy()
