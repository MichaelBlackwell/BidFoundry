"""
Document Types Model

Defines the document types that the adversarial swarm can generate,
along with their section structures and metadata schemas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json
import uuid


class DocumentType(str, Enum):
    """Types of strategy documents the swarm can generate."""

    CAPABILITY_STATEMENT = "Capability Statement"
    COMPETITIVE_ANALYSIS = "Competitive Analysis"
    SWOT_ANALYSIS = "SWOT Analysis"
    BD_PIPELINE = "BD Pipeline"
    PROPOSAL_STRATEGY = "Proposal Strategy"
    GO_TO_MARKET = "Go-to-Market Strategy"
    TEAMING_STRATEGY = "Teaming Strategy"

    # Additional document types
    CAPTURE_PLAN = "Capture Plan"
    WIN_THEME_DOCUMENT = "Win Theme Document"
    EXECUTIVE_SUMMARY = "Executive Summary"
    COMPLIANCE_MATRIX = "Compliance Matrix"
    RISK_REGISTER = "Risk Register"


class DocumentStatus(str, Enum):
    """Document lifecycle status."""

    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    BLUE_TEAM_COMPLETE = "Blue Team Complete"
    RED_TEAM_REVIEW = "Red Team Review"
    REVISION = "Revision"
    FINAL = "Final"
    APPROVED = "Approved"


class SectionStatus(str, Enum):
    """Individual section status within a document."""

    NOT_STARTED = "Not Started"
    DRAFTING = "Drafting"
    DRAFTED = "Drafted"
    UNDER_CRITIQUE = "Under Critique"
    REVISING = "Revising"
    COMPLETE = "Complete"
    FLAGGED = "Flagged"  # Requires human review


@dataclass
class DocumentSection:
    """
    A section within a strategy document.

    Sections are the unit of work for agents - they draft, critique,
    and revise at the section level.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    order: int = 0
    content: str = ""
    status: SectionStatus = SectionStatus.NOT_STARTED

    # Metadata
    word_count: int = 0
    last_modified: Optional[datetime] = None
    modified_by: Optional[str] = None  # Agent role that last modified

    # Version tracking
    version: int = 1
    previous_versions: List[str] = field(default_factory=list)  # Content snapshots

    # Quality tracking
    critique_count: int = 0
    unresolved_critiques: int = 0
    confidence_score: Optional[float] = None

    def update_content(self, new_content: str, modified_by: str) -> None:
        """Update section content and track changes."""
        if self.content:
            self.previous_versions.append(self.content)
        self.content = new_content
        self.word_count = len(new_content.split())
        self.last_modified = datetime.utcnow()
        self.modified_by = modified_by
        self.version += 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "content": self.content,
            "status": self.status.value,
            "word_count": self.word_count,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "modified_by": self.modified_by,
            "version": self.version,
            "previous_versions": self.previous_versions,
            "critique_count": self.critique_count,
            "unresolved_critiques": self.unresolved_critiques,
            "confidence_score": self.confidence_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentSection":
        section = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            order=data.get("order", 0),
            content=data.get("content", ""),
            status=SectionStatus(data.get("status", "Not Started")),
            word_count=data.get("word_count", 0),
            last_modified=datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None,
            modified_by=data.get("modified_by"),
            version=data.get("version", 1),
            previous_versions=data.get("previous_versions", []),
            critique_count=data.get("critique_count", 0),
            unresolved_critiques=data.get("unresolved_critiques", 0),
            confidence_score=data.get("confidence_score"),
        )
        return section

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "DocumentSection":
        return cls.from_dict(json.loads(json_str))


