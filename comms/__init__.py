"""
Communication Layer for Adversarial Agentic Swarm

This package provides the messaging infrastructure for agent-to-agent
communication in the adversarial swarm workflow.

Main components:
- Message: Immutable message structure for agent communication
- MessageBus: Async pub/sub message bus
- ConversationHistory: Queryable history of the debate
- RoundManager: Manages debate round lifecycle

Usage:
    from comms import MessageBus, Message, MessageType, RoundManager

    # Create message bus
    bus = MessageBus()
    await bus.start()

    # Subscribe to messages
    await bus.subscribe(
        agent_role="Strategy Architect",
        message_types=[MessageType.CRITIQUE],
        handler=my_handler,
    )

    # Publish a message
    message = Message(
        message_type=MessageType.DRAFT,
        sender_role="Strategy Architect",
        payload=MessagePayload(content="..."),
    )
    await bus.publish(message)

    # Manage rounds
    round_manager = RoundManager()
    round_manager.start_round(RoundType.BLUE_BUILD)
    # ... agents do work ...
    summary = round_manager.end_round()
"""

from .message import (
    Message,
    MessageType,
    MessagePriority,
    MessagePayload,
    DeliveryStatus,
    create_draft_message,
    create_critique_message,
    create_response_message,
    create_control_message,
)

from .bus import (
    MessageBus,
    MessageBusConfig,
    Subscription,
    MessageHandler,
)

from .history import (
    ConversationHistory,
    ExchangeRecord,
    RoundRecord,
)

from .round import (
    RoundManager,
    RoundType,
    RoundPhase,
    RoundSummary,
    RoundConfig,
)

__all__ = [
    # Message types
    "Message",
    "MessageType",
    "MessagePriority",
    "MessagePayload",
    "DeliveryStatus",
    # Message factories
    "create_draft_message",
    "create_critique_message",
    "create_response_message",
    "create_control_message",
    # Message bus
    "MessageBus",
    "MessageBusConfig",
    "Subscription",
    "MessageHandler",
    # History
    "ConversationHistory",
    "ExchangeRecord",
    "RoundRecord",
    # Round management
    "RoundManager",
    "RoundType",
    "RoundPhase",
    "RoundSummary",
    "RoundConfig",
]
