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
                max_words=200,
                guidance=(
                    "Provide a compelling introduction that establishes:\n"
                    "- Company name and legal structure\n"
                    "- Years in business and founding story (brief)\n"
                    "- Mission statement or value proposition\n"
                    "- Primary service areas and target customers\n"
                    "Keep it concise and impactful - this sets the tone for the document."
                ),
            ),
            SectionSpec(
                name="Core Competencies",
                order=2,
                description="Primary capabilities and service offerings",
                min_words=100,
                max_words=400,
                dependencies=["Company Overview"],
                guidance=(
                    "List the company's primary capabilities:\n"
                    "- Use bullet points for scannability\n"
                    "- Be specific about technologies, methodologies, and approaches\n"
                    "- Focus on capabilities most relevant to target agencies\n"
                    "- Include any specialized expertise or certifications\n"
                    "Aim for 4-6 core competencies with brief descriptions."
                ),
            ),
            SectionSpec(
                name="Past Performance",
                order=3,
                description="Relevant contract experience with key accomplishments",
                min_words=100,
                max_words=500,
                dependencies=["Core Competencies"],
                guidance=(
                    "Highlight 2-4 most relevant contracts:\n"
                    "- Contract name and customer agency\n"
                    "- Contract value and period of performance\n"
                    "- Scope summary (1-2 sentences)\n"
                    "- Key accomplishments with quantified results where possible\n"
                    "- CPARS ratings if exceptional\n"
                    "Select contracts that best demonstrate capabilities listed above."
                ),
            ),
            SectionSpec(
                name="Differentiators",
                order=4,
                description="What sets the company apart from competitors",
                min_words=75,
                max_words=300,
                dependencies=["Core Competencies"],
                guidance=(
                    "Articulate 3-5 key differentiators:\n"
                    "- What makes the company unique?\n"
                    "- Proprietary tools, methodologies, or approaches\n"
                    "- Specialized expertise or niche capabilities\n"
                    "- Customer satisfaction metrics or testimonials\n"
                    "Be specific and provable - avoid generic claims."
                ),
            ),
            SectionSpec(
                name="Certifications & Clearances",
                order=5,
                description="Relevant certifications, clearances, and contract vehicles",
                min_words=50,
                max_words=200,
                guidance=(
                    "List key certifications and qualifications:\n"
                    "- Small business certifications (8(a), HUBZone, SDVOSB, etc.)\n"
                    "- Quality certifications (ISO, CMMI, etc.)\n"
                    "- Security clearances (facility clearance level)\n"
                    "- Contract vehicles (GSA Schedule, OASIS, etc.)\n"
                    "Use a clean, scannable format."
                ),
            ),
            SectionSpec(
                name="Contact Information",
                order=6,
                description="Company contact details and identifiers",
                min_words=25,
                max_words=100,
                required=True,
                guidance=(
                    "Include essential contact information:\n"
                    "- Company name and address\n"
                    "- Primary contact name and title\n"
                    "- Phone and email\n"
                    "- Website\n"
                    "- UEI/CAGE code\n"
                    "- Primary NAICS codes\n"
                    "Format clearly for easy reference."
                ),
            ),
        ]