@dataclass
class DocumentMetadata:
    """
    Metadata for a generated document.

    Tracks authorship, version history, and quality metrics.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_type: DocumentType = DocumentType.CAPABILITY_STATEMENT
    title: str = ""
    status: DocumentStatus = DocumentStatus.DRAFT

    # Associations
    company_profile_id: Optional[str] = None
    opportunity_id: Optional[str] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Version tracking
    version: int = 1
    revision_count: int = 0

    # Quality metrics
    overall_confidence: Optional[float] = None
    human_review_required: bool = False
    review_notes: str = ""

    # Debate tracking
    total_critiques: int = 0
    resolved_critiques: int = 0
    accepted_critiques: int = 0
    rebutted_critiques: int = 0
    debate_rounds: int = 0

    # Sections
    sections: List[DocumentSection] = field(default_factory=list)

    # Custom fields for specific document types
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if all sections are complete."""
        return all(s.status == SectionStatus.COMPLETE for s in self.sections)

    @property
    def completion_percentage(self) -> float:
        """Calculate document completion percentage."""
        if not self.sections:
            return 0.0
        complete = sum(1 for s in self.sections if s.status == SectionStatus.COMPLETE)
        return (complete / len(self.sections)) * 100

    @property
    def total_word_count(self) -> int:
        """Get total word count across all sections."""
        return sum(s.word_count for s in self.sections)

    def get_section(self, section_name: str) -> Optional[DocumentSection]:
        """Get a section by name."""
        for section in self.sections:
            if section.name == section_name:
                return section
        return None

    def get_section_by_id(self, section_id: str) -> Optional[DocumentSection]:
        """Get a section by ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def add_section(self, name: str, order: Optional[int] = None) -> DocumentSection:
        """Add a new section to the document."""
        if order is None:
            order = len(self.sections)
        section = DocumentSection(name=name, order=order)
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.order)
        return section

    def update_status(self, new_status: DocumentStatus) -> None:
        """Update document status with timestamp."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_status == DocumentStatus.FINAL:
            self.completed_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_type": self.document_type.value,
            "title": self.title,
            "status": self.status.value,
            "company_profile_id": self.company_profile_id,
            "opportunity_id": self.opportunity_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "version": self.version,
            "revision_count": self.revision_count,
            "overall_confidence": self.overall_confidence,
            "human_review_required": self.human_review_required,
            "review_notes": self.review_notes,
            "total_critiques": self.total_critiques,
            "resolved_critiques": self.resolved_critiques,
            "accepted_critiques": self.accepted_critiques,
            "rebutted_critiques": self.rebutted_critiques,
            "debate_rounds": self.debate_rounds,
            "sections": [s.to_dict() for s in self.sections],
            "custom_fields": self.custom_fields,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentMetadata":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            document_type=DocumentType(data.get("document_type", "Capability Statement")),
            title=data.get("title", ""),
            status=DocumentStatus(data.get("status", "Draft")),
            company_profile_id=data.get("company_profile_id"),
            opportunity_id=data.get("opportunity_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            version=data.get("version", 1),
            revision_count=data.get("revision_count", 0),
            overall_confidence=data.get("overall_confidence"),
            human_review_required=data.get("human_review_required", False),
            review_notes=data.get("review_notes", ""),
            total_critiques=data.get("total_critiques", 0),
            resolved_critiques=data.get("resolved_critiques", 0),
            accepted_critiques=data.get("accepted_critiques", 0),
            rebutted_critiques=data.get("rebutted_critiques", 0),
            debate_rounds=data.get("debate_rounds", 0),
            sections=[DocumentSection.from_dict(s) for s in data.get("sections", [])],
            custom_fields=data.get("custom_fields", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "DocumentMetadata":
        return cls.from_dict(json.loads(json_str))


# Document type templates - defines the standard sections for each document type
DOCUMENT_TEMPLATES: Dict[DocumentType, List[str]] = {
    DocumentType.CAPABILITY_STATEMENT: [
        "Company Overview",
        "Core Competencies",
        "Past Performance",
        "Differentiators",
        "Certifications & Clearances",
        "Contact Information",
    ],
    DocumentType.COMPETITIVE_ANALYSIS: [
        "Executive Summary",
        "Competitive Landscape Overview",
        "Competitor Profiles",
        "Comparative Analysis",
        "Our Competitive Position",
        "Recommended Strategy",
    ],
    DocumentType.SWOT_ANALYSIS: [
        "Executive Summary",
        "Strengths",
        "Weaknesses",
        "Opportunities",
        "Threats",
        "Strategic Implications",
        "Recommended Actions",
    ],
    DocumentType.BD_PIPELINE: [
        "Pipeline Overview",
        "Priority Opportunities",
        "Opportunity Details",
        "Resource Requirements",
        "Timeline & Milestones",
        "Risk Assessment",
    ],
    DocumentType.PROPOSAL_STRATEGY: [
        "Executive Summary",
        "Win Themes",
        "Discriminators",
        "Technical Approach Summary",
        "Management Approach Summary",
        "Pricing Strategy",
        "Risk Mitigation",
        "Compliance Checklist",
    ],
    DocumentType.GO_TO_MARKET: [
        "Market Overview",
        "Target Segments",
        "Value Proposition",
        "Competitive Positioning",
        "Channel Strategy",
        "Marketing Approach",
        "Sales Strategy",
        "Success Metrics",
    ],
    DocumentType.TEAMING_STRATEGY: [
        "Teaming Objectives",
        "Gap Analysis",
        "Partner Criteria",
        "Potential Partners",
        "Partnership Structures",
        "Negotiation Approach",
        "Risk Considerations",
    ],
    DocumentType.CAPTURE_PLAN: [
        "Opportunity Overview",
        "Customer Analysis",
        "Competitive Assessment",
        "Win Strategy",
        "Solution Overview",
        "Teaming Strategy",
        "Price-to-Win",
        "Capture Schedule",
        "Action Items",
    ],
    DocumentType.WIN_THEME_DOCUMENT: [
        "Win Theme Summary",
        "Theme 1: [Primary Theme]",
        "Theme 2: [Secondary Theme]",
        "Theme 3: [Tertiary Theme]",
        "Supporting Evidence",
        "Integration Strategy",
    ],
    DocumentType.EXECUTIVE_SUMMARY: [
        "Introduction",
        "Understanding of Requirements",
        "Proposed Solution",
        "Why Choose Us",
        "Summary",
    ],
    DocumentType.COMPLIANCE_MATRIX: [
        "Instructions",
        "Compliance Summary",
        "Technical Requirements",
        "Management Requirements",
        "Past Performance Requirements",
        "Administrative Requirements",
    ],
    DocumentType.RISK_REGISTER: [
        "Risk Overview",
        "Risk Categories",
        "Risk Details",
        "Mitigation Plans",
        "Contingency Plans",
        "Monitoring Approach",
    ],
}


def create_document_from_template(
    doc_type: DocumentType,
    title: str,
    company_profile_id: Optional[str] = None,
    opportunity_id: Optional[str] = None,
) -> DocumentMetadata:
    """
    Create a new document with sections based on the document type template.

    Args:
        doc_type: The type of document to create
        title: Document title
        company_profile_id: Associated company profile ID
        opportunity_id: Associated opportunity ID

    Returns:
        DocumentMetadata with pre-populated sections
    """
    doc = DocumentMetadata(
        document_type=doc_type,
        title=title,
        company_profile_id=company_profile_id,
        opportunity_id=opportunity_id,
    )

    template_sections = DOCUMENT_TEMPLATES.get(doc_type, [])
    for order, section_name in enumerate(template_sections):
        doc.add_section(name=section_name, order=order)

    return doc
