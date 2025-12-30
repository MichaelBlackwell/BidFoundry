"""WebSocket message handler.

Handles incoming WebSocket messages and routes them to appropriate handlers.
"""

import json
import logging
from typing import Any, Callable, Optional

from fastapi import WebSocket, WebSocketDisconnect

from server.websocket.events import (
    ClientEventType,
    GenerationControlPayload,
    GenerationStartPayload,
    ServerEventType,
    create_error_message,
    create_server_message,
)
from server.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


# Type alias for event handlers
EventHandler = Callable[[str, dict[str, Any]], Any]


class WebSocketHandler:
    """
    Handles WebSocket message routing and processing.

    Features:
    - Routes incoming messages to registered handlers
    - Validates message format and payloads
    - Handles connection lifecycle events
    - Provides error handling and reporting
    """

    def __init__(self, connection_manager: ConnectionManager) -> None:
        """
        Initialize the handler.

        Args:
            connection_manager: The connection manager instance
        """
        self.manager = connection_manager
        self._handlers: dict[ClientEventType, EventHandler] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self.register_handler(ClientEventType.PING, self._handle_ping)

    def register_handler(self, event_type: ClientEventType, handler: EventHandler) -> None:
        """
        Register a handler for a client event type.

        Args:
            event_type: The client event type to handle
            handler: Async function(connection_id, payload) -> None
        """
        self._handlers[event_type] = handler
        logger.debug(f"Registered handler for {event_type.value}")

    def unregister_handler(self, event_type: ClientEventType) -> None:
        """Unregister a handler for an event type."""
        self._handlers.pop(event_type, None)

    async def _handle_ping(self, connection_id: str, payload: dict[str, Any]) -> None:
        """Handle ping messages from client."""
        await self.manager.update_ping(connection_id)
        await self.manager.send_to_connection(
            connection_id,
            ServerEventType.PONG,
            {"timestamp": payload.get("timestamp")},
        )

    async def handle_connection(self, websocket: WebSocket) -> None:
        """
        Handle a WebSocket connection lifecycle.

        This is the main entry point for WebSocket connections.
        Manages the full lifecycle from connect to disconnect.

        Args:
            websocket: The WebSocket connection
        """
        connection_id: Optional[str] = None

        try:
            # Accept the connection
            connection_id = await self.manager.connect(websocket)
            logger.info(f"New WebSocket connection: {connection_id}")

            # Start heartbeat if not running
            await self.manager.start_heartbeat()

            # Message processing loop
            await self._message_loop(connection_id, websocket)

        except ConnectionRefusedError as e:
            logger.warning(f"Connection refused: {e}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")

        except Exception as e:
            logger.error(f"WebSocket error: {e}")

        finally:
            if connection_id:
                await self.manager.disconnect(connection_id)

    async def _message_loop(self, connection_id: str, websocket: WebSocket) -> None:
        """
        Process incoming messages from a WebSocket.

        Args:
            connection_id: The connection ID
            websocket: The WebSocket connection
        """
        while True:
            try:
                # Receive and parse message
                raw_data = await websocket.receive_text()
                message = self._parse_message(raw_data)

                if message is None:
                    await self.manager.send_error(
                        connection_id,
                        "Invalid message format",
                        "INVALID_FORMAT",
                    )
                    continue

                # Route to handler
                await self._route_message(connection_id, message)

            except WebSocketDisconnect:
                raise
            except json.JSONDecodeError:
                await self.manager.send_error(
                    connection_id,
                    "Invalid JSON",
                    "INVALID_JSON",
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await self.manager.send_error(
                    connection_id,
                    f"Error processing message: {str(e)}",
                    "PROCESSING_ERROR",
                )

    def _parse_message(self, raw_data: str) -> Optional[dict[str, Any]]:
        """
        Parse and validate an incoming message.

        Args:
            raw_data: Raw JSON string

        Returns:
            Parsed message dict or None if invalid
        """
        try:
            message = json.loads(raw_data)

            # Validate required fields
            if not isinstance(message, dict):
                return None

            if "type" not in message:
                return None

            # Ensure payload exists
            if "payload" not in message:
                message["payload"] = {}

            return message

        except json.JSONDecodeError:
            return None

    async def _route_message(self, connection_id: str, message: dict[str, Any]) -> None:
        """
        Route a message to the appropriate handler.

        Args:
            connection_id: The connection ID
            message: The parsed message
        """
        event_type_str = message.get("type", "")
        payload = message.get("payload", {})
        request_id = message.get("requestId")

        # Try to get the event type
        try:
            event_type = ClientEventType(event_type_str)
        except ValueError:
            await self.manager.send_error(
                connection_id,
                f"Unknown event type: {event_type_str}",
                "UNKNOWN_EVENT",
                request_id,
            )
            return

        # Get the handler
        handler = self._handlers.get(event_type)
        if handler is None:
            await self.manager.send_error(
                connection_id,
                f"No handler for event: {event_type_str}",
                "NO_HANDLER",
                request_id,
            )
            return

        # Update ping timestamp on any activity
        await self.manager.update_ping(connection_id)

        # Execute handler
        try:
            await handler(connection_id, payload)
        except Exception as e:
            logger.error(f"Handler error for {event_type_str}: {e}")
            await self.manager.send_error(
                connection_id,
                f"Handler error: {str(e)}",
                "HANDLER_ERROR",
                request_id,
            )


class GenerationHandlerMixin:
    """
    Mixin providing generation-related WebSocket handlers.

    This mixin is designed to be used with OrchestratorService
    to handle generation control events.
    """

    def register_generation_handlers(
        self,
        handler: WebSocketHandler,
        start_handler: EventHandler,
        pause_handler: EventHandler,
        resume_handler: EventHandler,
        cancel_handler: EventHandler,
    ) -> None:
        """
        Register generation control handlers.

        Args:
            handler: The WebSocket handler instance
            start_handler: Handler for generation:start
            pause_handler: Handler for generation:pause
            resume_handler: Handler for generation:resume
            cancel_handler: Handler for generation:cancel
        """
        handler.register_handler(ClientEventType.GENERATION_START, start_handler)
        handler.register_handler(ClientEventType.GENERATION_PAUSE, pause_handler)
        handler.register_handler(ClientEventType.GENERATION_RESUME, resume_handler)
        handler.register_handler(ClientEventType.GENERATION_CANCEL, cancel_handler)


def validate_generation_start_payload(payload: dict[str, Any]) -> Optional[GenerationStartPayload]:
    """
    Validate a generation:start payload.

    Args:
        payload: The payload to validate

    Returns:
        Validated payload or None if invalid
    """
    try:
        return GenerationStartPayload(**payload)
    except Exception as e:
        logger.error(f"Invalid generation:start payload: {e}")
        return None


def validate_generation_control_payload(payload: dict[str, Any]) -> Optional[GenerationControlPayload]:
    """
    Validate a generation control payload (pause/resume/cancel).

    Args:
        payload: The payload to validate

    Returns:
        Validated payload or None if invalid
    """
    try:
        return GenerationControlPayload(**payload)
    except Exception as e:
        logger.error(f"Invalid generation control payload: {e}")
        return None


# Helper functions for common operations


async def subscribe_connection_to_generation(
    manager: ConnectionManager,
    connection_id: str,
    request_id: str,
) -> bool:
    """
    Subscribe a connection to receive generation updates.

    Args:
        manager: The connection manager
        connection_id: The connection to subscribe
        request_id: The generation request ID

    Returns:
        True if subscription was successful
    """
    return await manager.subscribe_to_request(connection_id, request_id)


async def broadcast_generation_event(
    manager: ConnectionManager,
    request_id: str,
    event_type: ServerEventType,
    payload: dict[str, Any],
) -> int:
    """
    Broadcast a generation event to all subscribed connections.

    Args:
        manager: The connection manager
        request_id: The generation request ID
        event_type: The event type to broadcast
        payload: The event payload

    Returns:
        Number of connections that received the message
    """
    return await manager.broadcast(request_id, event_type, payload)
