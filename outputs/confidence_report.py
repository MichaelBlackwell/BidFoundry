"""
Confidence Report Structure

Defines the confidence report that provides section-by-section
confidence scores and identifies areas requiring human review.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any
import json

from models.confidence import (
    ConfidenceScore, SectionConfidence, ConfidenceLevel,
    ConfidenceThresholds, RiskFlag
)


class ReviewPriority(str, Enum):
    """Priority level for human review."""

    CRITICAL = "critical"  # Must review before use
    HIGH = "high"  # Should review soon
    MEDIUM = "medium"  # Review recommended
    LOW = "low"  # Optional review
    NONE = "none"  # No review needed


@dataclass
class ReviewItem:
    """
    An item requiring human review.
    """

    section: str = ""
    issue: str = ""
    priority: ReviewPriority = ReviewPriority.MEDIUM
    reason: str = ""

    # Related critique info
    critique_id: Optional[str] = None
    critique_severity: Optional[str] = None

    # Suggestions
    suggested_action: str = ""
    estimated_effort: str = ""  # e.g., "5 minutes", "30 minutes"

    def to_dict(self) -> dict:
        return {
            "section": self.section,
            "issue": self.issue,
            "priority": self.priority.value,
            "reason": self.reason,
            "critique_id": self.critique_id,
            "critique_severity": self.critique_severity,
            "suggested_action": self.suggested_action,
            "estimated_effort": self.estimated_effort,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReviewItem":
        return cls(
            section=data.get("section", ""),
            issue=data.get("issue", ""),
            priority=ReviewPriority(data.get("priority", "Medium")),
            reason=data.get("reason", ""),
            critique_id=data.get("critique_id"),
            critique_severity=data.get("critique_severity"),
            suggested_action=data.get("suggested_action", ""),
            estimated_effort=data.get("estimated_effort", ""),
        )


@dataclass
class SectionReport:
    """
    Confidence report for a single section.
    """

    section_name: str = ""
    confidence_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MODERATE

    # Content metrics
    word_count: int = 0
    revision_count: int = 0

    # Critique summary
    total_critiques: int = 0
    resolved_critiques: int = 0
    unresolved_critiques: int = 0
    critical_critiques: int = 0
    major_critiques: int = 0

    # Score adjustments
    adjustments: List[Dict[str, Any]] = field(default_factory=list)

    # Risk flags
    risk_flags: List[str] = field(default_factory=list)

    # Review items for this section
    review_items: List[ReviewItem] = field(default_factory=list)

    @property
    def requires_review(self) -> bool:
        return len(self.review_items) > 0 or self.unresolved_critiques > 0

    @property
    def resolution_rate(self) -> float:
        if self.total_critiques == 0:
            return 100.0
        return (self.resolved_critiques / self.total_critiques) * 100

    def to_dict(self) -> dict:
        return {
            "section_name": self.section_name,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level.value,
            "word_count": self.word_count,
            "revision_count": self.revision_count,
            "total_critiques": self.total_critiques,
            "resolved_critiques": self.resolved_critiques,
            "unresolved_critiques": self.unresolved_critiques,
            "critical_critiques": self.critical_critiques,
            "major_critiques": self.major_critiques,
            "resolution_rate": self.resolution_rate,
            "adjustments": self.adjustments,
            "risk_flags": self.risk_flags,
            "requires_review": self.requires_review,
            "review_items": [r.to_dict() for r in self.review_items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SectionReport":
        report = cls(
            section_name=data.get("section_name", ""),
            confidence_score=data.get("confidence_score", 0.0),
            confidence_level=ConfidenceLevel(data.get("confidence_level", "Moderate")),
            word_count=data.get("word_count", 0),
            revision_count=data.get("revision_count", 0),
            total_critiques=data.get("total_critiques", 0),
            resolved_critiques=data.get("resolved_critiques", 0),
            unresolved_critiques=data.get("unresolved_critiques", 0),
            critical_critiques=data.get("critical_critiques", 0),
            major_critiques=data.get("major_critiques", 0),
            adjustments=data.get("adjustments", []),
            risk_flags=data.get("risk_flags", []),
        )
        report.review_items = [
            ReviewItem.from_dict(r) for r in data.get("review_items", [])
        ]
        return report

    @classmethod
    def from_section_confidence(cls, conf: SectionConfidence) -> "SectionReport":
        """Create a SectionReport from a SectionConfidence object."""
        report = cls(
            section_name=conf.section_name,
            confidence_score=conf.adjusted_score,
            confidence_level=conf.level,
            word_count=conf.word_count,
            revision_count=conf.revision_count,
            total_critiques=conf.critique_count,
            unresolved_critiques=conf.unresolved_critiques,
            resolved_critiques=conf.critique_count - conf.unresolved_critiques,
            critical_critiques=conf.critical_critiques,
            major_critiques=conf.major_critiques,
            adjustments=conf.adjustments,
            risk_flags=[f.value for f in conf.risk_flags],
        )
        return report


@dataclass
class ConfidenceReport:
    """
    Comprehensive confidence report for the generated document.

    Provides section-by-section confidence analysis and identifies
    areas requiring human review.
    """

    # Identification
    document_id: str = ""
    document_type: str = ""

    # Generation info
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Overall scores
    overall_score: float = 0.0
    overall_level: ConfidenceLevel = ConfidenceLevel.MODERATE

    # Document metrics
    total_sections: int = 0
    total_word_count: int = 0

    # Debate metrics
    debate_rounds: int = 0
    total_critiques: int = 0
    resolved_critiques: int = 0
    consensus_reached: bool = False

    # Section reports
    section_reports: List[SectionReport] = field(default_factory=list)

    # Document-level risk flags
    risk_flags: List[str] = field(default_factory=list)

    # Review requirements
    requires_human_review: bool = False
    review_priority: ReviewPriority = ReviewPriority.NONE
    review_items: List[ReviewItem] = field(default_factory=list)

    # Thresholds used
    thresholds: ConfidenceThresholds = field(default_factory=ConfidenceThresholds)

    @property
    def resolution_rate(self) -> float:
        if self.total_critiques == 0:
            return 100.0
        return (self.resolved_critiques / self.total_critiques) * 100

    @property
    def lowest_section_score(self) -> float:
        if not self.section_reports:
            return 0.0
        return min(s.confidence_score for s in self.section_reports)

    @property
    def sections_requiring_review(self) -> List[str]:
        return [s.section_name for s in self.section_reports if s.requires_review]

    def add_section_report(self, report: SectionReport) -> None:
        """Add a section report."""
        self.section_reports.append(report)
        self.total_sections = len(self.section_reports)

        # Collect review items
        for item in report.review_items:
            self.review_items.append(item)

    def calculate_overall(self) -> None:
        """Calculate overall scores from section reports."""
        if not self.section_reports:
            self.overall_score = 0.0
            self.overall_level = ConfidenceLevel.VERY_LOW
            return

        # Use the minimum section score as the overall score
        # This ensures the overall confidence reflects the weakest section
        self.overall_score = min(
            s.confidence_score for s in self.section_reports
        )

        # Determine level
        self.overall_level = self.thresholds.get_level(self.overall_score)

        # Update review requirements
        self._evaluate_review_requirements()

    def _evaluate_review_requirements(self) -> None:
        """Determine review requirements."""
        self.requires_human_review = False
        self.review_priority = ReviewPriority.NONE

        reasons = []

        # Check overall threshold
        if self.overall_score < self.thresholds.human_review_threshold:
            self.requires_human_review = True
            self.review_priority = ReviewPriority.HIGH
            reasons.append("Overall confidence below threshold")

        # Check for critical unresolved
        critical_unresolved = sum(
            s.critical_critiques for s in self.section_reports
            if s.unresolved_critiques > 0
        )
        if critical_unresolved > 0:
            self.requires_human_review = True
            self.review_priority = ReviewPriority.CRITICAL
            reasons.append(f"{critical_unresolved} unresolved critical critique(s)")

        # Check for weak sections
        weak_sections = [
            s for s in self.section_reports
            if s.confidence_score < self.thresholds.min_section_score
        ]
        if weak_sections:
            self.requires_human_review = True
            if self.review_priority != ReviewPriority.CRITICAL:
                self.review_priority = ReviewPriority.HIGH
            reasons.append(f"{len(weak_sections)} section(s) below threshold")

        # Add document-level review items for the reasons
        for reason in reasons:
            self.review_items.append(ReviewItem(
                section="Document",
                issue=reason,
                priority=self.review_priority,
                reason="Confidence threshold check",
            ))

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "generated_at": self.generated_at.isoformat(),

            "overall": {
                "score": self.overall_score,
                "level": self.overall_level.value,
                "requires_human_review": self.requires_human_review,
                "review_priority": self.review_priority.value,
            },

            "metrics": {
                "total_sections": self.total_sections,
                "total_word_count": self.total_word_count,
                "debate_rounds": self.debate_rounds,
                "total_critiques": self.total_critiques,
                "resolved_critiques": self.resolved_critiques,
                "resolution_rate": self.resolution_rate,
                "consensus_reached": self.consensus_reached,
                "lowest_section_score": self.lowest_section_score,
            },

            "risk_flags": self.risk_flags,
            "sections_requiring_review": self.sections_requiring_review,
            "section_reports": [s.to_dict() for s in self.section_reports],
            "review_items": [r.to_dict() for r in self.review_items],
            "thresholds": self.thresholds.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConfidenceReport":
        report = cls()
        report.document_id = data.get("document_id", "")
        report.document_type = data.get("document_type", "")

        if data.get("generated_at"):
            report.generated_at = datetime.fromisoformat(data["generated_at"])

        overall = data.get("overall", {})
        report.overall_score = overall.get("score", 0.0)
        report.overall_level = ConfidenceLevel(overall.get("level", "Moderate"))
        report.requires_human_review = overall.get("requires_human_review", False)
        report.review_priority = ReviewPriority(overall.get("review_priority", "None"))

        metrics = data.get("metrics", {})
        report.total_sections = metrics.get("total_sections", 0)
        report.total_word_count = metrics.get("total_word_count", 0)
        report.debate_rounds = metrics.get("debate_rounds", 0)
        report.total_critiques = metrics.get("total_critiques", 0)
        report.resolved_critiques = metrics.get("resolved_critiques", 0)
        report.consensus_reached = metrics.get("consensus_reached", False)

        report.risk_flags = data.get("risk_flags", [])
        report.section_reports = [
            SectionReport.from_dict(s) for s in data.get("section_reports", [])
        ]
        report.review_items = [
            ReviewItem.from_dict(r) for r in data.get("review_items", [])
        ]

        if data.get("thresholds"):
            report.thresholds = ConfidenceThresholds.from_dict(data["thresholds"])

        return report

    @classmethod
    def from_confidence_score(cls, conf: ConfidenceScore) -> "ConfidenceReport":
        """Create a ConfidenceReport from a ConfidenceScore object."""
        report = cls(
            document_id=conf.document_id,
            document_type=conf.document_type,
            overall_score=conf.overall_score,
            overall_level=conf.overall_level,
            total_critiques=conf.total_critiques,
            resolved_critiques=conf.resolved_critiques,
            debate_rounds=conf.debate_rounds,
            consensus_reached=conf.consensus_reached,
            risk_flags=[f.value for f in conf.risk_flags],
            requires_human_review=conf.requires_human_review,
            thresholds=conf.thresholds,
        )

        # Convert section scores
        for section_conf in conf.section_scores:
            section_report = SectionReport.from_section_confidence(section_conf)
            report.add_section_report(section_report)

        # Add review items
        for reason in conf.review_reasons:
            report.review_items.append(ReviewItem(
                section="Document",
                issue=reason,
                priority=ReviewPriority.HIGH if conf.overall_score < 0.7 else ReviewPriority.MEDIUM,
                reason="Confidence evaluation",
            ))

        # Set review priority
        if conf.requires_human_review:
            if any(f == RiskFlag.UNRESOLVED_CRITICAL_CRITIQUE for f in conf.risk_flags):
                report.review_priority = ReviewPriority.CRITICAL
            elif conf.overall_score < 0.6:
                report.review_priority = ReviewPriority.HIGH
            else:
                report.review_priority = ReviewPriority.MEDIUM

        return report

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "ConfidenceReport":
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))

    def to_markdown(self) -> str:
        """Export report as Markdown."""
        lines = []

        # Header
        lines.append("# Confidence Report")
        lines.append("")
        lines.append(f"**Document:** {self.document_type}")
        lines.append(f"**Document ID:** {self.document_id}")
        lines.append(f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Overall Confidence
        lines.append("## Overall Confidence")
        lines.append("")
        lines.append(f"- **Score:** {self.overall_score:.2f} ({self.overall_level.value})")
        lines.append(f"- **Review Required:** {'Yes' if self.requires_human_review else 'No'}")
        if self.requires_human_review:
            lines.append(f"- **Review Priority:** {self.review_priority.value}")
        lines.append("")

        # Metrics Summary
        lines.append("## Process Metrics")
        lines.append("")
        lines.append(f"- **Debate Rounds:** {self.debate_rounds}")
        lines.append(f"- **Total Critiques:** {self.total_critiques}")
        lines.append(f"- **Resolved:** {self.resolved_critiques} ({self.resolution_rate:.1f}%)")
        lines.append(f"- **Consensus:** {'Reached' if self.consensus_reached else 'Not Reached'}")
        lines.append("")

        # Risk Flags
        if self.risk_flags:
            lines.append("## Risk Flags")
            lines.append("")
            for flag in self.risk_flags:
                lines.append(f"- {flag}")
            lines.append("")

        # Section Breakdown
        lines.append("## Section Confidence")
        lines.append("")
        lines.append("| Section | Score | Level | Critiques | Resolved | Review |")
        lines.append("|---------|-------|-------|-----------|----------|--------|")

        for section in sorted(self.section_reports, key=lambda s: s.confidence_score):
            review_status = "Yes" if section.requires_review else "No"
            lines.append(
                f"| {section.section_name} | "
                f"{section.confidence_score:.2f} | "
                f"{section.confidence_level.value} | "
                f"{section.total_critiques} | "
                f"{section.resolved_critiques} | "
                f"{review_status} |"
            )
        lines.append("")

        # Review Items
        if self.review_items:
            lines.append("## Items Requiring Review")
            lines.append("")

            # Group by priority
            by_priority: Dict[ReviewPriority, List[ReviewItem]] = {}
            for item in self.review_items:
                if item.priority not in by_priority:
                    by_priority[item.priority] = []
                by_priority[item.priority].append(item)

            for priority in [ReviewPriority.CRITICAL, ReviewPriority.HIGH, ReviewPriority.MEDIUM, ReviewPriority.LOW]:
                if priority in by_priority:
                    lines.append(f"### {priority.value} Priority")
                    lines.append("")
                    for item in by_priority[priority]:
                        lines.append(f"- **{item.section}:** {item.issue}")
                        if item.suggested_action:
                            lines.append(f"  - *Suggested:* {item.suggested_action}")
                        if item.estimated_effort:
                            lines.append(f"  - *Effort:* {item.estimated_effort}")
                    lines.append("")

        # Detailed Section Reports
        lines.append("## Detailed Section Analysis")
        lines.append("")

        for section in self.section_reports:
            lines.append(f"### {section.section_name}")
            lines.append("")
            lines.append(f"- **Confidence:** {section.confidence_score:.2f} ({section.confidence_level.value})")
            lines.append(f"- **Word Count:** {section.word_count}")
            lines.append(f"- **Revisions:** {section.revision_count}")
            lines.append(f"- **Critiques:** {section.total_critiques} total, {section.resolved_critiques} resolved")

            if section.risk_flags:
                lines.append("- **Risk Flags:**")
                for flag in section.risk_flags:
                    lines.append(f"  - {flag}")

            if section.adjustments:
                lines.append("- **Score Adjustments:**")
                for adj in section.adjustments:
                    lines.append(f"  - {adj.get('reason', 'Unknown')}: {adj.get('delta', 0):+.2f}")

            lines.append("")

        return "\n".join(lines)

    def get_summary_text(self) -> str:
        """Get a brief text summary of the report."""
        return (
            f"Confidence Report: Overall score {self.overall_score:.2f} ({self.overall_level.value}). "
            f"{self.total_sections} sections, {self.resolution_rate:.1f}% critiques resolved. "
            f"Review {'required' if self.requires_human_review else 'not required'}."
        )
