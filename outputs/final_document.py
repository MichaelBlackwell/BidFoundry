"""
Final Document Structure

Defines the structure and formatting for final synthesized documents
produced by the adversarial swarm.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any
import json


class DocumentFormat(str, Enum):
    """Supported output formats for final documents."""

    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    PDF = "pdf"  # Requires additional rendering


class DocumentStatus(str, Enum):
    """Status of the final document."""

    DRAFT = "Draft"
    REVIEW_REQUIRED = "Review Required"
    APPROVED = "Approved"
    FINAL = "Final"


@dataclass
class BlueTeamContribution:
    """
    A contribution from a blue team agent to the final document.

    Captures analysis outputs from Market Analyst, Compliance Navigator,
    Capture Strategist, and other blue team agents during defense rounds.
    """

    agent_role: str = ""
    agent_name: str = ""
    content: str = ""
    content_type: str = ""  # market_analysis, compliance, capture_strategy
    metadata: Dict[str, Any] = field(default_factory=dict)
    round_number: int = 0
    round_type: str = ""  # BlueBuild, BlueDefense
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "agent_role": self.agent_role,
            "agent_name": self.agent_name,
            "content": self.content,
            "content_type": self.content_type,
            "metadata": self.metadata,
            "round_number": self.round_number,
            "round_type": self.round_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BlueTeamContribution":
        contrib = cls(
            agent_role=data.get("agent_role", ""),
            agent_name=data.get("agent_name", ""),
            content=data.get("content", ""),
            content_type=data.get("content_type", ""),
            metadata=data.get("metadata", {}),
            round_number=data.get("round_number", 0),
            round_type=data.get("round_type", ""),
        )
        if data.get("created_at"):
            contrib.created_at = datetime.fromisoformat(data["created_at"])
        return contrib


@dataclass
class DocumentSection:
    """
    A section within the final document.
    """

    name: str = ""
    content: str = ""
    order: int = 0

    # Metadata
    word_count: int = 0
    confidence_score: float = 0.0

    # Revision tracking
    revision_count: int = 0
    last_revised_at: Optional[datetime] = None

    # Critique summary
    critiques_received: int = 0
    critiques_resolved: int = 0

    # Annotations
    annotations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.content and not self.word_count:
            self.word_count = len(self.content.split())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "content": self.content,
            "order": self.order,
            "word_count": self.word_count,
            "confidence_score": self.confidence_score,
            "revision_count": self.revision_count,
            "last_revised_at": self.last_revised_at.isoformat() if self.last_revised_at else None,
            "critiques_received": self.critiques_received,
            "critiques_resolved": self.critiques_resolved,
            "annotations": self.annotations,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentSection":
        section = cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            order=data.get("order", 0),
            word_count=data.get("word_count", 0),
            confidence_score=data.get("confidence_score", 0.0),
            revision_count=data.get("revision_count", 0),
            critiques_received=data.get("critiques_received", 0),
            critiques_resolved=data.get("critiques_resolved", 0),
            annotations=data.get("annotations", []),
            warnings=data.get("warnings", []),
        )
        if data.get("last_revised_at"):
            section.last_revised_at = datetime.fromisoformat(data["last_revised_at"])
        return section


@dataclass
class DocumentMetadata:
    """
    Metadata about the final document.
    """

    # Identification
    document_id: str = ""
    document_type: str = ""
    version: str = "1.0"

    # Company context
    company_name: str = ""
    company_id: str = ""

    # Opportunity context
    opportunity_title: str = ""
    opportunity_id: str = ""
    agency: str = ""

    # Generation info
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    generated_by: str = "Adversarial Swarm"

    # Quality metrics
    overall_confidence: float = 0.0
    resolution_rate: float = 0.0
    total_sections: int = 0
    total_word_count: int = 0

    # Process metrics
    debate_rounds: int = 0
    total_critiques: int = 0
    resolved_critiques: int = 0
    consensus_reached: bool = False

    # Status
    status: DocumentStatus = DocumentStatus.DRAFT
    requires_review: bool = False
    review_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "version": self.version,
            "company_name": self.company_name,
            "company_id": self.company_id,
            "opportunity_title": self.opportunity_title,
            "opportunity_id": self.opportunity_id,
            "agency": self.agency,
            "generated_at": self.generated_at.isoformat(),
            "generated_by": self.generated_by,
            "overall_confidence": self.overall_confidence,
            "resolution_rate": self.resolution_rate,
            "total_sections": self.total_sections,
            "total_word_count": self.total_word_count,
            "debate_rounds": self.debate_rounds,
            "total_critiques": self.total_critiques,
            "resolved_critiques": self.resolved_critiques,
            "consensus_reached": self.consensus_reached,
            "status": self.status.value,
            "requires_review": self.requires_review,
            "review_reasons": self.review_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentMetadata":
        return cls(
            document_id=data.get("document_id", ""),
            document_type=data.get("document_type", ""),
            version=data.get("version", "1.0"),
            company_name=data.get("company_name", ""),
            company_id=data.get("company_id", ""),
            opportunity_title=data.get("opportunity_title", ""),
            opportunity_id=data.get("opportunity_id", ""),
            agency=data.get("agency", ""),
            generated_at=datetime.fromisoformat(data["generated_at"]) if data.get("generated_at") else datetime.now(timezone.utc),
            generated_by=data.get("generated_by", "Adversarial Swarm"),
            overall_confidence=data.get("overall_confidence", 0.0),
            resolution_rate=data.get("resolution_rate", 0.0),
            total_sections=data.get("total_sections", 0),
            total_word_count=data.get("total_word_count", 0),
            debate_rounds=data.get("debate_rounds", 0),
            total_critiques=data.get("total_critiques", 0),
            resolved_critiques=data.get("resolved_critiques", 0),
            consensus_reached=data.get("consensus_reached", False),
            status=DocumentStatus(data.get("status", "Draft")),
            requires_review=data.get("requires_review", False),
            review_reasons=data.get("review_reasons", []),
        )


@dataclass
class FinalDocument:
    """
    The complete final document produced by the adversarial swarm.

    Contains all sections, metadata, and supporting information.
    """

    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    sections: List[DocumentSection] = field(default_factory=list)

    # Executive summary (generated separately)
    executive_summary: str = ""

    # Blue team contributions (from all agents during defense rounds)
    blue_team_contributions: List[BlueTeamContribution] = field(default_factory=list)

    # Appendices
    appendices: List[Dict[str, Any]] = field(default_factory=list)

    # Supporting documents
    attachments: List[str] = field(default_factory=list)

    @property
    def total_word_count(self) -> int:
        """Calculate total word count across all sections."""
        return sum(s.word_count for s in self.sections)

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence across sections."""
        if not self.sections:
            return 0.0
        return sum(s.confidence_score for s in self.sections) / len(self.sections)

    @property
    def sections_by_name(self) -> Dict[str, DocumentSection]:
        """Get sections indexed by name."""
        return {s.name: s for s in self.sections}

    def get_section(self, name: str) -> Optional[DocumentSection]:
        """Get a section by name."""
        return self.sections_by_name.get(name)

    def add_section(self, section: DocumentSection) -> None:
        """Add a section to the document."""
        if not section.order:
            section.order = len(self.sections)
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.order)
        self.metadata.total_sections = len(self.sections)
        self.metadata.total_word_count = self.total_word_count

    def remove_section(self, name: str) -> bool:
        """Remove a section by name."""
        for i, section in enumerate(self.sections):
            if section.name == name:
                self.sections.pop(i)
                self.metadata.total_sections = len(self.sections)
                self.metadata.total_word_count = self.total_word_count
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata.to_dict(),
            "executive_summary": self.executive_summary,
            "sections": [s.to_dict() for s in self.sections],
            "blue_team_contributions": [c.to_dict() for c in self.blue_team_contributions],
            "appendices": self.appendices,
            "attachments": self.attachments,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FinalDocument":
        doc = cls()
        doc.metadata = DocumentMetadata.from_dict(data.get("metadata", {}))
        doc.executive_summary = data.get("executive_summary", "")
        doc.sections = [DocumentSection.from_dict(s) for s in data.get("sections", [])]
        doc.blue_team_contributions = [
            BlueTeamContribution.from_dict(c) for c in data.get("blue_team_contributions", [])
        ]
        doc.appendices = data.get("appendices", [])
        doc.attachments = data.get("attachments", [])
        return doc

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "FinalDocument":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_markdown(self) -> str:
        """Export document as Markdown."""
        lines = []

        # Title and metadata
        lines.append(f"# {self.metadata.document_type}")
        lines.append("")
        lines.append(f"**Company:** {self.metadata.company_name}")
        if self.metadata.opportunity_title:
            lines.append(f"**Opportunity:** {self.metadata.opportunity_title}")
        if self.metadata.agency:
            lines.append(f"**Agency:** {self.metadata.agency}")
        lines.append(f"**Generated:** {self.metadata.generated_at.strftime('%Y-%m-%d')}")
        lines.append(f"**Confidence:** {self.metadata.overall_confidence:.0%}")
        lines.append("")

        # Status banner
        if self.metadata.requires_review:
            lines.append("> **REVIEW REQUIRED**")
            for reason in self.metadata.review_reasons:
                lines.append(f"> - {reason}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Executive Summary
        if self.executive_summary:
            lines.append("## Executive Summary")
            lines.append("")
            lines.append(self.executive_summary)
            lines.append("")
            lines.append("---")
            lines.append("")

        # Sections
        for section in self.sections:
            lines.append(f"## {section.name}")
            lines.append("")

            # Section metadata (as comment)
            if section.warnings:
                for warning in section.warnings:
                    lines.append(f"> **Note:** {warning}")
                lines.append("")

            lines.append(section.content)
            lines.append("")

        # Blue Team Contributions
        if self.blue_team_contributions:
            lines.append("---")
            lines.append("")
            lines.append("## Blue Team Analysis")
            lines.append("")
            lines.append("*Analysis contributions from all blue team agents during the adversarial process.*")
            lines.append("")

            for contrib in self.blue_team_contributions:
                lines.append(f"### {contrib.agent_name} ({contrib.agent_role})")
                lines.append("")
                lines.append(f"*Round {contrib.round_number} - {contrib.round_type}*")
                lines.append("")
                lines.append(contrib.content)
                lines.append("")

        # Appendices
        if self.appendices:
            lines.append("---")
            lines.append("")
            lines.append("## Appendices")
            lines.append("")
            for i, appendix in enumerate(self.appendices, 1):
                title = appendix.get("title", f"Appendix {i}")
                content = appendix.get("content", "")
                lines.append(f"### {title}")
                lines.append("")
                lines.append(content)
                lines.append("")

        return "\n".join(lines)

    def to_html(self) -> str:
        """Export document as HTML."""
        lines = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{self.metadata.document_type}</title>",
            "<style>",
            "body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; line-height: 1.6; }",
            "h1 { color: #1a365d; border-bottom: 3px solid #2b6cb0; padding-bottom: 10px; }",
            "h2 { color: #2d3748; margin-top: 40px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }",
            ".metadata { background: #f7fafc; padding: 20px; border-radius: 8px; margin-bottom: 30px; }",
            ".metadata p { margin: 5px 0; color: #4a5568; }",
            ".review-banner { background: #fed7d7; border: 1px solid #fc8181; padding: 15px; border-radius: 8px; margin-bottom: 20px; }",
            ".review-banner h3 { color: #c53030; margin: 0 0 10px 0; }",
            ".section { margin-bottom: 40px; }",
            ".section-content { color: #2d3748; }",
            ".warning { background: #fefcbf; border-left: 4px solid #d69e2e; padding: 10px 15px; margin-bottom: 15px; }",
            ".executive-summary { background: #ebf8ff; padding: 20px; border-radius: 8px; margin-bottom: 30px; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        # Title
        lines.append(f"<h1>{self.metadata.document_type}</h1>")

        # Metadata block
        lines.append("<div class='metadata'>")
        lines.append(f"<p><strong>Company:</strong> {self.metadata.company_name}</p>")
        if self.metadata.opportunity_title:
            lines.append(f"<p><strong>Opportunity:</strong> {self.metadata.opportunity_title}</p>")
        if self.metadata.agency:
            lines.append(f"<p><strong>Agency:</strong> {self.metadata.agency}</p>")
        lines.append(f"<p><strong>Generated:</strong> {self.metadata.generated_at.strftime('%Y-%m-%d')}</p>")
        lines.append(f"<p><strong>Confidence:</strong> {self.metadata.overall_confidence:.0%}</p>")
        lines.append("</div>")

        # Review banner
        if self.metadata.requires_review:
            lines.append("<div class='review-banner'>")
            lines.append("<h3>Review Required</h3>")
            lines.append("<ul>")
            for reason in self.metadata.review_reasons:
                lines.append(f"<li>{reason}</li>")
            lines.append("</ul>")
            lines.append("</div>")

        # Executive Summary
        if self.executive_summary:
            lines.append("<div class='executive-summary'>")
            lines.append("<h2>Executive Summary</h2>")
            lines.append(f"<p>{self._text_to_html(self.executive_summary)}</p>")
            lines.append("</div>")

        # Sections
        for section in self.sections:
            lines.append("<div class='section'>")
            lines.append(f"<h2>{section.name}</h2>")

            if section.warnings:
                for warning in section.warnings:
                    lines.append(f"<div class='warning'>{warning}</div>")

            lines.append(f"<div class='section-content'>{self._text_to_html(section.content)}</div>")
            lines.append("</div>")

        # Blue Team Contributions
        if self.blue_team_contributions:
            lines.append("<div class='section'>")
            lines.append("<h2>Blue Team Analysis</h2>")
            lines.append("<p><em>Analysis contributions from all blue team agents during the adversarial process.</em></p>")

            for contrib in self.blue_team_contributions:
                lines.append("<div style='margin-bottom: 30px; padding: 15px; background: #f0fff4; border-radius: 8px;'>")
                lines.append(f"<h3 style='color: #276749;'>{contrib.agent_name} ({contrib.agent_role})</h3>")
                lines.append(f"<p><em>Round {contrib.round_number} - {contrib.round_type}</em></p>")
                lines.append(f"<div class='section-content'>{self._text_to_html(contrib.content)}</div>")
                lines.append("</div>")

            lines.append("</div>")

        lines.extend([
            "</body>",
            "</html>",
        ])

        return "\n".join(lines)

    def _text_to_html(self, text: str) -> str:
        """Convert plain text to HTML paragraphs."""
        paragraphs = text.split("\n\n")
        html_paragraphs = []
        for p in paragraphs:
            if p.strip():
                # Convert line breaks within paragraphs
                p = p.replace("\n", "<br>")
                html_paragraphs.append(f"<p>{p}</p>")
        return "\n".join(html_paragraphs)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the document."""
        return {
            "document_id": self.metadata.document_id,
            "document_type": self.metadata.document_type,
            "status": self.metadata.status.value,
            "sections": len(self.sections),
            "word_count": self.total_word_count,
            "confidence": self.metadata.overall_confidence,
            "requires_review": self.metadata.requires_review,
            "generated_at": self.metadata.generated_at.isoformat(),
        }
