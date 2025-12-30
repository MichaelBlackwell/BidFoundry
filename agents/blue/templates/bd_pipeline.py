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
                guidance=(
                    "Provide a high-level pipeline summary:\n"
                    "- Total number of opportunities tracked\n"
                    "- Total addressable pipeline value\n"
                    "- Weighted pipeline value (probability-adjusted)\n"
                    "- Distribution by stage (forecast/RFI/RFP/submitted)\n"
                    "- Distribution by priority tier\n"
                    "- Key trends or changes from previous period"
                ),
            ),
            SectionSpec(
                name="Priority Opportunities",
                order=2,
                description="Top priority opportunities with rationale",
                min_words=150,
                max_words=500,
                dependencies=["Pipeline Overview"],
                guidance=(
                    "List the top 5-10 priority opportunities:\n"
                    "For each opportunity:\n"
                    "- Title and agency\n"
                    "- Estimated value\n"
                    "- Expected RFP/award dates\n"
                    "- Priority rating (Must Win/High/Medium/Low)\n"
                    "- Rationale for prioritization\n"
                    "- Current capture status\n"
                    "Order by priority, not alphabetically."
                ),
            ),
            SectionSpec(
                name="Opportunity Details",
                order=3,
                description="Detailed information on key opportunities",
                min_words=200,
                max_words=600,
                dependencies=["Priority Opportunities"],
                guidance=(
                    "Provide detailed analysis of top opportunities:\n"
                    "For each (focus on top 3-5):\n"
                    "- Scope summary\n"
                    "- Set-aside and evaluation approach\n"
                    "- Key requirements alignment\n"
                    "- Competitive landscape summary\n"
                    "- Win probability estimate\n"
                    "- Capture strategy summary\n"
                    "Organize by priority tier."
                ),
            ),
            SectionSpec(
                name="Resource Requirements",
                order=4,
                description="Resources needed to pursue priority opportunities",
                min_words=100,
                max_words=350,
                dependencies=["Opportunity Details"],
                guidance=(
                    "Outline resource needs:\n"
                    "- BD/Capture personnel requirements\n"
                    "- Proposal team capacity needs\n"
                    "- Subject matter expert availability\n"
                    "- Investment requirements (B&P budget)\n"
                    "- Teaming/subcontracting needs\n"
                    "- Identify any resource conflicts or gaps"
                ),
            ),
            SectionSpec(
                name="Timeline & Milestones",
                order=5,
                description="Key dates and milestones for pipeline opportunities",
                min_words=100,
                max_words=350,
                dependencies=["Priority Opportunities"],
                guidance=(
                    "Map out critical dates:\n"
                    "- Industry day dates\n"
                    "- RFI/Sources Sought response dates\n"
                    "- Expected RFP release dates\n"
                    "- Proposal due dates\n"
                    "- Go/No-Go decision points\n"
                    "- Expected award dates\n"
                    "Organize chronologically for the next 6-12 months."
                ),
            ),
            SectionSpec(
                name="Risk Assessment",
                order=6,
                description="Key risks to pipeline success and mitigation",
                min_words=100,
                max_words=350,
                dependencies=["Opportunity Details"],
                guidance=(
                    "Assess pipeline risks:\n"
                    "- Concentration risk (too dependent on few opportunities)\n"
                    "- Capacity risk (can we pursue everything?)\n"
                    "- Timing risk (clustered deadlines)\n"
                    "- Win rate assumptions\n"
                    "- Funding/budget risks\n\n"
                    "For each risk:\n"
                    "- Describe the risk\n"
                    "- Assess probability and impact\n"
                    "- Provide mitigation strategy"
                ),
            ),
        ]
