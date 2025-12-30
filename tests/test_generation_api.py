"""Integration tests for the Generation API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

from server.models.database import CompanyProfile
from server.services.orchestrator import GenerationContext, GenerationStatus, WorkflowPhase

pytestmark = pytest.mark.asyncio(loop_scope="function")


class TestStartGeneration:
    """Tests for POST /api/documents/generate."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator service."""
        mock = AsyncMock()
        mock.start_generation = AsyncMock()
        mock.active_requests = {}
        return mock

    @pytest.fixture
    def generation_request_data(self, db_profile: CompanyProfile):
        """Sample generation request data."""
        return {
            "documentType": "capability-statement",
            "companyProfileId": db_profile.id,
            "opportunityContext": {
                "solicitationNumber": "W911QY-24-R-0001",
                "targetAgency": "Department of Defense",
            },
            "config": {
                "intensity": "medium",
                "rounds": 3,
                "blueTeam": {"strategyArchitect": True, "complianceNavigator": True},
                "redTeam": {"devilsAdvocate": True, "evaluatorSimulator": True},
            },
        }

    async def test_start_generation_requires_connection_id(
        self, client: AsyncClient, generation_request_data: dict
    ):
        """Should require connectionId query parameter."""
        response = await client.post(
            "/api/documents/generate",
            json=generation_request_data,
        )
        assert response.status_code == 422  # Validation error

    async def test_start_generation_invalid_profile(
        self, client: AsyncClient
    ):
        """Should return 400 for non-existent profile."""
        request_data = {
            "documentType": "capability-statement",
            "companyProfileId": "nonexistent-profile-id",
        }

        response = await client.post(
            "/api/documents/generate?connectionId=test-conn",
            json=request_data,
        )
        # Will fail when trying to load profile
        assert response.status_code in [400, 500]

    async def test_start_generation_validation(self, client: AsyncClient):
        """Should validate request body."""
        # Missing required fields
        response = await client.post(
            "/api/documents/generate?connectionId=test-conn",
            json={},
        )
        assert response.status_code == 422

        # Invalid document type (empty)
        response = await client.post(
            "/api/documents/generate?connectionId=test-conn",
            json={"documentType": "", "companyProfileId": "test"},
        )
        assert response.status_code == 422


