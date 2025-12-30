"""Integration tests for WebSocket functionality."""

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from server.main import app
from server.websocket.events import ClientEventType, ServerEventType
from server.websocket.manager import ConnectionManager, Connection

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestConnectionManager:
    """Tests for the ConnectionManager class."""

    @pytest_asyncio.fixture
    async def manager(self) -> ConnectionManager:
        """Create a fresh ConnectionManager for testing."""
        return ConnectionManager()

    async def test_manager_initialization(self, manager: ConnectionManager):
        """Should initialize with empty connections."""
        assert manager.connection_count == 0
        assert manager.get_all_connections() == []

    async def test_subscribe_to_request(self, manager: ConnectionManager):
        """Should track request subscriptions."""
        # Create mock connection
        manager._connections["conn1"] = Connection(
            id="conn1",
            websocket=AsyncMock(),
        )

        result = await manager.subscribe_to_request("conn1", "req1")
        assert result is True
        assert manager.get_request_subscriber_count("req1") == 1

    async def test_unsubscribe_from_request(self, manager: ConnectionManager):
        """Should remove request subscriptions."""
        # Setup
        manager._connections["conn1"] = Connection(
            id="conn1",
            websocket=AsyncMock(),
        )
        await manager.subscribe_to_request("conn1", "req1")

        # Unsubscribe
        result = await manager.unsubscribe_from_request("conn1", "req1")
        assert result is True
        assert manager.get_request_subscriber_count("req1") == 0

    async def test_subscribe_nonexistent_connection(self, manager: ConnectionManager):
        """Should return False for nonexistent connection."""
        result = await manager.subscribe_to_request("nonexistent", "req1")
        assert result is False

    async def test_multiple_subscriptions(self, manager: ConnectionManager):
        """Should handle multiple connections per request."""
        # Create mock connections
        for i in range(3):
            manager._connections[f"conn{i}"] = Connection(
                id=f"conn{i}",
                websocket=AsyncMock(),
            )
            await manager.subscribe_to_request(f"conn{i}", "req1")

        assert manager.get_request_subscriber_count("req1") == 3

    async def test_disconnect_cleanup(self, manager: ConnectionManager):
        """Should clean up subscriptions on disconnect."""
        ws = AsyncMock()
        manager._connections["conn1"] = Connection(
            id="conn1",
            websocket=ws,
        )
        await manager.subscribe_to_request("conn1", "req1")
        await manager.subscribe_to_request("conn1", "req2")

        await manager.disconnect("conn1")

        assert manager.connection_count == 0
        assert manager.get_request_subscriber_count("req1") == 0
        assert manager.get_request_subscriber_count("req2") == 0

    async def test_send_to_connection(self, manager: ConnectionManager):
        """Should send messages to specific connections."""
        ws = AsyncMock()
        manager._connections["conn1"] = Connection(
            id="conn1",
            websocket=ws,
        )

        result = await manager.send_to_connection(
            "conn1",
            ServerEventType.CONNECTED,
            {"connection_id": "conn1"},
        )

        assert result is True
        ws.send_json.assert_called_once()

    async def test_broadcast_to_subscribers(self, manager: ConnectionManager):
        """Should broadcast to all request subscribers."""
        ws1, ws2, ws3 = AsyncMock(), AsyncMock(), AsyncMock()

        manager._connections["conn1"] = Connection(id="conn1", websocket=ws1)
        manager._connections["conn2"] = Connection(id="conn2", websocket=ws2)
        manager._connections["conn3"] = Connection(id="conn3", websocket=ws3)

        await manager.subscribe_to_request("conn1", "req1")
        await manager.subscribe_to_request("conn2", "req1")
        # conn3 not subscribed

        count = await manager.broadcast(
            "req1",
            ServerEventType.ROUND_START,
            {"round": 1},
        )

        assert count == 2
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
        ws3.send_json.assert_not_called()

    async def test_broadcast_to_all(self, manager: ConnectionManager):
        """Should broadcast to all connections."""
        ws1, ws2 = AsyncMock(), AsyncMock()

        manager._connections["conn1"] = Connection(id="conn1", websocket=ws1)
        manager._connections["conn2"] = Connection(id="conn2", websocket=ws2)

        count = await manager.broadcast_to_all(
            ServerEventType.CONNECTED,
            {"message": "hello"},
        )

        assert count == 2
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    async def test_send_error(self, manager: ConnectionManager):
        """Should send error messages."""
        ws = AsyncMock()
        manager._connections["conn1"] = Connection(id="conn1", websocket=ws)

        result = await manager.send_error(
            "conn1",
            "Something went wrong",
            "ERROR_CODE",
            "req1",
        )

        assert result is True
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["payload"]["message"] == "Something went wrong"
        assert call_args["payload"]["code"] == "ERROR_CODE"

    async def test_update_ping(self, manager: ConnectionManager):
        """Should update connection ping time."""
        from datetime import datetime

        ws = AsyncMock()
        conn = Connection(id="conn1", websocket=ws)
        manager._connections["conn1"] = conn
        original_ping = conn.last_ping

        await asyncio.sleep(0.01)  # Small delay
        await manager.update_ping("conn1")

        assert conn.last_ping > original_ping


