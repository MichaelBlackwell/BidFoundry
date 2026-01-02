"""Orchestrator service for document generation.

Bridges the agent system to the WebSocket layer, managing generation workflows
and translating agent messages to real-time client events.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.database import CompanyProfile, Document, GenerationRequest


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    # Handle acronyms and standard camelCase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def convert_keys_to_snake_case(data: Any) -> Any:
    """
    Recursively convert all dictionary keys from camelCase to snake_case.

    This is necessary because the frontend sends profile data in camelCase,
    but the agents expect snake_case keys.
    """
    if isinstance(data, dict):
        return {camel_to_snake(k): convert_keys_to_snake_case(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_snake_case(item) for item in data]
    else:
        return data


from server.config import get_llm_settings
from server.models.schemas import DocumentGenerationRequest, SwarmConfigSchema
from server.websocket.events import (
    AgentCompletePayload,
    AgentInfo,
    AgentInsightsUpdatePayload,
    AgentRegisteredPayload,
    AgentStreamingPayload,
    AgentThinkingPayload,
    ConfidenceUpdatePayload,
    DraftUpdatePayload,
    EscalationPayload,
    GenerationCompletePayload,
    GenerationErrorPayload,
    GenerationStartedPayload,
    PhaseChangePayload,
    RoundEndPayload,
    RoundStartPayload,
    ServerEventType,
)
from server.websocket.manager import ConnectionManager

# Import agent system components
try:
    from agents.orchestrator.arbiter import ArbiterAgent, DocumentRequest, FinalOutput
    from agents.registry import get_registry
    from agents.types import AgentRole, ROLE_CATEGORIES, AgentCategory
    from agents.config import configure_llm_settings
    from comms.bus import MessageBus
    from comms.message import Message, MessageType

    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    # Define stubs for type hints when agents not available
    ArbiterAgent = None
    DocumentRequest = None
    FinalOutput = None
    MessageBus = None
    Message = None
    MessageType = None
    configure_llm_settings = None

logger = logging.getLogger(__name__)


class GenerationStatus(str, Enum):
    """Status of a generation request."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


class WorkflowPhase(str, Enum):
    """Phases of the document generation workflow."""

    INITIALIZING = "initializing"
    BLUE_BUILD = "blue-build"
    RED_ATTACK = "red-attack"
    BLUE_DEFENSE = "blue-defense"
    SYNTHESIS = "synthesis"
    COMPLETE = "complete"


@dataclass
class GenerationContext:
    """Context for an active generation request."""

    request_id: str
    document_id: str
    company_profile_id: str
    config: SwarmConfigSchema

    # Agent system components
    arbiter: Optional[Any] = None  # ArbiterAgent when available
    message_bus: Optional[Any] = None  # MessageBus when available
    task: Optional[asyncio.Task] = None

    # State tracking
    status: GenerationStatus = GenerationStatus.QUEUED
    current_round: int = 0
    total_rounds: int = 3
    current_phase: WorkflowPhase = WorkflowPhase.INITIALIZING

    # Draft tracking - accumulates sections as they're generated
    current_sections: dict = field(default_factory=dict)  # section_name -> {id, title, content, confidence}
    draft_version: int = 0  # Increments with each update

    # Pause/resume support
    pause_event: asyncio.Event = field(default_factory=asyncio.Event)
    cancel_requested: bool = False

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    def __post_init__(self):
        """Initialize the pause event to allow running."""
        self.pause_event.set()  # Not paused by default


