"""WebSocket connection manager.

Manages WebSocket connections, including lifecycle, broadcasting, and cleanup.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from server.config import settings
from server.websocket.events import (
    ConnectedPayload,
    ServerEventType,
    create_error_message,
    create_server_message,
)

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Represents an active WebSocket connection."""

    id: str
    websocket: WebSocket
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    subscribed_requests: set[str] = field(default_factory=set)

    def is_subscribed_to(self, request_id: str) -> bool:
        """Check if connection is subscribed to a request."""
        return request_id in self.subscribed_requests

    def subscribe(self, request_id: str) -> None:
        """Subscribe to a generation request."""
        self.subscribed_requests.add(request_id)

    def unsubscribe(self, request_id: str) -> None:
        """Unsubscribe from a generation request."""
        self.subscribed_requests.discard(request_id)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Features:
    - Connection lifecycle management (connect, disconnect, cleanup)
    - Request-based subscriptions for targeted broadcasting
    - Heartbeat monitoring to detect stale connections
    - Automatic reconnection support through connection IDs
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._connections: dict[str, Connection] = {}
        self._request_subscriptions: dict[str, set[str]] = {}  # request_id -> connection_ids
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    async def start_heartbeat(self) -> None:
        """Start the heartbeat monitoring task."""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("Heartbeat monitoring started")

    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat monitoring task."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("Heartbeat monitoring stopped")

    async def _heartbeat_loop(self) -> None:
        """Background task to monitor connection health and send keep-alive pings."""
        while True:
            try:
                await asyncio.sleep(settings.ws_heartbeat_interval)
                # Send keep-alive pings to all connections
                await self._send_keep_alive_pings()
                # Then check for stale connections
                await self._check_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _send_keep_alive_pings(self) -> None:
        """Send keep-alive pings to all active connections."""
        async with self._lock:
            connection_ids = list(self._connections.keys())

        for conn_id in connection_ids:
            try:
                connection = self._connections.get(conn_id)
                if connection:
                    await connection.websocket.send_json({
                        "type": "pong",
                        "payload": {"serverTime": int(datetime.utcnow().timestamp() * 1000)},
                        "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    })
                    # Update last_ping on successful keep-alive to prevent stale detection
                    connection.last_ping = datetime.utcnow()
            except Exception as e:
                logger.debug(f"Failed to send keep-alive to {conn_id}: {e}")

    async def _check_connections(self) -> None:
        """Check and clean up stale connections."""
        now = datetime.utcnow()
        # Use generation timeout + buffer for stale detection to handle long LLM operations
        # This ensures connections aren't killed during extended API calls
        stale_timeout = max(
            settings.ws_heartbeat_interval * 5,  # At least 5 missed heartbeats
            settings.generation_timeout_seconds + 60,  # Or generation timeout + 1 min buffer
        )

        async with self._lock:
            stale_connections = [
                conn_id
                for conn_id, conn in self._connections.items()
                if (now - conn.last_ping).total_seconds() > stale_timeout
            ]

        for conn_id in stale_connections:
            logger.warning(f"Removing stale connection: {conn_id}")
            await self.disconnect(conn_id)

    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket to accept

        Returns:
            The connection ID for this connection

        Raises:
            ConnectionRefusedError: If max connections exceeded
        """
        async with self._lock:
            if len(self._connections) >= settings.ws_max_connections:
                await websocket.close(code=1013, reason="Max connections exceeded")
                raise ConnectionRefusedError("Max WebSocket connections exceeded")

            await websocket.accept()

            connection_id = str(uuid.uuid4())
            connection = Connection(id=connection_id, websocket=websocket)
            self._connections[connection_id] = connection

        logger.info(f"WebSocket connected: {connection_id}")

        # Send connected event
        await self._send_to_connection(
            connection_id,
            create_server_message(
                ServerEventType.CONNECTED,
                ConnectedPayload(
                    connection_id=connection_id,
                    server_time=int(datetime.utcnow().timestamp() * 1000),
                ).model_dump(by_alias=True),
            ),
        )

        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect and clean up a WebSocket connection.

        Args:
            connection_id: The ID of the connection to disconnect
        """
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            if connection is None:
                return

            # Remove from all request subscriptions
            for request_id in connection.subscribed_requests:
                if request_id in self._request_subscriptions:
                    self._request_subscriptions[request_id].discard(connection_id)
                    if not self._request_subscriptions[request_id]:
                        del self._request_subscriptions[request_id]

        try:
            await connection.websocket.close()
        except Exception:
            pass  # Connection may already be closed

        logger.info(f"WebSocket disconnected: {connection_id}")

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by ID."""
        return self._connections.get(connection_id)

    async def subscribe_to_request(self, connection_id: str, request_id: str) -> bool:
        """
        Subscribe a connection to a generation request.

        Args:
            connection_id: The connection to subscribe
            request_id: The request to subscribe to

        Returns:
            True if subscription was successful
        """
        async with self._lock:
            connection = self._connections.get(connection_id)
            if connection is None:
                return False

            connection.subscribe(request_id)

            if request_id not in self._request_subscriptions:
                self._request_subscriptions[request_id] = set()
            self._request_subscriptions[request_id].add(connection_id)

        logger.debug(f"Connection {connection_id} subscribed to request {request_id}")
        return True

    async def unsubscribe_from_request(self, connection_id: str, request_id: str) -> bool:
        """
        Unsubscribe a connection from a generation request.

        Args:
            connection_id: The connection to unsubscribe
            request_id: The request to unsubscribe from

        Returns:
            True if unsubscription was successful
        """
        async with self._lock:
            connection = self._connections.get(connection_id)
            if connection is None:
                return False

            connection.unsubscribe(request_id)

            if request_id in self._request_subscriptions:
                self._request_subscriptions[request_id].discard(connection_id)
                if not self._request_subscriptions[request_id]:
                    del self._request_subscriptions[request_id]

        logger.debug(f"Connection {connection_id} unsubscribed from request {request_id}")
        return True

    async def update_ping(self, connection_id: str) -> None:
        """Update the last ping time for a connection."""
        connection = self._connections.get(connection_id)
        if connection:
            connection.last_ping = datetime.utcnow()

    async def _send_to_connection(
        self, connection_id: str, message: dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            connection_id: The target connection
            message: The message to send

        Returns:
            True if message was sent successfully
        """
        connection = self._connections.get(connection_id)
        if connection is None:
            return False

        try:
            await connection.websocket.send_json(message)
            # Refresh ping timestamp on successful send to keep connection alive
            connection.last_ping = datetime.utcnow()
            return True
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False

    async def send_to_connection(
        self,
        connection_id: str,
        event_type: ServerEventType,
        payload: dict[str, Any],
        request_id: Optional[str] = None,
    ) -> bool:
        """
        Send a typed event to a specific connection.

        Args:
            connection_id: The target connection
            event_type: The type of server event
            payload: The event payload
            request_id: Optional request ID context

        Returns:
            True if message was sent successfully
        """
        message = create_server_message(event_type, payload, request_id)
        return await self._send_to_connection(connection_id, message)

    async def broadcast(
        self,
        request_id: str,
        event_type: ServerEventType,
        payload: dict[str, Any],
    ) -> int:
        """
        Broadcast an event to all connections subscribed to a request.

        Args:
            request_id: The request ID to broadcast to
            event_type: The type of server event
            payload: The event payload

        Returns:
            Number of connections that received the message
        """
        message = create_server_message(event_type, payload, request_id)

        async with self._lock:
            connection_ids = list(self._request_subscriptions.get(request_id, set()))

        sent_count = 0
        for conn_id in connection_ids:
            if await self._send_to_connection(conn_id, message):
                sent_count += 1

        return sent_count

    async def broadcast_to_all(
        self,
        event_type: ServerEventType,
        payload: dict[str, Any],
    ) -> int:
        """
        Broadcast an event to all connected clients.

        Args:
            event_type: The type of server event
            payload: The event payload

        Returns:
            Number of connections that received the message
        """
        message = create_server_message(event_type, payload, None)

        async with self._lock:
            connection_ids = list(self._connections.keys())

        sent_count = 0
        for conn_id in connection_ids:
            if await self._send_to_connection(conn_id, message):
                sent_count += 1

        return sent_count

    async def send_error(
        self,
        connection_id: str,
        message: str,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """
        Send an error message to a connection.

        Args:
            connection_id: The target connection
            message: Error message
            code: Optional error code
            request_id: Optional request context

        Returns:
            True if error was sent successfully
        """
        error_message = create_error_message(message, code, request_id)
        return await self._send_to_connection(connection_id, error_message)

    def get_request_subscriber_count(self, request_id: str) -> int:
        """Get the number of connections subscribed to a request."""
        return len(self._request_subscriptions.get(request_id, set()))

    def get_all_connections(self) -> list[Connection]:
        """Get all active connections."""
        return list(self._connections.values())


# Global connection manager instance
connection_manager = ConnectionManager()
