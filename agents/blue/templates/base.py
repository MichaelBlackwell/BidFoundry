"""
Base Document Template

Abstract base class for document structure templates.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.document_types import DocumentType


@dataclass
class SectionSpec:
    """Specification for a document section."""

    name: str
    order: int
    description: str
    required: bool = True
    min_words: int = 100
    max_words: int = 1000
    dependencies: List[str] = field(default_factory=list)  # Sections that should be drafted first
    guidance: str = ""
    example_content: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "order": self.order,
            "description": self.description,
            "required": self.required,
            "min_words": self.min_words,
            "max_words": self.max_words,
            "dependencies": self.dependencies,
            "guidance": self.guidance,
            "example_content": self.example_content,
        }


class DocumentTemplate(ABC):
    """
    Abstract base class for document structure templates.

    Each template defines:
    - The sections required for the document type
    - Section ordering and dependencies
    - Section-specific guidance for the LLM
    - Validation rules for generated content
    """

    @property
    @abstractmethod
    def document_type(self) -> str:
        """Get the document type this template is for."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a description of the document type."""
        pass

    @property
    @abstractmethod
    def sections(self) -> List[SectionSpec]:
        """Get the section specifications for this document type."""
        pass

    @property
    def requires_opportunity(self) -> bool:
        """Check if this document type requires opportunity context."""
        return False

    @property
    def section_names(self) -> List[str]:
        """Get ordered list of section names."""
        return [s.name for s in sorted(self.sections, key=lambda x: x.order)]

    @property
    def required_sections(self) -> List[str]:
        """Get list of required section names."""
        return [s.name for s in self.sections if s.required]

    def get_section_spec(self, section_name: str) -> Optional[SectionSpec]:
        """Get the specification for a specific section."""
        for section in self.sections:
            if section.name == section_name:
                return section
        return None

    def get_section_order(self, section_name: str) -> int:
        """Get the order index for a section."""
        spec = self.get_section_spec(section_name)
        return spec.order if spec else -1

    def get_section_guidance(self, section_name: str) -> str:
        """Get the drafting guidance for a section."""
        spec = self.get_section_spec(section_name)
        return spec.guidance if spec else ""

    def get_section_dependencies(self, section_name: str) -> List[str]:
        """Get sections that should be drafted before this one."""
        spec = self.get_section_spec(section_name)
        return spec.dependencies if spec else []

    def validate_section_content(
        self,
        section_name: str,
        content: str,
    ) -> List[str]:
        """
        Validate section content against template requirements.

        Args:
            section_name: Name of the section
            content: Content to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        spec = self.get_section_spec(section_name)

        if not spec:
            errors.append(f"Unknown section: {section_name}")
            return errors

        word_count = len(content.split())

        if word_count < spec.min_words:
            errors.append(
                f"Section '{section_name}' is too short: {word_count} words "
                f"(minimum: {spec.min_words})"
            )

        if word_count > spec.max_words:
            errors.append(
                f"Section '{section_name}' is too long: {word_count} words "
                f"(maximum: {spec.max_words})"
            )

        return errors

    def validate_document(
        self,
        sections: Dict[str, str],
    ) -> List[str]:
        """
        Validate a complete document against template requirements.

        Args:
            sections: Dictionary of section name to content

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for required sections
        for section_name in self.required_sections:
            if section_name not in sections:
                errors.append(f"Missing required section: {section_name}")
            elif not sections[section_name].strip():
                errors.append(f"Required section is empty: {section_name}")

        # Validate each provided section
        for section_name, content in sections.items():
            section_errors = self.validate_section_content(section_name, content)
            errors.extend(section_errors)

        return errors

    def get_drafting_order(self) -> List[str]:
        """
        Get the recommended order for drafting sections.

        Respects dependencies so that dependent sections are drafted
        after their dependencies.

        Returns:
            Ordered list of section names
        """
        # Simple topological sort based on dependencies
        ordered = []
        remaining = {s.name: s for s in self.sections}

        while remaining:
            # Find sections with all dependencies satisfied
            ready = [
                name for name, spec in remaining.items()
                if all(dep in ordered for dep in spec.dependencies)
            ]

            if not ready:
                # No progress - circular dependency or error
                # Fall back to order-based sorting
                ready = sorted(remaining.keys(), key=lambda n: remaining[n].order)

            # Add ready sections in order
            ready.sort(key=lambda n: remaining[n].order)
            for name in ready:
                ordered.append(name)
                del remaining[name]

        return ordered

    def to_dict(self) -> dict:
        """Serialize template to dictionary."""
        return {
            "document_type": self.document_type,
            "description": self.description,
            "requires_opportunity": self.requires_opportunity,
            "sections": [s.to_dict() for s in self.sections],
        }


# Template registry
_TEMPLATE_REGISTRY: Dict[str, type] = {}


def register_template(template_class: type) -> type:
    """Register a template class for a document type."""
    instance = template_class()
    _TEMPLATE_REGISTRY[instance.document_type] = template_class
    return template_class


def get_template_for_document_type(document_type: str) -> Optional[DocumentTemplate]:
    """
    Get the template for a document type.

    Args:
        document_type: The document type string

    Returns:
        Template instance or None if not found
    """
    template_class = _TEMPLATE_REGISTRY.get(document_type)
    if template_class:
        return template_class()
    return None
