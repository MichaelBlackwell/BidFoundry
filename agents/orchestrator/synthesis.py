"""
Document Synthesis

Compiles the final document from all debate rounds, incorporating
resolved critiques and producing a polished output.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set
import logging
import json

from agents.base import SwarmContext


logger = logging.getLogger(__name__)


@dataclass
class SynthesisConfig:
    """
    Configuration for document synthesis.
    """

    # Output format
    output_format: str = "markdown"  # markdown, json, html

    # Content options
    include_revision_notes: bool = False
    include_confidence_annotations: bool = True
    include_section_metadata: bool = True

    # Quality thresholds
    min_section_word_count: int = 50
    max_section_word_count: int = 5000

    def to_dict(self) -> dict:
        return {
            "output_format": self.output_format,
            "include_revision_notes": self.include_revision_notes,
            "include_confidence_annotations": self.include_confidence_annotations,
            "include_section_metadata": self.include_section_metadata,
            "min_section_word_count": self.min_section_word_count,
            "max_section_word_count": self.max_section_word_count,
        }


@dataclass
class SectionMetadata:
    """
    Metadata about a synthesized section.
    """

    section_name: str = ""
    word_count: int = 0
    revision_count: int = 0

    # Critique summary
    total_critiques: int = 0
    resolved_critiques: int = 0
    accepted_changes: int = 0
    rebutted_critiques: int = 0

    # Confidence
    confidence_score: float = 0.0

    # History
    created_at: Optional[datetime] = None
    last_revised_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "section_name": self.section_name,
            "word_count": self.word_count,
            "revision_count": self.revision_count,
            "total_critiques": self.total_critiques,
            "resolved_critiques": self.resolved_critiques,
            "accepted_changes": self.accepted_changes,
            "rebutted_critiques": self.rebutted_critiques,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_revised_at": self.last_revised_at.isoformat() if self.last_revised_at else None,
        }


class DocumentSynthesizer:
    """
    Synthesizes final documents from debate rounds.

    Combines section drafts with critique resolutions to produce
    a polished final document.
    """

    def __init__(self, config: Optional[SynthesisConfig] = None):
        """
        Initialize the synthesizer.

        Args:
            config: Optional synthesis configuration
        """
        self._config = config or SynthesisConfig()
        self._logger = logging.getLogger("DocumentSynthesizer")

    @property
    def config(self) -> SynthesisConfig:
        """Get the current configuration."""
        return self._config

    async def synthesize(
        self,
        sections: Dict[str, str],
        critiques: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        context: SwarmContext,
        blue_team_contributions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize the final document.

        Args:
            sections: Dictionary of section names to content
            critiques: List of all critiques
            responses: List of all responses
            context: The swarm context
            blue_team_contributions: Optional list of blue team agent contributions

        Returns:
            Final document as a dictionary
        """
        self._logger.info(f"Synthesizing document with {len(sections)} sections")
        blue_team_contributions = blue_team_contributions or []

        # Build response lookup
        response_map = {
            r.get("critique_id"): r
            for r in responses
            if r.get("critique_id")
        }

        # Process each section
        section_metadata: Dict[str, SectionMetadata] = {}
        final_sections: Dict[str, str] = {}

        for section_name, content in sections.items():
            # Get critiques for this section
            section_critiques = [
                c for c in critiques
                if c.get("target_section") == section_name
            ]

            # Calculate section metadata
            metadata = self._calculate_section_metadata(
                section_name=section_name,
                content=content,
                critiques=section_critiques,
                response_map=response_map,
            )
            section_metadata[section_name] = metadata

            # Process section content
            final_content = self._process_section(
                content=content,
                critiques=section_critiques,
                response_map=response_map,
            )
            final_sections[section_name] = final_content

        # Build final document structure
        document = self._build_document_structure(
            sections=final_sections,
            metadata=section_metadata,
            context=context,
            critiques=critiques,
            responses=responses,
            blue_team_contributions=blue_team_contributions,
        )

        return document

    def _calculate_section_metadata(
        self,
        section_name: str,
        content: str,
        critiques: List[Dict[str, Any]],
        response_map: Dict[str, Dict[str, Any]],
    ) -> SectionMetadata:
        """Calculate metadata for a section."""
        metadata = SectionMetadata(
            section_name=section_name,
            word_count=len(content.split()),
            total_critiques=len(critiques),
            created_at=datetime.now(timezone.utc),
        )

        # Count resolutions
        for critique in critiques:
            critique_id = critique.get("id")
            response = response_map.get(critique_id)

            if response:
                metadata.resolved_critiques += 1
                disposition = response.get("disposition", "")

                if disposition in ("Accept", "Partial Accept"):
                    metadata.accepted_changes += 1
                    metadata.revision_count += 1
                elif disposition == "Rebut":
                    metadata.rebutted_critiques += 1

        # Calculate confidence (simplified)
        if metadata.total_critiques > 0:
            resolution_rate = metadata.resolved_critiques / metadata.total_critiques
            metadata.confidence_score = 0.7 + (0.3 * resolution_rate)
        else:
            metadata.confidence_score = 0.85

        return metadata

    def _process_section(
        self,
        content: str,
        critiques: List[Dict[str, Any]],
        response_map: Dict[str, Dict[str, Any]],
    ) -> str:
        """
        Process a section's content.

        For now, this returns the content as-is since revisions
        should have been applied during the defense phase.

        In a more advanced implementation, this could apply
        any final formatting or cleanup.
        """
        # Content should already be revised from defense phase
        processed = content.strip()

        # Add confidence annotations if configured
        if self._config.include_confidence_annotations:
            # Add subtle markers for sections with unresolved issues
            unresolved = [
                c for c in critiques
                if c.get("id") not in response_map
            ]

            if unresolved:
                critical = [c for c in unresolved if c.get("severity") == "critical"]
                major = [c for c in unresolved if c.get("severity") == "major"]

                if critical:
                    processed = f"<!-- ATTENTION: {len(critical)} unresolved critical issue(s) -->\n\n{processed}"
                elif major:
                    processed = f"<!-- NOTE: {len(major)} unresolved major issue(s) -->\n\n{processed}"

        return processed

    def _build_document_structure(
        self,
        sections: Dict[str, str],
        metadata: Dict[str, SectionMetadata],
        context: SwarmContext,
        critiques: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        blue_team_contributions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build the final document structure."""
        # Determine section ordering (common GovCon document structure)
        section_order = self._determine_section_order(sections.keys())

        # Calculate document-level stats
        total_critiques = len(critiques)
        resolved_critiques = len([
            r for r in responses
            if r.get("disposition") in ("Accept", "Partial Accept", "Rebut", "Acknowledge")
        ])
        resolution_rate = (
            resolved_critiques / total_critiques * 100
            if total_critiques > 0 else 100.0
        )

        # Build ordered sections
        ordered_sections = []
        for section_name in section_order:
            if section_name in sections:
                section_meta = metadata.get(section_name, SectionMetadata(section_name=section_name))
                ordered_sections.append({
                    "name": section_name,
                    "content": sections[section_name],
                    "metadata": section_meta.to_dict() if self._config.include_section_metadata else None,
                })

        # Add any sections not in the standard order
        for section_name in sections:
            if section_name not in section_order:
                section_meta = metadata.get(section_name, SectionMetadata(section_name=section_name))
                ordered_sections.append({
                    "name": section_name,
                    "content": sections[section_name],
                    "metadata": section_meta.to_dict() if self._config.include_section_metadata else None,
                })

        document = {
            "id": context.request_id,
            "type": context.document_type,
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),

            # Document content
            "sections": ordered_sections,

            # Blue team contributions from all agents
            "blue_team_contributions": blue_team_contributions or [],

            # Document-level metadata
            "metadata": {
                "total_sections": len(sections),
                "total_word_count": sum(m.word_count for m in metadata.values()),
                "debate_rounds": context.round_number,
                "total_critiques": total_critiques,
                "resolved_critiques": resolved_critiques,
                "resolution_rate": resolution_rate,
                "blue_team_contributions_count": len(blue_team_contributions or []),
            },

            # Company and opportunity context
            "context": {
                "company": context.company_profile.get("name") if context.company_profile else None,
                "opportunity": context.opportunity.get("title") if context.opportunity else None,
            },
        }

        # Add revision notes if configured
        if self._config.include_revision_notes:
            document["revision_notes"] = self._generate_revision_notes(
                critiques, responses, metadata
            )

        return document

    def _determine_section_order(self, section_names: Any) -> List[str]:
        """
        Determine the order of sections in the final document.

        Uses standard GovCon document ordering conventions.
        """
        # Standard section ordering for GovCon documents
        standard_order = [
            # Common to most documents
            "Executive Summary",
            "Company Overview",
            "Introduction",

            # Capability Statement
            "Core Competencies",
            "Core Capabilities",
            "Differentiators",
            "Past Performance",
            "Certifications",

            # SWOT Analysis
            "Strengths",
            "Weaknesses",
            "Opportunities",
            "Threats",
            "SWOT Summary",

            # Competitive Analysis
            "Market Overview",
            "Market Analysis",
            "Competitive Landscape",
            "Competitor Analysis",
            "Competitive Position",

            # Proposal Strategy
            "Technical Approach",
            "Management Approach",
            "Win Themes",
            "Win Strategy",
            "Discriminators",
            "Ghost Team Analysis",
            "Price Strategy",
            "Risk Analysis",
            "Risk Mitigation",

            # Go-to-Market
            "Target Market",
            "Target Agencies",
            "Value Proposition",
            "Marketing Strategy",
            "Capture Strategy",
            "Partnership Strategy",

            # Teaming Strategy
            "Teaming Approach",
            "Partner Criteria",
            "Potential Partners",
            "Team Structure",

            # BD Pipeline
            "Pipeline Overview",
            "Active Opportunities",
            "Forecast",
            "Resource Requirements",

            # Common endings
            "Recommendations",
            "Next Steps",
            "Conclusion",
            "Appendices",
        ]

        # Return sections in order, maintaining any that aren't in standard order
        ordered = []
        remaining = set(section_names)

        for standard_section in standard_order:
            if standard_section in remaining:
                ordered.append(standard_section)
                remaining.remove(standard_section)

        # Append any non-standard sections at the end
        ordered.extend(sorted(remaining))

        return ordered

    def _generate_revision_notes(
        self,
        critiques: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        metadata: Dict[str, SectionMetadata],
    ) -> List[Dict[str, Any]]:
        """Generate revision notes documenting changes made."""
        notes = []

        # Build response lookup
        response_map = {
            r.get("critique_id"): r
            for r in responses
        }

        # Group by section
        sections_with_changes: Set[str] = set()

        for critique in critiques:
            section = critique.get("target_section", "General")
            critique_id = critique.get("id")
            response = response_map.get(critique_id)

            if response and response.get("disposition") in ("Accept", "Partial Accept"):
                sections_with_changes.add(section)
                notes.append({
                    "section": section,
                    "type": "accepted_critique",
                    "severity": critique.get("severity"),
                    "issue": critique.get("title"),
                    "resolution": response.get("summary") or response.get("action"),
                })

        # Add section-level summaries
        for section_name, meta in metadata.items():
            if meta.revision_count > 0:
                notes.append({
                    "section": section_name,
                    "type": "section_summary",
                    "revisions": meta.revision_count,
                    "critiques_addressed": meta.resolved_critiques,
                    "final_confidence": meta.confidence_score,
                })

        return notes

    def format_as_markdown(self, document: Dict[str, Any]) -> str:
        """
        Format the synthesized document as Markdown.

        Args:
            document: The synthesized document dictionary

        Returns:
            Markdown-formatted string
        """
        lines = []

        # Title
        doc_type = document.get("type", "Document")
        lines.append(f"# {doc_type}")
        lines.append("")

        # Metadata block
        metadata = document.get("metadata", {})
        lines.append(f"*Generated: {document.get('generated_at', 'Unknown')}*")
        lines.append(f"*Resolution Rate: {metadata.get('resolution_rate', 0):.1f}%*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Sections
        for section in document.get("sections", []):
            section_name = section.get("name", "Untitled")
            content = section.get("content", "")

            lines.append(f"## {section_name}")
            lines.append("")
            lines.append(content)
            lines.append("")

        # Revision notes (if present)
        revision_notes = document.get("revision_notes", [])
        if revision_notes:
            lines.append("---")
            lines.append("")
            lines.append("## Revision History")
            lines.append("")

            for note in revision_notes:
                if note.get("type") == "accepted_critique":
                    lines.append(
                        f"- **{note.get('section')}**: {note.get('issue')} "
                        f"({note.get('severity')}) - {note.get('resolution')}"
                    )

            lines.append("")

        return "\n".join(lines)

    def format_as_json(self, document: Dict[str, Any]) -> str:
        """
        Format the synthesized document as JSON.

        Args:
            document: The synthesized document dictionary

        Returns:
            JSON-formatted string
        """
        return json.dumps(document, indent=2, default=str)

    def format_as_html(self, document: Dict[str, Any]) -> str:
        """
        Format the synthesized document as HTML.

        Args:
            document: The synthesized document dictionary

        Returns:
            HTML-formatted string
        """
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{document.get('type', 'Document')}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 1px solid #ddd; padding-bottom: 5px; }",
            ".metadata { color: #888; font-size: 0.9em; margin-bottom: 20px; }",
            ".section { margin-bottom: 30px; }",
            ".content { line-height: 1.6; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        # Title
        doc_type = document.get("type", "Document")
        lines.append(f"<h1>{doc_type}</h1>")

        # Metadata
        metadata = document.get("metadata", {})
        lines.append("<div class='metadata'>")
        lines.append(f"<p>Generated: {document.get('generated_at', 'Unknown')}</p>")
        lines.append(f"<p>Resolution Rate: {metadata.get('resolution_rate', 0):.1f}%</p>")
        lines.append("</div>")

        # Sections
        for section in document.get("sections", []):
            section_name = section.get("name", "Untitled")
            content = section.get("content", "")

            lines.append("<div class='section'>")
            lines.append(f"<h2>{section_name}</h2>")
            lines.append(f"<div class='content'>{self._markdown_to_html(content)}</div>")
            lines.append("</div>")

        lines.extend([
            "</body>",
            "</html>",
        ])

        return "\n".join(lines)

    def _markdown_to_html(self, markdown: str) -> str:
        """
        Simple Markdown to HTML conversion.

        For production use, consider using a proper Markdown library.
        """
        html = markdown

        # Paragraphs
        paragraphs = html.split("\n\n")
        html = "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

        # Bold
        import re
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # Italic
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

        # Lists (simple)
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        return html