class OrchestratorService:
    """
    Manages document generation workflows.

    Responsibilities:
    - Creates and configures ArbiterAgent instances
    - Subscribes to MessageBus events
    - Translates agent messages to WebSocket events
    - Tracks active generation requests
    - Handles pause/resume/cancel operations
    """

    def __init__(self, ws_manager: ConnectionManager) -> None:
        """
        Initialize the orchestrator service.

        Args:
            ws_manager: WebSocket connection manager for broadcasting events
        """
        self.ws_manager = ws_manager
        self.active_requests: dict[str, GenerationContext] = {}
        self._lock = asyncio.Lock()
        self._message_bus_subscriptions: dict[str, str] = {}  # request_id -> subscription_id

    async def start_generation(
        self,
        request_id: str,
        request: DocumentGenerationRequest,
        db: AsyncSession,
        connection_id: str,
    ) -> GenerationContext:
        """
        Start a new document generation workflow.

        Args:
            request_id: Unique ID for this generation request
            request: The generation request details
            db: Database session
            connection_id: WebSocket connection ID to subscribe

        Returns:
            GenerationContext for the started generation

        Raises:
            ValueError: If company profile not found or agents not available
        """
        if not AGENTS_AVAILABLE:
            raise ValueError("Agent system not available. Please ensure agent modules are installed.")

        # Check for existing request
        async with self._lock:
            if request_id in self.active_requests:
                raise ValueError(f"Generation request {request_id} already exists")

        # Load company profile
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == request.company_profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError(f"Company profile not found: {request.company_profile_id}")

        # Create document record
        document = Document(
            id=str(uuid.uuid4()),
            type=request.document_type,
            title=f"{request.document_type} - {profile.name}",
            company_profile_id=profile.id,
            status="draft",
            generation_config=request.config.model_dump(by_alias=True),
        )
        db.add(document)

        # Create generation request record
        gen_request = GenerationRequest(
            id=request_id,
            document_id=document.id,
            status=GenerationStatus.QUEUED.value,
            total_rounds=str(request.config.rounds),
        )
        db.add(gen_request)
        await db.commit()

        # Create generation context
        context = GenerationContext(
            request_id=request_id,
            document_id=document.id,
            company_profile_id=profile.id,
            config=request.config,
            total_rounds=request.config.rounds,
        )

        # Store context
        async with self._lock:
            self.active_requests[request_id] = context

        # Subscribe the connection to receive updates
        await self.ws_manager.subscribe_to_request(connection_id, request_id)

        # Start the generation workflow in background
        context.task = asyncio.create_task(
            self._run_generation(
                context=context,
                profile=profile,
                request=request,
                db=db,
            )
        )

        logger.info(f"Started generation request {request_id} for document {document.id}")
        return context

    async def _run_generation(
        self,
        context: GenerationContext,
        profile: CompanyProfile,
        request: DocumentGenerationRequest,
        db: AsyncSession,
    ) -> None:
        """
        Run the document generation workflow.

        Args:
            context: Generation context
            profile: Company profile
            request: Original generation request
            db: Database session
        """
        try:
            context.started_at = datetime.now(timezone.utc)
            context.status = GenerationStatus.RUNNING

            # Update database
            await self._update_db_status(context, db)

            # Notify start
            await self._broadcast_event(
                context.request_id,
                ServerEventType.GENERATION_STARTED,
                GenerationStartedPayload(request_id=context.request_id).model_dump(by_alias=True),
            )

            # Create message bus
            context.message_bus = MessageBus()
            await context.message_bus.start()

            # Subscribe to message bus events
            subscription_id = await context.message_bus.subscribe(
                agent_role="websocket_bridge",
                message_types=[
                    MessageType.DRAFT,
                    MessageType.CRITIQUE,
                    MessageType.RESPONSE,
                    MessageType.ROUND_START,
                    MessageType.ROUND_END,
                    MessageType.STATUS,
                ],
                handler=lambda msg: self._on_message_bus_event(msg, context.request_id),
            )
            self._message_bus_subscriptions[context.request_id] = subscription_id

            # Create arbiter
            context.arbiter = ArbiterAgent()
            await context.arbiter.initialize(
                registry=get_registry(),
                message_bus=context.message_bus,
            )

            # Broadcast registered agents
            await self._broadcast_registered_agents(context)

            # Create DocumentRequest for arbiter
            # Build fallback profile from database columns if full_profile is not available
            fallback_profile = {
                "name": profile.name,
                "description": profile.description,
                "naics_codes": profile.naics_codes or [],
                "certifications": profile.certifications or [],
                "past_performance": profile.past_performance or [],
            }

            # Use full_profile if available (contains all 40+ fields), otherwise use fallback
            # Convert camelCase keys to snake_case since frontend sends camelCase
            # but agents/formatters expect snake_case
            if profile.full_profile:
                company_profile_data = convert_keys_to_snake_case(profile.full_profile)
                # Merge in root-level fields that are stored separately in the DB
                # These are not part of full_profile but are needed by agents
                company_profile_data["name"] = profile.name
                if profile.description:
                    company_profile_data["description"] = profile.description
                if profile.naics_codes:
                    company_profile_data["naics_codes"] = profile.naics_codes
                if profile.certifications:
                    company_profile_data["certifications"] = profile.certifications
                if profile.past_performance:
                    company_profile_data["past_performance"] = profile.past_performance

                # Calculate years_in_business from formation_date if not already present
                if "years_in_business" not in company_profile_data and company_profile_data.get("formation_date"):
                    try:
                        formation_str = company_profile_data["formation_date"]
                        formation_date = date.fromisoformat(formation_str)
                        today = date.today()
                        years = today.year - formation_date.year
                        # Adjust if birthday hasn't occurred yet this year
                        if (today.month, today.day) < (formation_date.month, formation_date.day):
                            years -= 1
                        company_profile_data["years_in_business"] = max(0, years)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not calculate years_in_business from formation_date: {e}")
            else:
                company_profile_data = fallback_profile

            # Log warning if using incomplete fallback
            if not profile.full_profile:
                logger.warning(
                    f"Company profile {profile.id} ({profile.name}) lacks full_profile data. "
                    f"Document generation will use limited fields. Consider updating the profile "
                    f"with complete information for better document quality."
                )

            doc_request = DocumentRequest(
                id=context.request_id,
                document_type=request.document_type,
                company_profile=company_profile_data,
                opportunity=request.opportunity_context.model_dump(by_alias=True) if request.opportunity_context else None,
                max_adversarial_rounds=request.config.rounds,
                consensus_threshold=0.80,
                confidence_threshold=request.config.escalation_thresholds.confidence_min / 100,
            )

            # Run the generation workflow
            result = await self._run_with_pause_support(context, doc_request)

            if context.cancel_requested:
                context.status = GenerationStatus.CANCELLED
                await self._broadcast_event(
                    context.request_id,
                    ServerEventType.GENERATION_CANCELLED,
                    {"requestId": context.request_id},
                )
            elif result:
                # Save result to database
                await self._save_generation_result(context, result, db)

                # If human review is required, send escalation event first
                if result.requires_human_review:
                    await self._broadcast_event(
                        context.request_id,
                        ServerEventType.ESCALATION_TRIGGERED,
                        EscalationPayload(
                            reasons=result.review_reasons if hasattr(result, 'review_reasons') else [],
                            disputes=[],  # Disputes are populated during review
                        ).model_dump(by_alias=True),
                    )

                # Broadcast completion
                context.status = GenerationStatus.COMPLETE
                await self._broadcast_event(
                    context.request_id,
                    ServerEventType.GENERATION_COMPLETE,
                    GenerationCompletePayload(
                        result=self._format_final_output(result, context.document_id)
                    ).model_dump(by_alias=True),
                )

        except asyncio.CancelledError:
            context.status = GenerationStatus.CANCELLED
            logger.info(f"Generation {context.request_id} was cancelled")
            await self._broadcast_event(
                context.request_id,
                ServerEventType.GENERATION_CANCELLED,
                {"requestId": context.request_id},
            )

        except Exception as e:
            logger.error(f"Generation {context.request_id} failed: {e}", exc_info=True)
            context.status = GenerationStatus.ERROR
            context.error_message = str(e)

            await self._broadcast_event(
                context.request_id,
                ServerEventType.GENERATION_ERROR,
                GenerationErrorPayload(
                    error=str(e),
                    code="GENERATION_FAILED",
                    recoverable=False,
                ).model_dump(by_alias=True),
            )

        finally:
            context.completed_at = datetime.now(timezone.utc)
            await self._cleanup_generation(context, db)

    async def _run_with_pause_support(
        self,
        context: GenerationContext,
        doc_request: Any,  # DocumentRequest
    ) -> Optional[Any]:  # FinalOutput
        """
        Run generation with pause/resume/cancel support.

        Args:
            context: Generation context
            doc_request: Document request for arbiter

        Returns:
            FinalOutput if successful, None if cancelled
        """
        # Check for cancel before starting
        if context.cancel_requested:
            return None

        # Wait if paused
        await context.pause_event.wait()

        # Run the generation
        result = await context.arbiter.generate_document(doc_request)

        return result

    async def _on_message_bus_event(self, message: Message, request_id: str) -> None:
        """
        Handle messages from the agent MessageBus.

        Converts internal Message objects to WebSocket events.

        Args:
            message: The message from the bus
            request_id: The generation request ID
        """
        context = self.active_requests.get(request_id)
        if not context:
            return

        try:
            if message.message_type == MessageType.ROUND_START:
                data = message.get_structured_data()
                context.current_round = data.get("round_number", context.current_round + 1)
                # Normalize round_type to match WorkflowPhase enum values (using dashes)
                round_type = data.get("round_type", "blue-build").lower().replace(" ", "-").replace("_", "-")
                # Handle cases like "bluebuild" -> "blue-build", "redattack" -> "red-attack"
                phase_mapping = {
                    "bluebuild": "blue-build",
                    "redattack": "red-attack",
                    "bluedefense": "blue-defense",
                }
                round_type = phase_mapping.get(round_type, round_type)
                try:
                    context.current_phase = WorkflowPhase(round_type)
                except ValueError:
                    logger.warning(f"Unknown round_type '{round_type}', defaulting to blue-build")
                    context.current_phase = WorkflowPhase.BLUE_BUILD

                await self._broadcast_event(
                    request_id,
                    ServerEventType.ROUND_START,
                    RoundStartPayload(
                        round=context.current_round,
                        total_rounds=context.total_rounds,
                        phase=context.current_phase.value,
                        agents=data.get("agents", []),
                    ).model_dump(by_alias=True),
                )

                await self._broadcast_event(
                    request_id,
                    ServerEventType.PHASE_CHANGE,
                    PhaseChangePayload(
                        phase=context.current_phase.value,
                        round=context.current_round,
                    ).model_dump(by_alias=True),
                )

            elif message.message_type == MessageType.ROUND_END:
                data = message.get_structured_data()
                await self._broadcast_event(
                    request_id,
                    ServerEventType.ROUND_END,
                    RoundEndPayload(
                        round=context.current_round,
                        summary=data,
                    ).model_dump(by_alias=True),
                )

            elif message.message_type == MessageType.DRAFT:
                section_name = message.section_name or "unknown"
                content = message.get_content()

                await self._broadcast_event(
                    request_id,
                    ServerEventType.AGENT_COMPLETE,
                    AgentCompletePayload(
                        agent_id=message.sender_role.lower().replace(" ", "_"),
                        response={
                            "action": "draft",
                            "content": content[:500] + "..." if len(content) > 500 else content,
                        },
                    ).model_dump(by_alias=True),
                )

                # Accumulate section into current draft
                section_id = f"sec-{section_name.lower().replace(' ', '-').replace('_', '-')}"
                context.current_sections[section_name] = {
                    "id": section_id,
                    "title": section_name,
                    "content": content,
                    "confidence": 75,  # Initial confidence before red team review
                    "unresolvedCritiques": 0,
                }
                context.draft_version += 1

                # Build full DocumentDraft structure for frontend
                # Preserve section order by sorting alphabetically (or could use template order)
                sections_list = [
                    {
                        "id": sec_data["id"],
                        "title": sec_data["title"],
                        "content": sec_data["content"],
                        "confidence": sec_data["confidence"],
                        "unresolvedCritiques": sec_data["unresolvedCritiques"],
                    }
                    for sec_data in context.current_sections.values()
                ]

                # Use a stable draft ID so frontend updates in place rather than
                # creating many entries. Version is tracked separately.
                full_draft = {
                    "id": f"draft-{context.document_id}",
                    "sections": sections_list,
                    "overallConfidence": min(s["confidence"] for s in sections_list) if sections_list else 0,
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                    "version": context.draft_version,  # Track version for diffing
                }

                await self._broadcast_event(
                    request_id,
                    ServerEventType.DRAFT_UPDATE,
                    DraftUpdatePayload(
                        draft=full_draft,
                        changed_sections=[section_name],
                    ).model_dump(by_alias=True),
                )

            elif message.message_type == MessageType.CRITIQUE:
                data = message.get_structured_data()
                target_section = data.get("target_section")
                agent_id = message.sender_role.lower().replace(" ", "_")

                # DEBUG: Log critique received
                logger.info(
                    f"Orchestrator: Critique received from {agent_id} - "
                    f"severity={data.get('severity', 'unknown')}, "
                    f"target={target_section}, "
                    f"round={message.round_number}"
                )

                await self._broadcast_event(
                    request_id,
                    ServerEventType.AGENT_COMPLETE,
                    AgentCompletePayload(
                        agent_id=agent_id,
                        critique={
                            "id": data.get("id", message.id),
                            "severity": data.get("severity", "minor"),
                            "targetSection": target_section,
                            "content": data.get("argument", ""),
                            "suggestions": [data.get("suggested_remedy")] if data.get("suggested_remedy") else [],
                            "round": message.round_number,
                            "phase": "red-attack",
                            "status": data.get("status", "pending"),
                            "agentId": agent_id,
                        },
                    ).model_dump(by_alias=True),
                )

                # Update unresolved critiques count on the affected section
                if target_section and target_section in context.current_sections:
                    context.current_sections[target_section]["unresolvedCritiques"] += 1
                    # Reduce confidence based on severity
                    severity = data.get("severity", "minor")
                    confidence_penalty = {"critical": 15, "major": 10, "minor": 5}.get(severity, 3)
                    current_conf = context.current_sections[target_section]["confidence"]
                    context.current_sections[target_section]["confidence"] = max(0, current_conf - confidence_penalty)

                    # Send updated draft to frontend
                    context.draft_version += 1
                    sections_list = [
                        {
                            "id": sec_data["id"],
                            "title": sec_data["title"],
                            "content": sec_data["content"],
                            "confidence": sec_data["confidence"],
                            "unresolvedCritiques": sec_data["unresolvedCritiques"],
                        }
                        for sec_data in context.current_sections.values()
                    ]
                    full_draft = {
                        "id": f"draft-{context.document_id}",
                        "sections": sections_list,
                        "overallConfidence": min(s["confidence"] for s in sections_list) if sections_list else 0,
                        "updatedAt": datetime.now(timezone.utc).isoformat(),
                        "version": context.draft_version,
                    }
                    await self._broadcast_event(
                        request_id,
                        ServerEventType.DRAFT_UPDATE,
                        DraftUpdatePayload(
                            draft=full_draft,
                            changed_sections=[target_section],
                        ).model_dump(by_alias=True),
                    )

            elif message.message_type == MessageType.RESPONSE:
                data = message.get_structured_data()
                disposition = data.get("disposition", "acknowledge").lower()
                target_section = data.get("target_section")

                await self._broadcast_event(
                    request_id,
                    ServerEventType.AGENT_COMPLETE,
                    AgentCompletePayload(
                        agent_id=message.sender_role.lower().replace(" ", "_"),
                        response={
                            "action": disposition,
                            "content": data.get("summary", ""),
                            "changesMade": data.get("action"),
                        },
                    ).model_dump(by_alias=True),
                )

                # If response resolves a critique, update the section's confidence
                if target_section and target_section in context.current_sections:
                    section = context.current_sections[target_section]
                    if section["unresolvedCritiques"] > 0:
                        section["unresolvedCritiques"] -= 1
                        # Restore confidence when critique is addressed
                        if disposition in ("accept", "partial accept"):
                            section["confidence"] = min(100, section["confidence"] + 8)
                        elif disposition == "rebut":
                            section["confidence"] = min(100, section["confidence"] + 5)

                        # Send updated draft to frontend
                        context.draft_version += 1
                        sections_list = [
                            {
                                "id": sec_data["id"],
                                "title": sec_data["title"],
                                "content": sec_data["content"],
                                "confidence": sec_data["confidence"],
                                "unresolvedCritiques": sec_data["unresolvedCritiques"],
                            }
                            for sec_data in context.current_sections.values()
                        ]
                        full_draft = {
                            "id": f"draft-{context.document_id}",
                            "sections": sections_list,
                            "overallConfidence": min(s["confidence"] for s in sections_list) if sections_list else 0,
                            "updatedAt": datetime.now(timezone.utc).isoformat(),
                            "version": context.draft_version,
                        }
                        await self._broadcast_event(
                            request_id,
                            ServerEventType.DRAFT_UPDATE,
                            DraftUpdatePayload(
                                draft=full_draft,
                                changed_sections=[target_section],
                            ).model_dump(by_alias=True),
                        )

            elif message.message_type == MessageType.STATUS:
                data = message.get_structured_data()
                status_type = data.get("type", "")

                if status_type == "agent_thinking":
                    await self._broadcast_event(
                        request_id,
                        ServerEventType.AGENT_THINKING,
                        AgentThinkingPayload(
                            agent_id=data.get("agent_id", message.sender_role.lower().replace(" ", "_")),
                            target=data.get("target"),
                        ).model_dump(by_alias=True),
                    )
                elif status_type == "agent_streaming":
                    await self._broadcast_event(
                        request_id,
                        ServerEventType.AGENT_STREAMING,
                        AgentStreamingPayload(
                            agent_id=data.get("agent_id", message.sender_role.lower().replace(" ", "_")),
                            chunk=data.get("chunk", ""),
                        ).model_dump(by_alias=True),
                    )
                elif status_type == "confidence_update":
                    await self._broadcast_event(
                        request_id,
                        ServerEventType.CONFIDENCE_UPDATE,
                        ConfidenceUpdatePayload(
                            overall=data.get("overall", 0),
                            sections=data.get("sections", {}),
                        ).model_dump(by_alias=True),
                    )
                elif status_type == "document_updated":
                    # Handle full document state updates from Arbiter
                    # Updates section content in the frontend preview
                    sections_data = data.get("sections", [])
                    for sec in sections_data:
                        section_name = sec.get("name", "unknown")
                        content = sec.get("content", "")
                        section_id = f"sec-{section_name.lower().replace(' ', '-').replace('_', '-')}"

                        # Preserve existing confidence and critique counts, or use defaults
                        existing = context.current_sections.get(section_name, {})
                        context.current_sections[section_name] = {
                            "id": section_id,
                            "title": section_name,
                            "content": content,
                            "confidence": existing.get("confidence", 75),
                            "unresolvedCritiques": existing.get("unresolvedCritiques", 0),
                        }

                    # Emit draft:update with all sections
                    if context.current_sections:
                        context.draft_version += 1
                        sections_list = [
                            {
                                "id": sec_data["id"],
                                "title": sec_data["title"],
                                "content": sec_data["content"],
                                "confidence": sec_data["confidence"],
                                "unresolvedCritiques": sec_data["unresolvedCritiques"],
                            }
                            for sec_data in context.current_sections.values()
                        ]
                        full_draft = {
                            "id": f"draft-{context.document_id}",
                            "sections": sections_list,
                            "overallConfidence": min(s["confidence"] for s in sections_list) if sections_list else 0,
                            "updatedAt": datetime.now(timezone.utc).isoformat(),
                            "version": context.draft_version,
                        }
                        await self._broadcast_event(
                            request_id,
                            ServerEventType.DRAFT_UPDATE,
                            DraftUpdatePayload(
                                draft=full_draft,
                                changed_sections=[sec.get("name", "") for sec in sections_data],
                            ).model_dump(by_alias=True),
                        )
                elif status_type == "agent_contribution":
                    # Handle agent contribution events (for Agent Insights panel)
                    # This forwards analysis data from blue team agents to the frontend
                    await self._broadcast_event(
                        request_id,
                        ServerEventType.AGENT_INSIGHTS_UPDATE,
                        AgentInsightsUpdatePayload(
                            agent_role=data.get("agent_role", ""),
                            agent_name=data.get("agent_name", ""),
                            content=data.get("content"),
                            metadata=data.get("metadata", {}),
                        ).model_dump(by_alias=True),
                    )

        except Exception as e:
            logger.error(f"Error handling message bus event: {e}", exc_info=True)

    async def _broadcast_registered_agents(self, context: GenerationContext) -> None:
        """Broadcast the list of registered agents."""
        agents = []

        # Map config to agent info
        blue_config = context.config.blue_team
        red_config = context.config.red_team

        if blue_config.strategy_architect:
            agents.append(AgentInfo(id="strategy_architect", name="Strategy Architect", role="Strategy Architect", category="blue"))
        if blue_config.market_analyst:
            agents.append(AgentInfo(id="market_analyst", name="Market Analyst", role="Market Analyst", category="blue"))
        if blue_config.compliance_navigator:
            agents.append(AgentInfo(id="compliance_navigator", name="Compliance Navigator", role="Compliance Navigator", category="blue"))
        if blue_config.capture_strategist:
            agents.append(AgentInfo(id="capture_strategist", name="Capture Strategist", role="Capture Strategist", category="blue"))

        if red_config.devils_advocate:
            agents.append(AgentInfo(id="devils_advocate", name="Devil's Advocate", role="Devil's Advocate", category="red"))
        if red_config.competitor_simulator:
            agents.append(AgentInfo(id="competitor_simulator", name="Competitor Simulator", role="Competitor Simulator", category="red"))
        if red_config.evaluator_simulator:
            agents.append(AgentInfo(id="evaluator_simulator", name="Evaluator Simulator", role="Evaluator Simulator", category="red"))
        if red_config.risk_assessor:
            agents.append(AgentInfo(id="risk_assessor", name="Risk Assessor", role="Risk Assessor", category="red"))

        # Always add the arbiter/orchestrator agent for synthesis phase
        agents.append(AgentInfo(id="arbiter", name="Arbiter", role="Arbiter", category="orchestrator"))

        await self._broadcast_event(
            context.request_id,
            ServerEventType.AGENT_REGISTERED,
            AgentRegisteredPayload(agents=agents).model_dump(by_alias=True),
        )

    async def pause_generation(self, request_id: str) -> bool:
        """
        Pause an active generation.

        Args:
            request_id: The generation request ID

        Returns:
            True if pause was successful
        """
        context = self.active_requests.get(request_id)
        if not context:
            return False

        if context.status != GenerationStatus.RUNNING:
            return False

        context.pause_event.clear()
        context.status = GenerationStatus.PAUSED

        await self._broadcast_event(
            request_id,
            ServerEventType.GENERATION_PAUSED,
            {"requestId": request_id},
        )

        logger.info(f"Paused generation {request_id}")
        return True

    async def resume_generation(self, request_id: str) -> bool:
        """
        Resume a paused generation.

        Args:
            request_id: The generation request ID

        Returns:
            True if resume was successful
        """
        context = self.active_requests.get(request_id)
        if not context:
            return False

        if context.status != GenerationStatus.PAUSED:
            return False

        context.pause_event.set()
        context.status = GenerationStatus.RUNNING

        await self._broadcast_event(
            request_id,
            ServerEventType.GENERATION_RESUMED,
            {"requestId": request_id},
        )

        logger.info(f"Resumed generation {request_id}")
        return True

    async def cancel_generation(self, request_id: str) -> bool:
        """
        Cancel an active generation.

        Args:
            request_id: The generation request ID

        Returns:
            True if cancellation was successful
        """
        context = self.active_requests.get(request_id)
        if not context:
            return False

        if context.status in (GenerationStatus.COMPLETE, GenerationStatus.ERROR, GenerationStatus.CANCELLED):
            return False

        context.cancel_requested = True
        context.pause_event.set()  # Unblock if paused

        if context.task and not context.task.done():
            context.task.cancel()

        logger.info(f"Cancelled generation {request_id}")
        return True

    async def get_generation_status(self, request_id: str, db: AsyncSession) -> Optional[dict]:
        """
        Get the status of a generation request.

        Args:
            request_id: The generation request ID
            db: Database session

        Returns:
            Status dictionary or None if not found
        """
        # Check active requests first
        context = self.active_requests.get(request_id)
        if context:
            return {
                "request_id": request_id,
                "status": context.status.value,
                "current_round": context.current_round,
                "total_rounds": context.total_rounds,
                "current_phase": context.current_phase.value if context.current_phase else None,
                "document_id": context.document_id,
                "error_message": context.error_message,
                "started_at": context.started_at,
                "completed_at": context.completed_at,
            }

        # Check database
        result = await db.execute(
            select(GenerationRequest).where(GenerationRequest.id == request_id)
        )
        gen_request = result.scalar_one_or_none()
        if gen_request:
            return {
                "request_id": gen_request.id,
                "status": gen_request.status,
                "current_round": int(gen_request.current_round) if gen_request.current_round else 0,
                "total_rounds": int(gen_request.total_rounds) if gen_request.total_rounds else 0,
                "current_phase": gen_request.current_phase,
                "document_id": gen_request.document_id,
                "error_message": gen_request.error_message,
                "started_at": gen_request.started_at,
                "completed_at": gen_request.completed_at,
            }

        return None

    async def _broadcast_event(
        self,
        request_id: str,
        event_type: ServerEventType,
        payload: dict,
    ) -> None:
        """Broadcast an event to all subscribers."""
        await self.ws_manager.broadcast(request_id, event_type, payload)

    async def _update_db_status(self, context: GenerationContext, db: AsyncSession) -> None:
        """Update generation request status in database."""
        try:
            result = await db.execute(
                select(GenerationRequest).where(GenerationRequest.id == context.request_id)
            )
            gen_request = result.scalar_one_or_none()
            if gen_request:
                gen_request.status = context.status.value
                gen_request.current_round = str(context.current_round)
                gen_request.current_phase = context.current_phase.value if context.current_phase else None
                gen_request.started_at = context.started_at
                gen_request.completed_at = context.completed_at
                gen_request.error_message = context.error_message
                gen_request.error_code = context.error_code
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update DB status: {e}")

    async def _save_generation_result(
        self,
        context: GenerationContext,
        result: Any,  # FinalOutput
        db: AsyncSession,
    ) -> None:
        """Save generation result to database."""
        try:
            # Only save if generation was successful and has content
            if not result.success:
                logger.warning(f"Generation {context.request_id} did not succeed, skipping save")
                return

            # Check that we have actual content
            has_content = result.sections and len(result.sections) > 0
            if not has_content:
                logger.warning(f"Generation {context.request_id} has no content, skipping save")
                return

            doc_result = await db.execute(
                select(Document).where(Document.id == context.document_id)
            )
            document = doc_result.scalar_one_or_none()
            if document:
                document.content = result.document
                document.confidence = result.confidence.overall_score if result.confidence else 0
                document.confidence_report = result.confidence.to_dict() if result.confidence else None
                document.red_team_report = result.red_team_report
                document.debate_log = result.debate_log if hasattr(result, 'debate_log') else []
                document.requires_human_review = result.requires_human_review
                # Calculate severity counts from red_team_report
                critiques_by_severity = result.red_team_report.get("critiques_by_severity", {}) if result.red_team_report else {}
                responses_by_disposition = result.red_team_report.get("responses_by_disposition", {}) if result.red_team_report else {}

                document.metrics = {
                    "rounds_completed": result.total_rounds,
                    "total_critiques": result.total_critiques,
                    "critical_count": critiques_by_severity.get("critical", 0),
                    "major_count": critiques_by_severity.get("major", 0),
                    "minor_count": critiques_by_severity.get("minor", 0),
                    "accepted_count": responses_by_disposition.get("Accept", 0) + responses_by_disposition.get("Partial Accept", 0),
                    "rebutted_count": responses_by_disposition.get("Rebut", 0),
                    "acknowledged_count": responses_by_disposition.get("Acknowledge", 0),
                    "time_elapsed_ms": int(result.duration_seconds * 1000),
                }
                # Update timestamp to indicate generation completed
                document.updated_at = datetime.now(timezone.utc)
                await db.commit()

                # DEBUG: Log final metrics being saved
                logger.info(
                    f"Orchestrator: Saved generation result for document {context.document_id} - "
                    f"rounds={result.total_rounds}, critiques={result.total_critiques}, "
                    f"resolved={result.resolved_critiques}, consensus={result.consensus_reached}"
                )
                if result.total_critiques == 0:
                    logger.warning(
                        f"Orchestrator: Document {context.document_id} completed with 0 critiques! "
                        f"Check server logs for RedAttack warnings to diagnose the issue."
                    )
        except Exception as e:
            logger.error(f"Failed to save generation result: {e}")

    async def _cleanup_generation(self, context: GenerationContext, db: AsyncSession) -> None:
        """Clean up resources after generation completes."""
        # Update database
        await self._update_db_status(context, db)

        # Stop message bus
        if context.message_bus:
            try:
                # Unsubscribe
                sub_id = self._message_bus_subscriptions.pop(context.request_id, None)
                if sub_id:
                    await context.message_bus.unsubscribe(sub_id)
                await context.message_bus.stop()
            except Exception as e:
                logger.error(f"Error stopping message bus: {e}")

        # Remove from active requests after a delay (for status queries)
        async def remove_after_delay():
            await asyncio.sleep(300)  # Keep for 5 minutes
            async with self._lock:
                self.active_requests.pop(context.request_id, None)

        asyncio.create_task(remove_after_delay())

    def _format_final_output(self, result: Any, document_id: str) -> dict:
        """Format FinalOutput for WebSocket transmission."""
        return {
            "documentId": document_id,
            "content": {
                "id": document_id,
                "sections": [
                    {
                        "id": f"sec-{i}",
                        "title": name,
                        "content": content,
                        "confidence": 85,  # Would come from actual confidence scores
                        "unresolvedCritiques": 0,
                    }
                    for i, (name, content) in enumerate(result.sections.items())
                ],
                "overallConfidence": round(result.confidence.overall_score * 100, 2) if result.confidence else 0,
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            },
            "confidence": {
                "overall": round(result.confidence.overall_score * 100, 2) if result.confidence else 0,
                "sections": {
                    s.section_name: round(s.adjusted_score * 100, 2)
                    for s in (result.confidence.section_scores if result.confidence else [])
                },
            },
            "redTeamReport": result.red_team_report or {},
            "debateLog": result.debate_log if hasattr(result, 'debate_log') else [],
            "metrics": {
                "roundsCompleted": result.total_rounds,
                "totalCritiques": result.total_critiques,
                "criticalCount": (result.red_team_report or {}).get("critiques_by_severity", {}).get("critical", 0),
                "majorCount": (result.red_team_report or {}).get("critiques_by_severity", {}).get("major", 0),
                "minorCount": (result.red_team_report or {}).get("critiques_by_severity", {}).get("minor", 0),
                "acceptedCount": len([e for e in (result.red_team_report or {}).get("exchanges", [])
                                     if e and (e.get("response") or {}).get("disposition") in ("Accept", "Partial Accept")]),
                "rebuttedCount": len([e for e in (result.red_team_report or {}).get("exchanges", [])
                                     if e and (e.get("response") or {}).get("disposition") == "Rebut"]),
                "acknowledgedCount": len([e for e in (result.red_team_report or {}).get("exchanges", [])
                                         if e and (e.get("response") or {}).get("disposition") == "Acknowledge"]),
                "timeElapsedMs": int(result.duration_seconds * 1000),
            },
            "requiresHumanReview": result.requires_human_review,
        }


# Global orchestrator instance (initialized in main.py)
orchestrator_service: Optional[OrchestratorService] = None


def get_orchestrator() -> OrchestratorService:
    """Get the global orchestrator service instance."""
    if orchestrator_service is None:
        raise RuntimeError("OrchestratorService not initialized")
    return orchestrator_service


def init_orchestrator(ws_manager: ConnectionManager) -> OrchestratorService:
    """Initialize the global orchestrator service."""
    global orchestrator_service

    # Inject LLM settings into agent config system
    if AGENTS_AVAILABLE and configure_llm_settings:
        llm_settings = get_llm_settings()
        configure_llm_settings(
            provider=llm_settings["provider"],
            model=llm_settings["model"],
            api_key_env_var=llm_settings["api_key_env_var"],
        )

    orchestrator_service = OrchestratorService(ws_manager)
    return orchestrator_service
