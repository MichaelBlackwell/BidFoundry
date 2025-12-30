"""
Consensus Detection

Logic for detecting when the adversarial debate has reached consensus,
allowing early termination of the debate cycle.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any, Set
import logging


logger = logging.getLogger(__name__)


class ConsensusStatus(str, Enum):
    """Status of consensus detection."""

    NOT_CHECKED = "Not Checked"
    IN_PROGRESS = "In Progress"
    REACHED = "Reached"
    NOT_REACHED = "Not Reached"
    BLOCKED = "Blocked"  # Blocked by critical unresolved issues


@dataclass
class ConsensusResult:
    """
    Result of consensus detection.

    Contains information about whether consensus was reached
    and the factors contributing to that determination.
    """

    status: ConsensusStatus = ConsensusStatus.NOT_CHECKED
    reached: bool = False
    confidence: float = 0.0

    # Metrics
    total_critiques: int = 0
    resolved_critiques: int = 0
    unresolved_critiques: int = 0
    resolution_rate: float = 0.0

    # Blocking issues
    blocking_issues: List[Dict[str, Any]] = field(default_factory=list)
    has_blocking_issues: bool = False

    # Breakdown by severity
    critiques_by_severity: Dict[str, int] = field(default_factory=dict)
    unresolved_by_severity: Dict[str, int] = field(default_factory=dict)

    # Breakdown by disposition
    responses_by_disposition: Dict[str, int] = field(default_factory=dict)

    # Timestamp
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "reached": self.reached,
            "confidence": self.confidence,
            "total_critiques": self.total_critiques,
            "resolved_critiques": self.resolved_critiques,
            "unresolved_critiques": self.unresolved_critiques,
            "resolution_rate": self.resolution_rate,
            "blocking_issues": self.blocking_issues,
            "has_blocking_issues": self.has_blocking_issues,
            "critiques_by_severity": self.critiques_by_severity,
            "unresolved_by_severity": self.unresolved_by_severity,
            "responses_by_disposition": self.responses_by_disposition,
            "checked_at": self.checked_at.isoformat(),
        }


@dataclass
class ConsensusConfig:
    """
    Configuration for consensus detection.

    Defines thresholds and weights for determining consensus.
    """

    # Resolution threshold (percentage of critiques that must be addressed)
    resolution_threshold: float = 0.80

    # Severity weights for consensus calculation
    critical_weight: float = 3.0
    major_weight: float = 2.0
    minor_weight: float = 1.0
    observation_weight: float = 0.5

    # Blocking criteria
    block_on_critical: bool = True
    max_unresolved_major: int = 2
    max_unresolved_minor: int = 5

    # Disposition scoring
    accept_score: float = 1.0
    partial_accept_score: float = 0.8
    rebut_score: float = 0.7
    acknowledge_score: float = 0.5
    defer_score: float = 0.3

    def to_dict(self) -> dict:
        return {
            "resolution_threshold": self.resolution_threshold,
            "critical_weight": self.critical_weight,
            "major_weight": self.major_weight,
            "minor_weight": self.minor_weight,
            "observation_weight": self.observation_weight,
            "block_on_critical": self.block_on_critical,
            "max_unresolved_major": self.max_unresolved_major,
            "max_unresolved_minor": self.max_unresolved_minor,
            "accept_score": self.accept_score,
            "partial_accept_score": self.partial_accept_score,
            "rebut_score": self.rebut_score,
            "acknowledge_score": self.acknowledge_score,
            "defer_score": self.defer_score,
        }


class ConsensusDetector:
    """
    Detects when the adversarial debate has reached consensus.

    Analyzes critiques and responses to determine if the debate
    can be terminated early with acceptable confidence.
    """

    def __init__(self, config: Optional[ConsensusConfig] = None):
        """
        Initialize the consensus detector.

        Args:
            config: Optional consensus configuration
        """
        self._config = config or ConsensusConfig()
        self._logger = logging.getLogger("ConsensusDetector")

    @property
    def config(self) -> ConsensusConfig:
        """Get the current configuration."""
        return self._config

    def check(
        self,
        critiques: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        threshold: Optional[float] = None,
    ) -> ConsensusResult:
        """
        Check if consensus has been reached.

        Args:
            critiques: List of all critiques from red team
            responses: List of all responses from blue team
            threshold: Optional override for resolution threshold

        Returns:
            ConsensusResult with consensus status and metrics
        """
        result = ConsensusResult(status=ConsensusStatus.IN_PROGRESS)
        effective_threshold = threshold or self._config.resolution_threshold

        # Handle edge case of no critiques
        if not critiques:
            result.status = ConsensusStatus.REACHED
            result.reached = True
            result.confidence = 1.0
            result.resolution_rate = 100.0
            return result

        result.total_critiques = len(critiques)

        # Build response lookup
        response_by_critique = self._build_response_map(responses)

        # Categorize critiques
        severity_counts = self._count_by_severity(critiques)
        result.critiques_by_severity = severity_counts

        # Analyze resolution status
        resolved_critiques = []
        unresolved_critiques = []
        blocking_issues = []

        for critique in critiques:
            critique_id = critique.get("id")
            severity = critique.get("severity", "minor")
            response = response_by_critique.get(critique_id)

            if response:
                resolved_critiques.append(critique)
                disposition = response.get("disposition", "Acknowledge")
                result.responses_by_disposition[disposition] = (
                    result.responses_by_disposition.get(disposition, 0) + 1
                )
            else:
                unresolved_critiques.append(critique)

                # Track unresolved by severity
                result.unresolved_by_severity[severity] = (
                    result.unresolved_by_severity.get(severity, 0) + 1
                )

                # Check for blocking issues
                if severity == "critical" and self._config.block_on_critical:
                    blocking_issues.append({
                        "critique_id": critique_id,
                        "severity": severity,
                        "reason": "Unresolved critical critique",
                        "section": critique.get("target_section"),
                        "title": critique.get("title"),
                    })

        result.resolved_critiques = len(resolved_critiques)
        result.unresolved_critiques = len(unresolved_critiques)
        result.blocking_issues = blocking_issues
        result.has_blocking_issues = len(blocking_issues) > 0

        # Calculate resolution rate
        if result.total_critiques > 0:
            result.resolution_rate = result.resolved_critiques / result.total_critiques
        else:
            result.resolution_rate = 1.0

        # Check for blocking conditions
        if result.has_blocking_issues:
            result.status = ConsensusStatus.BLOCKED
            result.reached = False
            result.confidence = 0.0
            return result

        # Check additional blocking criteria
        unresolved_major = result.unresolved_by_severity.get("major", 0)
        unresolved_minor = result.unresolved_by_severity.get("minor", 0)

        if unresolved_major > self._config.max_unresolved_major:
            result.status = ConsensusStatus.BLOCKED
            result.reached = False
            result.blocking_issues.append({
                "reason": f"Too many unresolved major critiques: {unresolved_major}",
                "threshold": self._config.max_unresolved_major,
            })
            result.has_blocking_issues = True
            return result

        # Calculate weighted consensus score
        weighted_score = self._calculate_weighted_score(
            resolved_critiques,
            unresolved_critiques,
            response_by_critique,
        )

        result.confidence = weighted_score

        # Determine consensus status
        if result.resolution_rate >= effective_threshold:
            result.status = ConsensusStatus.REACHED
            result.reached = True
        else:
            result.status = ConsensusStatus.NOT_REACHED
            result.reached = False

        return result

    def _build_response_map(
        self,
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Build a lookup map from critique ID to response."""
        return {
            r.get("critique_id"): r
            for r in responses
            if r.get("critique_id")
        }

    def _count_by_severity(
        self,
        critiques: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count critiques by severity level."""
        counts: Dict[str, int] = {}
        for critique in critiques:
            severity = critique.get("severity", "minor")
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _calculate_weighted_score(
        self,
        resolved: List[Dict[str, Any]],
        unresolved: List[Dict[str, Any]],
        response_map: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Calculate a weighted consensus score.

        Takes into account:
        - Severity of critiques
        - Quality of responses (disposition)
        - Remaining unresolved issues

        Returns a score between 0 and 1.
        """
        if not resolved and not unresolved:
            return 1.0

        total_weight = 0.0
        resolved_weight = 0.0

        # Weight for unresolved critiques
        for critique in unresolved:
            weight = self._get_severity_weight(critique.get("severity", "minor"))
            total_weight += weight

        # Weight for resolved critiques (adjusted by disposition quality)
        for critique in resolved:
            weight = self._get_severity_weight(critique.get("severity", "minor"))
            total_weight += weight

            critique_id = critique.get("id")
            response = response_map.get(critique_id, {})
            disposition_score = self._get_disposition_score(
                response.get("disposition", "Acknowledge")
            )

            resolved_weight += weight * disposition_score

        if total_weight == 0:
            return 1.0

        return resolved_weight / total_weight

    def _get_severity_weight(self, severity: str) -> float:
        """Get the weight for a severity level."""
        weights = {
            "critical": self._config.critical_weight,
            "major": self._config.major_weight,
            "minor": self._config.minor_weight,
            "observation": self._config.observation_weight,
        }
        return weights.get(severity, self._config.minor_weight)

    def _get_disposition_score(self, disposition: str) -> float:
        """Get the resolution score for a disposition."""
        scores = {
            "Accept": self._config.accept_score,
            "Partial Accept": self._config.partial_accept_score,
            "Rebut": self._config.rebut_score,
            "Acknowledge": self._config.acknowledge_score,
            "Defer": self._config.defer_score,
        }
        return scores.get(disposition, self._config.acknowledge_score)

    def analyze_convergence(
        self,
        round_results: List[ConsensusResult],
    ) -> Dict[str, Any]:
        """
        Analyze convergence trends across multiple rounds.

        Useful for understanding if the debate is making progress
        toward consensus.

        Args:
            round_results: Consensus results from each round

        Returns:
            Analysis of convergence trends
        """
        if not round_results:
            return {"trend": "unknown", "message": "No rounds to analyze"}

        resolution_rates = [r.resolution_rate for r in round_results]
        confidence_scores = [r.confidence for r in round_results]

        # Calculate trends
        resolution_trend = self._calculate_trend(resolution_rates)
        confidence_trend = self._calculate_trend(confidence_scores)

        # Determine overall convergence
        if len(round_results) >= 2:
            recent_improvement = (
                resolution_rates[-1] - resolution_rates[-2]
                if len(resolution_rates) >= 2 else 0
            )
            is_converging = recent_improvement > 0
        else:
            is_converging = None

        return {
            "rounds_analyzed": len(round_results),
            "resolution_rates": resolution_rates,
            "confidence_scores": confidence_scores,
            "resolution_trend": resolution_trend,
            "confidence_trend": confidence_trend,
            "is_converging": is_converging,
            "current_rate": resolution_rates[-1] if resolution_rates else 0,
            "current_confidence": confidence_scores[-1] if confidence_scores else 0,
            "improvement_last_round": (
                resolution_rates[-1] - resolution_rates[-2]
                if len(resolution_rates) >= 2 else None
            ),
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate the trend of a series of values."""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear trend
        improvements = sum(
            1 for i in range(1, len(values))
            if values[i] > values[i - 1]
        )
        declines = sum(
            1 for i in range(1, len(values))
            if values[i] < values[i - 1]
        )

        if improvements > declines:
            return "improving"
        elif declines > improvements:
            return "declining"
        else:
            return "stable"

    def get_blocking_summary(self, result: ConsensusResult) -> str:
        """
        Get a human-readable summary of blocking issues.

        Args:
            result: The consensus result to summarize

        Returns:
            A string describing why consensus is blocked
        """
        if not result.has_blocking_issues:
            return "No blocking issues"

        lines = ["Consensus blocked due to:"]
        for issue in result.blocking_issues:
            if "critique_id" in issue:
                lines.append(
                    f"  - {issue.get('severity', 'Unknown')} issue in "
                    f"{issue.get('section', 'unknown section')}: "
                    f"{issue.get('title', 'No title')}"
                )
            else:
                lines.append(f"  - {issue.get('reason', 'Unknown reason')}")

        return "\n".join(lines)

    def suggest_next_action(self, result: ConsensusResult) -> Dict[str, Any]:
        """
        Suggest the next action based on consensus status.

        Args:
            result: The consensus result

        Returns:
            Dictionary with suggested action and reasoning
        """
        if result.reached:
            return {
                "action": "proceed_to_synthesis",
                "reason": "Consensus reached with sufficient resolution rate",
                "confidence": result.confidence,
            }

        if result.status == ConsensusStatus.BLOCKED:
            return {
                "action": "address_blocking_issues",
                "reason": f"Cannot proceed: {len(result.blocking_issues)} blocking issues",
                "issues": result.blocking_issues,
                "priority_sections": list(set(
                    i.get("section") for i in result.blocking_issues
                    if i.get("section")
                )),
            }

        if result.resolution_rate < 0.5:
            return {
                "action": "continue_debate",
                "reason": "Resolution rate too low for consensus",
                "current_rate": result.resolution_rate,
                "target_rate": self._config.resolution_threshold,
                "critiques_remaining": result.unresolved_critiques,
            }

        # Close to threshold but not quite
        return {
            "action": "targeted_resolution",
            "reason": "Close to consensus - focus on remaining issues",
            "current_rate": result.resolution_rate,
            "target_rate": self._config.resolution_threshold,
            "critiques_remaining": result.unresolved_critiques,
            "priority_severities": [
                sev for sev, count in result.unresolved_by_severity.items()
                if count > 0
            ],
        }
