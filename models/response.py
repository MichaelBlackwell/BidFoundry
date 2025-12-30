"""
Response Model

Defines the structure for blue team responses to red team critiques.
Responses can accept, rebut, or acknowledge critiques.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import json
import uuid


class Disposition(str, Enum):
    """How the blue team chooses to handle a critique."""

    ACCEPT = "Accept"  # Agree with critique, will make changes
    REBUT = "Rebut"  # Disagree with critique, provide counter-argument
    ACKNOWLEDGE = "Acknowledge"  # Recognize validity but limited/no action
    PARTIAL_ACCEPT = "Partial Accept"  # Accept part, rebut part
    DEFER = "Defer"  # Defer to human decision-maker


class ActionType(str, Enum):
    """Types of actions taken in response to a critique."""

    REVISE_CONTENT = "Revise Content"
    ADD_CONTENT = "Add Content"
    REMOVE_CONTENT = "Remove Content"
    RESTRUCTURE = "Restructure"
    ADD_EVIDENCE = "Add Evidence"
    CLARIFY = "Clarify"
    NO_ACTION = "No Action"
    ESCALATE = "Escalate"


@dataclass
class Response:
    """
    A structured response from a blue team agent to a red team critique.

    Responses must address the critique directly and explain the chosen
    disposition with supporting evidence.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Link to critique
    critique_id: str = ""

    # Source
    agent: str = ""  # Role of the responding agent
    round_number: int = 1

    # Disposition
    disposition: Disposition = Disposition.ACKNOWLEDGE

    # Content
    summary: str = ""  # Brief summary of the response
    action: str = ""  # What action is being taken
    action_type: ActionType = ActionType.NO_ACTION
    rationale: str = ""  # Why this disposition was chosen
    evidence: Optional[str] = None  # Supporting evidence for rebuttal

    # For partial accepts
    accepted_portion: Optional[str] = None
    rebutted_portion: Optional[str] = None

    # Residual considerations
    residual_risk: Optional[str] = None  # Any remaining risk after action
    mitigation_plan: Optional[str] = None  # How residual risk will be managed

    # Changes made
    original_content: Optional[str] = None  # Content before changes
    revised_content: Optional[str] = None  # Content after changes

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate required fields after initialization."""
        if not self.critique_id:
            raise ValueError("Response must reference a critique_id")
        if not self.agent:
            raise ValueError("Response must specify the source agent")

    @property
    def requires_revision(self) -> bool:
        """Check if this response requires document revision."""
        return self.disposition in {Disposition.ACCEPT, Disposition.PARTIAL_ACCEPT}

    @property
    def has_residual_risk(self) -> bool:
        """Check if there is acknowledged residual risk."""
        return bool(self.residual_risk)

    @property
    def made_changes(self) -> bool:
        """Check if changes were made to the document."""
        return self.revised_content is not None and self.revised_content != self.original_content

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "critique_id": self.critique_id,
            "agent": self.agent,
            "round_number": self.round_number,
            "disposition": self.disposition.value,
            "summary": self.summary,
            "action": self.action,
            "action_type": self.action_type.value,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "accepted_portion": self.accepted_portion,
            "rebutted_portion": self.rebutted_portion,
            "residual_risk": self.residual_risk,
            "mitigation_plan": self.mitigation_plan,
            "original_content": self.original_content,
            "revised_content": self.revised_content,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Response":
        # Handle validation by providing defaults
        response = cls.__new__(cls)
        response.id = data.get("id", str(uuid.uuid4()))
        response.critique_id = data.get("critique_id", "unknown")
        response.agent = data.get("agent", "Unknown")
        response.round_number = data.get("round_number", 1)
        response.disposition = Disposition(data.get("disposition", "Acknowledge"))
        response.summary = data.get("summary", "")
        response.action = data.get("action", "")
        response.action_type = ActionType(data.get("action_type", "No Action"))
        response.rationale = data.get("rationale", "")
        response.evidence = data.get("evidence")
        response.accepted_portion = data.get("accepted_portion")
        response.rebutted_portion = data.get("rebutted_portion")
        response.residual_risk = data.get("residual_risk")
        response.mitigation_plan = data.get("mitigation_plan")
        response.original_content = data.get("original_content")
        response.revised_content = data.get("revised_content")
        response.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()
        return response

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Response":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ResponseSummary:
    """
    Summary of responses for a debate round.

    Used for tracking blue team defense effectiveness.
    """

    document_id: str = ""
    round_number: int = 1

    # Counts by disposition
    total: int = 0
    accepted: int = 0
    rebutted: int = 0
    acknowledged: int = 0
    partial_accepted: int = 0
    deferred: int = 0

    # Action counts
    revisions_made: int = 0
    content_added: int = 0
    content_removed: int = 0

    # Risk tracking
    responses_with_residual_risk: int = 0

    @property
    def acceptance_rate(self) -> float:
        """Calculate the rate at which critiques were accepted."""
        if self.total == 0:
            return 0.0
        accepted = self.accepted + self.partial_accepted
        return (accepted / self.total) * 100

    @property
    def rebuttal_rate(self) -> float:
        """Calculate the rate at which critiques were rebutted."""
        if self.total == 0:
            return 0.0
        return (self.rebutted / self.total) * 100

    @classmethod
    def from_responses(
        cls,
        responses: List[Response],
        document_id: str = "",
        round_number: int = 1,
    ) -> "ResponseSummary":
        """Generate a summary from a list of responses."""
        summary = cls(document_id=document_id, round_number=round_number)
        summary.total = len(responses)

        for response in responses:
            # Count by disposition
            if response.disposition == Disposition.ACCEPT:
                summary.accepted += 1
            elif response.disposition == Disposition.REBUT:
                summary.rebutted += 1
            elif response.disposition == Disposition.ACKNOWLEDGE:
                summary.acknowledged += 1
            elif response.disposition == Disposition.PARTIAL_ACCEPT:
                summary.partial_accepted += 1
            elif response.disposition == Disposition.DEFER:
                summary.deferred += 1

            # Count actions
            if response.action_type == ActionType.REVISE_CONTENT:
                summary.revisions_made += 1
            elif response.action_type == ActionType.ADD_CONTENT:
                summary.content_added += 1
            elif response.action_type == ActionType.REMOVE_CONTENT:
                summary.content_removed += 1

            # Track residual risk
            if response.has_residual_risk:
                summary.responses_with_residual_risk += 1

        return summary

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "round_number": self.round_number,
            "total": self.total,
            "accepted": self.accepted,
            "rebutted": self.rebutted,
            "acknowledged": self.acknowledged,
            "partial_accepted": self.partial_accepted,
            "deferred": self.deferred,
            "revisions_made": self.revisions_made,
            "content_added": self.content_added,
            "content_removed": self.content_removed,
            "responses_with_residual_risk": self.responses_with_residual_risk,
            "acceptance_rate": self.acceptance_rate,
            "rebuttal_rate": self.rebuttal_rate,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class DebateExchange:
    """
    A complete critique-response exchange.

    Pairs a critique with its response for tracking the full debate history.
    """

    critique: "Critique" = None  # Forward reference
    response: Optional[Response] = None
    exchange_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    round_number: int = 1

    @property
    def is_resolved(self) -> bool:
        """Check if this exchange has been resolved."""
        return self.response is not None

    @property
    def outcome(self) -> Optional[str]:
        """Get the outcome of this exchange."""
        if self.response is None:
            return None
        return self.response.disposition.value

    def to_dict(self) -> dict:
        # Import here to avoid circular import
        from .critique import Critique

        return {
            "exchange_id": self.exchange_id,
            "round_number": self.round_number,
            "critique": self.critique.to_dict() if self.critique else None,
            "response": self.response.to_dict() if self.response else None,
            "is_resolved": self.is_resolved,
            "outcome": self.outcome,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DebateExchange":
        # Import here to avoid circular import
        from .critique import Critique

        return cls(
            exchange_id=data.get("exchange_id", str(uuid.uuid4())),
            round_number=data.get("round_number", 1),
            critique=Critique.from_dict(data["critique"]) if data.get("critique") else None,
            response=Response.from_dict(data["response"]) if data.get("response") else None,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "DebateExchange":
        return cls.from_dict(json.loads(json_str))
