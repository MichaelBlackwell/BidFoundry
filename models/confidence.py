"""
Confidence Scoring Model

Defines the structure for confidence scores that track the quality
and reliability of generated documents. Confidence scores are used
to determine if human review is required.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
import json


class ConfidenceLevel(str, Enum):
    """Qualitative confidence levels."""

    VERY_HIGH = "Very High"  # >= 0.90
    HIGH = "High"  # >= 0.80
    MODERATE = "Moderate"  # >= 0.70
    LOW = "Low"  # >= 0.50
    VERY_LOW = "Very Low"  # < 0.50


class RiskFlag(str, Enum):
    """Flags that can reduce confidence."""

    UNRESOLVED_CRITICAL_CRITIQUE = "Unresolved Critical Critique"
    HIGH_CRITIQUE_DENSITY = "High Critique Density"
    LOW_EVIDENCE_SUPPORT = "Low Evidence Support"
    COMPLIANCE_CONCERNS = "Compliance Concerns"
    COMPETITIVE_VULNERABILITY = "Competitive Vulnerability"
    MISSING_REQUIRED_CONTENT = "Missing Required Content"
    INSUFFICIENT_PAST_PERFORMANCE = "Insufficient Past Performance"
    SCOPE_MISMATCH = "Scope Mismatch"
    FEASIBILITY_CONCERNS = "Feasibility Concerns"


@dataclass
class ConfidenceThresholds:
    """
    Configurable thresholds for confidence scoring.

    These thresholds determine when human review is required
    and how confidence levels are interpreted.
    """

    # Overall document thresholds
    min_approval_score: float = 0.70  # Minimum score for auto-approval
    human_review_threshold: float = 0.70  # Below this triggers human review
    critical_threshold: float = 0.50  # Below this halts processing

    # Section thresholds
    min_section_score: float = 0.60  # Minimum acceptable section score

    # Critique impact weights
    critical_critique_penalty: float = 0.15
    major_critique_penalty: float = 0.08
    minor_critique_penalty: float = 0.03

    # Resolution bonuses
    accepted_resolution_bonus: float = 0.05
    rebutted_resolution_bonus: float = 0.03

    def get_level(self, score: float) -> ConfidenceLevel:
        """Convert a numeric score to a confidence level."""
        if score >= 0.90:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.80:
            return ConfidenceLevel.HIGH
        elif score >= 0.70:
            return ConfidenceLevel.MODERATE
        elif score >= 0.50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def to_dict(self) -> dict:
        return {
            "min_approval_score": self.min_approval_score,
            "human_review_threshold": self.human_review_threshold,
            "critical_threshold": self.critical_threshold,
            "min_section_score": self.min_section_score,
            "critical_critique_penalty": self.critical_critique_penalty,
            "major_critique_penalty": self.major_critique_penalty,
            "minor_critique_penalty": self.minor_critique_penalty,
            "accepted_resolution_bonus": self.accepted_resolution_bonus,
            "rebutted_resolution_bonus": self.rebutted_resolution_bonus,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConfidenceThresholds":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ConfidenceThresholds":
        return cls.from_dict(json.loads(json_str))


@dataclass
class SectionConfidence:
    """
    Confidence score for a single document section.

    Tracks the factors contributing to the section's confidence level.
    """

    section_id: str = ""
    section_name: str = ""

    # Core score
    base_score: float = 0.80  # Starting score before adjustments
    adjusted_score: float = 0.80  # Final score after adjustments
    level: ConfidenceLevel = ConfidenceLevel.HIGH

    # Contributing factors
    critique_count: int = 0
    unresolved_critiques: int = 0
    critical_critiques: int = 0
    major_critiques: int = 0

    # Adjustments applied
    adjustments: List[Dict[str, float]] = field(default_factory=list)

    # Risk flags
    risk_flags: List[RiskFlag] = field(default_factory=list)

    # Metadata
    word_count: int = 0
    revision_count: int = 0

    def apply_adjustment(self, reason: str, delta: float) -> None:
        """Apply an adjustment to the confidence score."""
        self.adjustments.append({"reason": reason, "delta": delta})
        self.adjusted_score = max(0.0, min(1.0, self.adjusted_score + delta))

    def add_risk_flag(self, flag: RiskFlag) -> None:
        """Add a risk flag to the section."""
        if flag not in self.risk_flags:
            self.risk_flags.append(flag)

    def finalize(self, thresholds: ConfidenceThresholds) -> None:
        """Finalize the score and set the confidence level."""
        self.level = thresholds.get_level(self.adjusted_score)

    def to_dict(self) -> dict:
        return {
            "section_id": self.section_id,
            "section_name": self.section_name,
            "base_score": self.base_score,
            "adjusted_score": self.adjusted_score,
            "level": self.level.value,
            "critique_count": self.critique_count,
            "unresolved_critiques": self.unresolved_critiques,
            "critical_critiques": self.critical_critiques,
            "major_critiques": self.major_critiques,
            "adjustments": self.adjustments,
            "risk_flags": [f.value for f in self.risk_flags],
            "word_count": self.word_count,
            "revision_count": self.revision_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SectionConfidence":
        section = cls(
            section_id=data.get("section_id", ""),
            section_name=data.get("section_name", ""),
            base_score=data.get("base_score", 0.80),
            adjusted_score=data.get("adjusted_score", 0.80),
            level=ConfidenceLevel(data.get("level", "High")),
            critique_count=data.get("critique_count", 0),
            unresolved_critiques=data.get("unresolved_critiques", 0),
            critical_critiques=data.get("critical_critiques", 0),
            major_critiques=data.get("major_critiques", 0),
            adjustments=data.get("adjustments", []),
            risk_flags=[RiskFlag(f) for f in data.get("risk_flags", [])],
            word_count=data.get("word_count", 0),
            revision_count=data.get("revision_count", 0),
        )
        return section

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "SectionConfidence":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ConfidenceScore:
    """
    Overall confidence score for a generated document.

    Aggregates section scores and applies document-level adjustments
    to determine if human review is required.
    """

    document_id: str = ""
    document_type: str = ""

    # Overall scores
    overall_score: float = 0.80
    overall_level: ConfidenceLevel = ConfidenceLevel.HIGH

    # Section breakdown
    section_scores: List[SectionConfidence] = field(default_factory=list)

    # Aggregate metrics
    total_critiques: int = 0
    resolved_critiques: int = 0
    unresolved_critical: int = 0
    unresolved_major: int = 0

    # Debate metrics
    debate_rounds: int = 0
    consensus_reached: bool = False

    # Risk assessment
    risk_flags: List[RiskFlag] = field(default_factory=list)

    # Review requirements
    requires_human_review: bool = False
    review_reasons: List[str] = field(default_factory=list)

    # Thresholds used
    thresholds: ConfidenceThresholds = field(default_factory=ConfidenceThresholds)

    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def lowest_section_score(self) -> float:
        """Get the lowest section score."""
        if not self.section_scores:
            return 0.0
        return min(s.adjusted_score for s in self.section_scores)

    @property
    def sections_below_threshold(self) -> List[SectionConfidence]:
        """Get sections below the minimum threshold."""
        return [
            s for s in self.section_scores
            if s.adjusted_score < self.thresholds.min_section_score
        ]

    @property
    def resolution_rate(self) -> float:
        """Calculate the critique resolution rate."""
        if self.total_critiques == 0:
            return 100.0
        return (self.resolved_critiques / self.total_critiques) * 100

    def add_section_score(self, section: SectionConfidence) -> None:
        """Add a section confidence score."""
        self.section_scores.append(section)

    def add_risk_flag(self, flag: RiskFlag, reason: Optional[str] = None) -> None:
        """Add a document-level risk flag."""
        if flag not in self.risk_flags:
            self.risk_flags.append(flag)
        if reason and reason not in self.review_reasons:
            self.review_reasons.append(reason)

    def calculate_overall_score(self) -> None:
        """Calculate the overall confidence score from section scores."""
        if not self.section_scores:
            self.overall_score = 0.0
            self.overall_level = ConfidenceLevel.VERY_LOW
            return

        # Use the minimum section score as the overall score
        # This ensures the overall confidence reflects the weakest section
        self.overall_score = min(s.adjusted_score for s in self.section_scores)

        # Apply document-level penalties
        if self.unresolved_critical > 0:
            penalty = self.unresolved_critical * self.thresholds.critical_critique_penalty
            self.overall_score = max(0.0, self.overall_score - penalty)
            self.add_risk_flag(
                RiskFlag.UNRESOLVED_CRITICAL_CRITIQUE,
                f"{self.unresolved_critical} unresolved critical critique(s)"
            )

        if self.unresolved_major > 2:
            self.add_risk_flag(
                RiskFlag.HIGH_CRITIQUE_DENSITY,
                f"{self.unresolved_major} unresolved major critiques"
            )

        # Set the confidence level
        self.overall_level = self.thresholds.get_level(self.overall_score)

        # Determine if human review is required
        self._evaluate_review_requirement()

    def _evaluate_review_requirement(self) -> None:
        """Determine if human review is required based on scores and flags."""
        self.requires_human_review = False
        self.review_reasons = []

        # Check overall threshold
        if self.overall_score < self.thresholds.human_review_threshold:
            self.requires_human_review = True
            self.review_reasons.append(
                f"Overall confidence ({self.overall_score:.2f}) below threshold "
                f"({self.thresholds.human_review_threshold})"
            )

        # Check for unresolved critical critiques
        if self.unresolved_critical > 0:
            self.requires_human_review = True
            self.review_reasons.append(
                f"{self.unresolved_critical} unresolved critical critique(s)"
            )

        # Check for sections below threshold
        weak_sections = self.sections_below_threshold
        if weak_sections:
            self.requires_human_review = True
            section_names = ", ".join(s.section_name for s in weak_sections)
            self.review_reasons.append(
                f"Section(s) below threshold: {section_names}"
            )

        # Check for critical risk flags
        critical_flags = {
            RiskFlag.COMPLIANCE_CONCERNS,
            RiskFlag.MISSING_REQUIRED_CONTENT,
            RiskFlag.SCOPE_MISMATCH,
        }
        for flag in self.risk_flags:
            if flag in critical_flags:
                self.requires_human_review = True
                self.review_reasons.append(f"Risk flag: {flag.value}")

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "overall_score": self.overall_score,
            "overall_level": self.overall_level.value,
            "section_scores": [s.to_dict() for s in self.section_scores],
            "total_critiques": self.total_critiques,
            "resolved_critiques": self.resolved_critiques,
            "unresolved_critical": self.unresolved_critical,
            "unresolved_major": self.unresolved_major,
            "debate_rounds": self.debate_rounds,
            "consensus_reached": self.consensus_reached,
            "risk_flags": [f.value for f in self.risk_flags],
            "requires_human_review": self.requires_human_review,
            "review_reasons": self.review_reasons,
            "resolution_rate": self.resolution_rate,
            "lowest_section_score": self.lowest_section_score,
            "thresholds": self.thresholds.to_dict(),
            "calculated_at": self.calculated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConfidenceScore":
        return cls(
            document_id=data.get("document_id", ""),
            document_type=data.get("document_type", ""),
            overall_score=data.get("overall_score", 0.80),
            overall_level=ConfidenceLevel(data.get("overall_level", "High")),
            section_scores=[SectionConfidence.from_dict(s) for s in data.get("section_scores", [])],
            total_critiques=data.get("total_critiques", 0),
            resolved_critiques=data.get("resolved_critiques", 0),
            unresolved_critical=data.get("unresolved_critical", 0),
            unresolved_major=data.get("unresolved_major", 0),
            debate_rounds=data.get("debate_rounds", 0),
            consensus_reached=data.get("consensus_reached", False),
            risk_flags=[RiskFlag(f) for f in data.get("risk_flags", [])],
            requires_human_review=data.get("requires_human_review", False),
            review_reasons=data.get("review_reasons", []),
            thresholds=ConfidenceThresholds.from_dict(data["thresholds"]) if data.get("thresholds") else ConfidenceThresholds(),
            calculated_at=datetime.fromisoformat(data["calculated_at"]) if data.get("calculated_at") else datetime.utcnow(),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ConfidenceScore":
        return cls.from_dict(json.loads(json_str))

    def get_summary(self) -> str:
        """Get a human-readable summary of the confidence score."""
        summary_lines = [
            f"Document Confidence Score: {self.overall_score:.2f} ({self.overall_level.value})",
            f"Sections: {len(self.section_scores)}",
            f"Critique Resolution: {self.resolved_critiques}/{self.total_critiques} ({self.resolution_rate:.1f}%)",
            f"Debate Rounds: {self.debate_rounds}",
        ]

        if self.requires_human_review:
            summary_lines.append("⚠️ HUMAN REVIEW REQUIRED")
            for reason in self.review_reasons:
                summary_lines.append(f"  - {reason}")

        if self.risk_flags:
            summary_lines.append("Risk Flags:")
            for flag in self.risk_flags:
                summary_lines.append(f"  - {flag.value}")

        return "\n".join(summary_lines)
