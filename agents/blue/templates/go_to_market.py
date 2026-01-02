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
                required=True,
                guidance=(
                    "Describe the target market with specifics:\n\n"
                    "**Market Definition:**\n"
                    "- Service area / capability focus\n"
                    "- NAICS codes and PSC codes\n"
                    "- Geographic scope\n\n"
                    "**Target Agencies:**\n"
                    "- Primary agencies (list top 3-5)\n"
                    "- Sub-agencies or components\n"
                    "- Why these agencies (alignment rationale)\n\n"
                    "**Market Size:**\n"
                    "- Total Addressable Market (TAM) with source\n"
                    "- Serviceable Available Market (SAM)\n"
                    "- Serviceable Obtainable Market (SOM) - realistic target\n\n"
                    "**Market Dynamics:**\n"
                    "- Budget trends (growing/stable/declining)\n"
                    "- Key drivers (legislation, priorities, technology)\n"
                    "- Procurement patterns (contract types, set-asides)\n"
                    "- Major contract vehicles used\n\n"
                    "Ground strategy in DATA, not assumptions."
                ),
            ),
            SectionSpec(
                name="Target Segments",
                order=2,
                description="Specific customer segments to pursue",
                min_words=150,
                max_words=400,
                required=True,
                dependencies=["Market Overview"],
                guidance=(
                    "Define 2-4 target customer segments:\n\n"
                    "**For Each Segment:**\n\n"
                    "**Segment Profile:**\n"
                    "- Agency/customer type\n"
                    "- Typical organization size\n"
                    "- Budget authority level\n\n"
                    "**Requirements Pattern:**\n"
                    "- Common service needs\n"
                    "- Typical contract size/duration\n"
                    "- Preferred contract types\n\n"
                    "**Decision Dynamics:**\n"
                    "- Key decision makers (titles)\n"
                    "- Buying process / procurement cycle\n"
                    "- Influencers and gatekeepers\n\n"
                    "**Our Fit Score:** (1-5)\n"
                    "- Capability alignment\n"
                    "- Past performance relevance\n"
                    "- Relationship strength\n"
                    "- Competitive position\n\n"
                    "**Priority:** Primary / Secondary / Tertiary\n\n"
                    "Prioritize by fit AND opportunity size."
                ),
            ),
            SectionSpec(
                name="Value Proposition",
                order=3,
                description="Our unique value for this market",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Target Segments"],
                guidance=(
                    "Articulate the value proposition:\n\n"
                    "**Value Proposition Statement:** (2-3 sentences)\n"
                    "For [target segment], who need [key need],\n"
                    "[Company] provides [solution/capability]\n"
                    "that delivers [key benefit/outcome].\n"
                    "Unlike [alternatives], we [key differentiator].\n\n"
                    "**Problem We Solve:**\n"
                    "- Customer pain points addressed\n"
                    "- Why current solutions fall short\n\n"
                    "**How We Solve It Better:**\n"
                    "- Our unique approach\n"
                    "- Specific capabilities leveraged\n\n"
                    "**Outcomes Delivered:**\n"
                    "- Quantified results (from past performance)\n"
                    "- Customer testimonials or CPARS highlights\n\n"
                    "**Why Choose Us:**\n"
                    "- Top 3 reasons to select us\n\n"
                    "Must resonate with GOVERNMENT buyers specifically."
                ),
            ),
            SectionSpec(
                name="Competitive Positioning",
                order=4,
                description="How we position against competitors",
                min_words=150,
                max_words=400,
                required=True,
                dependencies=["Value Proposition"],
                guidance=(
                    "Define competitive positioning:\n\n"
                    "**Key Competitors:** (list 3-5)\n"
                    "For each:\n"
                    "- Company name and size\n"
                    "- Market share estimate\n"
                    "- Key strengths\n"
                    "- Known weaknesses\n\n"
                    "**Competitive Advantages:**\n"
                    "- Where we win (specific proof points)\n"
                    "- Unique differentiators\n\n"
                    "**Competitive Gaps:**\n"
                    "- Where competitors lead\n"
                    "- Mitigation strategies\n\n"
                    "**Positioning Statement:**\n"
                    "How we want to be perceived vs. competitors\n\n"
                    "**Ghosting Strategies:**\n"
                    "- Language that highlights competitor weaknesses\n"
                    "- Without naming names\n\n"
                    "**Head-to-Head Playbook:**\n"
                    "- How to win against each major competitor\n\n"
                    "Be HONEST about competitive dynamics."
                ),
            ),
            SectionSpec(
                name="Channel Strategy",
                order=5,
                description="How we access this market",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Target Segments"],
                guidance=(
                    "Define market access approach:\n\n"
                    "**Contract Vehicles - Current:**\n"
                    "- GSA Schedules (list specific)\n"
                    "- GWACs (OASIS, SEWP, CIO-SP3, etc.)\n"
                    "- Agency-specific IDIQs/BPAs\n\n"
                    "**Contract Vehicles - Target:**\n"
                    "- Vehicles to pursue\n"
                    "- Timeline and investment\n\n"
                    "**Prime vs. Sub Strategy:**\n"
                    "- Where we prime\n"
                    "- Where we sub (and to whom)\n"
                    "- Target work share\n\n"
                    "**Key Partnerships:**\n"
                    "- Strategic partners (names)\n"
                    "- Partnership value\n\n"
                    "**Market Entry Points:**\n"
                    "- How to break into new accounts\n"
                    "- Small task orders to prove capability"
                ),
            ),
            SectionSpec(
                name="Marketing Approach",
                order=6,
                description="How we build awareness and generate leads",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Value Proposition"],
                guidance=(
                    "Outline marketing activities:\n\n"
                    "**Thought Leadership:**\n"
                    "- Key topics to own\n"
                    "- White papers, articles, webinars\n"
                    "- Speaking opportunities\n\n"
                    "**Events & Conferences:**\n"
                    "- Must-attend events (list specific)\n"
                    "- Sponsorship opportunities\n"
                    "- Customer engagement events\n\n"
                    "**Industry Associations:**\n"
                    "- Key associations to join/engage\n"
                    "- Committee participation\n\n"
                    "**Digital Presence:**\n"
                    "- Website optimization\n"
                    "- LinkedIn strategy\n"
                    "- GovWin/BGov presence\n\n"
                    "**Collateral Needs:**\n"
                    "- Capability statements\n"
                    "- Case studies\n"
                    "- Differentiator one-pagers\n\n"
                    "Focus on activities that reach GOVERNMENT BUYERS."
                ),
            ),
            SectionSpec(
                name="Sales Strategy",
                order=7,
                description="How we pursue and win opportunities",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Channel Strategy"],
                guidance=(
                    "Define the sales/capture approach:\n\n"
                    "**Account Targeting:**\n"
                    "- Criteria for pursuing an agency\n"
                    "- Account prioritization framework\n"
                    "- Named accounts to pursue\n\n"
                    "**Relationship Development:**\n"
                    "- Customer engagement plan\n"
                    "- Key contacts to develop\n"
                    "- Cadence of touchpoints\n\n"
                    "**Opportunity Qualification:**\n"
                    "- Go/No-Go criteria\n"
                    "- Pwin thresholds\n"
                    "- Gate review process\n\n"
                    "**Capture Investment:**\n"
                    "- B&P budget allocation\n"
                    "- Investment by opportunity tier\n\n"
                    "**Pipeline Goals:**\n"
                    "- Pipeline value target\n"
                    "- Number of opportunities by stage\n"
                    "- Opportunity flow rate\n\n"
                    "**Win Rate Targets:**\n"
                    "- Target win rate by tier\n"
                    "- Historical baseline"
                ),
            ),
            SectionSpec(
                name="Success Metrics",
                order=8,
                description="How we measure go-to-market success",
                min_words=75,
                max_words=200,
                required=True,
                dependencies=["Sales Strategy", "Marketing Approach"],
                guidance=(
                    "Define success metrics with specific targets:\n\n"
                    "**Pipeline Metrics:**\n"
                    "- Total pipeline value: $X\n"
                    "- Qualified opportunities: X\n"
                    "- Pipeline coverage ratio: X:1\n\n"
                    "**Win Metrics:**\n"
                    "- Win rate target: X%\n"
                    "- Wins per quarter: X\n"
                    "- New contract value: $X\n\n"
                    "**Revenue Metrics:**\n"
                    "- Revenue target: $X\n"
                    "- Growth rate: X%\n"
                    "- Market share: X%\n\n"
                    "**Relationship Metrics:**\n"
                    "- New agency relationships: X\n"
                    "- Customer meetings per month: X\n\n"
                    "**Brand Metrics:**\n"
                    "- Speaking engagements: X\n"
                    "- Published content: X pieces\n\n"
                    "All metrics must be SPECIFIC and MEASURABLE with timeframes."
                ),
            ),
        ]
