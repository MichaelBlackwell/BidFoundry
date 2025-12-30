"""Generation API endpoints.

Provides REST endpoints for starting document generation and checking status.
Real-time updates are delivered via WebSocket.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.dependencies import DbSession
from server.models.schemas import (
    DocumentGenerationRequest,
    GenerationStartResponse,
    GenerationStatusResponse,
)
from server.services.orchestrator import get_orchestrator, OrchestratorService

router = APIRouter()


def get_orchestrator_dep() -> OrchestratorService:
    """Dependency to get orchestrator service."""
    return get_orchestrator()


OrchestratorDep = Annotated[OrchestratorService, Depends(get_orchestrator_dep)]


@router.post(
    "/generate",
    response_model=GenerationStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start document generation",
    description="Start a new document generation workflow. Real-time updates are delivered via WebSocket.",
)
async def start_generation(
    request: DocumentGenerationRequest,
    db: DbSession,
    orchestrator: OrchestratorDep,
    connection_id: str = Query(
        ...,
        alias="connectionId",
        description="WebSocket connection ID for receiving updates",
    ),
) -> GenerationStartResponse:
    """
    Start a new document generation workflow.

    The generation runs asynchronously. Subscribe to WebSocket events using the
    returned requestId to receive real-time updates on progress.

    Required:
    - connectionId: Active WebSocket connection ID for receiving updates

    Returns:
    - requestId: Unique identifier for tracking this generation
    - status: Initial status (always "started")
    - estimatedDuration: Estimated time in milliseconds
    """
    request_id = f"req_{uuid.uuid4().hex[:12]}"

    try:
        context = await orchestrator.start_generation(
            request_id=request_id,
            request=request,
            db=db,
            connection_id=connection_id,
        )

        # Estimate duration based on config
        rounds = request.config.rounds
        estimated_duration = rounds * 60000  # ~60 seconds per round

        return GenerationStartResponse(
            request_id=request_id,
            status="started",
            estimated_duration=estimated_duration,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REQUEST",
                "message": str(e),
            },
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "GENERATION_START_FAILED",
                "message": f"Failed to start generation: {str(e)}",
            },
        )


@router.get(
    "/generate/{request_id}/status",
    response_model=GenerationStatusResponse,
    summary="Get generation status",
    description="Get the current status of a document generation request.",
)
async def get_generation_status(
    request_id: str,
    db: DbSession,
    orchestrator: OrchestratorDep,
) -> GenerationStatusResponse:
    """
    Get the current status of a generation request.

    Returns detailed status including:
    - Current phase and round
    - Document ID when available
    - Error information if failed
    - Timing information
    """
    status_data = await orchestrator.get_generation_status(request_id, db)

    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "GENERATION_NOT_FOUND",
                "message": f"Generation request not found: {request_id}",
            },
        )

    return GenerationStatusResponse(
        request_id=status_data["request_id"],
        status=status_data["status"],
        current_round=status_data.get("current_round", 0),
        total_rounds=status_data.get("total_rounds", 0),
        current_phase=status_data.get("current_phase"),
        document_id=status_data.get("document_id"),
        error_message=status_data.get("error_message"),
        started_at=status_data.get("started_at"),
        completed_at=status_data.get("completed_at"),
    )


@router.post(
    "/generate/{request_id}/pause",
    status_code=status.HTTP_200_OK,
    summary="Pause generation",
    description="Pause an active document generation workflow.",
)
async def pause_generation(
    request_id: str,
    orchestrator: OrchestratorDep,
) -> dict:
    """
    Pause an active generation workflow.

    The generation can be resumed later using the resume endpoint.
    Pausing preserves all progress made so far.
    """
    success = await orchestrator.pause_generation(request_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PAUSE_FAILED",
                "message": f"Cannot pause generation {request_id}. It may not be running or may not exist.",
            },
        )

    return {"requestId": request_id, "status": "paused"}


@router.post(
    "/generate/{request_id}/resume",
    status_code=status.HTTP_200_OK,
    summary="Resume generation",
    description="Resume a paused document generation workflow.",
)
async def resume_generation(
    request_id: str,
    orchestrator: OrchestratorDep,
) -> dict:
    """
    Resume a paused generation workflow.

    The generation continues from where it was paused.
    """
    success = await orchestrator.resume_generation(request_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "RESUME_FAILED",
                "message": f"Cannot resume generation {request_id}. It may not be paused or may not exist.",
            },
        )

    return {"requestId": request_id, "status": "running"}


@router.post(
    "/generate/{request_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel generation",
    description="Cancel an active or paused document generation workflow.",
)
async def cancel_generation(
    request_id: str,
    orchestrator: OrchestratorDep,
) -> dict:
    """
    Cancel a generation workflow.

    This immediately stops the generation. Any partial results are discarded.
    The generation cannot be resumed after cancellation.
    """
    success = await orchestrator.cancel_generation(request_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CANCEL_FAILED",
                "message": f"Cannot cancel generation {request_id}. It may already be complete or may not exist.",
            },
        )

    return {"requestId": request_id, "status": "cancelled"}
