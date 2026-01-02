"""
Message Bus

Provides the pub/sub communication layer for agent-to-agent messaging
in the adversarial swarm.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Set, Optional, Callable, Awaitable, Any, TYPE_CHECKING
import logging
import uuid

from .message import Message, MessageType, MessagePriority, DeliveryStatus

if TYPE_CHECKING:
    from agents.base import AbstractAgent


# Type alias for message handlers
MessageHandler = Callable[[Message], Awaitable[None]]


@dataclass
class Subscription:
    """
    Represents an agent's subscription to message types.

    Tracks what messages an agent wants to receive and how to deliver them.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_role: str = ""
    agent_id: Optional[str] = None
    message_types: Set[MessageType] = field(default_factory=set)
    handler: Optional[MessageHandler] = None
    filter_func: Optional[Callable[[Message], bool]] = None
    priority: int = 0  # Higher priority subscribers get messages first
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def matches(self, message: Message) -> bool:
        """Check if this subscription should receive a message."""
        if not self.is_active:
            return False

        # Check message type
        if self.message_types and message.message_type not in self.message_types:
            return False

        # Check custom filter
        if self.filter_func and not self.filter_func(message):
            return False

        # Check if recipient matches
        if not message.broadcast:
            if message.recipients and self.agent_role not in message.recipients:
                return False

        return True


@dataclass
class MessageBusConfig:
    """Configuration for the MessageBus."""

    max_queue_size: int = 10000
    max_message_age_seconds: int = 3600  # 1 hour
    enable_persistence: bool = False
    enable_logging: bool = True
    delivery_timeout_seconds: float = 30.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0


