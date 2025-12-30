"""
Conversation History Tracker

Provides queryable history of the adversarial debate, including
messages, critiques, responses, and round summaries.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set, Tuple
from collections import defaultdict
import json
import uuid

from .message import Message, MessageType


@dataclass
class ExchangeRecord:
    """
    Record of a single critique-response exchange.

    Tracks the full lifecycle of a critique from creation to resolution.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    round_number: int = 1

    # Critique details
    critique_message_id: str = ""
    critique_agent: str = ""
    critique_type: str = ""  # ChallengeType value
    critique_severity: str = ""  # Severity value
    critique_summary: str = ""
    target_section: str = ""

    # Response details
    response_message_id: Optional[str] = None
    response_agent: Optional[str] = None
    response_disposition: Optional[str] = None  # Disposition value
    response_summary: Optional[str] = None

    # Resolution
    is_resolved: bool = False
    resolution_outcome: Optional[str] = None  # accepted, rebutted, acknowledged

    # Timestamps
    critique_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "round_number": self.round_number,
            "critique_message_id": self.critique_message_id,
            "critique_agent": self.critique_agent,
            "critique_type": self.critique_type,
            "critique_severity": self.critique_severity,
            "critique_summary": self.critique_summary,
            "target_section": self.target_section,
            "response_message_id": self.response_message_id,
            "response_agent": self.response_agent,
            "response_disposition": self.response_disposition,
            "response_summary": self.response_summary,
            "is_resolved": self.is_resolved,
            "resolution_outcome": self.resolution_outcome,
            "critique_at": self.critique_at.isoformat(),
            "response_at": self.response_at.isoformat() if self.response_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExchangeRecord":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            round_number=data.get("round_number", 1),
            critique_message_id=data.get("critique_message_id", ""),
            critique_agent=data.get("critique_agent", ""),
            critique_type=data.get("critique_type", ""),
            critique_severity=data.get("critique_severity", ""),
            critique_summary=data.get("critique_summary", ""),
            target_section=data.get("target_section", ""),
            response_message_id=data.get("response_message_id"),
            response_agent=data.get("response_agent"),
            response_disposition=data.get("response_disposition"),
            response_summary=data.get("response_summary"),
            is_resolved=data.get("is_resolved", False),
            resolution_outcome=data.get("resolution_outcome"),
            critique_at=datetime.fromisoformat(data["critique_at"]) if data.get("critique_at") else datetime.now(timezone.utc),
            response_at=datetime.fromisoformat(data["response_at"]) if data.get("response_at") else None,
        )


