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
                required=True,
                guidance=(
                    "Provide a brief overview:\n"
                    "- Context: Company-wide analysis OR opportunity-specific (name the opportunity)\n"
                    "- Top 2 Strengths that drive competitive advantage\n"
                    "- Top 2 Weaknesses that require attention\n"
                    "- Top 2 Opportunities to pursue\n"
                    "- Top 2 Threats to monitor/mitigate\n"
                    "- Overall Strategic Assessment: Favorable/Neutral/Challenging\n"
                    "- Primary Recommendation (one clear action)\n"
                    "This summary must be usable as a standalone briefing."
                ),
            ),
            SectionSpec(
                name="Strengths",
                order=2,
                description="Internal positive attributes and resources",
                min_words=150,
                max_words=400,
                required=True,
                guidance=(
                    "Identify 5-8 internal strengths. For EACH strength include:\n\n"
                    "**Categories to Consider:**\n"
                    "- Technical capabilities and specialized expertise\n"
                    "- Relevant past performance (specific contracts)\n"
                    "- Certifications (ISO, CMMI, CMMC, etc.)\n"
                    "- Security clearances (facility and personnel)\n"
                    "- Key personnel qualifications and experience\n"
                    "- Customer relationships and incumbency\n"
                    "- Contract vehicles (GSA, OASIS, etc.)\n"
                    "- Financial stability and bonding capacity\n\n"
                    "**For Each Strength:**\n"
                    "- Specific description (not generic)\n"
                    "- Relevance to target market/opportunity\n"
                    "- Evidence/proof points (quantified where possible)\n"
                    "- Impact rating: High/Medium/Low\n\n"
                    "Prioritize by strategic impact."
                ),
            ),
            SectionSpec(
                name="Weaknesses",
                order=3,
                description="Internal negative attributes and gaps",
                min_words=150,
                max_words=400,
                required=True,
                guidance=(
                    "Honestly assess 5-8 internal weaknesses. For EACH weakness:\n\n"
                    "**Categories to Consider:**\n"
                    "- Capability gaps vs. target requirements\n"
                    "- Limited/no past performance in key areas\n"
                    "- Missing certifications or clearances\n"
                    "- Resource/capacity constraints\n"
                    "- Geographic limitations\n"
                    "- Teaming gaps or dependencies\n"
                    "- Pricing competitiveness issues\n"
                    "- Brand recognition gaps\n\n"
                    "**For Each Weakness:**\n"
                    "- Honest, specific description\n"
                    "- Impact Assessment: High/Medium/Low\n"
                    "- Mitigation Strategy: What can be done to address it?\n"
                    "- Timeline: How long to remediate?\n\n"
                    "DO NOT sugar-coat. Honest assessment is essential for strategy."
                ),
            ),
            SectionSpec(
                name="Opportunities",
                order=4,
                description="External factors that could benefit the company",
                min_words=150,
                max_words=400,
                required=True,
                guidance=(
                    "Identify 5-8 external opportunities. For EACH opportunity:\n\n"
                    "**Categories to Consider:**\n"
                    "- Agency priorities aligned with our capabilities\n"
                    "- Budget trends favoring our services\n"
                    "- Upcoming recompetes with weak/vulnerable incumbents\n"
                    "- New requirements matching our expertise\n"
                    "- Teaming/partnership opportunities\n"
                    "- Set-aside advantages (8(a), HUBZone, SDVOSB, etc.)\n"
                    "- Technology trends we can leverage\n"
                    "- Regulatory changes creating demand\n\n"
                    "**For Each Opportunity:**\n"
                    "- Specific description with source/evidence\n"
                    "- Why we can capitalize (alignment to strengths)\n"
                    "- Probability: High/Medium/Low\n"
                    "- Suggested Action to pursue\n"
                    "- Timeline/urgency"
                ),
            ),
            SectionSpec(
                name="Threats",
                order=5,
                description="External factors that could harm the company",
                min_words=150,
                max_words=400,
                required=True,
                guidance=(
                    "Assess 5-8 external threats. For EACH threat:\n\n"
                    "**Categories to Consider:**\n"
                    "- Strong incumbent positions\n"
                    "- Well-funded/aggressive competitor activity\n"
                    "- Budget cuts or program cancellations\n"
                    "- Changing agency priorities\n"
                    "- Regulatory/compliance changes (CMMC, etc.)\n"
                    "- Technological disruption\n"
                    "- Economic factors affecting pricing\n"
                    "- Talent market challenges\n\n"
                    "**For Each Threat:**\n"
                    "- Specific description\n"
                    "- Likelihood: High/Medium/Low\n"
                    "- Impact: High/Medium/Low\n"
                    "- Risk Mitigation strategy\n"
                    "- Early warning indicators to monitor"
                ),
            ),
            SectionSpec(
                name="Strategic Implications",
                order=6,
                description="Analysis of how SWOT factors interact",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Strengths", "Weaknesses", "Opportunities", "Threats"],
                guidance=(
                    "Analyze SWOT factor interactions using the TOWS matrix:\n\n"
                    "**S-O Intersection (Leverage):**\n"
                    "- Which strengths can exploit which opportunities?\n"
                    "- Quick wins available?\n\n"
                    "**S-T Intersection (Defend):**\n"
                    "- Which strengths can counter which threats?\n"
                    "- Defensive positioning needed?\n\n"
                    "**W-O Intersection (Improve):**\n"
                    "- Which weaknesses limit which opportunities?\n"
                    "- Investment priorities to close gaps?\n\n"
                    "**W-T Intersection (Avoid):**\n"
                    "- Where do weaknesses amplify threats?\n"
                    "- Critical vulnerabilities requiring immediate action?\n\n"
                    "Identify the 2-3 most critical intersections."
                ),
            ),
            SectionSpec(
                name="Recommended Actions",
                order=7,
                description="Priority actions based on SWOT analysis",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Strategic Implications"],
                guidance=(
                    "Provide prioritized action items by TOWS strategy:\n\n"
                    "**SO Strategies (Pursue):** 2-3 actions\n"
                    "- Use strengths to pursue opportunities\n"
                    "- Owner, timeline, success metric\n\n"
                    "**WO Strategies (Invest):** 2-3 actions\n"
                    "- Address weaknesses to enable opportunities\n"
                    "- Owner, timeline, investment required\n\n"
                    "**ST Strategies (Defend):** 2-3 actions\n"
                    "- Use strengths to mitigate threats\n"
                    "- Owner, timeline, success metric\n\n"
                    "**WT Strategies (Avoid):** 1-2 actions\n"
                    "- Minimize weaknesses and avoid threats\n"
                    "- Owner, timeline, risk indicator\n\n"
                    "Each action must be SPECIFIC, ASSIGNABLE, and TIME-BOUND."
                ),
            ),
        ]
