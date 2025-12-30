"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from server.api.router import api_router
from server.config import settings
from server.exceptions import register_exception_handlers
from server.logging_config import setup_logging
from server.middleware import register_middleware, add_metrics_endpoint
from server.models.database import get_db, init_db
from server.services.orchestrator import init_orchestrator, get_orchestrator
from server.websocket import WebSocketHandler, connection_manager
from server.websocket.events import ClientEventType
from server.websocket.handler import (
    validate_generation_control_payload,
    validate_generation_start_payload,
)

# Import agent registration
from agents.registration import register_all_agents

# Setup structured logging
setup_logging(
    log_level="DEBUG" if settings.debug else "INFO",
    json_output=not settings.debug,  # JSON in production, human-readable in dev
)

logger = logging.getLogger(__name__)

# Create WebSocket handler with the global connection manager
ws_handler = WebSocketHandler(connection_manager)

# Initialize orchestrator service
orchestrator = init_orchestrator(connection_manager)


async def _handle_generation_start(connection_id: str, payload: dict[str, Any]) -> None:
    """Handle generation:start WebSocket events."""
    from server.models.schemas import DocumentGenerationRequest

    validated = validate_generation_start_payload(payload)
    if not validated:
        await connection_manager.send_error(
            connection_id,
            "Invalid generation:start payload",
            "INVALID_PAYLOAD",
        )
        return

    # Create request from payload
    request = DocumentGenerationRequest(
        document_type=validated.document_type,
        company_profile_id=validated.company_profile_id,
        opportunity_context=validated.opportunity_context,
        config=validated.config,
    )

    # Get database session
    async for db in get_db():
        try:
            await orchestrator.start_generation(
                request_id=validated.request_id,
                request=request,
                db=db,
                connection_id=connection_id,
            )
        except Exception as e:
            logger.error(f"Generation start failed: {e}")
            await connection_manager.send_error(
                connection_id,
                f"Failed to start generation: {str(e)}",
                "GENERATION_START_FAILED",
                validated.request_id,
            )
        break


async def _handle_generation_pause(connection_id: str, payload: dict[str, Any]) -> None:
    """Handle generation:pause WebSocket events."""
    validated = validate_generation_control_payload(payload)
    if not validated:
        await connection_manager.send_error(
            connection_id,
            "Invalid generation:pause payload",
            "INVALID_PAYLOAD",
        )
        return

    success = await orchestrator.pause_generation(validated.request_id)
    if not success:
        await connection_manager.send_error(
            connection_id,
            f"Cannot pause generation {validated.request_id}",
            "PAUSE_FAILED",
            validated.request_id,
        )


async def _handle_generation_resume(connection_id: str, payload: dict[str, Any]) -> None:
    """Handle generation:resume WebSocket events."""
    validated = validate_generation_control_payload(payload)
    if not validated:
        await connection_manager.send_error(
            connection_id,
            "Invalid generation:resume payload",
            "INVALID_PAYLOAD",
        )
        return

    success = await orchestrator.resume_generation(validated.request_id)
    if not success:
        await connection_manager.send_error(
            connection_id,
            f"Cannot resume generation {validated.request_id}",
            "RESUME_FAILED",
            validated.request_id,
        )


async def _handle_generation_cancel(connection_id: str, payload: dict[str, Any]) -> None:
    """Handle generation:cancel WebSocket events."""
    validated = validate_generation_control_payload(payload)
    if not validated:
        await connection_manager.send_error(
            connection_id,
            "Invalid generation:cancel payload",
            "INVALID_PAYLOAD",
        )
        return

    success = await orchestrator.cancel_generation(validated.request_id)
    if not success:
        await connection_manager.send_error(
            connection_id,
            f"Cannot cancel generation {validated.request_id}",
            "CANCEL_FAILED",
            validated.request_id,
        )


# Register generation handlers
ws_handler.register_handler(ClientEventType.GENERATION_START, _handle_generation_start)
ws_handler.register_handler(ClientEventType.GENERATION_PAUSE, _handle_generation_pause)
ws_handler.register_handler(ClientEventType.GENERATION_RESUME, _handle_generation_resume)
ws_handler.register_handler(ClientEventType.GENERATION_CANCEL, _handle_generation_cancel)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    await init_db()

    # Register all agents with the global registry
    logger.info("Registering agents...")
    register_all_agents()

    await connection_manager.start_heartbeat()
    logger.info("Adversarial Swarm API started")
    yield
    # Shutdown
    await connection_manager.stop_heartbeat()
    logger.info("Adversarial Swarm API stopped")


app = FastAPI(
    title="Adversarial Swarm API",
    description="Backend server for the Adversarial Swarm document generation system",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register custom exception handlers
register_exception_handlers(app)

# Register middleware (request ID, logging, metrics)
register_middleware(app)

# Add metrics endpoint
add_metrics_endpoint(app)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "Adversarial Swarm API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Include API router
app.include_router(api_router)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time agent streaming.

    Handles:
    - Connection lifecycle (connect, disconnect, reconnect)
    - Generation control events (start, pause, resume, cancel)
    - Real-time updates during document generation
    """
    await ws_handler.handle_connection(websocket)


@app.get("/ws/stats")
async def websocket_stats() -> dict:
    """Get WebSocket connection statistics."""
    return {
        "active_connections": connection_manager.connection_count,
        "max_connections": settings.ws_max_connections,
        "heartbeat_interval": settings.ws_heartbeat_interval,
    }