@dataclass
class RoundRecord:
    """
    Record of activity within a single debate round.

    Summarizes the exchanges and outcomes for a round.
    """

    round_number: int = 1
    round_type: str = "BlueBuild"  # BlueBuild, RedAttack, BlueDefense, Synthesis

    # Activity tracking
    exchanges: List[ExchangeRecord] = field(default_factory=list)
    message_count: int = 0
    critique_count: int = 0
    response_count: int = 0

    # Participation
    active_agents: Set[str] = field(default_factory=set)
    blue_team_agents: Set[str] = field(default_factory=set)
    red_team_agents: Set[str] = field(default_factory=set)

    # Outcomes
    critiques_by_severity: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    responses_by_disposition: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    sections_affected: Set[str] = field(default_factory=set)

    # Timing
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get round duration in seconds."""
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None

    @property
    def resolution_rate(self) -> float:
        """Calculate the percentage of critiques that were resolved."""
        if not self.exchanges:
            return 100.0
        resolved = sum(1 for e in self.exchanges if e.is_resolved)
        return (resolved / len(self.exchanges)) * 100

    @property
    def pending_critiques(self) -> List[ExchangeRecord]:
        """Get unresolved exchanges."""
        return [e for e in self.exchanges if not e.is_resolved]

    def add_exchange(self, exchange: ExchangeRecord) -> None:
        """Add an exchange to the round."""
        self.exchanges.append(exchange)
        self.critique_count += 1
        self.active_agents.add(exchange.critique_agent)
        self.red_team_agents.add(exchange.critique_agent)
        self.sections_affected.add(exchange.target_section)
        self.critiques_by_severity[exchange.critique_severity] = (
            self.critiques_by_severity.get(exchange.critique_severity, 0) + 1
        )

    def resolve_exchange(
        self,
        exchange_id: str,
        response_message_id: str,
        response_agent: str,
        disposition: str,
        summary: str,
    ) -> bool:
        """
        Record a response to a critique.

        Returns True if exchange was found and updated.
        """
        for exchange in self.exchanges:
            if exchange.id == exchange_id:
                exchange.response_message_id = response_message_id
                exchange.response_agent = response_agent
                exchange.response_disposition = disposition
                exchange.response_summary = summary
                exchange.is_resolved = True
                exchange.response_at = datetime.now(timezone.utc)

                # Map disposition to outcome
                if disposition in ("Accept", "Partial Accept"):
                    exchange.resolution_outcome = "accepted"
                elif disposition == "Rebut":
                    exchange.resolution_outcome = "rebutted"
                else:
                    exchange.resolution_outcome = "acknowledged"

                self.response_count += 1
                self.active_agents.add(response_agent)
                self.blue_team_agents.add(response_agent)
                self.responses_by_disposition[disposition] = (
                    self.responses_by_disposition.get(disposition, 0) + 1
                )
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "round_type": self.round_type,
            "exchanges": [e.to_dict() for e in self.exchanges],
            "message_count": self.message_count,
            "critique_count": self.critique_count,
            "response_count": self.response_count,
            "active_agents": list(self.active_agents),
            "blue_team_agents": list(self.blue_team_agents),
            "red_team_agents": list(self.red_team_agents),
            "critiques_by_severity": dict(self.critiques_by_severity),
            "responses_by_disposition": dict(self.responses_by_disposition),
            "sections_affected": list(self.sections_affected),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "resolution_rate": self.resolution_rate,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RoundRecord":
        record = cls(
            round_number=data.get("round_number", 1),
            round_type=data.get("round_type", "BlueBuild"),
            message_count=data.get("message_count", 0),
            critique_count=data.get("critique_count", 0),
            response_count=data.get("response_count", 0),
            active_agents=set(data.get("active_agents", [])),
            blue_team_agents=set(data.get("blue_team_agents", [])),
            red_team_agents=set(data.get("red_team_agents", [])),
            sections_affected=set(data.get("sections_affected", [])),
        )
        record.exchanges = [ExchangeRecord.from_dict(e) for e in data.get("exchanges", [])]
        record.critiques_by_severity = defaultdict(int, data.get("critiques_by_severity", {}))
        record.responses_by_disposition = defaultdict(int, data.get("responses_by_disposition", {}))
        record.started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        record.ended_at = datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None
        return record


class ConversationHistory:
    """
    Queryable history of the adversarial debate.

    Tracks all messages, exchanges, and round summaries throughout
    the document generation process.
    """

    def __init__(self, session_id: Optional[str] = None, document_id: Optional[str] = None):
        """
        Initialize conversation history.

        Args:
            session_id: Optional session identifier
            document_id: Optional document identifier
        """
        self._session_id = session_id or str(uuid.uuid4())
        self._document_id = document_id

        # Message storage
        self._messages: List[Message] = []
        self._message_index: Dict[str, Message] = {}

        # Round tracking
        self._rounds: Dict[int, RoundRecord] = {}
        self._current_round: int = 0

        # Exchange tracking
        self._exchanges: Dict[str, ExchangeRecord] = {}
        self._exchanges_by_critique: Dict[str, str] = {}  # critique_msg_id -> exchange_id

        # Agent participation
        self._agent_messages: Dict[str, List[str]] = defaultdict(list)  # agent -> message_ids

        # Section tracking
        self._section_history: Dict[str, List[str]] = defaultdict(list)  # section -> message_ids

        # Timestamps
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)

    @property
    def session_id(self) -> str:
        """Get the session ID."""
        return self._session_id

    @property
    def document_id(self) -> Optional[str]:
        """Get the document ID."""
        return self._document_id

    @property
    def current_round(self) -> int:
        """Get the current round number."""
        return self._current_round

    @property
    def total_messages(self) -> int:
        """Get total message count."""
        return len(self._messages)

    @property
    def total_exchanges(self) -> int:
        """Get total exchange count."""
        return len(self._exchanges)

    def record_message(self, message: Message) -> None:
        """
        Record a message in the history.

        Args:
            message: The message to record
        """
        self._messages.append(message)
        self._message_index[message.id] = message
        self._agent_messages[message.sender_role].append(message.id)

        if message.section_name:
            self._section_history[message.section_name].append(message.id)

        # Update round message count
        if message.round_number in self._rounds:
            self._rounds[message.round_number].message_count += 1

        # Track critique-response exchanges
        if message.is_critique:
            self._record_critique(message)
        elif message.is_response and message.parent_id:
            self._record_response(message)

        self._updated_at = datetime.now(timezone.utc)

    def _record_critique(self, message: Message) -> None:
        """Record a critique message as a new exchange."""
        data = message.get_structured_data()

        exchange = ExchangeRecord(
            round_number=message.round_number,
            critique_message_id=message.id,
            critique_agent=message.sender_role,
            critique_type=data.get("challenge_type", ""),
            critique_severity=data.get("severity", ""),
            critique_summary=data.get("title", data.get("argument", "")[:100]),
            target_section=data.get("target_section", message.section_name or ""),
            critique_at=message.created_at,
        )

        self._exchanges[exchange.id] = exchange
        self._exchanges_by_critique[message.id] = exchange.id

        # Add to round
        if message.round_number in self._rounds:
            self._rounds[message.round_number].add_exchange(exchange)

    def _record_response(self, message: Message) -> None:
        """Record a response message and link to its critique."""
        # Find the exchange for this response
        parent_msg = self._message_index.get(message.parent_id)
        if not parent_msg:
            return

        exchange_id = self._exchanges_by_critique.get(message.parent_id)
        if not exchange_id:
            return

        data = message.get_structured_data()

        # Update the round record
        if message.round_number in self._rounds:
            self._rounds[message.round_number].resolve_exchange(
                exchange_id=exchange_id,
                response_message_id=message.id,
                response_agent=message.sender_role,
                disposition=data.get("disposition", "Acknowledge"),
                summary=data.get("summary", ""),
            )

    def start_round(self, round_number: int, round_type: str = "BlueBuild") -> RoundRecord:
        """
        Start a new round.

        Args:
            round_number: The round number
            round_type: Type of round (BlueBuild, RedAttack, BlueDefense, Synthesis)

        Returns:
            The new RoundRecord
        """
        record = RoundRecord(
            round_number=round_number,
            round_type=round_type,
            started_at=datetime.now(timezone.utc),
        )
        self._rounds[round_number] = record
        self._current_round = round_number
        return record

    def end_round(self, round_number: int) -> Optional[RoundRecord]:
        """
        End a round.

        Args:
            round_number: The round number to end

        Returns:
            The RoundRecord if found
        """
        if round_number in self._rounds:
            self._rounds[round_number].ended_at = datetime.now(timezone.utc)
            return self._rounds[round_number]
        return None

    def get_round(self, round_number: int) -> Optional[RoundRecord]:
        """Get a specific round record."""
        return self._rounds.get(round_number)

    def get_all_rounds(self) -> List[RoundRecord]:
        """Get all round records in order."""
        return [self._rounds[r] for r in sorted(self._rounds.keys())]

    def get_message(self, message_id: str) -> Optional[Message]:
        """Get a specific message by ID."""
        return self._message_index.get(message_id)

    def get_messages(
        self,
        round_number: Optional[int] = None,
        message_type: Optional[MessageType] = None,
        agent_role: Optional[str] = None,
        section_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        Query messages with optional filters.

        Args:
            round_number: Filter by round
            message_type: Filter by message type
            agent_role: Filter by sender role
            section_name: Filter by section
            limit: Maximum number of messages

        Returns:
            List of matching messages, sorted by creation time
        """
        messages = self._messages.copy()

        if round_number is not None:
            messages = [m for m in messages if m.round_number == round_number]

        if message_type is not None:
            messages = [m for m in messages if m.message_type == message_type]

        if agent_role is not None:
            messages = [m for m in messages if m.sender_role == agent_role]

        if section_name is not None:
            messages = [m for m in messages if m.section_name == section_name]

        # Sort by creation time
        messages.sort(key=lambda m: m.created_at)

        if limit:
            messages = messages[:limit]

        return messages

    def get_exchanges(
        self,
        round_number: Optional[int] = None,
        resolved_only: bool = False,
        unresolved_only: bool = False,
    ) -> List[ExchangeRecord]:
        """
        Query exchanges with optional filters.

        Args:
            round_number: Filter by round
            resolved_only: Only return resolved exchanges
            unresolved_only: Only return unresolved exchanges

        Returns:
            List of matching exchanges
        """
        exchanges = list(self._exchanges.values())

        if round_number is not None:
            exchanges = [e for e in exchanges if e.round_number == round_number]

        if resolved_only:
            exchanges = [e for e in exchanges if e.is_resolved]

        if unresolved_only:
            exchanges = [e for e in exchanges if not e.is_resolved]

        return sorted(exchanges, key=lambda e: e.critique_at)

    def get_agent_participation(self) -> Dict[str, Dict[str, Any]]:
        """
        Get participation statistics for each agent.

        Returns:
            Dictionary mapping agent role to participation stats
        """
        result = {}
        for agent_role, message_ids in self._agent_messages.items():
            messages = [self._message_index[mid] for mid in message_ids if mid in self._message_index]
            result[agent_role] = {
                "message_count": len(messages),
                "rounds_participated": list(set(m.round_number for m in messages)),
                "message_types": list(set(m.message_type.value for m in messages)),
                "critiques_made": sum(1 for m in messages if m.is_critique),
                "responses_made": sum(1 for m in messages if m.is_response),
            }
        return result

    def get_section_activity(self, section_name: str) -> Dict[str, Any]:
        """
        Get activity summary for a specific section.

        Args:
            section_name: The section name

        Returns:
            Dictionary with section activity stats
        """
        message_ids = self._section_history.get(section_name, [])
        messages = [self._message_index[mid] for mid in message_ids if mid in self._message_index]

        critiques = [m for m in messages if m.is_critique]
        responses = [m for m in messages if m.is_response]

        return {
            "section_name": section_name,
            "total_messages": len(messages),
            "critique_count": len(critiques),
            "response_count": len(responses),
            "agents_involved": list(set(m.sender_role for m in messages)),
            "rounds_with_activity": list(set(m.round_number for m in messages)),
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the conversation history.

        Returns:
            Dictionary with conversation statistics
        """
        all_exchanges = list(self._exchanges.values())
        resolved = [e for e in all_exchanges if e.is_resolved]
        unresolved = [e for e in all_exchanges if not e.is_resolved]

        # Outcome breakdown
        outcome_counts = defaultdict(int)
        for e in resolved:
            outcome_counts[e.resolution_outcome or "unknown"] += 1

        return {
            "session_id": self._session_id,
            "document_id": self._document_id,
            "total_rounds": len(self._rounds),
            "current_round": self._current_round,
            "total_messages": len(self._messages),
            "total_exchanges": len(all_exchanges),
            "resolved_exchanges": len(resolved),
            "unresolved_exchanges": len(unresolved),
            "resolution_rate": (len(resolved) / len(all_exchanges) * 100) if all_exchanges else 100.0,
            "outcome_breakdown": dict(outcome_counts),
            "agents_participated": list(self._agent_messages.keys()),
            "sections_affected": list(self._section_history.keys()),
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
        }

    def to_dict(self) -> dict:
        """Serialize the entire history to a dictionary."""
        return {
            "session_id": self._session_id,
            "document_id": self._document_id,
            "messages": [m.to_dict() for m in self._messages],
            "rounds": {str(k): v.to_dict() for k, v in self._rounds.items()},
            "exchanges": {k: v.to_dict() for k, v in self._exchanges.items()},
            "current_round": self._current_round,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationHistory":
        """Deserialize from a dictionary."""
        history = cls(
            session_id=data.get("session_id"),
            document_id=data.get("document_id"),
        )

        # Restore messages
        for msg_data in data.get("messages", []):
            msg = Message.from_dict(msg_data)
            history._messages.append(msg)
            history._message_index[msg.id] = msg
            history._agent_messages[msg.sender_role].append(msg.id)
            if msg.section_name:
                history._section_history[msg.section_name].append(msg.id)

        # Restore rounds
        for round_num_str, round_data in data.get("rounds", {}).items():
            history._rounds[int(round_num_str)] = RoundRecord.from_dict(round_data)

        # Restore exchanges
        for ex_id, ex_data in data.get("exchanges", {}).items():
            exchange = ExchangeRecord.from_dict(ex_data)
            history._exchanges[ex_id] = exchange
            history._exchanges_by_critique[exchange.critique_message_id] = ex_id

        history._current_round = data.get("current_round", 0)
        history._created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc)
        history._updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(timezone.utc)

        return history

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ConversationHistory":
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))
