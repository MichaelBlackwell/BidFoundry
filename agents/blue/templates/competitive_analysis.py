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
                required=True,
                guidance=(
                    "Provide a concise overview of:\n"
                    "- The opportunity being analyzed (title, agency, value)\n"
                    "- Number and strength of competitors (e.g., '5-7 strong competitors expected')\n"
                    "- Incumbent status (name if known, advantage level)\n"
                    "- Our company's competitive position (Frontrunner/Competitive/Underdog)\n"
                    "- Win probability estimate (percentage with rationale)\n"
                    "- Top 2-3 strategic recommendations\n"
                    "This section must stand alone as a complete briefing."
                ),
            ),
            SectionSpec(
                name="Competitive Landscape Overview",
                order=2,
                description="Summary of market dynamics and competitive density",
                min_words=150,
                max_words=400,
                required=True,
                dependencies=["Executive Summary"],
                guidance=(
                    "Describe the competitive environment:\n"
                    "- Competitive density (Low: 2-3 / Medium: 4-6 / High: 7+)\n"
                    "- Incumbent name, contract value, and years on contract\n"
                    "- Incumbent advantage level (Strong/Moderate/Weak/None)\n"
                    "- Set-aside status and implications for competition\n"
                    "- Historical award patterns (who wins similar work?)\n"
                    "- Key evaluation factors from the RFP/RFI\n"
                    "- Procurement approach (LPTA, Best Value, Trade-off)\n"
                    "- Any pre-RFP intelligence gathered"
                ),
            ),
            SectionSpec(
                name="Competitor Profiles",
                order=3,
                description="Detailed profiles of key competitors",
                min_words=300,
                max_words=800,
                required=True,
                dependencies=["Competitive Landscape Overview"],
                guidance=(
                    "Profile the top 3-5 competitors. For EACH competitor include:\n\n"
                    "**Company Overview:**\n"
                    "- Company name, size, and small business status\n"
                    "- Relevant NAICS codes and certifications\n\n"
                    "**Relevant Experience:**\n"
                    "- Specific contracts with this agency\n"
                    "- Similar scope/value contracts elsewhere\n"
                    "- Known CPARS ratings\n\n"
                    "**Strengths (for this opportunity):**\n"
                    "- Technical capabilities alignment\n"
                    "- Relationship/incumbency advantages\n"
                    "- Pricing advantages\n\n"
                    "**Weaknesses/Vulnerabilities:**\n"
                    "- Performance issues or protests\n"
                    "- Capability gaps\n"
                    "- Capacity constraints\n\n"
                    "**Likely Strategy:**\n"
                    "- Expected bid approach\n"
                    "- Likely teaming partners\n\n"
                    "Mark INCUMBENT clearly. Rate each: High/Medium/Low threat."
                ),
            ),
            SectionSpec(
                name="Comparative Analysis",
                order=4,
                description="Side-by-side comparison on key factors",
                min_words=200,
                max_words=500,
                required=True,
                dependencies=["Competitor Profiles"],
                guidance=(
                    "Create a structured comparative assessment:\n\n"
                    "**Comparison Matrix:**\n"
                    "Rate each competitor (including us) on each evaluation factor:\n"
                    "- Technical Approach: Advantage (+) / Neutral (=) / Disadvantage (-)\n"
                    "- Management Approach: +/=/- \n"
                    "- Past Performance: +/=/- \n"
                    "- Price Competitiveness: +/=/- \n"
                    "- Key Personnel: +/=/- \n"
                    "- Small Business/Socioeconomic: +/=/- \n\n"
                    "**Evidence for Ratings:**\n"
                    "Provide specific evidence for each rating (not just opinions).\n\n"
                    "**Summary Score:**\n"
                    "Count advantages vs disadvantages for overall ranking."
                ),
            ),
            SectionSpec(
                name="Our Competitive Position",
                order=5,
                description="Assessment of our company's position in this competition",
                min_words=150,
                max_words=400,
                required=True,
                dependencies=["Comparative Analysis"],
                guidance=(
                    "Assess our competitive position honestly:\n\n"
                    "**Competitive Advantages:**\n"
                    "- List specific advantages with proof points\n"
                    "- Quantify where possible (e.g., '3 similar contracts vs competitors' 1')\n\n"
                    "**At Parity:**\n"
                    "- Areas where we match competitors\n"
                    "- Why parity is acceptable or how to differentiate\n\n"
                    "**Competitive Disadvantages:**\n"
                    "- Be honest about gaps\n"
                    "- Include mitigation strategies for each\n\n"
                    "**Overall Position Assessment:**\n"
                    "- Frontrunner: Clear path to win\n"
                    "- Competitive: Viable with strong execution\n"
                    "- Underdog: Uphill battle, needs breakthrough\n\n"
                    "**Win Probability:** X% with rationale"
                ),
            ),
            SectionSpec(
                name="Recommended Strategy",
                order=6,
                description="Strategic recommendations for winning",
                min_words=200,
                max_words=500,
                required=True,
                dependencies=["Our Competitive Position"],
                guidance=(
                    "Provide actionable strategic recommendations:\n\n"
                    "**Leverage Advantages:**\n"
                    "- How to emphasize and prove our strengths\n"
                    "- Proposal themes that highlight advantages\n\n"
                    "**Mitigate Disadvantages:**\n"
                    "- Specific actions to close gaps before proposal\n"
                    "- Teaming to fill capability gaps\n"
                    "- Messaging to neutralize weaknesses\n\n"
                    "**Ghosting Strategies:**\n"
                    "- How to highlight competitor weaknesses without naming them\n"
                    "- Evaluation criteria language that favors us\n\n"
                    "**Teaming Recommendations:**\n"
                    "- Specific partners to pursue and why\n"
                    "- Work share considerations\n\n"
                    "**Pricing Strategy:**\n"
                    "- Price-to-win guidance based on competitive intel\n"
                    "- Aggressive vs. premium positioning\n\n"
                    "**Key Win Themes:**\n"
                    "- 3-5 themes that differentiate us\n"
                    "Each recommendation must be SPECIFIC and ACTIONABLE."
                ),
            ),
        ]
