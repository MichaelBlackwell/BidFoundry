"""
Capability Statement Template

Defines the structure for GovCon Capability Statements.
"""

from typing import List
from .base import DocumentTemplate, SectionSpec, register_template


@register_template
class CapabilityStatementTemplate(DocumentTemplate):
    """
    Template for Capability Statement documents.

    A Capability Statement is a concise marketing document that showcases
    a company's capabilities, past performance, and differentiators to
    potential government customers and teaming partners.
    """

    @property
    def document_type(self) -> str:
        return "Capability Statement"

    @property
    def description(self) -> str:
        return (
            "A concise 1-2 page marketing document that showcases company "
            "capabilities to government customers and potential teaming partners. "
            "Used for industry days, capability briefings, and partner outreach."
        )

    @property
    def requires_opportunity(self) -> bool:
        return False  # Can be created without a specific opportunity

    @property
    def sections(self) -> List[SectionSpec]:
        return [
            SectionSpec(
                name="Company Overview",
                order=1,
                description="Brief introduction to the company, mission, and value proposition",
                min_words=50,
                max_words=250,
                required=True,
                guidance=(
                    "Provide a compelling introduction that establishes:\n"
                    "- Company name and legal structure (LLC, Inc., etc.)\n"
                    "- Headquarters location\n"
                    "- Years in business\n"
                    "- Mission statement or value proposition (1-2 sentences)\n"
                    "- Primary service areas and target customers\n"
                    "- Number of employees and annual revenue (if appropriate)\n"
                    "Keep it concise and impactful - this sets the tone for the document."
                ),
            ),
            SectionSpec(
                name="Core Competencies",
                order=2,
                description="Primary capabilities and service offerings aligned with NAICS codes",
                min_words=100,
                max_words=400,
                required=True,
                dependencies=["Company Overview"],
                guidance=(
                    "List the company's primary capabilities:\n"
                    "- Align each competency with relevant NAICS codes\n"
                    "- Use bullet points for scannability\n"
                    "- Be specific about technologies, methodologies, and approaches\n"
                    "- Focus on capabilities most relevant to target agencies\n"
                    "- Include any specialized expertise\n"
                    "Aim for 4-6 core competencies with brief descriptions.\n"
                    "Example format: 'Systems Integration (NAICS 541512): End-to-end...'"
                ),
            ),
            SectionSpec(
                name="Past Performance",
                order=3,
                description="Relevant contract experience with quantified accomplishments",
                min_words=150,
                max_words=600,
                required=True,
                dependencies=["Core Competencies"],
                guidance=(
                    "Highlight 2-4 most relevant contracts:\n"
                    "For each contract include:\n"
                    "- Contract name/title and customer agency\n"
                    "- Contract value (or range) and period of performance\n"
                    "- Contract type (FFP, T&M, CPFF, etc.)\n"
                    "- Scope summary (2-3 sentences)\n"
                    "- Key accomplishments with QUANTIFIED results\n"
                    "  (e.g., 'reduced processing time by 40%', 'saved $2M annually')\n"
                    "- CPARS ratings if Exceptional or Very Good\n"
                    "- Point of contact (name and agency)\n"
                    "Select contracts that best demonstrate capabilities listed above.\n"
                    "If past performance is limited, include relevant commercial work."
                ),
            ),
            SectionSpec(
                name="Differentiators",
                order=4,
                description="What sets the company apart from competitors",
                min_words=100,
                max_words=350,
                required=True,
                dependencies=["Core Competencies"],
                guidance=(
                    "Articulate 3-5 key differentiators:\n"
                    "- What makes the company UNIQUE vs. competitors?\n"
                    "- Proprietary tools, methodologies, or approaches\n"
                    "- Specialized expertise or niche capabilities\n"
                    "- Customer satisfaction metrics or testimonials\n"
                    "- Speed, flexibility, or responsiveness advantages\n"
                    "- Technical innovations or patents\n"
                    "- Key personnel expertise\n\n"
                    "Be SPECIFIC and PROVABLE - avoid generic claims like 'dedicated team'.\n"
                    "Each differentiator should answer: 'Why choose us over alternatives?'"
                ),
            ),
            SectionSpec(
                name="Certifications & Clearances",
                order=5,
                description="Certifications, clearances, contract vehicles, and compliance status",
                min_words=75,
                max_words=300,
                required=True,
                guidance=(
                    "List key certifications and qualifications:\n\n"
                    "**Small Business Certifications:**\n"
                    "- SBA 8(a), HUBZone, SDVOSB, WOSB/EDWOSB status\n"
                    "- Applicable state/local certifications\n\n"
                    "**Quality & Security Certifications:**\n"
                    "- ISO 9001, ISO 27001, ISO 20000\n"
                    "- CMMI Level (if applicable)\n"
                    "- CMMC Level (current or target)\n"
                    "- FedRAMP authorization status\n"
                    "- Facility Clearance Level (FCL)\n\n"
                    "**Contract Vehicles:**\n"
                    "- GSA Schedule(s) and contract number(s)\n"
                    "- OASIS, SEWP, CIO-SP3, ITES, etc.\n"
                    "- Agency-specific IDIQs or BPAs\n\n"
                    "**Compliance:**\n"
                    "- SAM registration status and expiration\n"
                    "- DFARS compliance status\n"
                    "Use a clean, scannable format with clear categories."
                ),
            ),
            SectionSpec(
                name="Contact Information",
                order=6,
                description="Company contact details and federal identifiers",
                min_words=40,
                max_words=150,
                required=True,
                guidance=(
                    "Include essential contact information:\n"
                    "- Company legal name\n"
                    "- Full headquarters address\n"
                    "- Primary contact name and title\n"
                    "- Phone number and email\n"
                    "- Website URL\n\n"
                    "**Federal Identifiers:**\n"
                    "- UEI (Unique Entity ID)\n"
                    "- CAGE Code\n"
                    "- Primary NAICS codes (list top 3-5)\n"
                    "- DUNS (if still applicable)\n\n"
                    "Format clearly for easy reference and quick lookup."
                ),
            ),
        ]
