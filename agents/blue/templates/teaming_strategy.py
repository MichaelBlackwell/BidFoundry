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
                guidance=(
                    "Define teaming objectives:\n"
                    "- Why are we teaming (capability gaps, set-aside strategy, etc.)?\n"
                    "- Prime vs. subcontractor positioning\n"
                    "- Desired work share split\n"
                    "- Key capabilities needed from partners\n"
                    "- Strategic vs. tactical teaming\n"
                    "Clear objectives guide partner selection."
                ),
            ),
            SectionSpec(
                name="Gap Analysis",
                order=2,
                description="Capability gaps that teaming must address",
                min_words=100,
                max_words=350,
                dependencies=["Teaming Objectives"],
                guidance=(
                    "Identify gaps requiring partners:\n"
                    "- Technical capability gaps\n"
                    "- Past performance gaps\n"
                    "- Certification/clearance gaps\n"
                    "- Geographic coverage gaps\n"
                    "- Key personnel gaps\n"
                    "- Pricing/rate gaps\n\n"
                    "For each gap:\n"
                    "- Describe the gap\n"
                    "- Explain why it matters\n"
                    "- Define what a partner must provide"
                ),
            ),
            SectionSpec(
                name="Partner Criteria",
                order=3,
                description="Criteria for evaluating potential partners",
                min_words=100,
                max_words=300,
                dependencies=["Gap Analysis"],
                guidance=(
                    "Define partner evaluation criteria:\n"
                    "- Must-have requirements\n"
                    "- Nice-to-have qualifications\n"
                    "- Disqualifying factors\n"
                    "- Cultural fit considerations\n"
                    "- Financial stability requirements\n"
                    "- Past teaming track record\n\n"
                    "Weight criteria by importance."
                ),
            ),
            SectionSpec(
                name="Potential Partners",
                order=4,
                description="Identified potential teaming partners",
                min_words=150,
                max_words=500,
                dependencies=["Partner Criteria"],
                guidance=(
                    "List potential partners by category:\n"
                    "For each potential partner:\n"
                    "- Company name and profile\n"
                    "- Relevant capabilities\n"
                    "- Past performance relevance\n"
                    "- Relationship status (new/existing)\n"
                    "- Strengths and weaknesses\n"
                    "- Strategic fit score\n"
                    "- Potential concerns\n\n"
                    "Prioritize by fit and likelihood."
                ),
            ),
            SectionSpec(
                name="Partnership Structures",
                order=5,
                description="Proposed teaming arrangements and work share",
                min_words=100,
                max_words=300,
                dependencies=["Potential Partners"],
                guidance=(
                    "Define partnership structure:\n"
                    "- Proposed team configuration\n"
                    "- Prime vs. sub roles\n"
                    "- Work share percentages\n"
                    "- Subcontracting goals alignment\n"
                    "- Exclusive vs. non-exclusive arrangements\n"
                    "- Joint venture considerations (if applicable)\n\n"
                    "Consider regulatory requirements."
                ),
            ),
            SectionSpec(
                name="Negotiation Approach",
                order=6,
                description="Strategy for partner negotiations",
                min_words=100,
                max_words=300,
                dependencies=["Partnership Structures"],
                guidance=(
                    "Outline negotiation strategy:\n"
                    "- Key terms to negotiate\n"
                    "- Our must-haves vs. nice-to-haves\n"
                    "- Anticipated partner concerns\n"
                    "- Our leverage points\n"
                    "- Walk-away criteria\n"
                    "- Timeline for agreements\n\n"
                    "Consider competitive dynamics."
                ),
            ),
            SectionSpec(
                name="Risk Considerations",
                order=7,
                description="Teaming risks and mitigation strategies",
                min_words=100,
                max_words=350,
                dependencies=["Partnership Structures"],
                guidance=(
                    "Assess teaming risks:\n"
                    "- Partner performance risk\n"
                    "- Competitive conflict risk\n"
                    "- Information sharing risk\n"
                    "- Exclusivity constraints\n"
                    "- Negotiation breakdown risk\n"
                    "- Integration challenges\n\n"
                    "For each risk:\n"
                    "- Describe the risk\n"
                    "- Assess likelihood and impact\n"
                    "- Define mitigation approach"
                ),
            ),
        ]
