"""
Go-to-Market Strategy Template

Defines the structure for Go-to-Market Strategy documents.
"""

from typing import List
from .base import DocumentTemplate, SectionSpec, register_template


@register_template
class GoToMarketTemplate(DocumentTemplate):
    """
    Template for Go-to-Market Strategy documents.

    A Go-to-Market strategy document outlines how a company will approach
    a target market segment, including value proposition, positioning,
    and sales/marketing approach.
    """

    @property
    def document_type(self) -> str:
        return "Go-to-Market Strategy"

    @property
    def description(self) -> str:
        return (
            "A strategic plan for entering or expanding within a government "
            "market segment. Covers target segments, value proposition, "
            "competitive positioning, and sales/marketing approach."
        )

    @property
    def requires_opportunity(self) -> bool:
        return False  # Market-level strategy, not opportunity-specific

    @property
    def sections(self) -> List[SectionSpec]:
        return [
            SectionSpec(
                name="Market Overview",
                order=1,
                description="Summary of the target government market",
                min_words=150,
                max_words=400,
                guidance=(
                    "Describe the target market:\n"
                    "- Market segment definition\n"
                    "- Target agencies and sub-agencies\n"
                    "- Total addressable market (TAM) estimate\n"
                    "- Budget trends and outlook\n"
                    "- Key market drivers\n"
                    "- Procurement patterns and vehicles\n"
                    "Ground the strategy in market reality."
                ),
            ),
            SectionSpec(
                name="Target Segments",
                order=2,
                description="Specific customer segments to pursue",
                min_words=150,
                max_words=400,
                dependencies=["Market Overview"],
                guidance=(
                    "Define target customer segments:\n"
                    "- Primary segment (highest priority)\n"
                    "- Secondary segments\n"
                    "For each segment:\n"
                    "- Agency/customer profile\n"
                    "- Typical requirements\n"
                    "- Budget size and growth\n"
                    "- Decision-making process\n"
                    "- Our alignment score\n"
                    "Prioritize segments by fit and opportunity."
                ),
            ),
            SectionSpec(
                name="Value Proposition",
                order=3,
                description="Our unique value for this market",
                min_words=100,
                max_words=300,
                dependencies=["Target Segments"],
                guidance=(
                    "Articulate the value proposition:\n"
                    "- What problem do we solve?\n"
                    "- How do we solve it better?\n"
                    "- What outcomes do we deliver?\n"
                    "- Why should they choose us?\n\n"
                    "Craft a clear, compelling value statement that:\n"
                    "- Is specific to the target segments\n"
                    "- Differentiates from alternatives\n"
                    "- Resonates with government buyers"
                ),
            ),
            SectionSpec(
                name="Competitive Positioning",
                order=4,
                description="How we position against competitors",
                min_words=150,
                max_words=400,
                dependencies=["Value Proposition"],
                guidance=(
                    "Define competitive positioning:\n"
                    "- Key competitors in this space\n"
                    "- Our competitive advantages\n"
                    "- Areas where we trail\n"
                    "- Positioning statement\n"
                    "- Ghosting strategies\n"
                    "- Head-to-head win approach\n\n"
                    "Be honest about competitive dynamics."
                ),
            ),
            SectionSpec(
                name="Channel Strategy",
                order=5,
                description="How we access this market",
                min_words=100,
                max_words=300,
                dependencies=["Target Segments"],
                guidance=(
                    "Define market access approach:\n"
                    "- Contract vehicles to leverage\n"
                    "- Contract vehicles to pursue\n"
                    "- Teaming strategy (prime vs. sub)\n"
                    "- Key partner relationships\n"
                    "- Direct vs. indirect approaches\n"
                    "- Entry points for new accounts"
                ),
            ),
            SectionSpec(
                name="Marketing Approach",
                order=6,
                description="How we build awareness and generate leads",
                min_words=100,
                max_words=300,
                dependencies=["Value Proposition"],
                guidance=(
                    "Outline marketing activities:\n"
                    "- Thought leadership topics\n"
                    "- Events and conferences\n"
                    "- Industry associations\n"
                    "- Digital presence\n"
                    "- Collateral needs\n"
                    "- Partner marketing\n"
                    "Focus on activities that reach government buyers."
                ),
            ),
            SectionSpec(
                name="Sales Strategy",
                order=7,
                description="How we pursue and win opportunities",
                min_words=100,
                max_words=300,
                dependencies=["Channel Strategy"],
                guidance=(
                    "Define the sales approach:\n"
                    "- Account targeting criteria\n"
                    "- Relationship development plan\n"
                    "- Opportunity qualification process\n"
                    "- Capture investment approach\n"
                    "- Win rate targets\n"
                    "- Pipeline goals"
                ),
            ),
            SectionSpec(
                name="Success Metrics",
                order=8,
                description="How we measure go-to-market success",
                min_words=75,
                max_words=200,
                dependencies=["Sales Strategy", "Marketing Approach"],
                guidance=(
                    "Define success metrics:\n"
                    "- Pipeline value targets\n"
                    "- Win rate goals\n"
                    "- Revenue targets\n"
                    "- Market share objectives\n"
                    "- Relationship metrics\n"
                    "- Brand awareness indicators\n\n"
                    "Make metrics specific and measurable."
                ),
            ),
        ]
