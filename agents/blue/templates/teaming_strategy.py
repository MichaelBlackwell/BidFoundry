"""
Teaming Strategy Template

Defines the structure for Teaming Strategy documents.
"""

from typing import List
from .base import DocumentTemplate, SectionSpec, register_template


@register_template
class TeamingStrategyTemplate(DocumentTemplate):
    """
    Template for Teaming Strategy documents.

    A Teaming Strategy document outlines the approach to building winning
    teams for specific opportunities or market segments, including partner
    identification, negotiation approach, and risk considerations.
    """

    @property
    def document_type(self) -> str:
        return "Teaming Strategy"

    @property
    def description(self) -> str:
        return (
            "A strategic plan for building winning teams. Covers gap analysis, "
            "partner identification, evaluation criteria, partnership structures, "
            "and negotiation approach."
        )

    @property
    def requires_opportunity(self) -> bool:
        return False  # Can be opportunity-specific or general

    @property
    def sections(self) -> List[SectionSpec]:
        return [
            SectionSpec(
                name="Teaming Objectives",
                order=1,
                description="Goals and rationale for teaming",
                min_words=75,
                max_words=250,
                required=True,
                guidance=(
                    "Define teaming objectives clearly:\n\n"
                    "**Context:**\n"
                    "- Opportunity-specific OR general strategy?\n"
                    "- If opportunity-specific: title, agency, value\n\n"
                    "**Why We're Teaming:**\n"
                    "- Capability gaps to fill\n"
                    "- Set-aside strategy requirements\n"
                    "- Past performance needs\n"
                    "- Competitive positioning\n"
                    "- Customer relationship access\n\n"
                    "**Prime vs. Sub Positioning:**\n"
                    "- Our preferred role and rationale\n"
                    "- Flexibility on role?\n\n"
                    "**Work Share Target:**\n"
                    "- Target percentage for us\n"
                    "- Minimum acceptable percentage\n\n"
                    "**Strategic vs. Tactical:**\n"
                    "- One-off teaming OR long-term partnership?\n\n"
                    "Clear objectives = better partner selection."
                ),
            ),
            SectionSpec(
                name="Gap Analysis",
                order=2,
                description="Capability gaps that teaming must address",
                min_words=100,
                max_words=350,
                required=True,
                dependencies=["Teaming Objectives"],
                guidance=(
                    "Identify gaps requiring partners. For EACH gap:\n\n"
                    "**Gap Categories:**\n"
                    "- Technical capability gaps\n"
                    "- Past performance gaps (agency, scope, size)\n"
                    "- Certification gaps (ISO, CMMI, CMMC)\n"
                    "- Clearance gaps (facility, personnel)\n"
                    "- Geographic coverage gaps\n"
                    "- Key personnel gaps\n"
                    "- Pricing/rate competitiveness\n"
                    "- Contract vehicle access\n"
                    "- Small business status needs\n\n"
                    "**For Each Gap:**\n"
                    "- Gap Description: What we lack\n"
                    "- Impact: Why it matters (High/Medium/Low)\n"
                    "- Requirement: What partner must provide\n"
                    "- Verification: How we'll confirm partner capability\n\n"
                    "Prioritize gaps by criticality to win."
                ),
            ),
            SectionSpec(
                name="Partner Criteria",
                order=3,
                description="Criteria for evaluating potential partners",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Gap Analysis"],
                guidance=(
                    "Define partner evaluation criteria:\n\n"
                    "**Must-Have Requirements:** (Deal-breakers)\n"
                    "- Specific capabilities required\n"
                    "- Certifications/clearances required\n"
                    "- Past performance minimums\n"
                    "- Financial stability thresholds\n\n"
                    "**Preferred Qualifications:** (Nice-to-have)\n"
                    "- Additional value-adds\n"
                    "- Strategic benefits\n\n"
                    "**Disqualifying Factors:**\n"
                    "- Competitor conflicts\n"
                    "- Reputation issues\n"
                    "- Financial red flags\n"
                    "- OCI concerns\n\n"
                    "**Cultural/Operational Fit:**\n"
                    "- Working style compatibility\n"
                    "- Communication expectations\n"
                    "- Geographic alignment\n\n"
                    "**Scoring Weight:**\n"
                    "Assign weights to criteria (total = 100%)"
                ),
            ),
            SectionSpec(
                name="Potential Partners",
                order=4,
                description="Identified potential teaming partners",
                min_words=150,
                max_words=500,
                required=True,
                dependencies=["Partner Criteria"],
                guidance=(
                    "List 3-6 potential partners. For EACH:\n\n"
                    "**Company Profile:**\n"
                    "- Name, size, location\n"
                    "- Small business status\n"
                    "- Core capabilities\n\n"
                    "**Gap Coverage:**\n"
                    "- Which gaps they fill\n"
                    "- Strength of coverage (Strong/Adequate/Partial)\n\n"
                    "**Relevant Experience:**\n"
                    "- Past performance with target agency\n"
                    "- Similar scope/size contracts\n"
                    "- CPARS ratings if known\n\n"
                    "**Relationship Status:**\n"
                    "- New contact / Existing relationship / Teamed before\n"
                    "- Key contacts known\n\n"
                    "**Strengths & Weaknesses:**\n"
                    "- What they bring\n"
                    "- Potential concerns\n\n"
                    "**Strategic Fit Score:** (1-5)\n"
                    "Based on partner criteria weighting\n\n"
                    "**Recommendation:** Pursue / Backup / Pass\n\n"
                    "Prioritize by fit AND likelihood of agreement."
                ),
            ),
            SectionSpec(
                name="Partnership Structures",
                order=5,
                description="Proposed teaming arrangements and work share",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Potential Partners"],
                guidance=(
                    "Define partnership structure options:\n\n"
                    "**Recommended Team Configuration:**\n"
                    "- Prime: [Company]\n"
                    "- Major Sub 1: [Company] - [Role] - [%]\n"
                    "- Major Sub 2: [Company] - [Role] - [%]\n"
                    "- Other subs as needed\n\n"
                    "**Work Share Breakdown:**\n"
                    "- Our work share: X%\n"
                    "- Partner work shares with justification\n\n"
                    "**Small Business Compliance:**\n"
                    "- Subcontracting plan alignment\n"
                    "- Set-aside requirements met?\n"
                    "- SB goal percentages\n\n"
                    "**Agreement Type:**\n"
                    "- Teaming Agreement (TA)\n"
                    "- Mentor-Protégé\n"
                    "- Joint Venture\n"
                    "- Subcontract only\n\n"
                    "**Exclusivity:**\n"
                    "- Exclusive vs. non-exclusive\n"
                    "- Scope of exclusivity\n"
                    "- Duration"
                ),
            ),
            SectionSpec(
                name="Negotiation Approach",
                order=6,
                description="Strategy for partner negotiations",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Partnership Structures"],
                guidance=(
                    "Outline negotiation strategy:\n\n"
                    "**Key Terms to Negotiate:**\n"
                    "- Work share percentages\n"
                    "- Exclusivity provisions\n"
                    "- Proposal cost sharing\n"
                    "- IP and data rights\n"
                    "- Non-compete clauses\n"
                    "- Termination provisions\n\n"
                    "**Our Must-Haves:**\n"
                    "- Non-negotiable terms\n"
                    "- Walk-away triggers\n\n"
                    "**Our Tradables:**\n"
                    "- Terms we can flex on\n"
                    "- Concessions available\n\n"
                    "**Anticipated Partner Concerns:**\n"
                    "- What they'll push back on\n"
                    "- Our response strategy\n\n"
                    "**Our Leverage:**\n"
                    "- Why they need us\n"
                    "- What we bring to table\n\n"
                    "**Timeline:**\n"
                    "- Target agreement date\n"
                    "- Key milestones"
                ),
            ),
            SectionSpec(
                name="Risk Considerations",
                order=7,
                description="Teaming risks and mitigation strategies",
                min_words=100,
                max_words=350,
                required=True,
                dependencies=["Partnership Structures"],
                guidance=(
                    "Assess teaming risks. For EACH risk:\n\n"
                    "**Risk Categories:**\n\n"
                    "**Partner Performance Risk:**\n"
                    "- Can they deliver?\n"
                    "- Capacity concerns?\n\n"
                    "**Competitive Conflict Risk:**\n"
                    "- Are they teaming with competitors?\n"
                    "- Exclusivity protection?\n\n"
                    "**Information Sharing Risk:**\n"
                    "- Proprietary data exposure\n"
                    "- NDA adequacy\n\n"
                    "**Negotiation Failure Risk:**\n"
                    "- What if they walk away?\n"
                    "- Backup options?\n\n"
                    "**Integration Risk:**\n"
                    "- Cultural compatibility\n"
                    "- Process alignment\n\n"
                    "**Financial Risk:**\n"
                    "- Partner financial stability\n"
                    "- Cost overrun exposure\n\n"
                    "**For Each Risk:**\n"
                    "- Likelihood: High/Medium/Low\n"
                    "- Impact: High/Medium/Low\n"
                    "- Mitigation Strategy\n"
                    "- Contingency Plan"
                ),
            ),
        ]
