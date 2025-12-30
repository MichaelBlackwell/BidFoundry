"""
Message Types and Structure

Defines the message types used for agent-to-agent communication
in the adversarial swarm.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any, Union
import json
import uuid


class MessageType(str, Enum):
    """Types of messages that can be exchanged between agents."""

    # Document lifecycle messages
    DRAFT = "Draft"  # Initial document draft from blue team
    REVISION = "Revision"  # Revised document content
    SECTION_UPDATE = "Section Update"  # Update to a specific section

    # Critique messages
    CRITIQUE = "Critique"  # Red team critique of blue team output
    CRITIQUE_BATCH = "Critique Batch"  # Multiple critiques bundled together

    # Response messages
    RESPONSE = "Response"  # Blue team response to critique
    RESPONSE_BATCH = "Response Batch"  # Multiple responses bundled together

    # Synthesis messages
    SYNTHESIS = "Synthesis"  # Final synthesized document
    SUMMARY = "Summary"  # Summary of round or debate

    # Control messages
    ROUND_START = "Round Start"  # Signal start of a debate round
    ROUND_END = "Round End"  # Signal end of a debate round
    REQUEST = "Request"  # Request for specific action
    ACKNOWLEDGMENT = "Acknowledgment"  # Acknowledge receipt

    # System messages
    ERROR = "Error"  # Error notification
    WARNING = "Warning"  # Warning notification
    STATUS = "Status"  # Status update


class MessagePriority(str, Enum):
    """Priority levels for message processing."""

    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    URGENT = "Urgent"


class DeliveryStatus(str, Enum):
    """Status of message delivery."""

    PENDING = "Pending"  # Not yet delivered
    DELIVERED = "Delivered"  # Delivered to recipient
    READ = "Read"  # Recipient has processed
    FAILED = "Failed"  # Delivery failed
    EXPIRED = "Expired"  # Message expired before delivery


@dataclass
class MessagePayload:
    """
    Generic payload container for message content.

    Supports both structured data and raw content.
    """

    content_type: str = "text"  # text, json, markdown, binary
    content: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)

    def get_as_dict(self) -> Dict[str, Any]:
        """Get structured data, parsing from content if needed."""
        if self.structured_data:
            return self.structured_data
        if self.content_type == "json" and self.content:
            return json.loads(self.content)
        return {"content": self.content}

    def to_dict(self) -> dict:
        return {
            "content_type": self.content_type,
            "content": self.content,
            "structured_data": self.structured_data,
            "attachments": self.attachments,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MessagePayload":
        return cls(
            content_type=data.get("content_type", "text"),
            content=data.get("content", ""),
            structured_data=data.get("structured_data", {}),
            attachments=data.get("attachments", []),
        )


@dataclass
class Message:
    """
    An immutable message exchanged between agents.

    Messages are the primary unit of communication in the adversarial swarm.
    They are timestamped, typed, and trackable through the system.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Message classification
    message_type: MessageType = MessageType.DRAFT
    priority: MessagePriority = MessagePriority.NORMAL

    # Source and destination
    sender_role: str = ""  # AgentRole value
    sender_id: Optional[str] = None  # Specific agent instance ID
    recipients: List[str] = field(default_factory=list)  # List of AgentRole values
    broadcast: bool = False  # If True, message goes to all agents in recipients' categories

    # Content
    payload: MessagePayload = field(default_factory=MessagePayload)

    # Context
    round_number: int = 1
    session_id: Optional[str] = None
    document_id: Optional[str] = None
    section_name: Optional[str] = None

    # Threading
    parent_id: Optional[str] = None  # ID of message this is responding to
    thread_id: Optional[str] = None  # ID of the thread this belongs to

    # Delivery tracking
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    delivered_to: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # Timestamps (immutable after creation)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        """Set thread_id to message id if not provided (starts new thread)."""
        if self.thread_id is None:
            self.thread_id = self.parent_id if self.parent_id else self.id

    @property
    def is_expired(self) -> bool:
        """Check if the message has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_delivered(self) -> bool:
        """Check if message has been delivered to all recipients."""
        if self.broadcast:
            return self.delivery_status == DeliveryStatus.DELIVERED
        return len(self.delivered_to) >= len(self.recipients)

    @property
    def is_critique(self) -> bool:
        """Check if this is a critique message."""
        return self.message_type in {MessageType.CRITIQUE, MessageType.CRITIQUE_BATCH}

    @property
    def is_response(self) -> bool:
        """Check if this is a response message."""
        return self.message_type in {MessageType.RESPONSE, MessageType.RESPONSE_BATCH}

    @property
    def is_control(self) -> bool:
        """Check if this is a control message."""
        return self.message_type in {
            MessageType.ROUND_START,
            MessageType.ROUND_END,
            MessageType.REQUEST,
            MessageType.ACKNOWLEDGMENT,
        }

    @property
    def is_system(self) -> bool:
        """Check if this is a system message."""
        return self.message_type in {
            MessageType.ERROR,
            MessageType.WARNING,
            MessageType.STATUS,
        }

    def get_content(self) -> str:
        """Get the message content as a string."""
        return self.payload.content

    def get_structured_data(self) -> Dict[str, Any]:
        """Get structured data from the payload."""
        return self.payload.get_as_dict()

    def mark_delivered(self, recipient: str) -> None:
        """Mark message as delivered to a recipient."""
        if recipient not in self.delivered_to:
            self.delivered_to.append(recipient)
        if self.is_delivered:
            self.delivery_status = DeliveryStatus.DELIVERED

    def mark_read(self) -> None:
        """Mark message as read/processed."""
        self.delivery_status = DeliveryStatus.READ

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "sender_role": self.sender_role,
            "sender_id": self.sender_id,
            "recipients": self.recipients,
            "broadcast": self.broadcast,
            "payload": self.payload.to_dict(),
            "round_number": self.round_number,
            "session_id": self.session_id,
            "document_id": self.document_id,
            "section_name": self.section_name,
            "parent_id": self.parent_id,
            "thread_id": self.thread_id,
            "delivery_status": self.delivery_status.value,
            "delivered_to": self.delivered_to,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        msg = cls.__new__(cls)
        msg.id = data.get("id", str(uuid.uuid4()))
        msg.message_type = MessageType(data.get("message_type", "Draft"))
        msg.priority = MessagePriority(data.get("priority", "Normal"))
        msg.sender_role = data.get("sender_role", "")
        msg.sender_id = data.get("sender_id")
        msg.recipients = data.get("recipients", [])
        msg.broadcast = data.get("broadcast", False)
        msg.payload = MessagePayload.from_dict(data.get("payload", {}))
        msg.round_number = data.get("round_number", 1)
        msg.session_id = data.get("session_id")
        msg.document_id = data.get("document_id")
        msg.section_name = data.get("section_name")
        msg.parent_id = data.get("parent_id")
        msg.thread_id = data.get("thread_id", msg.parent_id if msg.parent_id else msg.id)
        msg.delivery_status = DeliveryStatus(data.get("delivery_status", "Pending"))
        msg.delivered_to = data.get("delivered_to", [])
        msg.metadata = data.get("metadata", {})
        msg.tags = data.get("tags", [])
        msg.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc)
        msg.expires_at = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        return msg

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        return cls.from_dict(json.loads(json_str))


def create_draft_message(
    sender_role: str,
    content: str,
    document_id: str,
    recipients: Optional[List[str]] = None,
    round_number: int = 1,
    section_name: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Message:
    """Factory function to create a draft message."""
    return Message(
        message_type=MessageType.DRAFT,
        sender_role=sender_role,
        recipients=recipients or [],
        payload=MessagePayload(content_type="markdown", content=content),
        document_id=document_id,
        section_name=section_name,
        round_number=round_number,
        session_id=session_id,
    )


def create_critique_message(
    sender_role: str,
    critique_data: Dict[str, Any],
    parent_message_id: str,
    recipients: Optional[List[str]] = None,
    round_number: int = 1,
    session_id: Optional[str] = None,
) -> Message:
    """Factory function to create a critique message."""
    return Message(
        message_type=MessageType.CRITIQUE,
        sender_role=sender_role,
        recipients=recipients or [],
        payload=MessagePayload(
            content_type="json",
            content=json.dumps(critique_data),
            structured_data=critique_data,
        ),
        parent_id=parent_message_id,
        round_number=round_number,
        session_id=session_id,
        priority=MessagePriority.HIGH,
    )


def create_response_message(
    sender_role: str,
    response_data: Dict[str, Any],
    critique_message_id: str,
    recipients: Optional[List[str]] = None,
    round_number: int = 1,
    session_id: Optional[str] = None,
) -> Message:
    """Factory function to create a response message."""
    return Message(
        message_type=MessageType.RESPONSE,
        sender_role=sender_role,
        recipients=recipients or [],
        payload=MessagePayload(
            content_type="json",
            content=json.dumps(response_data),
            structured_data=response_data,
        ),
        parent_id=critique_message_id,
        round_number=round_number,
        session_id=session_id,
    )


def create_control_message(
    sender_role: str,
    message_type: MessageType,
    data: Optional[Dict[str, Any]] = None,
    broadcast: bool = True,
    round_number: int = 1,
    session_id: Optional[str] = None,
) -> Message:
    """Factory function to create a control message."""
    return Message(
        message_type=message_type,
        sender_role=sender_role,
        recipients=[],
        broadcast=broadcast,
        payload=MessagePayload(
            content_type="json",
            structured_data=data or {},
        ),
        round_number=round_number,
        session_id=session_id,
        priority=MessagePriority.HIGH,
    )


def create_status_message(
    sender_role: str,
    status_type: str,
    data: Optional[Dict[str, Any]] = None,
    round_number: int = 1,
    session_id: Optional[str] = None,
) -> Message:
    """Factory function to create a status message (e.g., agent_thinking, agent_streaming).

    Args:
        sender_role: The agent role sending the status
        status_type: Type of status (e.g., 'agent_thinking', 'agent_streaming', 'confidence_update')
        data: Additional data for the status message
        round_number: Current round number
        session_id: Optional session ID
    """
    return Message(
        message_type=MessageType.STATUS,
        sender_role=sender_role,
        recipients=[],
        broadcast=True,
        payload=MessagePayload(
            content_type="json",
            structured_data={
                "type": status_type,
                "agent_id": sender_role.lower().replace(" ", "_"),
                "agent_role": sender_role,
                **(data or {}),
            },
        ),
        round_number=round_number,
        session_id=session_id,
    )
