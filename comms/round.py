"""
Round Manager

Manages debate rounds in the adversarial swarm workflow, tracking
round state, transitions, and consensus detection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any, Set, Callable
import logging
import uuid

from .message import Message, MessageType, create_control_message
from .history import ConversationHistory, RoundRecord


class RoundType(str, Enum):
    """Types of debate rounds."""

    BLUE_BUILD = "BlueBuild"  # Blue team creates initial draft
    RED_ATTACK = "RedAttack"  # Red team critiques blue team output
    BLUE_DEFENSE = "BlueDefense"  # Blue team responds to critiques
    SYNTHESIS = "Synthesis"  # Final document synthesis


class RoundPhase(str, Enum):
    """Phases within a round."""

    PENDING = "Pending"  # Round not yet started
    ACTIVE = "Active"  # Round in progress
    WAITING = "Waiting"  # Waiting for agent responses
    COMPLETE = "Complete"  # Round finished
    ABORTED = "Aborted"  # Round was aborted


@dataclass
class RoundSummary:
    """
    Summary of a completed debate round.

    Provides metrics and outcomes for reporting and decision-making.
    """

    round_number: int
    round_type: RoundType

    # Timing
    started_at: datetime
    ended_at: datetime
    duration_seconds: float

    # Activity
    message_count: int = 0
    critique_count: int = 0
    response_count: int = 0

    # Participation
    blue_team_agents: List[str] = field(default_factory=list)
    red_team_agents: List[str] = field(default_factory=list)

    # Outcomes
    critiques_by_severity: Dict[str, int] = field(default_factory=dict)
    responses_by_disposition: Dict[str, int] = field(default_factory=dict)

    # Resolution
    total_critiques: int = 0
    resolved_critiques: int = 0
    unresolved_critiques: int = 0
    critical_unresolved: int = 0

    # Sections
    sections_modified: List[str] = field(default_factory=list)
    sections_with_issues: List[str] = field(default_factory=list)

    # Consensus
    consensus_reached: bool = False
    consensus_confidence: float = 0.0

    @property
    def resolution_rate(self) -> float:
        """Calculate critique resolution rate."""
        if self.total_critiques == 0:
            return 100.0
        return (self.resolved_critiques / self.total_critiques) * 100

    @property
    def has_blocking_issues(self) -> bool:
        """Check if there are blocking (critical unresolved) issues."""
        return self.critical_unresolved > 0

    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "round_type": self.round_type.value,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "message_count": self.message_count,
            "critique_count": self.critique_count,
            "response_count": self.response_count,
            "blue_team_agents": self.blue_team_agents,
            "red_team_agents": self.red_team_agents,
            "critiques_by_severity": self.critiques_by_severity,
            "responses_by_disposition": self.responses_by_disposition,
            "total_critiques": self.total_critiques,
            "resolved_critiques": self.resolved_critiques,
            "unresolved_critiques": self.unresolved_critiques,
            "critical_unresolved": self.critical_unresolved,
            "sections_modified": self.sections_modified,
            "sections_with_issues": self.sections_with_issues,
            "consensus_reached": self.consensus_reached,
            "consensus_confidence": self.consensus_confidence,
            "resolution_rate": self.resolution_rate,
            "has_blocking_issues": self.has_blocking_issues,
        }


@dataclass
class RoundConfig:
    """Configuration for a debate round."""

    round_type: RoundType
    max_duration_seconds: float = 300.0  # 5 minutes default
    min_critiques_required: int = 0  # Minimum critiques for red attack
    required_agents: List[str] = field(default_factory=list)  # Agents that must participate
    optional_agents: List[str] = field(default_factory=list)  # Optional participants
    consensus_threshold: float = 0.8  # Resolution rate for consensus
    allow_escalation: bool = True  # Allow human escalation
    auto_advance: bool = True  # Automatically advance when complete


class RoundManager:
    """
    Manages debate rounds in the adversarial workflow.

    Handles round lifecycle, transitions, and consensus detection
    for the document generation process.
    """

    # Default round sequence for document generation
    DEFAULT_ROUND_SEQUENCE = [
        RoundType.BLUE_BUILD,
        RoundType.RED_ATTACK,
        RoundType.BLUE_DEFENSE,
        RoundType.SYNTHESIS,
    ]

    def __init__(
        self,
        history: Optional[ConversationHistory] = None,
        max_adversarial_rounds: int = 3,
        consensus_threshold: float = 0.8,
    ):
        """
        Initialize the round manager.

        Args:
            history: Optional conversation history to use
            max_adversarial_rounds: Maximum number of red/blue cycles
            consensus_threshold: Resolution rate threshold for consensus
        """
        self._history = history or ConversationHistory()
        self._max_adversarial_rounds = max_adversarial_rounds
        self._consensus_threshold = consensus_threshold
        self._logger = logging.getLogger("RoundManager")

        # Round tracking
        self._current_round: int = 0
        self._current_phase: RoundPhase = RoundPhase.PENDING
        self._current_type: Optional[RoundType] = None
        self._round_configs: Dict[int, RoundConfig] = {}
        self._round_summaries: Dict[int, RoundSummary] = {}

        # Timing
        self._round_start_time: Optional[datetime] = None
        self._round_deadline: Optional[datetime] = None

        # Callbacks
        self._on_round_start: Optional[Callable[[int, RoundType], None]] = None
        self._on_round_end: Optional[Callable[[RoundSummary], None]] = None
        self._on_consensus: Optional[Callable[[int], None]] = None

        # State
        self._adversarial_cycle_count = 0
        self._consensus_reached = False

    @property
    def current_round(self) -> int:
        """Get the current round number."""
        return self._current_round

    @property
    def current_phase(self) -> RoundPhase:
        """Get the current round phase."""
        return self._current_phase

    @property
    def current_type(self) -> Optional[RoundType]:
        """Get the current round type."""
        return self._current_type

    @property
    def is_active(self) -> bool:
        """Check if a round is currently active."""
        return self._current_phase == RoundPhase.ACTIVE

    @property
    def consensus_reached(self) -> bool:
        """Check if consensus has been reached."""
        return self._consensus_reached

    @property
    def adversarial_cycles_remaining(self) -> int:
        """Get remaining adversarial cycles."""
        return max(0, self._max_adversarial_rounds - self._adversarial_cycle_count)

    def set_callbacks(
        self,
        on_round_start: Optional[Callable[[int, RoundType], None]] = None,
        on_round_end: Optional[Callable[[RoundSummary], None]] = None,
        on_consensus: Optional[Callable[[int], None]] = None,
    ) -> None:
        """Set callback functions for round events."""
        self._on_round_start = on_round_start
        self._on_round_end = on_round_end
        self._on_consensus = on_consensus

    def configure_round(self, round_number: int, config: RoundConfig) -> None:
        """
        Configure a specific round.

        Args:
            round_number: The round to configure
            config: Round configuration
        """
        self._round_configs[round_number] = config

    def start_round(
        self,
        round_type: RoundType,
        config: Optional[RoundConfig] = None,
    ) -> int:
        """
        Start a new debate round.

        Args:
            round_type: Type of round to start
            config: Optional round configuration

        Returns:
            The new round number

        Raises:
            RuntimeError: If a round is already active
        """
        if self._current_phase == RoundPhase.ACTIVE:
            raise RuntimeError(
                f"Cannot start new round while round {self._current_round} is active"
            )

        self._current_round += 1
        self._current_type = round_type
        self._current_phase = RoundPhase.ACTIVE
        self._round_start_time = datetime.now(timezone.utc)

        # Apply configuration
        if config:
            self._round_configs[self._current_round] = config
        elif self._current_round not in self._round_configs:
            self._round_configs[self._current_round] = RoundConfig(round_type=round_type)

        # Set deadline if configured
        round_config = self._round_configs[self._current_round]
        if round_config.max_duration_seconds:
            from datetime import timedelta
            self._round_deadline = self._round_start_time + timedelta(
                seconds=round_config.max_duration_seconds
            )

        # Track adversarial cycles
        if round_type == RoundType.BLUE_DEFENSE:
            self._adversarial_cycle_count += 1

        # Update history
        self._history.start_round(self._current_round, round_type.value)

        # Invoke callback
        if self._on_round_start:
            self._on_round_start(self._current_round, round_type)

        self._logger.info(
            f"Started round {self._current_round} ({round_type.value})"
        )

        return self._current_round

    def end_round(self, check_consensus: bool = True) -> RoundSummary:
        """
        End the current round.

        Args:
            check_consensus: Whether to check for consensus

        Returns:
            Summary of the completed round

        Raises:
            RuntimeError: If no round is active
        """
        if self._current_phase != RoundPhase.ACTIVE:
            raise RuntimeError("No active round to end")

        end_time = datetime.now(timezone.utc)
        duration = (end_time - self._round_start_time).total_seconds()

        # Get round record from history
        round_record = self._history.end_round(self._current_round)

        # Build summary
        summary = self._build_round_summary(round_record, end_time, duration)

        # Check consensus
        if check_consensus and self._current_type == RoundType.BLUE_DEFENSE:
            self._check_consensus(summary)

        # Store summary
        self._round_summaries[self._current_round] = summary

        # Update state
        self._current_phase = RoundPhase.COMPLETE

        # Invoke callback
        if self._on_round_end:
            self._on_round_end(summary)

        self._logger.info(
            f"Ended round {self._current_round} - "
            f"Resolution rate: {summary.resolution_rate:.1f}%"
        )

        return summary

    def _build_round_summary(
        self,
        round_record: Optional[RoundRecord],
        end_time: datetime,
        duration: float,
    ) -> RoundSummary:
        """Build a RoundSummary from a RoundRecord."""
        summary = RoundSummary(
            round_number=self._current_round,
            round_type=self._current_type,
            started_at=self._round_start_time,
            ended_at=end_time,
            duration_seconds=duration,
        )

        if round_record:
            summary.message_count = round_record.message_count
            summary.critique_count = round_record.critique_count
            summary.response_count = round_record.response_count
            summary.blue_team_agents = list(round_record.blue_team_agents)
            summary.red_team_agents = list(round_record.red_team_agents)
            summary.critiques_by_severity = dict(round_record.critiques_by_severity)
            summary.responses_by_disposition = dict(round_record.responses_by_disposition)
            summary.sections_modified = list(round_record.sections_affected)

            # Calculate resolution metrics
            summary.total_critiques = len(round_record.exchanges)
            summary.resolved_critiques = sum(
                1 for e in round_record.exchanges if e.is_resolved
            )
            summary.unresolved_critiques = sum(
                1 for e in round_record.exchanges if not e.is_resolved
            )
            summary.critical_unresolved = sum(
                1 for e in round_record.exchanges
                if not e.is_resolved and e.critique_severity == "critical"
            )
            summary.sections_with_issues = list(set(
                e.target_section for e in round_record.pending_critiques
            ))

        return summary

    def _check_consensus(self, summary: RoundSummary) -> None:
        """Check if consensus has been reached."""
        if summary.resolution_rate >= self._consensus_threshold * 100:
            if not summary.has_blocking_issues:
                summary.consensus_reached = True
                summary.consensus_confidence = summary.resolution_rate / 100
                self._consensus_reached = True

                if self._on_consensus:
                    self._on_consensus(self._current_round)

                self._logger.info(
                    f"Consensus reached in round {self._current_round} "
                    f"(confidence: {summary.consensus_confidence:.2f})"
                )

    def abort_round(self, reason: str = "") -> Optional[RoundSummary]:
        """
        Abort the current round.

        Args:
            reason: Optional reason for aborting

        Returns:
            Summary of the aborted round, or None if no round active
        """
        if self._current_phase != RoundPhase.ACTIVE:
            return None

        self._logger.warning(f"Aborting round {self._current_round}: {reason}")

        end_time = datetime.now(timezone.utc)
        duration = (end_time - self._round_start_time).total_seconds()
        round_record = self._history.end_round(self._current_round)

        summary = self._build_round_summary(round_record, end_time, duration)
        summary.consensus_reached = False

        self._round_summaries[self._current_round] = summary
        self._current_phase = RoundPhase.ABORTED

        return summary

    def get_next_round_type(self) -> Optional[RoundType]:
        """
        Determine the next round type in the sequence.

        Returns:
            The next RoundType, or None if debate should end
        """
        if self._current_type is None:
            return RoundType.BLUE_BUILD

        if self._consensus_reached:
            if self._current_type != RoundType.SYNTHESIS:
                return RoundType.SYNTHESIS
            return None

        if self._current_type == RoundType.BLUE_BUILD:
            return RoundType.RED_ATTACK

        if self._current_type == RoundType.RED_ATTACK:
            return RoundType.BLUE_DEFENSE

        if self._current_type == RoundType.BLUE_DEFENSE:
            if self._adversarial_cycle_count >= self._max_adversarial_rounds:
                return RoundType.SYNTHESIS
            # Check if last round's summary indicates we should continue
            last_summary = self._round_summaries.get(self._current_round)
            if last_summary and not last_summary.has_blocking_issues:
                # If no blocking issues and good resolution, go to synthesis
                if last_summary.resolution_rate >= self._consensus_threshold * 100:
                    return RoundType.SYNTHESIS
            return RoundType.RED_ATTACK

        if self._current_type == RoundType.SYNTHESIS:
            return None  # Debate complete

        return None

    def should_continue(self) -> bool:
        """
        Determine if the debate should continue.

        Returns:
            True if more rounds should be executed
        """
        if self._consensus_reached:
            # Still need synthesis
            return self._current_type != RoundType.SYNTHESIS

        if self._adversarial_cycle_count >= self._max_adversarial_rounds:
            # Need to force synthesis
            return self._current_type != RoundType.SYNTHESIS

        return True

    def get_round_summary(self, round_number: int) -> Optional[RoundSummary]:
        """Get the summary for a specific round."""
        return self._round_summaries.get(round_number)

    def get_all_summaries(self) -> List[RoundSummary]:
        """Get summaries for all completed rounds."""
        return [
            self._round_summaries[r]
            for r in sorted(self._round_summaries.keys())
        ]

    def get_debate_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the entire debate.

        Returns:
            Dictionary with debate statistics and outcomes
        """
        summaries = self.get_all_summaries()

        total_critiques = sum(s.total_critiques for s in summaries)
        resolved_critiques = sum(s.resolved_critiques for s in summaries)

        # Aggregate outcomes
        severity_totals: Dict[str, int] = {}
        disposition_totals: Dict[str, int] = {}
        for s in summaries:
            for sev, count in s.critiques_by_severity.items():
                severity_totals[sev] = severity_totals.get(sev, 0) + count
            for disp, count in s.responses_by_disposition.items():
                disposition_totals[disp] = disposition_totals.get(disp, 0) + count

        # Collect unique agents
        blue_agents: Set[str] = set()
        red_agents: Set[str] = set()
        for s in summaries:
            blue_agents.update(s.blue_team_agents)
            red_agents.update(s.red_team_agents)

        total_duration = sum(s.duration_seconds for s in summaries)

        return {
            "total_rounds": len(summaries),
            "adversarial_cycles": self._adversarial_cycle_count,
            "consensus_reached": self._consensus_reached,
            "total_critiques": total_critiques,
            "resolved_critiques": resolved_critiques,
            "overall_resolution_rate": (
                (resolved_critiques / total_critiques * 100) if total_critiques else 100.0
            ),
            "critiques_by_severity": severity_totals,
            "responses_by_disposition": disposition_totals,
            "blue_team_agents": list(blue_agents),
            "red_team_agents": list(red_agents),
            "total_duration_seconds": total_duration,
            "round_summaries": [s.to_dict() for s in summaries],
        }

    def create_round_start_message(self, sender_role: str = "Arbiter") -> Message:
        """Create a control message signaling round start."""
        return create_control_message(
            sender_role=sender_role,
            message_type=MessageType.ROUND_START,
            data={
                "round_number": self._current_round,
                "round_type": self._current_type.value if self._current_type else None,
                "adversarial_cycle": self._adversarial_cycle_count,
                "cycles_remaining": self.adversarial_cycles_remaining,
            },
            broadcast=True,
            round_number=self._current_round,
        )

    def create_round_end_message(
        self,
        summary: RoundSummary,
        sender_role: str = "Arbiter",
    ) -> Message:
        """Create a control message signaling round end."""
        return create_control_message(
            sender_role=sender_role,
            message_type=MessageType.ROUND_END,
            data={
                "round_number": self._current_round,
                "round_type": summary.round_type.value,
                "resolution_rate": summary.resolution_rate,
                "consensus_reached": summary.consensus_reached,
                "has_blocking_issues": summary.has_blocking_issues,
                "next_round_type": (
                    self.get_next_round_type().value
                    if self.get_next_round_type() else None
                ),
            },
            broadcast=True,
            round_number=self._current_round,
        )

    def is_round_expired(self) -> bool:
        """Check if the current round has exceeded its deadline."""
        if not self._round_deadline:
            return False
        return datetime.now(timezone.utc) > self._round_deadline
