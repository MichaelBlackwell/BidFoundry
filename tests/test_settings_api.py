"""
Unit tests for LLM Settings API endpoints.

Tests the settings API including the bug fix for LLM provider propagation
to the agent system.
"""

import os
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from server.main import app


# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_api_keys():
    """Mock both API keys as configured."""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GROQ_API_KEY": "test-groq-key",
    }):
        yield


# ============================================================================
# GET /api/settings Tests
# ============================================================================


class TestGetSettings:
    """Tests for GET /api/settings endpoint."""

    @pytest.mark.asyncio
    async def test_get_settings_returns_current_config(self, client: AsyncClient, mock_api_keys):
        """Test that GET /api/settings returns current LLM configuration."""
        response = await client.get("/api/settings")
        assert response.status_code == 200

        data = response.json()
        assert "provider" in data
        assert "model" in data
        assert "available_providers" in data
        assert data["provider"] in ("anthropic", "groq")

    @pytest.mark.asyncio
    async def test_get_settings_shows_available_providers(self, client: AsyncClient, mock_api_keys):
        """Test that available providers include both anthropic and groq."""
        response = await client.get("/api/settings")
        assert response.status_code == 200

        data = response.json()
        provider_ids = [p["id"] for p in data["available_providers"]]
        assert "anthropic" in provider_ids
        assert "groq" in provider_ids

    @pytest.mark.asyncio
    async def test_get_settings_shows_api_key_status(self, client: AsyncClient, mock_api_keys):
        """Test that settings response indicates which API keys are configured."""
        response = await client.get("/api/settings")
        assert response.status_code == 200

        data = response.json()
        assert "anthropic_configured" in data
        assert "groq_configured" in data
        # Both should be True with our mock
        assert data["anthropic_configured"] is True
        assert data["groq_configured"] is True


# ============================================================================
# PUT /api/settings Tests
# ============================================================================


class TestUpdateSettings:
    """Tests for PUT /api/settings endpoint."""

    @pytest.mark.asyncio
    async def test_update_settings_changes_provider(self, client: AsyncClient, mock_api_keys):
        """Test that updating settings changes the provider."""
        response = await client.put("/api/settings", json={
            "provider": "groq",
            "model": "llama-3.3-70b-versatile"
        })
        assert response.status_code == 200

        data = response.json()
        assert data["provider"] == "groq"
        assert data["model"] == "llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_update_settings_changes_model(self, client: AsyncClient, mock_api_keys):
        """Test that updating settings changes the model."""
        response = await client.put("/api/settings", json={
            "provider": "anthropic",
            "model": "claude-opus-4-5-20251101"
        })
        assert response.status_code == 200

        data = response.json()
        assert data["provider"] == "anthropic"
        assert data["model"] == "claude-opus-4-5-20251101"

    @pytest.mark.asyncio
    async def test_update_settings_invalid_provider(self, client: AsyncClient, mock_api_keys):
        """Test that invalid provider is rejected."""
        response = await client.put("/api/settings", json={
            "provider": "invalid_provider",
            "model": "some-model"
        })
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_settings_invalid_model_for_provider(self, client: AsyncClient, mock_api_keys):
        """Test that invalid model for provider is rejected."""
        response = await client.put("/api/settings", json={
            "provider": "anthropic",
            "model": "llama-3.3-70b-versatile"  # Groq model, not Anthropic
        })
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_MODEL"

    @pytest.mark.asyncio
    async def test_update_settings_requires_api_key(self, client: AsyncClient):
        """Test that changing to a provider without API key fails."""
        # Clear the Groq API key
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False):
            # Remove GROQ_API_KEY if it exists
            env_without_groq = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
            with patch.dict(os.environ, env_without_groq, clear=True):
                response = await client.put("/api/settings", json={
                    "provider": "groq",
                    "model": "llama-3.3-70b-versatile"
                })
                assert response.status_code == 400
                data = response.json()
                assert data["detail"]["code"] == "API_KEY_NOT_CONFIGURED"


# ============================================================================
# Settings Propagation Tests (Bug Fix Verification)
# ============================================================================


