"""
Unit Tests for Communication Layer (Chunk 3)

Tests for Message, MessageBus, ConversationHistory, and RoundManager.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta

from comms import (
    # Message types
    Message,
    MessageType,
    MessagePriority,
    MessagePayload,
    DeliveryStatus,
    create_draft_message,
    create_critique_message,
    create_response_message,
    create_control_message,
    # Message bus
    MessageBus,
    MessageBusConfig,
    # History
    ConversationHistory,
    ExchangeRecord,
    RoundRecord,
    # Round management
    RoundManager,
    RoundType,
    RoundPhase,
    RoundSummary,
    RoundConfig,
)


# =============================================================================
# Message Tests
# =============================================================================

class TestMessagePayload:
    """Tests for MessagePayload dataclass."""

    def test_create_text_payload(self):
        """Test creating a text payload."""
        payload = MessagePayload(content_type="text", content="Hello, world!")
        assert payload.content_type == "text"
        assert payload.content == "Hello, world!"
        assert payload.structured_data == {}

    def test_create_json_payload(self):
        """Test creating a JSON payload."""
        data = {"key": "value", "number": 42}
        payload = MessagePayload(
            content_type="json",
            content=json.dumps(data),
            structured_data=data,
        )
        assert payload.content_type == "json"
        assert payload.get_as_dict() == data

    def test_payload_serialization(self):
        """Test payload serialization/deserialization."""
        original = MessagePayload(
            content_type="markdown",
            content="# Header\n\nBody text",
            structured_data={"meta": "data"},
        )
        data = original.to_dict()
        restored = MessagePayload.from_dict(data)

        assert restored.content_type == original.content_type
        assert restored.content == original.content
        assert restored.structured_data == original.structured_data


class TestMessage:
    """Tests for Message dataclass."""

    def test_create_message(self):
        """Test creating a basic message."""
        msg = Message(
            message_type=MessageType.DRAFT,
            sender_role="Strategy Architect",
            recipients=["Market Analyst"],
            payload=MessagePayload(content="Draft content"),
        )

        assert msg.id is not None
        assert msg.message_type == MessageType.DRAFT
        assert msg.sender_role == "Strategy Architect"
        assert "Market Analyst" in msg.recipients
        assert msg.created_at is not None

    def test_message_thread_id_auto_set(self):
        """Test that thread_id is automatically set."""
        msg = Message(sender_role="Test")
        assert msg.thread_id == msg.id

    def test_message_thread_id_from_parent(self):
        """Test that thread_id is set from parent_id."""
        parent_id = "parent-123"
        msg = Message(sender_role="Test", parent_id=parent_id)
        assert msg.thread_id == parent_id

    def test_message_is_expired(self):
        """Test message expiration check."""
        # Not expired
        msg = Message(
            sender_role="Test",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert not msg.is_expired

        # Expired
        msg_expired = Message(
            sender_role="Test",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert msg_expired.is_expired

    def test_message_delivery_tracking(self):
        """Test delivery status tracking."""
        msg = Message(
            sender_role="Test",
            recipients=["Agent1", "Agent2"],
        )
        assert msg.delivery_status == DeliveryStatus.PENDING
        assert not msg.is_delivered

        msg.mark_delivered("Agent1")
        assert "Agent1" in msg.delivered_to
        assert not msg.is_delivered  # Still waiting for Agent2

        msg.mark_delivered("Agent2")
        assert msg.is_delivered
        assert msg.delivery_status == DeliveryStatus.DELIVERED

    def test_message_type_checks(self):
        """Test message type helper properties."""
        critique = Message(message_type=MessageType.CRITIQUE, sender_role="Test")
        assert critique.is_critique
        assert not critique.is_response
        assert not critique.is_control

        response = Message(message_type=MessageType.RESPONSE, sender_role="Test")
        assert response.is_response
        assert not response.is_critique

        control = Message(message_type=MessageType.ROUND_START, sender_role="Test")
        assert control.is_control
        assert not control.is_critique

    def test_message_serialization(self):
        """Test message serialization/deserialization."""
        original = Message(
            message_type=MessageType.CRITIQUE,
            sender_role="Devil's Advocate",
            recipients=["Strategy Architect"],
            payload=MessagePayload(
                content_type="json",
                structured_data={"severity": "major"},
            ),
            round_number=2,
            document_id="doc-123",
        )

        # To dict and back
        data = original.to_dict()
        restored = Message.from_dict(data)

        assert restored.id == original.id
        assert restored.message_type == original.message_type
        assert restored.sender_role == original.sender_role
        assert restored.round_number == original.round_number

        # To JSON and back
        json_str = original.to_json()
        from_json = Message.from_json(json_str)
        assert from_json.id == original.id


class TestMessageFactories:
    """Tests for message factory functions."""

    def test_create_draft_message(self):
        """Test draft message factory."""
        msg = create_draft_message(
            sender_role="Strategy Architect",
            content="# Draft Document\n\nContent here",
            document_id="doc-123",
            section_name="Executive Summary",
            round_number=1,
        )

        assert msg.message_type == MessageType.DRAFT
        assert msg.sender_role == "Strategy Architect"
        assert msg.document_id == "doc-123"
        assert msg.section_name == "Executive Summary"
        assert msg.payload.content_type == "markdown"

    def test_create_critique_message(self):
        """Test critique message factory."""
        critique_data = {
            "challenge_type": "logic",
            "severity": "major",
            "argument": "This claim is unsupported",
        }
        msg = create_critique_message(
            sender_role="Devil's Advocate",
            critique_data=critique_data,
            parent_message_id="draft-123",
            round_number=2,
        )

        assert msg.message_type == MessageType.CRITIQUE
        assert msg.parent_id == "draft-123"
        assert msg.priority == MessagePriority.HIGH
        assert msg.get_structured_data()["severity"] == "major"

    def test_create_response_message(self):
        """Test response message factory."""
        response_data = {
            "disposition": "Accept",
            "action": "Revising the section",
        }
        msg = create_response_message(
            sender_role="Strategy Architect",
            response_data=response_data,
            critique_message_id="critique-123",
        )

        assert msg.message_type == MessageType.RESPONSE
        assert msg.parent_id == "critique-123"

    def test_create_control_message(self):
        """Test control message factory."""
        msg = create_control_message(
            sender_role="Arbiter",
            message_type=MessageType.ROUND_START,
            data={"round_number": 1},
            broadcast=True,
        )

        assert msg.message_type == MessageType.ROUND_START
        assert msg.broadcast is True
        assert msg.priority == MessagePriority.HIGH


# =============================================================================
# MessageBus Tests
# =============================================================================

class TestMessageBus:
    """Tests for MessageBus class."""

    @pytest.fixture
    def bus(self):
        """Create a message bus for testing."""
        return MessageBus()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus):
        """Test basic subscribe and publish."""
        received_messages = []

        async def handler(msg):
            received_messages.append(msg)

        await bus.start()
        try:
            # Subscribe
            sub_id = await bus.subscribe(
                agent_role="Test Agent",
                message_types=[MessageType.DRAFT],
                handler=handler,
            )
            assert sub_id is not None

            # Publish
            msg = Message(
                message_type=MessageType.DRAFT,
                sender_role="Sender",
                recipients=["Test Agent"],
            )
            await bus.publish(msg, wait_for_delivery=True)

            # Wait for processing
            await bus.wait_for_queue_empty(timeout=5.0)

            assert len(received_messages) == 1
            assert received_messages[0].id == msg.id
        finally:
            await bus.stop()

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        """Test unsubscribing."""
        await bus.start()
        try:
            sub_id = await bus.subscribe(
                agent_role="Test Agent",
                message_types=[MessageType.DRAFT],
            )

            result = await bus.unsubscribe(sub_id)
            assert result is True

            # Unsubscribing again should fail
            result = await bus.unsubscribe(sub_id)
            assert result is False
        finally:
            await bus.stop()

    @pytest.mark.asyncio
    async def test_message_filtering(self, bus):
        """Test that messages are filtered by type."""
        draft_received = []
        critique_received = []

        async def draft_handler(msg):
            draft_received.append(msg)

        async def critique_handler(msg):
            critique_received.append(msg)

        await bus.start()
        try:
            await bus.subscribe(
                agent_role="Draft Handler",
                message_types=[MessageType.DRAFT],
                handler=draft_handler,
            )
            await bus.subscribe(
                agent_role="Critique Handler",
                message_types=[MessageType.CRITIQUE],
                handler=critique_handler,
            )

            # Publish draft
            draft = Message(
                message_type=MessageType.DRAFT,
                sender_role="Sender",
                broadcast=True,
            )
            await bus.publish(draft)

            # Publish critique
            critique = Message(
                message_type=MessageType.CRITIQUE,
                sender_role="Sender",
                broadcast=True,
            )
            await bus.publish(critique)

            await bus.wait_for_queue_empty(timeout=5.0)

            assert len(draft_received) == 1
            assert len(critique_received) == 1
        finally:
            await bus.stop()

    def test_get_history(self, bus):
        """Test getting message history (sync, no processing needed)."""
        # Add messages directly for testing history
        msg1 = Message(message_type=MessageType.DRAFT, sender_role="A", round_number=1)
        msg2 = Message(message_type=MessageType.CRITIQUE, sender_role="B", round_number=1)
        msg3 = Message(message_type=MessageType.DRAFT, sender_role="A", round_number=2)

        bus._messages = [msg1, msg2, msg3]
        bus._message_index = {m.id: m for m in bus._messages}
        bus._messages_by_round[1] = [msg1, msg2]
        bus._messages_by_round[2] = [msg3]
        bus._messages_by_type[MessageType.DRAFT] = [msg1, msg3]
        bus._messages_by_type[MessageType.CRITIQUE] = [msg2]

        # Filter by round
        round1 = bus.get_history(round_number=1)
        assert len(round1) == 2

        # Filter by type
        drafts = bus.get_history(message_type=MessageType.DRAFT)
        assert len(drafts) == 2

        # Filter by sender
        from_a = bus.get_history(sender_role="A")
        assert len(from_a) == 2


# =============================================================================
# ConversationHistory Tests
# =============================================================================

class TestConversationHistory:
    """Tests for ConversationHistory class."""

    @pytest.fixture
    def history(self):
        """Create a conversation history for testing."""
        return ConversationHistory(document_id="test-doc")

    def test_record_message(self, history):
        """Test recording a message."""
        msg = Message(
            message_type=MessageType.DRAFT,
            sender_role="Strategy Architect",
            section_name="Executive Summary",
        )
        history.record_message(msg)

        assert history.total_messages == 1
        assert history.get_message(msg.id) is not None

    def test_start_and_end_round(self, history):
        """Test round lifecycle."""
        record = history.start_round(1, "BlueBuild")
        assert record.round_number == 1
        assert history.current_round == 1

        ended = history.end_round(1)
        assert ended is not None
        assert ended.ended_at is not None

    def test_record_critique_exchange(self, history):
        """Test recording critique-response exchanges."""
        history.start_round(1, "RedAttack")

        # Record critique
        critique = Message(
            message_type=MessageType.CRITIQUE,
            sender_role="Devil's Advocate",
            payload=MessagePayload(
                content_type="json",
                structured_data={
                    "challenge_type": "logic",
                    "severity": "major",
                    "title": "Test critique",
                    "target_section": "Executive Summary",
                },
            ),
            round_number=1,
        )
        history.record_message(critique)

        assert history.total_exchanges == 1

        # Record response
        response = Message(
            message_type=MessageType.RESPONSE,
            sender_role="Strategy Architect",
            parent_id=critique.id,
            payload=MessagePayload(
                content_type="json",
                structured_data={
                    "disposition": "Accept",
                    "summary": "Will fix",
                },
            ),
            round_number=1,
        )
        history.record_message(response)

        # Check exchange was resolved
        exchanges = history.get_exchanges(resolved_only=True)
        assert len(exchanges) == 1

    def test_query_messages(self, history):
        """Test querying messages with filters."""
        history.start_round(1, "BlueBuild")

        msg1 = Message(
            message_type=MessageType.DRAFT,
            sender_role="Strategy Architect",
            round_number=1,
        )
        msg2 = Message(
            message_type=MessageType.CRITIQUE,
            sender_role="Devil's Advocate",
            round_number=1,
        )
        history.record_message(msg1)
        history.record_message(msg2)

        # Query by role
        from_sa = history.get_messages(agent_role="Strategy Architect")
        assert len(from_sa) == 1

        # Query by type
        critiques = history.get_messages(message_type=MessageType.CRITIQUE)
        assert len(critiques) == 1

    def test_get_summary(self, history):
        """Test getting conversation summary."""
        history.start_round(1, "BlueBuild")

        msg = Message(
            message_type=MessageType.DRAFT,
            sender_role="Strategy Architect",
            section_name="Overview",
        )
        history.record_message(msg)
        history.end_round(1)

        summary = history.get_summary()
        assert summary["total_rounds"] == 1
        assert summary["total_messages"] == 1
        assert "Strategy Architect" in summary["agents_participated"]

    def test_serialization(self, history):
        """Test history serialization/deserialization."""
        history.start_round(1, "BlueBuild")
        msg = Message(message_type=MessageType.DRAFT, sender_role="Test")
        history.record_message(msg)
        history.end_round(1)

        # To dict and back
        data = history.to_dict()
        restored = ConversationHistory.from_dict(data)

        assert restored.session_id == history.session_id
        assert restored.total_messages == 1

        # To JSON and back
        json_str = history.to_json()
        from_json = ConversationHistory.from_json(json_str)
        assert from_json.total_messages == 1


# =============================================================================
# RoundManager Tests
# =============================================================================

class TestRoundManager:
    """Tests for RoundManager class."""

    @pytest.fixture
    def manager(self):
        """Create a round manager for testing."""
        return RoundManager(max_adversarial_rounds=3)

    def test_start_round(self, manager):
        """Test starting a round."""
        round_num = manager.start_round(RoundType.BLUE_BUILD)

        assert round_num == 1
        assert manager.current_round == 1
        assert manager.current_type == RoundType.BLUE_BUILD
        assert manager.is_active

    def test_end_round(self, manager):
        """Test ending a round."""
        manager.start_round(RoundType.BLUE_BUILD)
        summary = manager.end_round()

        assert summary.round_number == 1
        assert summary.round_type == RoundType.BLUE_BUILD
        assert summary.duration_seconds >= 0
        assert not manager.is_active

    def test_cannot_start_while_active(self, manager):
        """Test that starting a round while one is active raises error."""
        manager.start_round(RoundType.BLUE_BUILD)

        with pytest.raises(RuntimeError):
            manager.start_round(RoundType.RED_ATTACK)

    def test_round_sequence(self, manager):
        """Test the expected round sequence."""
        # Initially, should suggest BLUE_BUILD
        assert manager.get_next_round_type() == RoundType.BLUE_BUILD

        # After BLUE_BUILD, should suggest RED_ATTACK
        manager.start_round(RoundType.BLUE_BUILD)
        manager.end_round()
        assert manager.get_next_round_type() == RoundType.RED_ATTACK

        # After RED_ATTACK, should suggest BLUE_DEFENSE
        manager.start_round(RoundType.RED_ATTACK)
        manager.end_round()
        assert manager.get_next_round_type() == RoundType.BLUE_DEFENSE

    def test_adversarial_cycle_tracking(self, manager):
        """Test that adversarial cycles are counted."""
        assert manager.adversarial_cycles_remaining == 3

        manager.start_round(RoundType.BLUE_BUILD)
        manager.end_round()

        manager.start_round(RoundType.RED_ATTACK)
        manager.end_round()

        manager.start_round(RoundType.BLUE_DEFENSE)
        manager.end_round()

        assert manager.adversarial_cycles_remaining == 2

    def test_consensus_detection(self, manager):
        """Test consensus detection in round manager."""
        # Create manager with history
        history = ConversationHistory()
        manager = RoundManager(history=history, consensus_threshold=0.8)

        # Start a round and add a resolved exchange
        history.start_round(1, "BlueDefense")

        # Add a resolved critique (simulating the process)
        critique = Message(
            message_type=MessageType.CRITIQUE,
            sender_role="Devil's Advocate",
            payload=MessagePayload(
                content_type="json",
                structured_data={
                    "challenge_type": "logic",
                    "severity": "minor",
                    "title": "Test",
                    "target_section": "Test",
                },
            ),
            round_number=1,
        )
        history.record_message(critique)

        response = Message(
            message_type=MessageType.RESPONSE,
            sender_role="Strategy Architect",
            parent_id=critique.id,
            payload=MessagePayload(
                content_type="json",
                structured_data={"disposition": "Accept", "summary": "Fixed"},
            ),
            round_number=1,
        )
        history.record_message(response)

        # Start and end round
        manager.start_round(RoundType.BLUE_DEFENSE)
        summary = manager.end_round(check_consensus=True)

        # With 100% resolution and no critical issues, consensus should be reached
        assert summary.resolution_rate == 100.0
        assert summary.consensus_reached or not summary.has_blocking_issues

    def test_abort_round(self, manager):
        """Test aborting a round."""
        manager.start_round(RoundType.BLUE_BUILD)
        summary = manager.abort_round("Testing abort")

        assert summary is not None
        assert manager.current_phase == RoundPhase.ABORTED
        assert not summary.consensus_reached

    def test_should_continue(self, manager):
        """Test should_continue logic."""
        assert manager.should_continue()  # Before any rounds

        manager.start_round(RoundType.BLUE_BUILD)
        manager.end_round()

        assert manager.should_continue()  # Need more rounds

    def test_get_debate_summary(self, manager):
        """Test getting overall debate summary."""
        manager.start_round(RoundType.BLUE_BUILD)
        manager.end_round()

        manager.start_round(RoundType.RED_ATTACK)
        manager.end_round()

        summary = manager.get_debate_summary()

        assert summary["total_rounds"] == 2
        assert "round_summaries" in summary

    def test_round_messages(self, manager):
        """Test creating round start/end messages."""
        manager.start_round(RoundType.BLUE_BUILD)

        start_msg = manager.create_round_start_message()
        assert start_msg.message_type == MessageType.ROUND_START
        assert start_msg.broadcast is True

        summary = manager.end_round()
        end_msg = manager.create_round_end_message(summary)
        assert end_msg.message_type == MessageType.ROUND_END


# =============================================================================
# Integration Tests
# =============================================================================

class TestCommsIntegration:
    """Integration tests for the communication layer."""

    @pytest.mark.asyncio
    async def test_full_debate_flow(self):
        """Test a complete debate flow with all components."""
        # Setup
        bus = MessageBus()
        history = ConversationHistory(document_id="test-doc")
        manager = RoundManager(history=history, max_adversarial_rounds=1)

        blue_received = []
        red_received = []

        async def blue_handler(msg):
            blue_received.append(msg)
            history.record_message(msg)

        async def red_handler(msg):
            red_received.append(msg)
            history.record_message(msg)

        await bus.start()
        try:
            # Subscribe agents
            await bus.subscribe(
                agent_role="Strategy Architect",
                message_types=[MessageType.CRITIQUE, MessageType.ROUND_START],
                handler=blue_handler,
            )
            await bus.subscribe(
                agent_role="Devil's Advocate",
                message_types=[MessageType.DRAFT, MessageType.ROUND_START],
                handler=red_handler,
            )

            # Round 1: Blue Build
            manager.start_round(RoundType.BLUE_BUILD)
            start_msg = manager.create_round_start_message()
            await bus.publish(start_msg)

            draft = create_draft_message(
                sender_role="Strategy Architect",
                content="Initial draft content",
                document_id="test-doc",
                round_number=1,
            )
            await bus.publish(draft)

            await bus.wait_for_queue_empty(timeout=5.0)

            summary = manager.end_round()
            assert summary.round_type == RoundType.BLUE_BUILD

            # Verify red team received the draft
            draft_msgs = [m for m in red_received if m.message_type == MessageType.DRAFT]
            assert len(draft_msgs) == 1

        finally:
            await bus.stop()

    def test_history_round_record_consistency(self):
        """Test that history and round records stay consistent."""
        history = ConversationHistory()
        manager = RoundManager(history=history)

        # Start round
        manager.start_round(RoundType.RED_ATTACK)

        # Add critique via history
        critique = Message(
            message_type=MessageType.CRITIQUE,
            sender_role="Devil's Advocate",
            payload=MessagePayload(
                content_type="json",
                structured_data={
                    "challenge_type": "evidence",
                    "severity": "major",
                    "title": "Missing proof",
                    "target_section": "Claims",
                },
            ),
            round_number=manager.current_round,
        )
        history.record_message(critique)

        # End round
        summary = manager.end_round()

        # Verify consistency
        round_record = history.get_round(1)
        assert round_record is not None
        assert len(round_record.exchanges) == 1
        assert round_record.critique_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