class MessageBus:
    """
    Async-safe message bus for agent communication.

    Provides pub/sub messaging with support for:
    - Typed message subscriptions
    - Broadcast and targeted delivery
    - Priority-based ordering
    - Message history tracking
    - Delivery status tracking
    """

    def __init__(self, config: Optional[MessageBusConfig] = None):
        """
        Initialize the message bus.

        Args:
            config: Optional configuration for the bus
        """
        self._config = config or MessageBusConfig()
        self._logger = logging.getLogger("MessageBus")

        # Subscriptions indexed by message type
        self._subscriptions: Dict[MessageType, List[Subscription]] = defaultdict(list)
        self._subscription_by_id: Dict[str, Subscription] = {}

        # Message storage
        self._messages: List[Message] = []
        self._message_index: Dict[str, Message] = {}
        self._messages_by_round: Dict[int, List[Message]] = defaultdict(list)
        self._messages_by_type: Dict[MessageType, List[Message]] = defaultdict(list)
        self._messages_by_thread: Dict[str, List[Message]] = defaultdict(list)

        # Delivery queue
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=self._config.max_queue_size)
        self._processing = False
        self._process_task: Optional[asyncio.Task] = None

        # Synchronization
        self._lock = asyncio.Lock()

        # Statistics
        self._stats = {
            "messages_published": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "active_subscriptions": 0,
        }

    async def start(self) -> None:
        """Start the message bus processing loop."""
        if self._processing:
            return
        self._processing = True
        self._process_task = asyncio.create_task(self._process_queue())
        self._logger.info("MessageBus started")

    async def stop(self) -> None:
        """Stop the message bus processing loop."""
        self._processing = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        self._logger.info("MessageBus stopped")

    async def subscribe(
        self,
        agent_role: str,
        message_types: List[MessageType],
        handler: Optional[MessageHandler] = None,
        agent_id: Optional[str] = None,
        filter_func: Optional[Callable[[Message], bool]] = None,
        priority: int = 0,
    ) -> str:
        """
        Subscribe an agent to specific message types.

        Args:
            agent_role: The role of the subscribing agent
            message_types: List of message types to subscribe to
            handler: Async callback for message delivery
            agent_id: Optional specific agent instance ID
            filter_func: Optional filter function for messages
            priority: Subscription priority (higher = first)

        Returns:
            Subscription ID for later unsubscription
        """
        subscription = Subscription(
            agent_role=agent_role,
            agent_id=agent_id,
            message_types=set(message_types),
            handler=handler,
            filter_func=filter_func,
            priority=priority,
        )

        async with self._lock:
            for msg_type in message_types:
                self._subscriptions[msg_type].append(subscription)
                # Keep sorted by priority (highest first)
                self._subscriptions[msg_type].sort(key=lambda s: -s.priority)

            self._subscription_by_id[subscription.id] = subscription
            self._stats["active_subscriptions"] += 1

        self._logger.debug(f"Agent {agent_role} subscribed to {message_types}")
        return subscription.id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Remove a subscription.

        Args:
            subscription_id: The subscription ID to remove

        Returns:
            True if subscription was found and removed
        """
        async with self._lock:
            if subscription_id not in self._subscription_by_id:
                return False

            subscription = self._subscription_by_id.pop(subscription_id)
            subscription.is_active = False

            for msg_type in subscription.message_types:
                self._subscriptions[msg_type] = [
                    s for s in self._subscriptions[msg_type]
                    if s.id != subscription_id
                ]

            self._stats["active_subscriptions"] -= 1

        self._logger.debug(f"Subscription {subscription_id} removed")
        return True

    async def publish(
        self,
        message: Message,
        wait_for_delivery: bool = False,
    ) -> Message:
        """
        Publish a message to the bus.

        Args:
            message: The message to publish
            wait_for_delivery: If True, wait for message to be delivered

        Returns:
            The published message (with updated ID if needed)
        """
        async with self._lock:
            # Store message
            self._messages.append(message)
            self._message_index[message.id] = message
            self._messages_by_round[message.round_number].append(message)
            self._messages_by_type[message.message_type].append(message)
            if message.thread_id:
                self._messages_by_thread[message.thread_id].append(message)

            self._stats["messages_published"] += 1

        # Queue for delivery
        await self._queue.put(message)

        if wait_for_delivery:
            # Wait for delivery to complete
            await self._wait_for_delivery(message)

        return message

    async def _wait_for_delivery(self, message: Message) -> None:
        """Wait for a message to be delivered."""
        timeout = self._config.delivery_timeout_seconds
        start = datetime.now(timezone.utc)

        while not message.is_delivered:
            if (datetime.now(timezone.utc) - start).total_seconds() > timeout:
                self._logger.warning(f"Delivery timeout for message {message.id}")
                return
            await asyncio.sleep(0.1)

    async def _process_queue(self) -> None:
        """Background task to process the message queue."""
        while self._processing:
            try:
                message = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,
                )
                await self._deliver_message(message)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error processing message: {e}")

    async def _deliver_message(self, message: Message) -> None:
        """Deliver a message to all matching subscribers."""
        if message.is_expired:
            message.delivery_status = DeliveryStatus.EXPIRED
            return

        # Find matching subscriptions
        matching_subs: List[Subscription] = []

        async with self._lock:
            # Check subscriptions for this message type
            for sub in self._subscriptions.get(message.message_type, []):
                if sub.matches(message):
                    matching_subs.append(sub)

        if not matching_subs:
            self._logger.debug(f"No subscribers for message {message.id}")
            return

        # Deliver to each subscriber
        for sub in matching_subs:
            if sub.handler:
                try:
                    await sub.handler(message)
                    message.mark_delivered(sub.agent_role)
                    self._stats["messages_delivered"] += 1
                except Exception as e:
                    self._logger.error(
                        f"Handler error for {sub.agent_role}: {e}"
                    )
                    self._stats["messages_failed"] += 1
            else:
                # No handler, just mark as delivered
                message.mark_delivered(sub.agent_role)
                self._stats["messages_delivered"] += 1

    def get_message(self, message_id: str) -> Optional[Message]:
        """Get a message by its ID."""
        return self._message_index.get(message_id)

    def get_history(
        self,
        round_number: Optional[int] = None,
        message_type: Optional[MessageType] = None,
        sender_role: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        Get message history with optional filters.

        Args:
            round_number: Filter by debate round
            message_type: Filter by message type
            sender_role: Filter by sender role
            limit: Maximum number of messages to return

        Returns:
            List of matching messages, sorted by creation time
        """
        if round_number is not None:
            messages = self._messages_by_round.get(round_number, [])
        elif message_type is not None:
            messages = self._messages_by_type.get(message_type, [])
        else:
            messages = self._messages.copy()

        # Apply additional filters
        if message_type is not None and round_number is not None:
            messages = [m for m in messages if m.message_type == message_type]

        if sender_role is not None:
            messages = [m for m in messages if m.sender_role == sender_role]

        # Sort by creation time
        messages.sort(key=lambda m: m.created_at)

        if limit:
            messages = messages[:limit]

        return messages

    def get_thread(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread."""
        messages = self._messages_by_thread.get(thread_id, [])
        return sorted(messages, key=lambda m: m.created_at)

    def get_critiques_for_round(self, round_number: int) -> List[Message]:
        """Get all critique messages for a specific round."""
        return [
            m for m in self._messages_by_round.get(round_number, [])
            if m.is_critique
        ]

    def get_responses_for_round(self, round_number: int) -> List[Message]:
        """Get all response messages for a specific round."""
        return [
            m for m in self._messages_by_round.get(round_number, [])
            if m.is_response
        ]

    def get_undelivered_messages(self) -> List[Message]:
        """Get all messages that haven't been fully delivered."""
        return [
            m for m in self._messages
            if m.delivery_status == DeliveryStatus.PENDING
        ]

    async def clear_history(self, before_round: Optional[int] = None) -> int:
        """
        Clear message history.

        Args:
            before_round: Only clear messages before this round number

        Returns:
            Number of messages cleared
        """
        async with self._lock:
            if before_round is None:
                count = len(self._messages)
                self._messages.clear()
                self._message_index.clear()
                self._messages_by_round.clear()
                self._messages_by_type.clear()
                self._messages_by_thread.clear()
                return count

            # Clear only messages before specified round
            cleared = 0
            for round_num in list(self._messages_by_round.keys()):
                if round_num < before_round:
                    for msg in self._messages_by_round[round_num]:
                        self._message_index.pop(msg.id, None)
                        self._messages.remove(msg)
                        self._messages_by_type[msg.message_type].remove(msg)
                        if msg.thread_id:
                            thread_msgs = self._messages_by_thread.get(msg.thread_id, [])
                            if msg in thread_msgs:
                                thread_msgs.remove(msg)
                        cleared += 1
                    del self._messages_by_round[round_num]

            return cleared

    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        return {
            **self._stats,
            "total_messages": len(self._messages),
            "queue_size": self._queue.qsize(),
            "is_processing": self._processing,
        }

    async def wait_for_queue_empty(self, timeout: float = 30.0) -> bool:
        """
        Wait for the message queue to be empty.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if queue is empty, False if timeout
        """
        start = datetime.now(timezone.utc)
        while not self._queue.empty():
            if (datetime.now(timezone.utc) - start).total_seconds() > timeout:
                return False
            await asyncio.sleep(0.1)
        return True
