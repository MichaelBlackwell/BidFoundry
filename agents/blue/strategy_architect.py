"""
Strategy Architect Agent

The primary document drafter for the adversarial swarm. Responsible for
synthesizing company profile, opportunity context, and blue team inputs
into comprehensive strategy documents.
"""

import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from agents.base import BlueTeamAgent, SwarmContext, AgentOutput
from agents.config import AgentConfig
from agents.types import AgentRole, AgentCategory

from .prompts.strategy_architect_prompts import (
    STRATEGY_ARCHITECT_SYSTEM_PROMPT,
    get_draft_prompt,
    get_revision_prompt,
    get_section_prompt,
)
from .templates.base import DocumentTemplate, get_template_for_document_type


@dataclass
class DraftResult:
    """Result of a drafting operation."""

    sections: Dict[str, str] = field(default_factory=dict)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)


class StrategyArchitectAgent(BlueTeamAgent):
    """
    The Strategy Architect is the primary document drafter for the adversarial swarm.

    Responsibilities:
    - Generate initial drafts for all supported document types
    - Incorporate feedback from other blue team agents
    - Revise sections based on accepted red team critiques
    - Maintain optimistic, opportunity-focused perspective

    The Strategy Architect synthesizes:
    - Company profile (capabilities, certifications, past performance)
    - Opportunity context (requirements, evaluation factors, competitors)
    - Blue team inputs (market analysis, compliance checks, win strategy)

    Into comprehensive, defensible strategy documents.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Strategy Architect agent.

        Args:
            config: Optional agent configuration. If not provided, uses defaults.
        """
        if config is None:
            from agents.config import get_default_config
            config = get_default_config(AgentRole.STRATEGY_ARCHITECT)

        super().__init__(config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.STRATEGY_ARCHITECT

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.BLUE

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and generate document content.

        The processing mode depends on the context:
        - BlueBuild round: Generate initial draft
        - BlueDefense round: Revise based on critiques
        - Specific section request: Draft/revise single section

        Args:
            context: SwarmContext containing all relevant information

        Returns:
            AgentOutput with generated content
        """
        start_time = time.time()

        # Validate context
        validation_errors = self.validate_context(context)
        if validation_errors:
            return self._create_output(
                success=False,
                error_message="; ".join(validation_errors),
            )

        try:
            # Determine processing mode
            if context.round_type == "BlueBuild":
                result = await self._generate_initial_draft(context)
            elif context.round_type == "BlueDefense":
                result = await self._revise_from_critiques(context)
            elif context.target_sections:
                result = await self._draft_specific_sections(context)
            else:
                # Default to full draft
                result = await self._generate_initial_draft(context)

            processing_time = int((time.time() - start_time) * 1000)

            return self._create_output(
                content=self._format_sections_as_content(result.sections),
                success=result.success,
                error_message=result.errors[0] if result.errors else None,
                sections=result.sections,
                responses=result.responses,  # Include responses for BlueDefense
                warnings=result.warnings,
                processing_time_ms=processing_time,
                token_usage=result.token_usage,
                metadata={
                    "round_type": context.round_type,
                    "document_type": context.document_type,
                    "section_count": len(result.sections),
                    "responses_count": len(result.responses),
                },
            )

        except Exception as e:
            self.log_error(f"Error in Strategy Architect processing: {e}")
            return self._create_output(
                success=False,
                error_message=f"Processing error: {str(e)}",
            )

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate the context for Strategy Architect processing.

        Args:
            context: The SwarmContext to validate

        Returns:
            List of validation error messages
        """
        errors = super().validate_context(context)

        # Require company profile
        if not context.company_profile:
            errors.append("Company profile is required for Strategy Architect")

        # Require document type
        if not context.document_type:
            errors.append("Document type must be specified")

        # Check if template exists for document type
        if context.document_type:
            template = get_template_for_document_type(context.document_type)
            if template and template.requires_opportunity and not context.opportunity:
                errors.append(
                    f"Document type '{context.document_type}' requires opportunity context"
                )

        return errors

    async def _generate_initial_draft(self, context: SwarmContext) -> DraftResult:
        """
        Generate an initial draft for all sections of the document.

        Args:
            context: SwarmContext with company profile and optional opportunity

        Returns:
            DraftResult with all drafted sections
        """
        result = DraftResult()
        start_time = time.time()

        # Get template for document type
        template = get_template_for_document_type(context.document_type)
        if not template:
            # Fall back to generic sections if no template
            section_names = self._get_default_sections(context.document_type)
        else:
            section_names = template.section_names

        # Build the drafting prompt
        prompt = get_draft_prompt(
            document_type=context.document_type,
            sections=section_names,
            company_profile=context.company_profile,
            opportunity=context.opportunity,
            additional_context=context.custom_data.get("blue_team_inputs"),
        )

        # Generate content (placeholder for actual LLM call)
        llm_response = await self._call_llm(
            system_prompt=STRATEGY_ARCHITECT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        # Parse sections from response
        content = llm_response.get("content", "")
        result.sections = self._parse_sections_from_response(content, section_names)
        result.token_usage = llm_response.get("usage", {})

        # Validate sections against template
        if template:
            for section_name, section_content in result.sections.items():
                section_errors = template.validate_section_content(
                    section_name, section_content
                )
                result.warnings.extend(section_errors)

        result.processing_time_ms = int((time.time() - start_time) * 1000)
        return result

    async def _revise_from_critiques(self, context: SwarmContext) -> DraftResult:
        """
        Revise sections based on accepted critiques.

        Args:
            context: SwarmContext with pending critiques and current drafts

        Returns:
            DraftResult with revised sections and responses
        """
        result = DraftResult()
        result.sections = dict(context.section_drafts)  # Start with current content
        responses = []  # Track responses to critiques

        # Debug logging
        self.log_info(f"BlueDefense: Received {len(context.pending_critiques)} critiques")
        self.log_info(f"BlueDefense: Available sections: {list(result.sections.keys())}")

        if not context.pending_critiques:
            self.log_warning("BlueDefense: No pending critiques to respond to!")
            result.responses = responses
            return result

        # Get critiques grouped by section, with section name normalization
        available_sections = list(result.sections.keys())
        critiques_by_section = self._group_and_normalize_critiques(
            context.pending_critiques,
            available_sections
        )

        self.log_info(f"BlueDefense: Normalized critiques by section: {list(critiques_by_section.keys())}")

        for section_name, critiques in critiques_by_section.items():
            if section_name not in result.sections:
                self.log_warning(f"BlueDefense: Section '{section_name}' not in available sections")
                result.warnings.append(
                    f"Critique targets unknown section: {section_name}"
                )
                continue

            self.log_info(f"BlueDefense: Processing {len(critiques)} critiques for section '{section_name}'")

            original_content = result.sections[section_name]

            # Build revision prompt
            prompt = get_revision_prompt(
                section_name=section_name,
                original_content=original_content,
                critiques=critiques,
                company_profile=context.company_profile,
                opportunity=context.opportunity,
            )

            # Generate revised content
            llm_response = await self._call_llm(
                system_prompt=STRATEGY_ARCHITECT_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            if llm_response.get("success"):
                content = llm_response.get("content", "")
                revised = self._extract_section_content(content, section_name)
                if revised:
                    result.sections[section_name] = revised
                    # Generate responses for each addressed critique
                    for critique in critiques:
                        responses.append({
                            "critique_id": critique.get("id", ""),
                            "message_id": critique.get("message_id", ""),  # Link to critique message
                            "target_section": section_name,
                            "action": "revised",
                            "disposition": "Accept",  # For consensus tracking
                            "summary": f"Revised {section_name} to address critique",
                            "original_critique": critique.get("content", critique.get("description", "")),
                            "changes_made": True,
                        })
                else:
                    result.warnings.append(
                        f"Could not extract revised content for {section_name}"
                    )
            else:
                result.warnings.append(
                    f"Failed to revise {section_name}: {llm_response.get('error')}"
                )

        # Store responses in result for the caller
        result.responses = responses
        return result

    async def _draft_specific_sections(self, context: SwarmContext) -> DraftResult:
        """
        Draft specific sections as requested.

        Args:
            context: SwarmContext with target_sections specified

        Returns:
            DraftResult with drafted sections
        """
        result = DraftResult()

        template = get_template_for_document_type(context.document_type)

        for section_name in context.target_sections:
            prompt = get_section_prompt(
                section_name=section_name,
                document_type=context.document_type,
                company_profile=context.company_profile,
                opportunity=context.opportunity,
                other_sections=context.section_drafts,
            )

            llm_response = await self._call_llm(
                system_prompt=STRATEGY_ARCHITECT_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            if llm_response.get("success"):
                content = llm_response.get("content", "")
                section_content = self._extract_section_content(content, section_name)
                if section_content:
                    result.sections[section_name] = section_content

                    # Validate against template
                    if template:
                        section_errors = template.validate_section_content(
                            section_name, section_content
                        )
                        result.warnings.extend(section_errors)
                else:
                    result.warnings.append(
                        f"Could not extract content for {section_name}"
                    )
            else:
                result.errors.append(
                    f"Failed to draft {section_name}: {llm_response.get('error')}"
                )

        result.success = len(result.errors) == 0
        return result

    async def draft_section(
        self,
        context: SwarmContext,
        section_name: str,
    ) -> str:
        """
        Draft content for a specific section.

        Args:
            context: The swarm context
            section_name: Name of the section to draft

        Returns:
            The drafted content for the section
        """
        context_copy = SwarmContext(
            request_id=context.request_id,
            document_type=context.document_type,
            company_profile=context.company_profile,
            opportunity=context.opportunity,
            section_drafts=context.section_drafts,
            target_sections=[section_name],
        )

        result = await self._draft_specific_sections(context_copy)
        return result.sections.get(section_name, "")

    async def revise_section(
        self,
        context: SwarmContext,
        section_name: str,
        critiques: List[Dict[str, Any]],
    ) -> str:
        """
        Revise a section based on accepted critiques.

        Args:
            context: The swarm context
            section_name: Name of the section to revise
            critiques: List of critiques to address

        Returns:
            The revised content for the section
        """
        original = context.section_drafts.get(section_name, "")
        if not original:
            return ""

        prompt = get_revision_prompt(
            section_name=section_name,
            original_content=original,
            critiques=critiques,
            company_profile=context.company_profile,
            opportunity=context.opportunity,
        )

        llm_response = await self._call_llm(
            system_prompt=STRATEGY_ARCHITECT_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            content = llm_response.get("content", "")
            revised = self._extract_section_content(content, section_name)
            return revised if revised else original

        return original

    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock content for testing purposes."""
        # Extract section names from the prompt
        section_pattern = r"^\d+\.\s+(.+)$"
        sections = []

        for line in prompt.split("\n"):
            match = re.match(section_pattern, line.strip())
            if match:
                sections.append(match.group(1))

        if not sections:
            sections = ["Content"]

        # Generate mock sections
        content_parts = []
        for section in sections:
            content_parts.append(f"## {section}")
            content_parts.append("")
            content_parts.append(
                f"This is placeholder content for the {section} section. "
                "In production, this would contain substantive content generated "
                "by the LLM based on the company profile and opportunity context."
            )
            content_parts.append("")
            content_parts.append(
                "Key points would be developed here based on the specific "
                "requirements and context provided."
            )
            content_parts.append("")

        return "\n".join(content_parts)

    def _parse_sections_from_response(
        self,
        content: str,
        expected_sections: List[str],
    ) -> Dict[str, str]:
        """
        Parse section content from an LLM response.

        Args:
            content: The full LLM response content
            expected_sections: List of expected section names

        Returns:
            Dictionary mapping section names to their content
        """
        sections = {}

        # Pattern to match section headers (## Section Name)
        section_pattern = r"^##\s+(.+?)$"

        lines = content.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            match = re.match(section_pattern, line.strip())
            if match:
                # Save previous section if exists
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                section_name = match.group(1).strip()
                # Try to match with expected sections
                current_section = self._match_section_name(
                    section_name, expected_sections
                )
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _match_section_name(
        self,
        found_name: str,
        expected_sections: List[str],
    ) -> Optional[str]:
        """
        Match a found section name to expected section names.

        Args:
            found_name: The section name found in the response
            expected_sections: List of expected section names

        Returns:
            The matched section name or the found name if no match
        """
        # Exact match
        if found_name in expected_sections:
            return found_name

        # Case-insensitive match
        found_lower = found_name.lower()
        for expected in expected_sections:
            if expected.lower() == found_lower:
                return expected

        # Partial match
        for expected in expected_sections:
            if expected.lower() in found_lower or found_lower in expected.lower():
                return expected

        # No match - return found name
        return found_name

    def _find_section_in_text(
        self,
        text: str,
        available_sections: List[str],
    ) -> Optional[str]:
        """
        Find a section name mentioned within a text string.

        Handles cases where target_section contains descriptive text
        like '- Section 2.1: "some content"' instead of just 'Executive Summary'.

        Args:
            text: The text to search within
            available_sections: List of available section names

        Returns:
            The first matching section name found, or None
        """
        text_lower = text.lower()

        # Try to find any available section mentioned in the text
        for section in available_sections:
            section_lower = section.lower()
            if section_lower in text_lower:
                return section

        # Try keyword matching for common section types
        section_keywords = {
            "executive summary": ["executive", "summary", "overview"],
            "main content": ["main", "content", "body", "details"],
            "recommendations": ["recommend", "suggestion", "action"],
            "conclusion": ["conclusion", "closing", "final"],
        }

        for section in available_sections:
            section_lower = section.lower()
            if section_lower in section_keywords:
                for keyword in section_keywords[section_lower]:
                    if keyword in text_lower:
                        return section

        # If no match found, default to "Main Content" if available
        # since most critiques relate to the main body
        for section in available_sections:
            if "main" in section.lower() or "content" in section.lower():
                return section

        # Return first non-title section as fallback
        for section in available_sections:
            if section.lower() not in ["title", "header"]:
                return section

        return None

    def _extract_section_content(
        self,
        content: str,
        section_name: str,
    ) -> Optional[str]:
        """
        Extract content for a specific section from a response.

        Args:
            content: The full response content
            section_name: The section to extract

        Returns:
            The section content or None if not found
        """
        sections = self._parse_sections_from_response(content, [section_name])
        return sections.get(section_name)

    def _group_critiques_by_section(
        self,
        critiques: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group critiques by their target section.

        Args:
            critiques: List of critique dictionaries

        Returns:
            Dictionary mapping section names to lists of critiques
        """
        grouped = {}
        for critique in critiques:
            section = critique.get("target_section", "Unknown")
            if section not in grouped:
                grouped[section] = []
            grouped[section].append(critique)
        return grouped

    def _group_and_normalize_critiques(
        self,
        critiques: List[Dict[str, Any]],
        available_sections: List[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group critiques by section with normalization to available section names.

        Handles cases where critique target_section values are descriptive text
        rather than exact section names.

        Args:
            critiques: List of critique dictionaries
            available_sections: List of actual section names in the document

        Returns:
            Dictionary mapping normalized section names to lists of critiques
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for critique in critiques:
            raw_section = critique.get("target_section", "")

            # Try to match/normalize the section name
            matched_section = self._match_section_name(raw_section, available_sections)

            if matched_section not in available_sections:
                # Try finding section mentioned in the text
                matched_section = self._find_section_in_text(raw_section, available_sections)

            if not matched_section or matched_section not in available_sections:
                # Default to Main Content if available, otherwise first section
                matched_section = None
                for section in available_sections:
                    if "main" in section.lower() or "content" in section.lower():
                        matched_section = section
                        break
                if not matched_section and available_sections:
                    # Skip company name or title sections
                    for section in available_sections:
                        if section.lower() not in ["title", "header"] and not any(
                            word in section.lower() for word in ["llc", "inc", "corp", "company"]
                        ):
                            matched_section = section
                            break
                if not matched_section and available_sections:
                    matched_section = available_sections[0]

            if matched_section:
                if matched_section not in grouped:
                    grouped[matched_section] = []
                grouped[matched_section].append(critique)
                self.log_debug(f"Mapped critique section '{raw_section}' -> '{matched_section}'")

        return grouped

    def _format_sections_as_content(self, sections: Dict[str, str]) -> str:
        """
        Format sections dictionary as a single content string.

        Args:
            sections: Dictionary of section name to content

        Returns:
            Formatted content string
        """
        parts = []
        for name, content in sections.items():
            parts.append(f"## {name}")
            parts.append("")
            parts.append(content)
            parts.append("")
        return "\n".join(parts)

    def _get_default_sections(self, document_type: str) -> List[str]:
        """
        Get default sections for a document type without a template.

        Args:
            document_type: The document type

        Returns:
            List of default section names
        """
        # Import here to avoid circular imports
        from models.document_types import DOCUMENT_TEMPLATES, DocumentType

        # Try to get from the models template
        try:
            doc_type_enum = DocumentType(document_type)
            return DOCUMENT_TEMPLATES.get(doc_type_enum, [
                "Executive Summary",
                "Main Content",
                "Recommendations",
            ])
        except ValueError:
            return [
                "Executive Summary",
                "Main Content",
                "Recommendations",
            ]
