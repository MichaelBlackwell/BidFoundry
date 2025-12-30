"""
Document Generation Workflow

Defines the workflow configuration and execution logic for generating
documents through the adversarial swarm.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any, Callable, Awaitable
import logging

from agents.types import AgentRole, AgentCategory
from agents.registry import AgentRegistry
from agents.base import SwarmContext, AbstractAgent

from comms.bus import MessageBus
from comms.history import ConversationHistory
from comms.round import RoundManager, RoundType, RoundSummary


logger = logging.getLogger(__name__)


class WorkflowPhase(str, Enum):
    """Phases of the document generation workflow."""

    INITIALIZATION = "Initialization"
    BLUE_BUILD = "BlueBuild"
    RED_ATTACK = "RedAttack"
    BLUE_DEFENSE = "BlueDefense"
    SYNTHESIS = "Synthesis"
    FINALIZATION = "Finalization"
    COMPLETE = "Complete"
    ERROR = "Error"


class WorkflowStatus(str, Enum):
    """Status of the workflow execution."""

    PENDING = "Pending"
    RUNNING = "Running"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


@dataclass
class WorkflowConfig:
    """
    Configuration for document generation workflow.

    Specifies which agents to use, how many rounds to run,
    and thresholds for consensus and confidence.
    """

    document_type: str = "General"

    # Round configuration
    max_adversarial_rounds: int = 3
    min_adversarial_rounds: int = 1

    # Threshold configuration
    consensus_threshold: float = 0.80
    confidence_threshold: float = 0.70
    early_termination_threshold: float = 0.95

    # Agent configuration
    required_blue_agents: List[AgentRole] = field(default_factory=list)
    optional_blue_agents: List[AgentRole] = field(default_factory=list)
    required_red_agents: List[AgentRole] = field(default_factory=list)
    optional_red_agents: List[AgentRole] = field(default_factory=list)

    # Section configuration
    required_sections: List[str] = field(default_factory=list)
    optional_sections: List[str] = field(default_factory=list)

    # Timing configuration
    max_round_duration_seconds: float = 300.0
    max_total_duration_seconds: float = 3600.0

    # Feature flags
    enable_parallel_agents: bool = True
    enable_early_termination: bool = True
    enable_human_escalation: bool = True

    def to_dict(self) -> dict:
        return {
            "document_type": self.document_type,
            "max_adversarial_rounds": self.max_adversarial_rounds,
            "min_adversarial_rounds": self.min_adversarial_rounds,
            "consensus_threshold": self.consensus_threshold,
            "confidence_threshold": self.confidence_threshold,
            "early_termination_threshold": self.early_termination_threshold,
            "required_blue_agents": [r.value for r in self.required_blue_agents],
            "optional_blue_agents": [r.value for r in self.optional_blue_agents],
            "required_red_agents": [r.value for r in self.required_red_agents],
            "optional_red_agents": [r.value for r in self.optional_red_agents],
            "required_sections": self.required_sections,
            "optional_sections": self.optional_sections,
            "max_round_duration_seconds": self.max_round_duration_seconds,
            "max_total_duration_seconds": self.max_total_duration_seconds,
            "enable_parallel_agents": self.enable_parallel_agents,
            "enable_early_termination": self.enable_early_termination,
            "enable_human_escalation": self.enable_human_escalation,
        }


@dataclass
class WorkflowState:
    """
    Runtime state of a workflow execution.

    Tracks current phase, progress, and accumulated results.
    """

    workflow_id: str = ""
    config: Optional[WorkflowConfig] = None

    # Current state
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_phase: WorkflowPhase = WorkflowPhase.INITIALIZATION
    current_round: int = 0
    adversarial_cycle: int = 0

    # Accumulated data
    section_drafts: Dict[str, str] = field(default_factory=dict)
    all_critiques: List[Dict[str, Any]] = field(default_factory=list)
    all_responses: List[Dict[str, Any]] = field(default_factory=list)

    # Metrics
    phase_durations: Dict[str, float] = field(default_factory=dict)
    agent_call_counts: Dict[str, int] = field(default_factory=dict)

    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def is_running(self) -> bool:
        return self.status == WorkflowStatus.RUNNING

    @property
    def is_complete(self) -> bool:
        return self.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED)

    @property
    def duration_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "config": self.config.to_dict() if self.config else None,
            "status": self.status.value,
            "current_phase": self.current_phase.value,
            "current_round": self.current_round,
            "adversarial_cycle": self.adversarial_cycle,
            "section_count": len(self.section_drafts),
            "critique_count": len(self.all_critiques),
            "response_count": len(self.all_responses),
            "phase_durations": self.phase_durations,
            "agent_call_counts": self.agent_call_counts,
            "errors": self.errors,
            "warnings": self.warnings,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


# Type for workflow event handlers
WorkflowEventHandler = Callable[[WorkflowState, WorkflowPhase], Awaitable[None]]


class DocumentWorkflow:
    """
    Manages the execution of document generation workflows.

    Coordinates agents, manages state transitions, and handles
    errors during document generation.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        message_bus: MessageBus,
        history: ConversationHistory,
        round_manager: RoundManager,
    ):
        """
        Initialize the workflow manager.

        Args:
            registry: Agent registry for creating agents
            message_bus: Message bus for communication
            history: Conversation history tracker
            round_manager: Round lifecycle manager
        """
        self._registry = registry
        self._message_bus = message_bus
        self._history = history
        self._round_manager = round_manager
        self._logger = logging.getLogger("DocumentWorkflow")

        # Event handlers
        self._on_phase_start: Optional[WorkflowEventHandler] = None
        self._on_phase_end: Optional[WorkflowEventHandler] = None
        self._on_error: Optional[Callable[[WorkflowState, Exception], Awaitable[None]]] = None

    def set_event_handlers(
        self,
        on_phase_start: Optional[WorkflowEventHandler] = None,
        on_phase_end: Optional[WorkflowEventHandler] = None,
        on_error: Optional[Callable[[WorkflowState, Exception], Awaitable[None]]] = None,
    ) -> None:
        """Set event handlers for workflow phases."""
        self._on_phase_start = on_phase_start
        self._on_phase_end = on_phase_end
        self._on_error = on_error

    async def execute(
        self,
        context: SwarmContext,
        config: WorkflowConfig,
    ) -> WorkflowState:
        """
        Execute a complete document generation workflow.

        Args:
            context: Initial swarm context
            config: Workflow configuration

        Returns:
            Final workflow state
        """
        state = WorkflowState(
            workflow_id=context.request_id,
            config=config,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Phase 1: Initialization
            await self._execute_phase(state, WorkflowPhase.INITIALIZATION, context)

            # Phase 2: Blue Build
            await self._execute_phase(state, WorkflowPhase.BLUE_BUILD, context)

            # Phases 3-4: Adversarial cycles
            while state.adversarial_cycle < config.max_adversarial_rounds:
                state.adversarial_cycle += 1

                # Red Attack
                await self._execute_phase(state, WorkflowPhase.RED_ATTACK, context)

                # Check if any critiques were generated
                if not self._has_new_critiques(state):
                    self._logger.info("No new critiques, ending adversarial phase")
                    break

                # Blue Defense
                await self._execute_phase(state, WorkflowPhase.BLUE_DEFENSE, context)

                # Check for early termination
                if config.enable_early_termination:
                    if self._should_terminate_early(state, config):
                        self._logger.info("Early termination criteria met")
                        break

            # Phase 5: Synthesis
            await self._execute_phase(state, WorkflowPhase.SYNTHESIS, context)

            # Phase 6: Finalization
            await self._execute_phase(state, WorkflowPhase.FINALIZATION, context)

            state.status = WorkflowStatus.COMPLETED
            state.current_phase = WorkflowPhase.COMPLETE

        except Exception as e:
            state.status = WorkflowStatus.FAILED
            state.current_phase = WorkflowPhase.ERROR
            state.errors.append(str(e))
            self._logger.error(f"Workflow failed: {e}")

            if self._on_error:
                await self._on_error(state, e)

        finally:
            state.completed_at = datetime.now(timezone.utc)

        return state

    async def _execute_phase(
        self,
        state: WorkflowState,
        phase: WorkflowPhase,
        context: SwarmContext,
    ) -> None:
        """
        Execute a single workflow phase.

        Args:
            state: Current workflow state
            phase: Phase to execute
            context: Swarm context
        """
        phase_start = datetime.now(timezone.utc)
        state.current_phase = phase

        self._logger.info(f"Starting phase: {phase.value}")

        if self._on_phase_start:
            await self._on_phase_start(state, phase)

        try:
            if phase == WorkflowPhase.INITIALIZATION:
                await self._phase_initialization(state, context)
            elif phase == WorkflowPhase.BLUE_BUILD:
                await self._phase_blue_build(state, context)
            elif phase == WorkflowPhase.RED_ATTACK:
                await self._phase_red_attack(state, context)
            elif phase == WorkflowPhase.BLUE_DEFENSE:
                await self._phase_blue_defense(state, context)
            elif phase == WorkflowPhase.SYNTHESIS:
                await self._phase_synthesis(state, context)
            elif phase == WorkflowPhase.FINALIZATION:
                await self._phase_finalization(state, context)

        finally:
            phase_duration = (datetime.now(timezone.utc) - phase_start).total_seconds()
            state.phase_durations[phase.value] = phase_duration

            if self._on_phase_end:
                await self._on_phase_end(state, phase)

    async def _phase_initialization(
        self,
        state: WorkflowState,
        context: SwarmContext,
    ) -> None:
        """Initialize the workflow."""
        # Validate configuration
        config = state.config

        # Check required agents are available
        for role in config.required_blue_agents:
            if not self._registry.is_registered(role):
                state.warnings.append(f"Required blue agent not registered: {role.value}")

        for role in config.required_red_agents:
            if not self._registry.is_registered(role):
                state.warnings.append(f"Required red agent not registered: {role.value}")

        # Initialize agents
        for role in config.required_blue_agents + config.optional_blue_agents:
            if self._registry.is_registered(role):
                agent = self._registry.create(role)
                await agent.initialize()

        for role in config.required_red_agents + config.optional_red_agents:
            if self._registry.is_registered(role):
                agent = self._registry.create(role)
                await agent.initialize()

    async def _phase_blue_build(
        self,
        state: WorkflowState,
        context: SwarmContext,
    ) -> None:
        """Execute the blue build phase."""
        config = state.config

        # Get blue team agents
        blue_agents = self._get_agents_for_phase(
            config.required_blue_agents,
            config.optional_blue_agents,
        )

        # Start round
        state.current_round = self._round_manager.start_round(RoundType.BLUE_BUILD)
        context.round_number = state.current_round
        context.round_type = RoundType.BLUE_BUILD.value

        # Run agents
        for agent in blue_agents:
            try:
                output = await agent.process(context)
                state.agent_call_counts[agent.role.value] = (
                    state.agent_call_counts.get(agent.role.value, 0) + 1
                )

                if output.success and output.sections:
                    state.section_drafts.update(output.sections)
                    context.section_drafts.update(output.sections)

            except Exception as e:
                state.warnings.append(f"Agent {agent.name} failed: {e}")
                self._logger.warning(f"Agent {agent.name} failed: {e}")

        # End round
        self._round_manager.end_round()

    async def _phase_red_attack(
        self,
        state: WorkflowState,
        context: SwarmContext,
    ) -> None:
        """Execute the red attack phase."""
        config = state.config

        # Get red team agents
        red_agents = self._get_agents_for_phase(
            config.required_red_agents,
            config.optional_red_agents,
        )

        # Start round
        state.current_round = self._round_manager.start_round(RoundType.RED_ATTACK)
        context.round_number = state.current_round
        context.round_type = RoundType.RED_ATTACK.value

        cycle_critiques = []

        # Run agents
        for agent in red_agents:
            try:
                output = await agent.process(context)
                state.agent_call_counts[agent.role.value] = (
                    state.agent_call_counts.get(agent.role.value, 0) + 1
                )

                if output.success and output.critiques:
                    cycle_critiques.extend(output.critiques)

            except Exception as e:
                state.warnings.append(f"Agent {agent.name} failed: {e}")
                self._logger.warning(f"Agent {agent.name} failed: {e}")

        # Store critiques
        state.all_critiques.extend(cycle_critiques)
        context.pending_critiques = cycle_critiques

        # End round
        self._round_manager.end_round()

    async def _phase_blue_defense(
        self,
        state: WorkflowState,
        context: SwarmContext,
    ) -> None:
        """Execute the blue defense phase."""
        config = state.config

        # Get blue team agents (primarily Strategy Architect for defense)
        blue_agents = self._get_agents_for_phase(
            config.required_blue_agents,
            config.optional_blue_agents,
        )

        # Start round
        state.current_round = self._round_manager.start_round(RoundType.BLUE_DEFENSE)
        context.round_number = state.current_round
        context.round_type = RoundType.BLUE_DEFENSE.value

        cycle_responses = []

        # Run primary responder (Strategy Architect)
        for agent in blue_agents:
            if agent.role == AgentRole.STRATEGY_ARCHITECT:
                try:
                    output = await agent.process(context)
                    state.agent_call_counts[agent.role.value] = (
                        state.agent_call_counts.get(agent.role.value, 0) + 1
                    )

                    if output.success:
                        if output.responses:
                            cycle_responses.extend(output.responses)
                        if output.sections:
                            state.section_drafts.update(output.sections)
                            context.section_drafts.update(output.sections)

                except Exception as e:
                    state.warnings.append(f"Agent {agent.name} failed: {e}")
                    self._logger.warning(f"Agent {agent.name} failed: {e}")
                break

        # Store responses
        state.all_responses.extend(cycle_responses)

        # Update context
        resolved_ids = {r.get("critique_id") for r in cycle_responses}
        context.resolved_critiques.extend([
            c for c in context.pending_critiques
            if c.get("id") in resolved_ids
        ])
        context.pending_critiques = [
            c for c in context.pending_critiques
            if c.get("id") not in resolved_ids
        ]

        # End round with consensus check
        self._round_manager.end_round(check_consensus=True)

    async def _phase_synthesis(
        self,
        state: WorkflowState,
        context: SwarmContext,
    ) -> None:
        """Execute the synthesis phase."""
        # Start round
        state.current_round = self._round_manager.start_round(RoundType.SYNTHESIS)
        context.round_number = state.current_round
        context.round_type = RoundType.SYNTHESIS.value

        # Synthesis is handled by the Arbiter directly
        # This phase marks completion of adversarial rounds

        # End round
        self._round_manager.end_round(check_consensus=False)

    async def _phase_finalization(
        self,
        state: WorkflowState,
        context: SwarmContext,
    ) -> None:
        """Execute the finalization phase."""
        # Cleanup agents
        config = state.config

        all_agents = (
            config.required_blue_agents +
            config.optional_blue_agents +
            config.required_red_agents +
            config.optional_red_agents
        )

        for role in all_agents:
            if self._registry.is_registered(role):
                try:
                    agent = self._registry.get_cached_instance(role)
                    if agent:
                        await agent.cleanup()
                except Exception as e:
                    self._logger.warning(f"Cleanup failed for {role.value}: {e}")

    def _get_agents_for_phase(
        self,
        required: List[AgentRole],
        optional: List[AgentRole],
    ) -> List[AbstractAgent]:
        """Get agents for a workflow phase."""
        agents = []

        # Add required agents
        for role in required:
            try:
                agent = self._registry.create(role)
                if agent.is_enabled:
                    agents.append(agent)
            except Exception as e:
                self._logger.warning(f"Could not create required agent {role}: {e}")

        # Add optional agents
        for role in optional:
            try:
                agent = self._registry.create(role)
                if agent.is_enabled:
                    agents.append(agent)
            except Exception:
                pass  # Optional agents failing is fine

        # Sort by priority
        return sorted(agents, key=lambda a: a.priority, reverse=True)

    def _has_new_critiques(self, state: WorkflowState) -> bool:
        """Check if the last red attack produced new critiques."""
        # Count critiques from the current adversarial cycle
        # This is a simplified check - in practice you'd want to track
        # critiques per cycle more explicitly
        return len(state.all_critiques) > 0

    def _should_terminate_early(
        self,
        state: WorkflowState,
        config: WorkflowConfig,
    ) -> bool:
        """
        Check if the workflow should terminate early.

        Returns True if:
        - All critiques have been resolved
        - Resolution rate exceeds early termination threshold
        - Minimum adversarial rounds have been completed
        """
        if state.adversarial_cycle < config.min_adversarial_rounds:
            return False

        if not state.all_critiques:
            return True

        # Calculate resolution rate
        resolved = len([
            r for r in state.all_responses
            if r.get("disposition") in ("Accept", "Partial Accept", "Rebut", "Acknowledge")
        ])
        rate = resolved / len(state.all_critiques)

        return rate >= config.early_termination_threshold