class TestWebSocketEvents:
    """Tests for WebSocket event handling."""

    async def test_connected_event_format(self):
        """Should format connected event correctly."""
        from server.websocket.events import create_server_message, ConnectedPayload

        payload = ConnectedPayload(
            connection_id="test-conn",
            server_time=1234567890,
        )
        message = create_server_message(
            ServerEventType.CONNECTED,
            payload.model_dump(by_alias=True),
        )

        assert message["type"] == "connected"
        assert message["payload"]["connectionId"] == "test-conn"
        assert message["payload"]["serverTime"] == 1234567890
        assert "timestamp" in message

    async def test_round_start_event_format(self):
        """Should format round:start event correctly."""
        from server.websocket.events import create_server_message, RoundStartPayload

        payload = RoundStartPayload(
            round=1,
            total_rounds=3,
            phase="blue_build",
            agents=["strategy_architect", "compliance_navigator"],
        )
        message = create_server_message(
            ServerEventType.ROUND_START,
            payload.model_dump(by_alias=True),
            request_id="req123",
        )

        assert message["type"] == "round:start"
        assert message["payload"]["round"] == 1
        assert message["payload"]["totalRounds"] == 3
        assert message["requestId"] == "req123"

    async def test_error_message_format(self):
        """Should format error messages correctly."""
        from server.websocket.events import create_error_message

        message = create_error_message(
            "Something failed",
            "FAILURE_CODE",
            "req123",
        )

        assert message["type"] == "error"
        assert message["payload"]["message"] == "Something failed"
        assert message["payload"]["code"] == "FAILURE_CODE"
        assert message["requestId"] == "req123"


class TestWebSocketConnection:
    """Tests for WebSocket connection lifecycle."""

    def test_websocket_endpoint_exists(self):
        """Should have WebSocket endpoint registered."""
        routes = [r.path for r in app.routes]
        assert "/ws" in routes

    def test_websocket_stats_endpoint(self):
        """Should return WebSocket statistics."""
        with TestClient(app) as client:
            response = client.get("/ws/stats")
            assert response.status_code == 200
            data = response.json()
            assert "active_connections" in data
            assert "max_connections" in data
            assert "heartbeat_interval" in data


class TestWebSocketMessageValidation:
    """Tests for WebSocket message validation."""

    async def test_validate_generation_start_payload(self):
        """Should validate generation:start payloads."""
        from server.websocket.handler import validate_generation_start_payload

        valid_payload = {
            "requestId": "req123",
            "documentType": "capability-statement",
            "companyProfileId": "profile123",
            "config": {
                "rounds": 3,
                "intensity": "medium",
            },
        }

        result = validate_generation_start_payload(valid_payload)
        assert result is not None
        assert result.request_id == "req123"

    async def test_validate_generation_start_invalid(self):
        """Should reject invalid generation:start payloads."""
        from server.websocket.handler import validate_generation_start_payload

        invalid_payload = {
            "requestId": "req123",
            # Missing required fields
        }

        result = validate_generation_start_payload(invalid_payload)
        assert result is None

    async def test_validate_generation_control_payload(self):
        """Should validate generation control payloads."""
        from server.websocket.handler import validate_generation_control_payload

        valid_payload = {"requestId": "req123"}

        result = validate_generation_control_payload(valid_payload)
        assert result is not None
        assert result.request_id == "req123"

    async def test_validate_generation_control_invalid(self):
        """Should reject invalid control payloads."""
        from server.websocket.handler import validate_generation_control_payload

        invalid_payload = {}  # Missing requestId

        result = validate_generation_control_payload(invalid_payload)
        assert result is None


class TestWebSocketHandler:
    """Tests for WebSocket message handler."""

    async def test_handler_registration(self):
        """Should register event handlers."""
        from server.websocket.handler import WebSocketHandler
        from server.websocket.manager import ConnectionManager

        manager = ConnectionManager()
        handler = WebSocketHandler(manager)

        async def test_handler(conn_id: str, payload: dict):
            pass

        handler.register_handler(ClientEventType.GENERATION_START, test_handler)
        assert ClientEventType.GENERATION_START in handler._handlers

    async def test_handler_invocation(self):
        """Should invoke registered handlers."""
        from server.websocket.handler import WebSocketHandler
        from server.websocket.manager import ConnectionManager

        manager = ConnectionManager()
        handler = WebSocketHandler(manager)

        handler_called = False
        received_payload = None

        async def test_handler(conn_id: str, payload: dict):
            nonlocal handler_called, received_payload
            handler_called = True
            received_payload = payload

        handler.register_handler(ClientEventType.GENERATION_PAUSE, test_handler)

        # Process a message
        await handler._process_message(
            "conn1",
            {
                "type": "generation:pause",
                "payload": {"requestId": "req123"},
            },
        )

        assert handler_called
        assert received_payload == {"requestId": "req123"}


class TestHeartbeat:
    """Tests for heartbeat functionality."""

    async def test_heartbeat_start_stop(self):
        """Should start and stop heartbeat task."""
        manager = ConnectionManager()

        await manager.start_heartbeat()
        assert manager._heartbeat_task is not None
        assert not manager._heartbeat_task.done()

        await manager.stop_heartbeat()
        await asyncio.sleep(0.1)  # Allow task to cancel
        assert manager._heartbeat_task.done()

    async def test_stale_connection_detection(self):
        """Should detect stale connections based on ping time."""
        from datetime import datetime, timedelta

        manager = ConnectionManager()
        ws = AsyncMock()

        # Create connection with old ping time
        conn = Connection(id="conn1", websocket=ws)
        conn.last_ping = datetime.utcnow() - timedelta(seconds=120)
        manager._connections["conn1"] = conn

        # Check should detect stale connection
        await manager._check_connections()

        # Connection should be removed
        assert manager.connection_count == 0