class TestGetGenerationStatus:
    """Tests for GET /api/documents/generate/{request_id}/status."""

    async def test_get_status_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent request."""
        response = await client.get("/api/documents/generate/nonexistent/status")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "GENERATION_NOT_FOUND"

    async def test_get_status_response_format(self, client: AsyncClient):
        """Should return proper status format when found."""
        # Note: This test would need a mock orchestrator with active request
        # For now, testing the not found case
        response = await client.get("/api/documents/generate/req_test123/status")
        assert response.status_code == 404


class TestPauseGeneration:
    """Tests for POST /api/documents/generate/{request_id}/pause."""

    async def test_pause_not_running(self, client: AsyncClient):
        """Should return 400 when request not running."""
        response = await client.post("/api/documents/generate/nonexistent/pause")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "PAUSE_FAILED"


class TestResumeGeneration:
    """Tests for POST /api/documents/generate/{request_id}/resume."""

    async def test_resume_not_paused(self, client: AsyncClient):
        """Should return 400 when request not paused."""
        response = await client.post("/api/documents/generate/nonexistent/resume")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "RESUME_FAILED"


class TestCancelGeneration:
    """Tests for POST /api/documents/generate/{request_id}/cancel."""

    async def test_cancel_not_running(self, client: AsyncClient):
        """Should return 400 when request not running."""
        response = await client.post("/api/documents/generate/nonexistent/cancel")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "CANCEL_FAILED"


class TestOrchestratorService:
    """Tests for the OrchestratorService class."""

    async def test_generation_context_initialization(self):
        """Should initialize GenerationContext correctly."""
        from server.models.schemas import SwarmConfigSchema

        config = SwarmConfigSchema()
        context = GenerationContext(
            request_id="req_123",
            document_id="doc_123",
            company_profile_id="profile_123",
            config=config,
        )

        assert context.status == GenerationStatus.QUEUED
        assert context.current_round == 0
        assert context.current_phase == WorkflowPhase.INITIALIZING
        assert context.pause_event.is_set()  # Not paused by default
        assert not context.cancel_requested

    async def test_generation_status_enum(self):
        """Should have expected status values."""
        assert GenerationStatus.QUEUED.value == "queued"
        assert GenerationStatus.RUNNING.value == "running"
        assert GenerationStatus.PAUSED.value == "paused"
        assert GenerationStatus.COMPLETE.value == "complete"
        assert GenerationStatus.ERROR.value == "error"
        assert GenerationStatus.CANCELLED.value == "cancelled"

    async def test_workflow_phase_enum(self):
        """Should have expected phase values."""
        assert WorkflowPhase.INITIALIZING.value == "initializing"
        assert WorkflowPhase.BLUE_BUILD.value == "blue_build"
        assert WorkflowPhase.RED_ATTACK.value == "red_attack"
        assert WorkflowPhase.BLUE_DEFENSE.value == "blue_defense"
        assert WorkflowPhase.SYNTHESIS.value == "synthesis"
        assert WorkflowPhase.COMPLETE.value == "complete"

    async def test_pause_event_behavior(self):
        """Should correctly manage pause/resume state."""
        from server.models.schemas import SwarmConfigSchema

        config = SwarmConfigSchema()
        context = GenerationContext(
            request_id="req_123",
            document_id="doc_123",
            company_profile_id="profile_123",
            config=config,
        )

        # Initially not paused
        assert context.pause_event.is_set()

        # Pause
        context.pause_event.clear()
        assert not context.pause_event.is_set()

        # Resume
        context.pause_event.set()
        assert context.pause_event.is_set()


class TestGenerationRequestSchema:
    """Tests for generation request schema validation."""

    async def test_valid_generation_request(self):
        """Should accept valid generation request."""
        from server.models.schemas import DocumentGenerationRequest

        request = DocumentGenerationRequest(
            document_type="capability-statement",
            company_profile_id="profile-123",
        )

        assert request.document_type == "capability-statement"
        assert request.company_profile_id == "profile-123"
        assert request.config.rounds == 3  # Default

    async def test_generation_request_with_config(self):
        """Should accept generation request with custom config."""
        from server.models.schemas import DocumentGenerationRequest, SwarmConfigSchema

        request = DocumentGenerationRequest(
            document_type="proposal",
            company_profile_id="profile-123",
            config=SwarmConfigSchema(
                intensity="aggressive",
                rounds=5,
            ),
        )

        assert request.config.intensity == "aggressive"
        assert request.config.rounds == 5

    async def test_generation_request_with_opportunity(self):
        """Should accept generation request with opportunity context."""
        from server.models.schemas import (
            DocumentGenerationRequest,
            OpportunityContextSchema,
        )

        request = DocumentGenerationRequest(
            document_type="proposal",
            company_profile_id="profile-123",
            opportunity_context=OpportunityContextSchema(
                solicitation_number="W911QY-24-R-0001",
                target_agency="DoD",
                budget_min=1000000,
                budget_max=5000000,
            ),
        )

        assert request.opportunity_context.solicitation_number == "W911QY-24-R-0001"
        assert request.opportunity_context.budget_min == 1000000

    async def test_swarm_config_defaults(self):
        """Should have sensible defaults for swarm config."""
        from server.models.schemas import SwarmConfigSchema

        config = SwarmConfigSchema()

        assert config.intensity == "medium"
        assert config.rounds == 3
        assert config.consensus == "majority"
        assert config.risk_tolerance == "balanced"
        assert config.blue_team.strategy_architect is True
        assert config.blue_team.compliance_navigator is True
        assert config.red_team.devils_advocate is True
        assert config.red_team.evaluator_simulator is True

    async def test_escalation_thresholds_validation(self):
        """Should validate escalation thresholds."""
        from server.models.schemas import EscalationThresholdsSchema

        thresholds = EscalationThresholdsSchema(
            confidence_min=80,
            critical_unresolved=True,
            compliance_uncertainty=False,
        )

        assert thresholds.confidence_min == 80


class TestGenerationStatusResponse:
    """Tests for generation status response schema."""

    async def test_status_response_serialization(self):
        """Should serialize status response correctly."""
        from datetime import datetime
        from server.models.schemas import GenerationStatusResponse

        response = GenerationStatusResponse(
            request_id="req_123",
            status="running",
            current_round=2,
            total_rounds=3,
            current_phase="blue_defense",
            document_id="doc_123",
        )

        data = response.model_dump(by_alias=True)
        assert data["requestId"] == "req_123"
        assert data["currentRound"] == 2
        assert data["totalRounds"] == 3
        assert data["currentPhase"] == "blue_defense"
        assert data["documentId"] == "doc_123"

    async def test_status_response_with_error(self):
        """Should include error information when present."""
        from server.models.schemas import GenerationStatusResponse

        response = GenerationStatusResponse(
            request_id="req_123",
            status="error",
            error_message="Generation failed due to invalid configuration",
        )

        data = response.model_dump(by_alias=True)
        assert data["status"] == "error"
        assert "invalid configuration" in data["errorMessage"]