class TestSettingsPropagation:
    """
    Tests to verify that LLM settings are properly propagated to the agent system.

    This tests the bug fix where changing settings via the API would update
    environment variables but NOT update the agent system's cached settings,
    causing agents to continue using the old provider (e.g., Groq instead of Anthropic).
    """

    @pytest.mark.asyncio
    async def test_settings_update_calls_configure_llm_settings(self, client: AsyncClient, mock_api_keys):
        """
        Test that updating settings calls configure_llm_settings to update agent system.

        This is the core test for the bug fix. Previously, the settings API would
        update os.environ but NOT call configure_llm_settings, so agents would
        continue using the cached provider/model from startup.
        """
        with patch("server.api.settings.configure_llm_settings") as mock_configure:
            with patch("server.api.settings.AGENTS_AVAILABLE", True):
                response = await client.put("/api/settings", json={
                    "provider": "anthropic",
                    "model": "claude-haiku-4-5-20251001"
                })
                assert response.status_code == 200

                # Verify configure_llm_settings was called with correct arguments
                mock_configure.assert_called_once_with(
                    provider="anthropic",
                    model="claude-haiku-4-5-20251001",
                    api_key_env_var="ANTHROPIC_API_KEY",
                )

    @pytest.mark.asyncio
    async def test_settings_update_propagates_groq_provider(self, client: AsyncClient, mock_api_keys):
        """Test that switching to Groq provider propagates correctly."""
        with patch("server.api.settings.configure_llm_settings") as mock_configure:
            with patch("server.api.settings.AGENTS_AVAILABLE", True):
                response = await client.put("/api/settings", json={
                    "provider": "groq",
                    "model": "llama-3.3-70b-versatile"
                })
                assert response.status_code == 200

                mock_configure.assert_called_once_with(
                    provider="groq",
                    model="llama-3.3-70b-versatile",
                    api_key_env_var="GROQ_API_KEY",
                )

    @pytest.mark.asyncio
    async def test_settings_update_propagates_anthropic_provider(self, client: AsyncClient, mock_api_keys):
        """Test that switching to Anthropic provider propagates correctly."""
        with patch("server.api.settings.configure_llm_settings") as mock_configure:
            with patch("server.api.settings.AGENTS_AVAILABLE", True):
                response = await client.put("/api/settings", json={
                    "provider": "anthropic",
                    "model": "claude-opus-4-5-20251101"
                })
                assert response.status_code == 200

                mock_configure.assert_called_once_with(
                    provider="anthropic",
                    model="claude-opus-4-5-20251101",
                    api_key_env_var="ANTHROPIC_API_KEY",
                )

    @pytest.mark.asyncio
    async def test_settings_update_works_without_agents(self, client: AsyncClient, mock_api_keys):
        """Test that settings can be updated even if agent system is not available."""
        with patch("server.api.settings.AGENTS_AVAILABLE", False):
            with patch("server.api.settings.configure_llm_settings", None):
                response = await client.put("/api/settings", json={
                    "provider": "anthropic",
                    "model": "claude-haiku-4-5-20251001"
                })
                # Should succeed even without agent system
                assert response.status_code == 200


# ============================================================================
# Integration Tests
# ============================================================================


class TestSettingsIntegration:
    """Integration tests for settings with agent config system."""

    @pytest.mark.asyncio
    async def test_full_provider_switch_flow(self, client: AsyncClient, mock_api_keys):
        """
        Test the full flow of switching providers and verifying agent config updates.

        This integration test verifies the complete bug fix by:
        1. Setting provider to Groq
        2. Switching to Anthropic
        3. Verifying the agent config system received the update
        """
        from agents.config import _server_llm_settings, configure_llm_settings

        # First, set to Groq
        configure_llm_settings("groq", "llama-3.3-70b-versatile", "GROQ_API_KEY")

        # Now switch to Anthropic via API
        response = await client.put("/api/settings", json={
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001"
        })
        assert response.status_code == 200

        # Import the module-level cache to verify it was updated
        from agents.config import _server_llm_settings
        assert _server_llm_settings is not None
        assert _server_llm_settings["provider"] == "anthropic"
        assert _server_llm_settings["model"] == "claude-haiku-4-5-20251001"
        assert _server_llm_settings["api_key_env_var"] == "ANTHROPIC_API_KEY"

    @pytest.mark.asyncio
    async def test_new_llm_config_uses_updated_settings(self, client: AsyncClient, mock_api_keys):
        """
        Test that new LLMConfig instances use the updated settings.

        This verifies that after updating settings via API, any new agent
        configuration will use the new provider/model.
        """
        from agents.config import LLMConfig, configure_llm_settings

        # First, configure for Groq
        configure_llm_settings("groq", "llama-3.3-70b-versatile", "GROQ_API_KEY")

        # Verify initial state
        config1 = LLMConfig()
        assert config1.provider == "groq"
        assert config1.model == "llama-3.3-70b-versatile"

        # Now switch to Anthropic via API
        response = await client.put("/api/settings", json={
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001"
        })
        assert response.status_code == 200

        # New LLMConfig should use the updated settings
        config2 = LLMConfig()
        assert config2.provider == "anthropic"
        assert config2.model == "claude-haiku-4-5-20251001"
        assert config2.api_key_env_var == "ANTHROPIC_API_KEY"


# ============================================================================
# GET /api/settings/models Tests
# ============================================================================


class TestGetModels:
    """Tests for GET /api/settings/models endpoint."""

    @pytest.mark.asyncio
    async def test_get_models_returns_both_providers(self, client: AsyncClient):
        """Test that models endpoint returns models for both providers."""
        response = await client.get("/api/settings/models")
        assert response.status_code == 200

        data = response.json()
        assert "anthropic" in data
        assert "groq" in data

    @pytest.mark.asyncio
    async def test_get_models_anthropic_list(self, client: AsyncClient):
        """Test that Anthropic models include expected Claude models."""
        response = await client.get("/api/settings/models")
        assert response.status_code == 200

        data = response.json()
        anthropic_models = data["anthropic"]
        assert "claude-haiku-4-5-20251001" in anthropic_models
        assert "claude-sonnet-4-5-20250929" in anthropic_models
        assert "claude-opus-4-5-20251101" in anthropic_models

    @pytest.mark.asyncio
    async def test_get_models_groq_list(self, client: AsyncClient):
        """Test that Groq models include expected Llama models."""
        response = await client.get("/api/settings/models")
        assert response.status_code == 200

        data = response.json()
        groq_models = data["groq"]
        assert "llama-3.3-70b-versatile" in groq_models
        assert "mixtral-8x7b-32768" in groq_models
