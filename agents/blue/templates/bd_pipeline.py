"""
BD Pipeline Template

Defines the structure for Business Development Pipeline documents.
"""

from typing import List
from .base import DocumentTemplate, SectionSpec, register_template


@register_template
class BDPipelineTemplate(DocumentTemplate):
    """
    Template for BD Pipeline documents.

    A BD Pipeline document provides an overview of target opportunities,
    prioritization, resource planning, and pursuit strategy.
    """

    @property
    def document_type(self) -> str:
        return "BD Pipeline"

    @property
    def description(self) -> str:
        return (
            "A strategic overview of business development opportunities in the "
            "pipeline. Includes opportunity prioritization, resource requirements, "
            "timelines, and risk assessment."
        )

    @property
    def requires_opportunity(self) -> bool:
        return False  # Pipeline overview doesn't require a single opportunity

    @property
    def sections(self) -> List[SectionSpec]:
        return [
            SectionSpec(
                name="Pipeline Overview",
                order=1,
                description="Summary of the current BD pipeline",
                min_words=100,
                max_words=300,
                required=True,
                guidance=(
                    "Provide a high-level pipeline summary:\n\n"
                    "**Pipeline Metrics:**\n"
                    "- Total opportunities tracked: X\n"
                    "- Total addressable value: $X\n"
                    "- Weighted value (Pwin-adjusted): $X\n"
                    "- Pipeline coverage ratio: X:1 (vs. revenue target)\n\n"
                    "**Distribution by Stage:**\n"
                    "- Forecast/Tracking: X opps, $X value\n"
                    "- Pre-RFP/Shaping: X opps, $X value\n"
                    "- RFP Released/Active: X opps, $X value\n"
                    "- Submitted/Awaiting Award: X opps, $X value\n\n"
                    "**Distribution by Priority:**\n"
                    "- Must Win: X opps\n"
                    "- High Priority: X opps\n"
                    "- Medium Priority: X opps\n"
                    "- Low/Tracking: X opps\n\n"
                    "**Trends:**\n"
                    "- Change from last period\n"
                    "- Key wins/losses since last review"
                ),
            ),
            SectionSpec(
                name="Priority Opportunities",
                order=2,
                description="Top priority opportunities with rationale",
                min_words=150,
                max_words=500,
                required=True,
                dependencies=["Pipeline Overview"],
                guidance=(
                    "List the top 5-10 priority opportunities. For EACH:\n\n"
                    "**Opportunity ID:** [Internal tracking #]\n\n"
                    "**Basic Info:**\n"
                    "- Title/Name\n"
                    "- Agency/Customer\n"
                    "- Solicitation # (if released)\n\n"
                    "**Value & Timeline:**\n"
                    "- Estimated value: $X\n"
                    "- Period of performance: X years\n"
                    "- Expected RFP: [date]\n"
                    "- Expected award: [date]\n\n"
                    "**Priority & Status:**\n"
                    "- Priority: Must Win / High / Medium / Low\n"
                    "- Pwin: X%\n"
                    "- Stage: [Forecast/Pre-RFP/RFP/Submitted]\n"
                    "- Capture Manager: [Name]\n\n"
                    "**Prioritization Rationale:**\n"
                    "- Why this priority level?\n"
                    "- Strategic importance\n\n"
                    "Order by PRIORITY, not alphabetically."
                ),
            ),
            SectionSpec(
                name="Opportunity Details",
                order=3,
                description="Detailed information on key opportunities",
                min_words=200,
                max_words=600,
                required=True,
                dependencies=["Priority Opportunities"],
                guidance=(
                    "Provide detailed analysis of top 3-5 opportunities:\n\n"
                    "**For Each Opportunity:**\n\n"
                    "**Scope Summary:**\n"
                    "- What is being procured (2-3 sentences)\n"
                    "- Key requirements\n\n"
                    "**Procurement Details:**\n"
                    "- Set-aside status\n"
                    "- Contract type (FFP, T&M, CPFF, etc.)\n"
                    "- Evaluation approach (LPTA, Best Value)\n"
                    "- NAICS code\n\n"
                    "**Our Alignment:**\n"
                    "- Capability fit (Strong/Moderate/Weak)\n"
                    "- Past performance relevance\n"
                    "- Key strengths for this opportunity\n"
                    "- Gaps to address\n\n"
                    "**Competitive Landscape:**\n"
                    "- Incumbent (if recompete)\n"
                    "- Known competitors\n"
                    "- Our competitive position\n\n"
                    "**Win Probability:** X%\n"
                    "- Rationale for estimate\n\n"
                    "**Capture Strategy Summary:**\n"
                    "- Key actions underway\n"
                    "- Next steps"
                ),
            ),
            SectionSpec(
                name="Resource Requirements",
                order=4,
                description="Resources needed to pursue priority opportunities",
                min_words=100,
                max_words=350,
                required=True,
                dependencies=["Opportunity Details"],
                guidance=(
                    "Outline resource needs for priority pursuits:\n\n"
                    "**BD/Capture Personnel:**\n"
                    "- Capture manager assignments\n"
                    "- BD support needed\n"
                    "- Capacity vs. demand analysis\n\n"
                    "**Proposal Team:**\n"
                    "- Proposal manager requirements\n"
                    "- Writer/SME needs by opportunity\n"
                    "- Peak demand periods\n\n"
                    "**Subject Matter Experts:**\n"
                    "- Technical SMEs needed\n"
                    "- Availability conflicts\n\n"
                    "**B&P Investment:**\n"
                    "- Budget allocation by opportunity tier\n"
                    "- Total B&P required vs. available\n"
                    "- Investment recommendations\n\n"
                    "**Teaming Requirements:**\n"
                    "- Partners needed by opportunity\n"
                    "- Status of teaming agreements\n\n"
                    "**Resource Conflicts/Gaps:**\n"
                    "- Overlapping deadlines\n"
                    "- Capacity shortfalls\n"
                    "- Mitigation actions"
                ),
            ),
            SectionSpec(
                name="Timeline & Milestones",
                order=5,
                description="Key dates and milestones for pipeline opportunities",
                min_words=100,
                max_words=350,
                required=True,
                dependencies=["Priority Opportunities"],
                guidance=(
                    "Map out critical dates for next 6-12 months:\n\n"
                    "**Upcoming Milestones by Month:**\n\n"
                    "For each month, list:\n"
                    "- Industry Days / Pre-proposal conferences\n"
                    "- RFI / Sources Sought responses due\n"
                    "- Expected RFP releases\n"
                    "- Proposal due dates\n"
                    "- Go/No-Go decision points\n"
                    "- Expected award announcements\n\n"
                    "**Format Example:**\n"
                    "**January 2024:**\n"
                    "- [Date]: [Opportunity] - Industry Day\n"
                    "- [Date]: [Opportunity] - Proposal Due\n"
                    "- [Date]: [Opportunity] - Go/No-Go Gate\n\n"
                    "**Critical Clusters:**\n"
                    "- Flag periods with multiple competing deadlines\n"
                    "- Resource surge requirements\n\n"
                    "**Key Decision Points:**\n"
                    "- Upcoming Go/No-Go reviews\n"
                    "- Teaming decisions needed"
                ),
            ),
            SectionSpec(
                name="Risk Assessment",
                order=6,
                description="Key risks to pipeline success and mitigation",
                min_words=100,
                max_words=350,
                required=True,
                dependencies=["Opportunity Details"],
                guidance=(
                    "Assess pipeline-level risks:\n\n"
                    "**Concentration Risk:**\n"
                    "- Over-reliance on few large opportunities?\n"
                    "- Single agency/customer dependence?\n"
                    "- Mitigation: Diversification strategy\n\n"
                    "**Capacity Risk:**\n"
                    "- Can we pursue all priority opportunities?\n"
                    "- Proposal team bandwidth\n"
                    "- Mitigation: Prioritization, augmentation\n\n"
                    "**Timing Risk:**\n"
                    "- Clustered deadlines\n"
                    "- Simultaneous proposal efforts\n"
                    "- Mitigation: Resource planning, early starts\n\n"
                    "**Win Rate Risk:**\n"
                    "- Are Pwin estimates realistic?\n"
                    "- Historical win rate comparison\n"
                    "- Mitigation: Conservative planning\n\n"
                    "**Funding/Budget Risk:**\n"
                    "- Customer budget uncertainties\n"
                    "- Program cancellation risks\n"
                    "- Mitigation: Diversification, intel monitoring\n\n"
                    "**For Each Risk:**\n"
                    "- Probability: High/Medium/Low\n"
                    "- Impact: High/Medium/Low\n"
                    "- Mitigation Strategy\n"
                    "- Owner"
                ),
            ),
        ]
