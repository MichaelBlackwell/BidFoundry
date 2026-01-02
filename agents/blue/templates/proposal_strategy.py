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
                required=True,
                guidance=(
                    "Provide a strategic overview that guides the entire proposal:\n\n"
                    "**Opportunity Snapshot:**\n"
                    "- Title, Agency, Solicitation Number\n"
                    "- Value, Period of Performance, Set-Aside\n"
                    "- RFP Release / Proposal Due dates\n\n"
                    "**Our Value Proposition:** (2-3 sentences)\n"
                    "- Why we are the best choice\n\n"
                    "**Win Strategy Summary:**\n"
                    "- Top 3 win themes (one line each)\n"
                    "- Competitive positioning (Frontrunner/Competitive/Underdog)\n"
                    "- Key discriminators\n\n"
                    "**Critical Success Factors:**\n"
                    "- What must go right to win\n"
                    "This section is the 'North Star' for proposal writers."
                ),
            ),
            SectionSpec(
                name="Win Themes",
                order=2,
                description="Core themes that differentiate our proposal",
                min_words=200,
                max_words=500,
                required=True,
                dependencies=["Executive Summary"],
                guidance=(
                    "Develop 3-5 compelling win themes. For EACH theme:\n\n"
                    "**Theme Statement:** (1-2 impactful sentences)\n"
                    "- Customer-focused, benefit-oriented\n"
                    "- Specific, not generic\n\n"
                    "**Evaluation Factor Alignment:**\n"
                    "- Which evaluation criterion does this address?\n"
                    "- Why does this matter to the evaluators?\n\n"
                    "**Customer Hot Buttons:**\n"
                    "- What pain points does this solve?\n"
                    "- Intel from customer engagement\n\n"
                    "**Proof Points:**\n"
                    "- Specific evidence (past performance, metrics)\n"
                    "- Quantified results where possible\n\n"
                    "**Proposal Integration:**\n"
                    "- Where to emphasize (Executive Summary, Technical, etc.)\n"
                    "- Key graphics or callouts\n\n"
                    "Themes must be DIFFERENTIATING, not table-stakes."
                ),
            ),
            SectionSpec(
                name="Discriminators",
                order=3,
                description="What sets us apart from competitors",
                min_words=150,
                max_words=400,
                required=True,
                dependencies=["Win Themes"],
                guidance=(
                    "Identify 4-6 key discriminators. For EACH:\n\n"
                    "**Categories to Consider:**\n"
                    "- Unique capabilities or specialized expertise\n"
                    "- Proprietary tools, IP, or methodologies\n"
                    "- Superior/directly relevant past performance\n"
                    "- Key personnel with unique qualifications\n"
                    "- Customer relationship/incumbent knowledge\n"
                    "- Teaming/subcontractor advantages\n"
                    "- Price/value advantages\n\n"
                    "**For Each Discriminator:**\n"
                    "- What makes it UNIQUE (competitors can't claim)\n"
                    "- Evidence/proof (specific, verifiable)\n"
                    "- Benefit to customer (so what?)\n"
                    "- Proposal placement strategy\n"
                    "- Ghosting opportunity (does this expose competitor weakness?)\n\n"
                    "Discriminators must pass the 'Only We Can Say' test."
                ),
            ),
            SectionSpec(
                name="Technical Approach Summary",
                order=4,
                description="High-level technical approach and innovation",
                min_words=200,
                max_words=500,
                required=True,
                dependencies=["Win Themes"],
                guidance=(
                    "Outline the technical approach at strategy level:\n\n"
                    "**Solution Overview:**\n"
                    "- High-level approach in 2-3 paragraphs\n"
                    "- Key methodologies or frameworks\n"
                    "- Technology stack (if applicable)\n\n"
                    "**Alignment to Requirements:**\n"
                    "- How approach addresses each major SOW area\n"
                    "- Compliance with mandatory requirements\n\n"
                    "**Technical Innovations:**\n"
                    "- What makes our approach better/different?\n"
                    "- Efficiency gains, quality improvements\n\n"
                    "**Transition Approach:**\n"
                    "- Phase-in strategy (especially for recompetes)\n"
                    "- Risk mitigation during transition\n\n"
                    "**Technical Risks:**\n"
                    "- Top 3 technical risks and mitigations\n\n"
                    "Focus on STRATEGIC elements. Detailed solutioning comes later."
                ),
            ),
            SectionSpec(
                name="Management Approach Summary",
                order=5,
                description="High-level management and staffing approach",
                min_words=150,
                max_words=400,
                required=True,
                dependencies=["Win Themes"],
                guidance=(
                    "Outline the management approach:\n\n"
                    "**Organization Structure:**\n"
                    "- Reporting relationships\n"
                    "- Customer interface model\n"
                    "- Subcontractor integration\n\n"
                    "**Key Personnel:**\n"
                    "- Program Manager qualifications (brief)\n"
                    "- Other key roles and why they're strong\n"
                    "- Any named personnel commitments\n\n"
                    "**Staffing Strategy:**\n"
                    "- Hiring/retention approach\n"
                    "- Clearance strategy\n"
                    "- Surge capacity\n\n"
                    "**Quality Assurance:**\n"
                    "- QA/QC methodology\n"
                    "- Continuous improvement approach\n\n"
                    "**Communication/Reporting:**\n"
                    "- Customer communication cadence\n"
                    "- Reporting deliverables\n\n"
                    "Emphasize management DIFFERENTIATORS."
                ),
            ),
            SectionSpec(
                name="Pricing Strategy",
                order=6,
                description="Approach to competitive pricing",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Technical Approach Summary", "Management Approach Summary"],
                guidance=(
                    "Outline pricing strategy:\n\n"
                    "**Price-to-Win Analysis:**\n"
                    "- Estimated competitive range\n"
                    "- Our target position (low/middle/high)\n"
                    "- Rationale for positioning\n\n"
                    "**Pricing Approach:**\n"
                    "- Aggressive (below market) / Competitive (market rate) / Premium (above market)\n"
                    "- Justification based on evaluation type\n\n"
                    "**Cost Efficiency Strategies:**\n"
                    "- Key cost drivers to optimize\n"
                    "- Efficiency innovations\n"
                    "- Make vs. buy decisions\n\n"
                    "**Investment Considerations:**\n"
                    "- B&P budget for this pursuit\n"
                    "- Any uncompensated effort in pricing\n\n"
                    "**Risk Reserves:**\n"
                    "- Contingency approach\n\n"
                    "For LPTA: Emphasize lowest compliant price.\n"
                    "For Best Value: Balance price with discriminating strengths."
                ),
            ),
            SectionSpec(
                name="Risk Mitigation",
                order=7,
                description="Key risks and mitigation strategies",
                min_words=100,
                max_words=300,
                required=True,
                dependencies=["Technical Approach Summary"],
                guidance=(
                    "Address proposal and execution risks:\n\n"
                    "**Risk Categories:**\n"
                    "For each, list top 1-2 risks with mitigation:\n\n"
                    "- **Technical Risks:** Technology, complexity\n"
                    "- **Schedule Risks:** Timeline, dependencies\n"
                    "- **Staffing Risks:** Hiring, retention, clearances\n"
                    "- **Cost Risks:** Overruns, pricing pressure\n"
                    "- **Competitive Risks:** Incumbent advantage, competitor strengths\n"
                    "- **Proposal Risks:** Compliance, schedule, resources\n\n"
                    "**For Each Risk:**\n"
                    "- Risk description\n"
                    "- Likelihood / Impact\n"
                    "- Mitigation strategy\n"
                    "- Contingency if mitigation fails\n\n"
                    "Show evaluators we UNDERSTAND and MANAGE risks proactively."
                ),
            ),
            SectionSpec(
                name="Compliance Checklist",
                order=8,
                description="Key compliance requirements and status",
                min_words=75,
                max_words=250,
                required=True,
                guidance=(
                    "List critical compliance items and status:\n\n"
                    "**Proposal Format:**\n"
                    "- Page limits by volume\n"
                    "- Font, margin, spacing requirements\n"
                    "- File naming conventions\n\n"
                    "**Required Certifications:**\n"
                    "- Reps and Certs status\n"
                    "- Required certifications (list with status)\n\n"
                    "**Mandatory Attachments:**\n"
                    "- List each with responsible party\n\n"
                    "**Security Requirements:**\n"
                    "- Clearance requirements vs. our status\n"
                    "- Facility clearance needs\n\n"
                    "**Small Business Requirements:**\n"
                    "- Subcontracting plan requirements\n"
                    "- Small business goals\n\n"
                    "**Compliance Risks:**\n"
                    "- Any gaps or concerns to address\n\n"
                    "Use ✓ for compliant, ⚠ for action needed, ✗ for gap."
                ),
            ),
        ]
