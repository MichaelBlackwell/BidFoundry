"""WebSocket event type definitions.

Defines all event types for client-server WebSocket communication.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ClientEventType(str, Enum):
    """Events sent from client to server."""

    GENERATION_START = "generation:start"
    GENERATION_PAUSE = "generation:pause"
    GENERATION_RESUME = "generation:resume"
    GENERATION_CANCEL = "generation:cancel"
    PING = "ping"


class ServerEventType(str, Enum):
    """Events sent from server to client."""

    # Round lifecycle
    ROUND_START = "round:start"
    ROUND_END = "round:end"

    # Phase changes
    PHASE_CHANGE = "phase:change"

    # Agent events
    AGENT_REGISTERED = "agent:registered"
    AGENT_THINKING = "agent:thinking"
    AGENT_STREAMING = "agent:streaming"
    AGENT_COMPLETE = "agent:complete"

    # Document updates
    DRAFT_UPDATE = "draft:update"
    CONFIDENCE_UPDATE = "confidence:update"

    # Generation lifecycle
    GENERATION_STARTED = "generation:started"
    GENERATION_COMPLETE = "generation:complete"
    GENERATION_ERROR = "generation:error"
    GENERATION_PAUSED = "generation:paused"
    GENERATION_RESUMED = "generation:resumed"
    GENERATION_CANCELLED = "generation:cancelled"

    # Escalation
    ESCALATION_TRIGGERED = "escalation:triggered"

    # Connection
    CONNECTED = "connected"
    PONG = "pong"
    ERROR = "error"


# ============================================================================
# Base Message Types
# ============================================================================


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""

    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))
    request_id: Optional[str] = Field(None, alias="requestId")

    class Config:
        populate_by_name = True


class ClientMessage(WebSocketMessage):
    """Message sent from client to server."""

    type: ClientEventType


class ServerMessage(WebSocketMessage):
    """Message sent from server to client."""

    type: ServerEventType


# ============================================================================
# Client Event Payloads
# ============================================================================


class GenerationStartPayload(BaseModel):
    """Payload for generation:start event."""

    request_id: str = Field(alias="requestId")
    document_type: str = Field(alias="documentType")
    company_profile_id: str = Field(alias="companyProfileId")
    opportunity_context: Optional[dict[str, Any]] = Field(None, alias="opportunityContext")
    config: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class GenerationControlPayload(BaseModel):
    """Payload for generation control events (pause/resume/cancel)."""

    request_id: str = Field(alias="requestId")

    class Config:
        populate_by_name = True


# ============================================================================
# Server Event Payloads
# ============================================================================


class ConnectedPayload(BaseModel):
    """Payload for connected event."""

    connection_id: str = Field(alias="connectionId")
    server_time: int = Field(alias="serverTime")

    class Config:
        populate_by_name = True


class RoundStartPayload(BaseModel):
    """Payload for round:start event."""

    round: int
    total_rounds: int = Field(alias="totalRounds")
    phase: str
    agents: list["AgentInfo"] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class RoundEndPayload(BaseModel):
    """Payload for round:end event."""

    round: int
    summary: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class PhaseChangePayload(BaseModel):
    """Payload for phase:change event."""

    phase: str
    round: int


class AgentInfo(BaseModel):
    """Agent information."""

    id: str
    name: str
    role: str
    category: str  # "blue", "red", "specialist", or "orchestrator"


class AgentRegisteredPayload(BaseModel):
    """Payload for agent:registered event."""

    agents: list[AgentInfo]


class AgentThinkingPayload(BaseModel):
    """Payload for agent:thinking event."""

    agent_id: str = Field(alias="agentId")
    target: Optional[str] = None

    class Config:
        populate_by_name = True


class AgentStreamingPayload(BaseModel):
    """Payload for agent:streaming event."""

    agent_id: str = Field(alias="agentId")
    chunk: str

    class Config:
        populate_by_name = True


class CritiqueData(BaseModel):
    """Critique data from an agent."""

    severity: str
    target_section: Optional[str] = Field(None, alias="targetSection")
    content: str
    suggestions: list[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class ResponseData(BaseModel):
    """Response data from an agent."""

    action: str  # "accept", "rebut", "acknowledge"
    content: str
    changes_made: Optional[str] = Field(None, alias="changesMade")

    class Config:
        populate_by_name = True


class AgentCompletePayload(BaseModel):
    """Payload for agent:complete event."""

    agent_id: str = Field(alias="agentId")
    critique: Optional[CritiqueData] = None
    response: Optional[ResponseData] = None

    class Config:
        populate_by_name = True


class DraftSectionUpdate(BaseModel):
    """Section update in draft."""

    id: str
    title: str
    content: str
    confidence: float


class DraftUpdatePayload(BaseModel):
    """Payload for draft:update event."""

    draft: dict[str, Any]
    changed_sections: list[str] = Field(default_factory=list, alias="changedSections")

    class Config:
        populate_by_name = True


class ConfidenceUpdatePayload(BaseModel):
    """Payload for confidence:update event."""

    overall: float
    sections: dict[str, float] = Field(default_factory=dict)


class EscalationPayload(BaseModel):
    """Payload for escalation:triggered event."""

    reasons: list[str] = Field(default_factory=list)
    disputes: list[dict[str, Any]] = Field(default_factory=list)


class GenerationStartedPayload(BaseModel):
    """Payload for generation:started event."""

    request_id: str = Field(alias="requestId")

    class Config:
        populate_by_name = True


class GenerationCompletePayload(BaseModel):
    """Payload for generation:complete event."""

    result: dict[str, Any]


class GenerationErrorPayload(BaseModel):
    """Payload for generation:error event."""

    error: str
    code: Optional[str] = None
    recoverable: bool = False


class ErrorPayload(BaseModel):
    """Payload for error event."""

    message: str
    code: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================


def create_server_message(
    event_type: ServerEventType,
    payload: dict[str, Any],
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    """Create a server message dictionary."""
    return {
        "type": event_type.value,
        "payload": payload,
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
        "requestId": request_id,
    }


def create_error_message(
    message: str,
    code: Optional[str] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    """Create an error message dictionary."""
    return create_server_message(
        ServerEventType.ERROR,
        {"message": message, "code": code},
        request_id,
    )
