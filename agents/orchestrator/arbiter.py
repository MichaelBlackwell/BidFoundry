"""
Arbiter Agent

The master orchestrator that manages the adversarial debate workflow,
coordinates blue and red team agents, detects consensus, and synthesizes
final documents.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set

from agents.base import OrchestratorAgent, SwarmContext, AgentOutput
from agents.types import AgentRole, AgentCategory
from agents.config import AgentConfig, get_default_config
from agents.registry import AgentRegistry, get_registry

from comms.bus import MessageBus
from comms.history import ConversationHistory
from comms.round import RoundManager, RoundType, RoundSummary
from comms.message import (
    Message, MessageType, MessagePayload,
    create_control_message, create_draft_message, create_status_message
)

from models.confidence import (
    ConfidenceScore, SectionConfidence, ConfidenceThresholds, RiskFlag
)

from .workflow import DocumentWorkflow, WorkflowConfig
from .consensus import ConsensusDetector, ConsensusResult
from .synthesis import DocumentSynthesizer


logger = logging.getLogger(__name__)


@dataclass
class DocumentRequest:
    """
    A request to generate a document through the adversarial workflow.
    """

    id: str = ""
    document_type: str = ""
    company_profile: Dict[str, Any] = field(default_factory=dict)
    opportunity: Optional[Dict[str, Any]] = None

    # Configuration overrides
    max_adversarial_rounds: int = 3
    consensus_threshold: float = 0.80
    confidence_threshold: float = 0.70

    # Optional section focus
    target_sections: List[str] = field(default_factory=list)

    # Metadata
    requested_by: str = ""
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_type": self.document_type,
            "company_profile": self.company_profile,
            "opportunity": self.opportunity,
            "max_adversarial_rounds": self.max_adversarial_rounds,
            "consensus_threshold": self.consensus_threshold,
            "confidence_threshold": self.confidence_threshold,
            "target_sections": self.target_sections,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
        }


@dataclass
class FinalOutput:
    """
    The complete output from the adversarial workflow.
    """

    request_id: str = ""
    document_type: str = ""

    # Final document
    document: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, str] = field(default_factory=dict)

    # Reports
    confidence: Optional[ConfidenceScore] = None
    red_team_report: Dict[str, Any] = field(default_factory=dict)

    # Blue team contributions (from all agents during defense rounds)
    blue_team_contributions: List[Dict[str, Any]] = field(default_factory=list)

    # Status
    success: bool = True
    requires_human_review: bool = False
    review_reasons: List[str] = field(default_factory=list)

    # Metrics
    total_rounds: int = 0
    total_critiques: int = 0
    resolved_critiques: int = 0
    consensus_reached: bool = False

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "document_type": self.document_type,
            "document": self.document,
            "sections": self.sections,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "red_team_report": self.red_team_report,
            "blue_team_contributions": self.blue_team_contributions,
            "success": self.success,
            "requires_human_review": self.requires_human_review,
            "review_reasons": self.review_reasons,
            "total_rounds": self.total_rounds,
            "total_critiques": self.total_critiques,
            "resolved_critiques": self.resolved_critiques,
            "consensus_reached": self.consensus_reached,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


class ArbiterAgent(OrchestratorAgent):
    """
    The Arbiter is the master orchestrator of the adversarial swarm.

    It coordinates the full document generation workflow:
    1. Routes requests to appropriate agent configurations
    2. Manages debate rounds (BlueBuild -> RedAttack -> BlueDefense)
    3. Detects consensus and terminates early when appropriate
    4. Forces resolution on contested points
    5. Synthesizes final documents with confidence ratings
    6. Generates Red Team Reports for transparency
    7. Triggers human escalation when thresholds are breached
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Arbiter agent.

        Args:
            config: Optional agent configuration
        """
        effective_config = config or get_default_config(AgentRole.ARBITER)
        super().__init__(effective_config)

        # Core components
        self._registry: Optional[AgentRegistry] = None
        self._message_bus: Optional[MessageBus] = None
        self._history: Optional[ConversationHistory] = None
        self._round_manager: Optional[RoundManager] = None

        # Workflow components
        self._workflow: Optional[DocumentWorkflow] = None
        self._consensus_detector: Optional[ConsensusDetector] = None
        self._synthesizer: Optional[DocumentSynthesizer] = None

        # State tracking
        self._current_request: Optional[DocumentRequest] = None
        self._current_context: Optional[SwarmContext] = None
        self._current_draft: Dict[str, str] = {}
        self._all_critiques: List[Dict[str, Any]] = []
        self._all_responses: List[Dict[str, Any]] = []
        self._blue_team_contributions: List[Dict[str, Any]] = []

        # Configuration
        self._workflow_config: Optional[WorkflowConfig] = None

    @property
    def role(self) -> AgentRole:
        return AgentRole.ARBITER

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.ORCHESTRATOR

    async def initialize(
        self,
        registry: Optional[AgentRegistry] = None,
        message_bus: Optional[MessageBus] = None,
    ) -> None:
        """
        Initialize the Arbiter with required components.

        Args:
            registry: Agent registry for creating agents
            message_bus: Message bus for communication
        """
        await super().initialize()

        self._registry = registry or get_registry()
        self._message_bus = message_bus or MessageBus()
        self._history = ConversationHistory()
        self._round_manager = RoundManager(
            history=self._history,
            max_adversarial_rounds=3,
            consensus_threshold=0.80,
        )

        # Initialize workflow components
        self._consensus_detector = ConsensusDetector()
        self._synthesizer = DocumentSynthesizer()

        self.log_info("Arbiter initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._message_bus:
            await self._message_bus.stop()
        await super().cleanup()

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process a document generation request.

        This is called when the Arbiter is used as a regular agent
        in a pipeline. For full workflow control, use generate_document().

        Args:
            context: The swarm context with request details

        Returns:
            AgentOutput with the orchestration results
        """
        start_time = datetime.now(timezone.utc)

        # Create a request from context
        request = DocumentRequest(
            id=context.request_id,
            document_type=context.document_type or "General",
            company_profile=context.company_profile or {},
            opportunity=context.opportunity,
        )

        try:
            # Run the full workflow
            output = await self.generate_document(request)

            return self._create_output(
                content=f"Document generated successfully. Confidence: {output.confidence.overall_score:.2f}" if output.confidence else "Document generated",
                success=output.success,
                sections=output.sections,
                metadata={
                    "total_rounds": output.total_rounds,
                    "consensus_reached": output.consensus_reached,
                    "requires_human_review": output.requires_human_review,
                },
            )

        except Exception as e:
            self.log_error(f"Document generation failed: {e}")
            return self._create_output(
                content="",
                success=False,
                error_message=str(e),
            )

    async def generate_document(self, request: DocumentRequest) -> FinalOutput:
        """
        Generate a document through the full adversarial workflow.

        This is the main entry point for document generation.

        Args:
            request: The document generation request

        Returns:
            FinalOutput containing the document and all reports
        """
        output = FinalOutput(
            request_id=request.id,
            document_type=request.document_type,
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Initialize for this request
            await self._setup_for_request(request)

            # Start message bus
            await self._message_bus.start()

            # Create workflow
            self._workflow = DocumentWorkflow(
                registry=self._registry,
                message_bus=self._message_bus,
                history=self._history,
                round_manager=self._round_manager,
            )

            # Get workflow configuration for document type
            self._workflow_config = self._get_workflow_config(request)

            # Phase 1: Blue Team Build
            self.log_info(f"Starting BlueBuild phase for {request.document_type}")
            draft = await self._run_blue_team_build()
            self._current_draft = draft

            # Early validation: check if blue team produced any content
            if not draft or len(draft) == 0:
                self.log_error("Blue team build phase produced no content")
                output.success = False
                output.requires_human_review = True
                output.review_reasons.append(
                    "Blue team failed to generate initial draft. "
                    "This may indicate an LLM API configuration issue (missing API key) "
                    "or a problem with the document type configuration."
                )
                # Skip remaining phases since we have no content to work with
                output.completed_at = datetime.now(timezone.utc)
                await self._message_bus.stop()
                return output

            # Phase 2: Adversarial Rounds
            adversarial_round = 0
            while adversarial_round < request.max_adversarial_rounds:
                adversarial_round += 1
                self.log_info(f"Starting adversarial cycle {adversarial_round}")

                # Red Team Attack
                critiques = await self._run_red_team_attack()
                self._all_critiques.extend(critiques)

                if not critiques:
                    self.log_info("No critiques generated, ending adversarial phase")
                    break

                # Blue Team Defense
                responses = await self._run_blue_team_defense(critiques)
                self._all_responses.extend(responses)

                # Apply accepted changes
                self._current_draft = await self._apply_accepted_changes(
                    self._current_draft, responses
                )

                # Check consensus
                consensus = self._check_consensus()
                if consensus.reached:
                    self.log_info(
                        f"Consensus reached in cycle {adversarial_round} "
                        f"(confidence: {consensus.confidence:.2f})"
                    )
                    output.consensus_reached = True
                    break

            # Phase 3: Synthesis
            self.log_info("Starting synthesis phase")
            final_document = await self._run_synthesis()

            # Phase 4: Confidence Scoring
            confidence = self._calculate_confidence(final_document)

            # Phase 5: Generate Reports
            red_team_report = self._generate_red_team_report()

            # Populate output
            output.document = final_document
            output.sections = self._current_draft
            output.confidence = confidence
            output.red_team_report = red_team_report
            output.blue_team_contributions = self._blue_team_contributions
            output.total_rounds = self._round_manager.current_round
            output.total_critiques = len(self._all_critiques)
            output.resolved_critiques = len([
                r for r in self._all_responses
                if r.get("disposition") in ("Accept", "Partial Accept", "Rebut")
            ])

            # Check for human review requirement
            if confidence.requires_human_review:
                output.requires_human_review = True
                output.review_reasons = confidence.review_reasons

            # Validate that we have actual content before marking as successful
            has_content = self._current_draft and len(self._current_draft) > 0
            if not has_content:
                self.log_error("Generation completed but no content was produced")
                output.success = False
                output.review_reasons.append("No content was generated")
                output.requires_human_review = True
            else:
                output.success = True

        except Exception as e:
            self.log_error(f"Workflow failed: {e}")
            output.success = False
            output.review_reasons.append(f"Workflow error: {str(e)}")
            output.requires_human_review = True

        finally:
            # Cleanup
            await self._message_bus.stop()
            output.completed_at = datetime.now(timezone.utc)

        return output

    async def _setup_for_request(self, request: DocumentRequest) -> None:
        """Set up internal state for a new request."""
        self._current_request = request

        # Reset state
        self._current_draft = {}
        self._all_critiques = []
        self._all_responses = []
        self._blue_team_contributions = []

        # Configure round manager
        self._round_manager = RoundManager(
            history=self._history,
            max_adversarial_rounds=request.max_adversarial_rounds,
            consensus_threshold=request.consensus_threshold,
        )

        # Create context
        self._current_context = SwarmContext(
            request_id=request.id,
            document_type=request.document_type,
            company_profile=request.company_profile,
            opportunity=request.opportunity,
            target_sections=request.target_sections,
        )

    def _get_workflow_config(self, request: DocumentRequest) -> WorkflowConfig:
        """Get workflow configuration for a document type."""
        # Default configuration
        config = WorkflowConfig(
            document_type=request.document_type,
            max_adversarial_rounds=request.max_adversarial_rounds,
            consensus_threshold=request.consensus_threshold,
            confidence_threshold=request.confidence_threshold,
        )

        # Document-type specific overrides
        document_configs = {
            "Capability Statement": WorkflowConfig(
                document_type="Capability Statement",
                max_adversarial_rounds=2,
                required_blue_agents=[
                    AgentRole.STRATEGY_ARCHITECT,
                    AgentRole.COMPLIANCE_NAVIGATOR,
                ],
                required_red_agents=[
                    AgentRole.DEVILS_ADVOCATE,
                    AgentRole.EVALUATOR_SIMULATOR,
                ],
            ),
            "Proposal Strategy": WorkflowConfig(
                document_type="Proposal Strategy",
                max_adversarial_rounds=3,
                required_blue_agents=[
                    AgentRole.STRATEGY_ARCHITECT,
                    AgentRole.CAPTURE_STRATEGIST,
                    AgentRole.COMPLIANCE_NAVIGATOR,
                ],
                required_red_agents=[
                    AgentRole.DEVILS_ADVOCATE,
                    AgentRole.COMPETITOR_SIMULATOR,
                    AgentRole.EVALUATOR_SIMULATOR,
                    AgentRole.RISK_ASSESSOR,
                ],
            ),
            "Competitive Analysis": WorkflowConfig(
                document_type="Competitive Analysis",
                max_adversarial_rounds=2,
                required_blue_agents=[
                    AgentRole.STRATEGY_ARCHITECT,
                    AgentRole.MARKET_ANALYST,
                    AgentRole.CAPTURE_STRATEGIST,
                ],
                required_red_agents=[
                    AgentRole.COMPETITOR_SIMULATOR,
                    AgentRole.DEVILS_ADVOCATE,
                ],
            ),
        }

        return document_configs.get(request.document_type, config)

    async def _run_blue_team_build(self) -> Dict[str, str]:
        """
        Execute the BlueBuild phase.

        Creates the initial document draft using blue team agents.

        Returns:
            Dictionary mapping section names to content
        """
        # Start round
        round_num = self._round_manager.start_round(RoundType.BLUE_BUILD)

        # Publish round start
        start_msg = self._round_manager.create_round_start_message(
            sender_role=self.role.value
        )
        await self._message_bus.publish(start_msg)

        # Update context
        self._current_context.round_number = round_num
        self._current_context.round_type = RoundType.BLUE_BUILD.value

        # Get blue team agents
        blue_agents = self._get_blue_team_agents()

        sections = {}

        # Run each blue team agent
        for agent in blue_agents:
            try:
                self.log_debug(f"Running blue team agent: {agent.name}")

                # Emit agent thinking status
                thinking_msg = create_status_message(
                    sender_role=agent.role.value,
                    status_type="agent_thinking",
                    data={"target": "Initial draft generation"},
                    round_number=round_num,
                )
                await self._message_bus.publish(thinking_msg)

                # Set up streaming callback for real-time output
                async def stream_handler(chunk: str, agent_role: str = agent.role.value, rn: int = round_num):
                    stream_msg = create_status_message(
                        sender_role=agent_role,
                        status_type="agent_streaming",
                        data={"chunk": chunk},
                        round_number=rn,
                    )
                    await self._message_bus.publish(stream_msg)

                # Wrap async handler for sync callback
                def sync_stream_callback(chunk: str, handler=stream_handler):
                    asyncio.create_task(handler(chunk))

                agent.set_stream_callback(sync_stream_callback)

                output = await agent.process(self._current_context)

                # Clear callback after processing
                agent.set_stream_callback(None)

                if not output.success:
                    # Log the failure with error details
                    error_msg = output.error_message or "Unknown error"
                    self.log_error(f"Blue team agent {agent.name} failed: {error_msg}")
                elif output.sections:
                    sections.update(output.sections)

                    # Publish draft message
                    for section_name, content in output.sections.items():
                        msg = create_draft_message(
                            sender_role=agent.role.value,
                            content=content,
                            document_id=self._current_request.id,
                            section_name=section_name,
                            round_number=round_num,
                        )
                        await self._message_bus.publish(msg)
                        self._history.record_message(msg)
                else:
                    self.log_warning(f"Blue team agent {agent.name} succeeded but returned no sections")

            except Exception as e:
                self.log_error(f"Blue team agent {agent.name} failed with exception: {e}")

        # Update context with draft
        self._current_context.section_drafts = sections

        # End round
        summary = self._round_manager.end_round()

        # Publish round end
        end_msg = self._round_manager.create_round_end_message(
            summary=summary,
            sender_role=self.role.value,
        )
        await self._message_bus.publish(end_msg)

        return sections

    async def _run_red_team_attack(self) -> List[Dict[str, Any]]:
        """
        Execute the RedAttack phase.

        Red team agents critique the current draft.

        Returns:
            List of critique dictionaries
        """
        # Start round
        round_num = self._round_manager.start_round(RoundType.RED_ATTACK)

        # Publish round start
        start_msg = self._round_manager.create_round_start_message(
            sender_role=self.role.value
        )
        await self._message_bus.publish(start_msg)

        # Update context
        self._current_context.round_number = round_num
        self._current_context.round_type = RoundType.RED_ATTACK.value

        # Get red team agents
        red_agents = self._get_red_team_agents()

        all_critiques = []

        # Run each red team agent
        for agent in red_agents:
            try:
                self.log_debug(f"Running red team agent: {agent.name}")

                # Emit agent thinking status
                thinking_msg = create_status_message(
                    sender_role=agent.role.value,
                    status_type="agent_thinking",
                    data={"target": "Analyzing document for critiques"},
                    round_number=round_num,
                )
                await self._message_bus.publish(thinking_msg)

                # Set up streaming callback for real-time output
                async def stream_handler(chunk: str, agent_role: str = agent.role.value, rn: int = round_num):
                    stream_msg = create_status_message(
                        sender_role=agent_role,
                        status_type="agent_streaming",
                        data={"chunk": chunk},
                        round_number=rn,
                    )
                    await self._message_bus.publish(stream_msg)

                def sync_stream_callback(chunk: str, handler=stream_handler):
                    asyncio.create_task(handler(chunk))

                agent.set_stream_callback(sync_stream_callback)

                output = await agent.process(self._current_context)

                agent.set_stream_callback(None)

                if output.success and output.critiques:
                    # Record critiques in history and track message IDs
                    for critique in output.critiques:
                        from comms.message import create_critique_message
                        msg = create_critique_message(
                            sender_role=agent.role.value,
                            critique_data=critique,
                            parent_message_id=self._current_request.id,
                            round_number=round_num,
                        )
                        await self._message_bus.publish(msg)
                        self._history.record_message(msg)

                        # Store message_id in critique for response linking
                        critique["message_id"] = msg.id
                        all_critiques.append(critique)

            except Exception as e:
                self.log_error(f"Red team agent {agent.name} failed: {e}")

        # Update context with pending critiques
        self._current_context.pending_critiques = all_critiques

        # End round
        summary = self._round_manager.end_round()

        # Publish round end
        end_msg = self._round_manager.create_round_end_message(
            summary=summary,
            sender_role=self.role.value,
        )
        await self._message_bus.publish(end_msg)

        return all_critiques

    async def _run_blue_team_defense(
        self,
        critiques: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute the BlueDefense phase.

        Blue team responds to red team critiques.

        Args:
            critiques: List of critiques to respond to

        Returns:
            List of response dictionaries
        """
        # Start round
        round_num = self._round_manager.start_round(RoundType.BLUE_DEFENSE)

        # Publish round start
        start_msg = self._round_manager.create_round_start_message(
            sender_role=self.role.value
        )
        await self._message_bus.publish(start_msg)

        # Update context
        self._current_context.round_number = round_num
        self._current_context.round_type = RoundType.BLUE_DEFENSE.value
        self._current_context.pending_critiques = critiques

        # Get blue team agents (Strategy Architect handles responses)
        blue_agents = self._get_blue_team_agents()

        all_responses = []

        # Primary responder is Strategy Architect
        primary_responder = None
        for agent in blue_agents:
            if agent.role == AgentRole.STRATEGY_ARCHITECT:
                primary_responder = agent
                break

        if primary_responder:
            try:
                self.log_debug("Strategy Architect responding to critiques")

                # Emit agent thinking status
                thinking_msg = create_status_message(
                    sender_role=primary_responder.role.value,
                    status_type="agent_thinking",
                    data={"target": "Responding to critiques"},
                    round_number=round_num,
                )
                await self._message_bus.publish(thinking_msg)

                # Set up streaming callback for real-time output
                async def stream_handler(chunk: str, agent_role: str = primary_responder.role.value, rn: int = round_num):
                    stream_msg = create_status_message(
                        sender_role=agent_role,
                        status_type="agent_streaming",
                        data={"chunk": chunk},
                        round_number=rn,
                    )
                    await self._message_bus.publish(stream_msg)

                def sync_stream_callback(chunk: str, handler=stream_handler):
                    asyncio.create_task(handler(chunk))

                primary_responder.set_stream_callback(sync_stream_callback)

                output = await primary_responder.process(self._current_context)

                primary_responder.set_stream_callback(None)

                if output.success and output.responses:
                    all_responses.extend(output.responses)

                    # Record responses in history
                    for response in output.responses:
                        from comms.message import create_response_message
                        # Use message_id for linking responses to critique messages
                        critique_message_id = response.get("message_id", response.get("critique_id", ""))
                        msg = create_response_message(
                            sender_role=primary_responder.role.value,
                            response_data=response,
                            critique_message_id=critique_message_id,
                            round_number=round_num,
                        )
                        await self._message_bus.publish(msg)
                        self._history.record_message(msg)

            except Exception as e:
                self.log_error(f"Defense phase failed: {e}")

        # Run all other blue team agents to capture their analysis contributions
        for agent in blue_agents:
            if agent.role != AgentRole.STRATEGY_ARCHITECT:
                try:
                    self.log_debug(f"Running blue team agent for analysis: {agent.name}")

                    # Emit agent thinking status
                    thinking_msg = create_status_message(
                        sender_role=agent.role.value,
                        status_type="agent_thinking",
                        data={"target": "Generating analysis contribution"},
                        round_number=round_num,
                    )
                    await self._message_bus.publish(thinking_msg)

                    output = await agent.process(self._current_context)

                    if output.success and output.content:
                        contribution = {
                            "agent_role": agent.role.value,
                            "agent_name": agent.name,
                            "content": output.content,
                            "content_type": output.metadata.get("analysis_type", "analysis"),
                            "metadata": output.metadata,
                            "round_number": round_num,
                            "round_type": "BlueDefense",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                        self._blue_team_contributions.append(contribution)
                        self.log_debug(f"Captured contribution from {agent.name}")

                except Exception as e:
                    self.log_error(f"Blue team agent {agent.name} analysis failed: {e}")

        # Move addressed critiques to resolved
        resolved_ids = {r.get("critique_id") for r in all_responses}
        self._current_context.resolved_critiques.extend([
            c for c in critiques if c.get("id") in resolved_ids
        ])
        self._current_context.pending_critiques = [
            c for c in critiques if c.get("id") not in resolved_ids
        ]

        # End round
        summary = self._round_manager.end_round(check_consensus=True)

        # Publish round end
        end_msg = self._round_manager.create_round_end_message(
            summary=summary,
            sender_role=self.role.value,
        )
        await self._message_bus.publish(end_msg)

        return all_responses

    async def _apply_accepted_changes(
        self,
        current_draft: Dict[str, str],
        responses: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Apply accepted critique responses to the draft.

        Args:
            current_draft: Current section drafts
            responses: Blue team responses

        Returns:
            Updated section drafts
        """
        updated_draft = current_draft.copy()

        # Find responses that accepted changes
        accepted_responses = [
            r for r in responses
            if r.get("disposition") in ("Accept", "Partial Accept")
        ]

        if not accepted_responses:
            return updated_draft

        # Get sections that need revision
        sections_to_revise = set()
        for response in accepted_responses:
            critique_id = response.get("critique_id")
            # Find the corresponding critique
            for critique in self._all_critiques:
                if critique.get("id") == critique_id:
                    section = critique.get("target_section")
                    if section:
                        sections_to_revise.add(section)

        # Have Strategy Architect revise affected sections
        if sections_to_revise:
            blue_agents = self._get_blue_team_agents()
            strategy_architect = None
            for agent in blue_agents:
                if agent.role == AgentRole.STRATEGY_ARCHITECT:
                    strategy_architect = agent
                    break

            if strategy_architect and hasattr(strategy_architect, 'revise_section'):
                for section in sections_to_revise:
                    section_critiques = [
                        c for c in self._all_critiques
                        if c.get("target_section") == section
                    ]
                    try:
                        revised = await strategy_architect.revise_section(
                            self._current_context,
                            section,
                            section_critiques,
                        )
                        updated_draft[section] = revised
                    except Exception as e:
                        self.log_error(f"Failed to revise section {section}: {e}")

        # Update context
        self._current_context.section_drafts = updated_draft

        return updated_draft

    async def _run_synthesis(self) -> Dict[str, Any]:
        """
        Execute the Synthesis phase.

        Compile the final document from all debate rounds.

        Returns:
            Final document as a dictionary
        """
        # Start round
        round_num = self._round_manager.start_round(RoundType.SYNTHESIS)

        # Update context
        self._current_context.round_number = round_num
        self._current_context.round_type = RoundType.SYNTHESIS.value

        # Use synthesizer to compile final document
        final_document = await self._synthesizer.synthesize(
            sections=self._current_draft,
            critiques=self._all_critiques,
            responses=self._all_responses,
            context=self._current_context,
            blue_team_contributions=self._blue_team_contributions,
        )

        # End round
        self._round_manager.end_round(check_consensus=False)

        return final_document

    def _check_consensus(self) -> ConsensusResult:
        """
        Check if consensus has been reached.

        Returns:
            ConsensusResult indicating consensus status
        """
        return self._consensus_detector.check(
            critiques=self._all_critiques,
            responses=self._all_responses,
            threshold=self._current_request.consensus_threshold,
        )

    def _calculate_confidence(
        self,
        final_document: Dict[str, Any]
    ) -> ConfidenceScore:
        """
        Calculate confidence scores for the final document.

        Args:
            final_document: The synthesized document

        Returns:
            ConfidenceScore with overall and section scores
        """
        thresholds = ConfidenceThresholds(
            human_review_threshold=self._current_request.confidence_threshold,
        )

        confidence = ConfidenceScore(
            document_id=self._current_request.id,
            document_type=self._current_request.document_type,
            thresholds=thresholds,
        )

        # Calculate section-level confidence
        for section_name, content in self._current_draft.items():
            section_conf = SectionConfidence(
                section_name=section_name,
                base_score=0.85,
            )

            # Get critiques for this section
            section_critiques = [
                c for c in self._all_critiques
                if c.get("target_section") == section_name
            ]

            section_conf.critique_count = len(section_critiques)

            # Apply penalties for unresolved critiques
            for critique in section_critiques:
                critique_id = critique.get("id")
                severity = critique.get("severity", "minor")

                # Check if resolved
                resolved = any(
                    r.get("critique_id") == critique_id
                    for r in self._all_responses
                )

                if not resolved:
                    section_conf.unresolved_critiques += 1
                    if severity == "critical":
                        section_conf.critical_critiques += 1
                        section_conf.apply_adjustment(
                            f"Unresolved critical: {critique.get('title', 'Unknown')}",
                            -thresholds.critical_critique_penalty,
                        )
                        section_conf.add_risk_flag(RiskFlag.UNRESOLVED_CRITICAL_CRITIQUE)
                    elif severity == "major":
                        section_conf.major_critiques += 1
                        section_conf.apply_adjustment(
                            f"Unresolved major: {critique.get('title', 'Unknown')}",
                            -thresholds.major_critique_penalty,
                        )
                    else:
                        section_conf.apply_adjustment(
                            f"Unresolved minor: {critique.get('title', 'Unknown')}",
                            -thresholds.minor_critique_penalty,
                        )
                else:
                    # Find the response disposition
                    for response in self._all_responses:
                        if response.get("critique_id") == critique_id:
                            disposition = response.get("disposition", "")
                            if disposition == "Accept":
                                section_conf.apply_adjustment(
                                    "Accepted critique resolved",
                                    thresholds.accepted_resolution_bonus,
                                )
                            elif disposition == "Rebut":
                                section_conf.apply_adjustment(
                                    "Critique successfully rebutted",
                                    thresholds.rebutted_resolution_bonus,
                                )
                            break

            section_conf.word_count = len(content.split())
            section_conf.finalize(thresholds)
            confidence.add_section_score(section_conf)

        # Calculate aggregate metrics
        confidence.total_critiques = len(self._all_critiques)
        confidence.resolved_critiques = len([
            r for r in self._all_responses
            if r.get("disposition") in ("Accept", "Partial Accept", "Rebut", "Acknowledge")
        ])
        confidence.unresolved_critical = sum(
            1 for s in confidence.section_scores
            if s.critical_critiques > 0 and s.unresolved_critiques > 0
        )
        confidence.unresolved_major = sum(
            s.major_critiques for s in confidence.section_scores
            if s.unresolved_critiques > 0
        )
        confidence.debate_rounds = self._round_manager.current_round
        confidence.consensus_reached = self._round_manager.consensus_reached

        # Calculate overall score
        confidence.calculate_overall_score()

        return confidence

    def _generate_red_team_report(self) -> Dict[str, Any]:
        """
        Generate the Red Team Report for transparency.

        Returns:
            Dictionary containing the complete debate history
        """
        # Get debate summary from round manager
        debate_summary = self._round_manager.get_debate_summary()

        # Get conversation history summary
        history_summary = self._history.get_summary()

        # Organize critiques by section
        critiques_by_section: Dict[str, List[Dict]] = {}
        for critique in self._all_critiques:
            section = critique.get("target_section", "General")
            if section not in critiques_by_section:
                critiques_by_section[section] = []
            critiques_by_section[section].append(critique)

        # Build response map
        response_map = {
            r.get("critique_id"): r
            for r in self._all_responses
        }

        # Create detailed exchange records
        exchanges = []
        for critique in self._all_critiques:
            critique_id = critique.get("id")
            response = response_map.get(critique_id)

            exchanges.append({
                "critique": {
                    "id": critique_id,
                    "agent": critique.get("agent"),
                    "section": critique.get("target_section"),
                    "type": critique.get("challenge_type"),
                    "severity": critique.get("severity"),
                    "title": critique.get("title"),
                    "argument": critique.get("argument"),
                    "suggested_remedy": critique.get("suggested_remedy"),
                },
                "response": {
                    "id": response.get("id") if response else None,
                    "agent": response.get("agent") if response else None,
                    "disposition": response.get("disposition") if response else "No Response",
                    "summary": response.get("summary") if response else None,
                    "action": response.get("action") if response else None,
                } if response else None,
                "resolved": response is not None,
                "outcome": response.get("disposition") if response else "Unresolved",
            })

        return {
            "document_id": self._current_request.id,
            "document_type": self._current_request.document_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),

            # Summary metrics
            "summary": {
                "total_rounds": debate_summary.get("total_rounds", 0),
                "adversarial_cycles": debate_summary.get("adversarial_cycles", 0),
                "consensus_reached": debate_summary.get("consensus_reached", False),
                "total_critiques": len(self._all_critiques),
                "resolved_critiques": len([e for e in exchanges if e["resolved"]]),
                "overall_resolution_rate": debate_summary.get("overall_resolution_rate", 0),
            },

            # Agent participation
            "participation": {
                "blue_team_agents": debate_summary.get("blue_team_agents", []),
                "red_team_agents": debate_summary.get("red_team_agents", []),
            },

            # Critique breakdown
            "critiques_by_severity": debate_summary.get("critiques_by_severity", {}),
            "critiques_by_section": {
                section: len(crits)
                for section, crits in critiques_by_section.items()
            },

            # Response breakdown
            "responses_by_disposition": debate_summary.get("responses_by_disposition", {}),

            # Detailed exchanges
            "exchanges": exchanges,

            # Unresolved issues
            "unresolved_issues": [
                e["critique"] for e in exchanges if not e["resolved"]
            ],

            # Round-by-round summaries
            "round_summaries": debate_summary.get("round_summaries", []),
        }

    def _get_blue_team_agents(self) -> List:
        """Get blue team agents for the current workflow."""
        if self._workflow_config and self._workflow_config.required_blue_agents:
            agents = []
            for role in self._workflow_config.required_blue_agents:
                try:
                    agent = self._registry.create(role)
                    if agent.is_enabled:
                        agents.append(agent)
                except Exception as e:
                    self.log_warning(f"Could not create agent {role}: {e}")
            return sorted(agents, key=lambda a: a.priority, reverse=True)

        return self._registry.create_blue_team(enabled_only=True)

    def _get_red_team_agents(self) -> List:
        """Get red team agents for the current workflow."""
        if self._workflow_config and self._workflow_config.required_red_agents:
            agents = []
            for role in self._workflow_config.required_red_agents:
                try:
                    agent = self._registry.create(role)
                    if agent.is_enabled:
                        agents.append(agent)
                except Exception as e:
                    self.log_warning(f"Could not create agent {role}: {e}")
            return sorted(agents, key=lambda a: a.priority, reverse=True)

        return self._registry.create_red_team(enabled_only=True)

    async def should_continue_debate(
        self,
        context: SwarmContext,
        current_round: int,
        max_rounds: int,
    ) -> bool:
        """
        Determine if the debate should continue.

        Args:
            context: Current swarm context
            current_round: Current round number
            max_rounds: Maximum allowed rounds

        Returns:
            True if debate should continue
        """
        # Check round manager's decision
        if not self._round_manager.should_continue():
            return False

        # Check if max rounds reached
        if current_round >= max_rounds:
            return False

        # Check if consensus reached
        if self._round_manager.consensus_reached:
            return False

        # Check if there are unresolved critical issues
        unresolved_critical = [
            c for c in self._current_context.pending_critiques
            if c.get("severity") == "critical"
        ]

        # Continue if there are critical issues to address
        return len(unresolved_critical) > 0

    async def synthesize_final_output(
        self,
        context: SwarmContext
    ) -> Dict[str, Any]:
        """
        Synthesize the final document output.

        Args:
            context: The complete swarm context

        Returns:
            Final document dictionary
        """
        return await self._synthesizer.synthesize(
            sections=context.section_drafts,
            critiques=context.resolved_critiques + context.pending_critiques,
            responses=self._all_responses,
            context=context,
            blue_team_contributions=self._blue_team_contributions,
        )
