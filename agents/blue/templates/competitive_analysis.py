"""
Competitive Analysis Template

Defines the structure for competitive analysis documents.
"""

from typing import List
from .base import DocumentTemplate, SectionSpec, register_template


@register_template
class CompetitiveAnalysisTemplate(DocumentTemplate):
    """
    Template for Competitive Analysis documents.

    A competitive analysis assesses the competitive landscape for a specific
    opportunity or market segment, identifying key competitors and the
    company's relative positioning.
    """

    @property
    def document_type(self) -> str:
        return "Competitive Analysis"

    @property
    def description(self) -> str:
        return (
            "An assessment of the competitive landscape for a specific opportunity "
            "or market segment. Identifies key competitors, analyzes their strengths "
            "and weaknesses, and develops competitive positioning strategies."
        )

    @property
    def requires_opportunity(self) -> bool:
        return True

    @property
    def sections(self) -> List[SectionSpec]:
        return [
            SectionSpec(
                name="Executive Summary",
                order=1,
                description="High-level summary of competitive landscape and key findings",
                min_words=100,
                max_words=300,
                guidance=(
                    "Provide a concise overview of:\n"
                    "- The opportunity being analyzed\n"
                    "- Number and strength of competitors\n"
                    "- Our company's competitive position (strong/moderate/weak)\n"
                    "- Key recommendations for competitive strategy\n"
                    "- Overall win probability assessment"
                ),
            ),
            SectionSpec(
                name="Competitive Landscape Overview",
                order=2,
                description="Summary of market dynamics and competitive density",
                min_words=150,
                max_words=400,
                dependencies=["Executive Summary"],
                guidance=(
                    "Describe the competitive environment:\n"
                    "- Number of expected competitors\n"
                    "- Incumbent status and advantage level\n"
                    "- Set-aside implications for competition\n"
                    "- Historical award patterns for similar work\n"
                    "- Key evaluation factors that will drive selection"
                ),
            ),
            SectionSpec(
                name="Competitor Profiles",
                order=3,
                description="Detailed profiles of key competitors",
                min_words=300,
                max_words=800,
                dependencies=["Competitive Landscape Overview"],
                guidance=(
                    "Profile the top 3-5 competitors:\n"
                    "For each competitor include:\n"
                    "- Company name and basic info\n"
                    "- Relevant past performance\n"
                    "- Known strengths for this opportunity\n"
                    "- Known weaknesses or vulnerabilities\n"
                    "- Likely bid strategy\n"
                    "- Potential teaming partners\n"
                    "Flag the incumbent separately if applicable."
                ),
            ),
            SectionSpec(
                name="Comparative Analysis",
                order=4,
                description="Side-by-side comparison on key factors",
                min_words=200,
                max_words=500,
                dependencies=["Competitor Profiles"],
                guidance=(
                    "Create a comparative assessment:\n"
                    "- Compare on each major evaluation factor\n"
                    "- Rate as: Advantage / Neutral / Disadvantage\n"
                    "- Include specific evidence for ratings\n"
                    "- Consider technical, management, past performance, and price\n"
                    "Present in a clear, structured format."
                ),
            ),
            SectionSpec(
                name="Our Competitive Position",
                order=5,
                description="Assessment of our company's position in this competition",
                min_words=150,
                max_words=400,
                dependencies=["Comparative Analysis"],
                guidance=(
                    "Assess our competitive position:\n"
                    "- Where we have competitive advantage\n"
                    "- Where we are at parity\n"
                    "- Where we are at disadvantage\n"
                    "- Overall assessment (frontrunner/competitive/underdog)\n"
                    "- Key proof points for our position\n"
                    "Be honest about gaps while highlighting strengths."
                ),
            ),
            SectionSpec(
                name="Recommended Strategy",
                order=6,
                description="Strategic recommendations for winning",
                min_words=200,
                max_words=500,
                dependencies=["Our Competitive Position"],
                guidance=(
                    "Provide actionable strategic recommendations:\n"
                    "- How to leverage our advantages\n"
                    "- How to mitigate our disadvantages\n"
                    "- Ghosting strategies against key competitors\n"
                    "- Teaming recommendations if applicable\n"
                    "- Pricing strategy implications\n"
                    "- Key themes to emphasize\n"
                    "Each recommendation should be specific and actionable."
                ),
            ),
        ]
