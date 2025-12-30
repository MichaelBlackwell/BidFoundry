"""
SWOT Analysis Template

Defines the structure for SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis documents.
"""

from typing import List
from .base import DocumentTemplate, SectionSpec, register_template


@register_template
class SWOTAnalysisTemplate(DocumentTemplate):
    """
    Template for SWOT Analysis documents.

    A SWOT analysis provides a structured assessment of internal strengths
    and weaknesses, and external opportunities and threats, for strategic
    planning purposes.
    """

    @property
    def document_type(self) -> str:
        return "SWOT Analysis"

    @property
    def description(self) -> str:
        return (
            "A strategic planning tool that identifies internal Strengths and "
            "Weaknesses, and external Opportunities and Threats. Used for "
            "go/no-go decisions, capture planning, and strategic positioning."
        )

    @property
    def requires_opportunity(self) -> bool:
        return False  # Can be done at company level or opportunity level

    @property
    def sections(self) -> List[SectionSpec]:
        return [
            SectionSpec(
                name="Executive Summary",
                order=1,
                description="High-level summary of the SWOT analysis",
                min_words=75,
                max_words=250,
                guidance=(
                    "Provide a brief overview:\n"
                    "- Context for the analysis (company-wide or opportunity-specific)\n"
                    "- Key findings from each quadrant\n"
                    "- Overall strategic assessment\n"
                    "- Primary recommendation"
                ),
            ),
            SectionSpec(
                name="Strengths",
                order=2,
                description="Internal positive attributes and resources",
                min_words=150,
                max_words=400,
                guidance=(
                    "Identify internal strengths:\n"
                    "- Technical capabilities and expertise\n"
                    "- Relevant past performance\n"
                    "- Certifications and clearances\n"
                    "- Key personnel qualifications\n"
                    "- Customer relationships\n"
                    "- Contract vehicles and access\n\n"
                    "For each strength:\n"
                    "- Describe the strength specifically\n"
                    "- Explain why it's relevant\n"
                    "- Provide evidence/proof points\n"
                    "Prioritize by impact."
                ),
            ),
            SectionSpec(
                name="Weaknesses",
                order=3,
                description="Internal negative attributes and gaps",
                min_words=150,
                max_words=400,
                guidance=(
                    "Honestly assess internal weaknesses:\n"
                    "- Capability gaps vs. requirements\n"
                    "- Limited or no past performance in key areas\n"
                    "- Missing certifications or clearances\n"
                    "- Resource constraints\n"
                    "- Geographic limitations\n"
                    "- Teaming gaps\n\n"
                    "For each weakness:\n"
                    "- Describe the gap honestly\n"
                    "- Assess impact (High/Medium/Low)\n"
                    "- Propose mitigation strategy\n"
                    "Don't sugar-coat - honest assessment is essential."
                ),
            ),
            SectionSpec(
                name="Opportunities",
                order=4,
                description="External factors that could benefit the company",
                min_words=150,
                max_words=400,
                guidance=(
                    "Identify external opportunities:\n"
                    "- Agency priorities aligned with capabilities\n"
                    "- Budget trends favoring our services\n"
                    "- Upcoming recompetes with weak incumbents\n"
                    "- New requirements matching our expertise\n"
                    "- Teaming/partnership opportunities\n"
                    "- Set-aside advantages\n\n"
                    "For each opportunity:\n"
                    "- Describe the opportunity\n"
                    "- Explain why we can capitalize\n"
                    "- Suggest action to pursue"
                ),
            ),
            SectionSpec(
                name="Threats",
                order=5,
                description="External factors that could harm the company",
                min_words=150,
                max_words=400,
                guidance=(
                    "Assess external threats:\n"
                    "- Strong incumbent positions\n"
                    "- Well-funded competitor activity\n"
                    "- Budget cuts or program cancellations\n"
                    "- Changing agency priorities\n"
                    "- Regulatory changes\n"
                    "- Technological disruption\n\n"
                    "For each threat:\n"
                    "- Describe the threat\n"
                    "- Assess likelihood and impact\n"
                    "- Propose risk mitigation"
                ),
            ),
            SectionSpec(
                name="Strategic Implications",
                order=6,
                description="Analysis of how SWOT factors interact",
                min_words=100,
                max_words=300,
                dependencies=["Strengths", "Weaknesses", "Opportunities", "Threats"],
                guidance=(
                    "Connect the SWOT factors:\n"
                    "- How can strengths exploit opportunities?\n"
                    "- How can strengths counter threats?\n"
                    "- How do weaknesses limit opportunities?\n"
                    "- Where do weaknesses amplify threats?\n\n"
                    "Identify the critical intersections."
                ),
            ),
            SectionSpec(
                name="Recommended Actions",
                order=7,
                description="Priority actions based on SWOT analysis",
                min_words=100,
                max_words=300,
                dependencies=["Strategic Implications"],
                guidance=(
                    "Provide prioritized action items:\n"
                    "- SO Strategies: Use strengths to pursue opportunities\n"
                    "- WO Strategies: Address weaknesses to enable opportunities\n"
                    "- ST Strategies: Use strengths to mitigate threats\n"
                    "- WT Strategies: Minimize weaknesses and avoid threats\n\n"
                    "Each action should be specific and assignable."
                ),
            ),
        ]
