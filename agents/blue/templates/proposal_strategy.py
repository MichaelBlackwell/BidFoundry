"""
Proposal Strategy Template

Defines the structure for Proposal Strategy documents.
"""

from typing import List
from .base import DocumentTemplate, SectionSpec, register_template


@register_template
class ProposalStrategyTemplate(DocumentTemplate):
    """
    Template for Proposal Strategy documents.

    A Proposal Strategy document provides the strategic framework for
    developing a winning proposal, including win themes, discriminators,
    and approach summaries.
    """

    @property
    def document_type(self) -> str:
        return "Proposal Strategy"

    @property
    def description(self) -> str:
        return (
            "A strategic framework for developing a winning proposal. Includes "
            "win themes, discriminators, technical and management approach "
            "summaries, pricing strategy, and compliance requirements."
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
                description="Overview of proposal strategy and key messages",
                min_words=100,
                max_words=300,
                guidance=(
                    "Provide a strategic overview:\n"
                    "- Brief opportunity description\n"
                    "- Our primary value proposition\n"
                    "- Key win strategy elements\n"
                    "- Competitive positioning summary\n"
                    "- Overall approach to winning\n"
                    "This section guides the entire proposal effort."
                ),
            ),
            SectionSpec(
                name="Win Themes",
                order=2,
                description="Core themes that differentiate our proposal",
                min_words=200,
                max_words=500,
                dependencies=["Executive Summary"],
                guidance=(
                    "Develop 3-5 compelling win themes:\n"
                    "Each theme should:\n"
                    "- Address a key evaluation criterion\n"
                    "- Differentiate us from competitors\n"
                    "- Be specific and provable\n"
                    "- Connect to customer hot buttons\n\n"
                    "For each theme provide:\n"
                    "- Theme statement (1-2 sentences)\n"
                    "- Why it matters to the customer\n"
                    "- Proof points supporting the theme\n"
                    "- How to weave throughout proposal"
                ),
            ),
            SectionSpec(
                name="Discriminators",
                order=3,
                description="What sets us apart from competitors",
                min_words=150,
                max_words=400,
                dependencies=["Win Themes"],
                guidance=(
                    "Identify 4-6 key discriminators:\n"
                    "- Unique capabilities or expertise\n"
                    "- Proprietary tools or methodologies\n"
                    "- Superior past performance\n"
                    "- Key personnel advantages\n"
                    "- Relationship or insight advantages\n"
                    "- Teaming advantages\n\n"
                    "For each discriminator:\n"
                    "- What makes it unique\n"
                    "- Proof/evidence\n"
                    "- Proposal placement strategy"
                ),
            ),
            SectionSpec(
                name="Technical Approach Summary",
                order=4,
                description="High-level technical approach and innovation",
                min_words=200,
                max_words=500,
                dependencies=["Win Themes"],
                guidance=(
                    "Outline the technical approach:\n"
                    "- Solution overview\n"
                    "- Key technical innovations\n"
                    "- Alignment to requirements\n"
                    "- Technical risk mitigation\n"
                    "- Transition approach\n\n"
                    "Focus on strategic elements, not detailed solutioning.\n"
                    "Highlight what makes our approach superior."
                ),
            ),
            SectionSpec(
                name="Management Approach Summary",
                order=5,
                description="High-level management and staffing approach",
                min_words=150,
                max_words=400,
                dependencies=["Win Themes"],
                guidance=(
                    "Outline the management approach:\n"
                    "- Organization structure\n"
                    "- Key personnel highlights\n"
                    "- Staffing strategy\n"
                    "- Quality assurance approach\n"
                    "- Communication and reporting\n"
                    "- Subcontractor management (if applicable)\n\n"
                    "Emphasize management strengths that differentiate."
                ),
            ),
            SectionSpec(
                name="Pricing Strategy",
                order=6,
                description="Approach to competitive pricing",
                min_words=100,
                max_words=300,
                dependencies=["Technical Approach Summary", "Management Approach Summary"],
                guidance=(
                    "Outline pricing strategy:\n"
                    "- Price-to-win estimate and rationale\n"
                    "- Pricing approach (aggressive/competitive/premium)\n"
                    "- Key cost drivers and efficiencies\n"
                    "- B&P investment considerations\n"
                    "- Competitive pricing intelligence\n"
                    "- Risk reserves approach\n\n"
                    "For LPTA: emphasize affordability\n"
                    "For Best Value: balance price with strengths"
                ),
            ),
            SectionSpec(
                name="Risk Mitigation",
                order=7,
                description="Key risks and mitigation strategies",
                min_words=100,
                max_words=300,
                dependencies=["Technical Approach Summary"],
                guidance=(
                    "Address proposal and execution risks:\n"
                    "- Technical risks and mitigation\n"
                    "- Schedule risks and mitigation\n"
                    "- Staffing risks and mitigation\n"
                    "- Cost risks and mitigation\n"
                    "- Competitive risks and mitigation\n\n"
                    "Show evaluators we understand and manage risks."
                ),
            ),
            SectionSpec(
                name="Compliance Checklist",
                order=8,
                description="Key compliance requirements and status",
                min_words=75,
                max_words=250,
                guidance=(
                    "List critical compliance items:\n"
                    "- Page limits and formatting requirements\n"
                    "- Required certifications/representations\n"
                    "- Mandatory attachments\n"
                    "- Security requirements\n"
                    "- Small business subcontracting requirements\n"
                    "- Any special compliance considerations\n\n"
                    "Note any compliance risks or concerns."
                ),
            ),
        ]
