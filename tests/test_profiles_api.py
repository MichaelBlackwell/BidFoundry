"""Tests for the Profiles API endpoints."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from server.main import app
from server.models.database import Base, engine

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_profile_data():
    """Sample company profile data for testing."""
    return {
        "name": "Acme Federal",
        "description": "IT services provider specializing in government contracts",
        "naicsCodes": ["541512", "541519"],
        "certifications": ["8(a)", "SDVOSB"],
        "pastPerformance": ["Contract A", "Contract B"],
    }


class TestListProfiles:
    """Tests for GET /api/profiles."""

    async def test_list_profiles_empty(self, client):
        """Should return empty list when no profiles exist."""
        response = await client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert data["profiles"] == []
        assert data["total"] == 0

    async def test_list_profiles_with_data(self, client, sample_profile_data):
        """Should return list of profiles."""
        # Create a profile first
        await client.post("/api/profiles", json=sample_profile_data)

        response = await client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data["profiles"]) == 1
        assert data["total"] == 1
        assert data["profiles"][0]["name"] == "Acme Federal"

    async def test_list_profiles_pagination(self, client, sample_profile_data):
        """Should respect limit and offset parameters."""
        # Create multiple profiles
        for i in range(5):
            profile_data = {**sample_profile_data, "name": f"Company {i}"}
            await client.post("/api/profiles", json=profile_data)

        # Test limit
        response = await client.get("/api/profiles?limit=2")
        data = response.json()
        assert len(data["profiles"]) == 2
        assert data["total"] == 5

        # Test offset
        response = await client.get("/api/profiles?limit=2&offset=2")
        data = response.json()
        assert len(data["profiles"]) == 2
        assert data["total"] == 5


class TestGetProfile:
    """Tests for GET /api/profiles/{id}."""

    async def test_get_profile_success(self, client, sample_profile_data):
        """Should return profile by ID."""
        # Create profile
        create_response = await client.post("/api/profiles", json=sample_profile_data)
        profile_id = create_response.json()["id"]

        # Get profile
        response = await client.get(f"/api/profiles/{profile_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile_id
        assert data["name"] == "Acme Federal"
        assert data["naicsCodes"] == ["541512", "541519"]

    async def test_get_profile_not_found(self, client):
        """Should return 404 for non-existent profile."""
        response = await client.get("/api/profiles/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "PROFILE_NOT_FOUND"


class TestCreateProfile:
    """Tests for POST /api/profiles."""

    async def test_create_profile_success(self, client, sample_profile_data):
        """Should create a new profile."""
        response = await client.post("/api/profiles", json=sample_profile_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "Acme Federal"
        assert data["description"] == "IT services provider specializing in government contracts"
        assert "createdAt" in data
        assert "updatedAt" in data

    async def test_create_profile_minimal(self, client):
        """Should create profile with only required fields."""
        response = await client.post("/api/profiles", json={"name": "Minimal Corp"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Corp"
        assert data["naicsCodes"] == []
        assert data["certifications"] == []

    async def test_create_profile_invalid_name(self, client):
        """Should reject profile with empty name."""
        response = await client.post("/api/profiles", json={"name": ""})
        assert response.status_code == 422  # Validation error


class TestUpdateProfile:
    """Tests for PUT /api/profiles/{id}."""

    async def test_update_profile_success(self, client, sample_profile_data):
        """Should update an existing profile."""
        # Create profile
        create_response = await client.post("/api/profiles", json=sample_profile_data)
        profile_id = create_response.json()["id"]

        # Update profile
        update_data = {"name": "Acme Federal Updated", "description": "Updated description"}
        response = await client.put(f"/api/profiles/{profile_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Acme Federal Updated"
        assert data["description"] == "Updated description"
        # Other fields should remain unchanged
        assert data["naicsCodes"] == ["541512", "541519"]

    async def test_update_profile_partial(self, client, sample_profile_data):
        """Should update only provided fields."""
        # Create profile
        create_response = await client.post("/api/profiles", json=sample_profile_data)
        profile_id = create_response.json()["id"]

        # Update only certifications
        response = await client.put(
            f"/api/profiles/{profile_id}",
            json={"certifications": ["HUBZone"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["certifications"] == ["HUBZone"]
        assert data["name"] == "Acme Federal"  # Unchanged

    async def test_update_profile_not_found(self, client):
        """Should return 404 for non-existent profile."""
        response = await client.put(
            "/api/profiles/nonexistent-id",
            json={"name": "New Name"},
        )
        assert response.status_code == 404


class TestDeleteProfile:
    """Tests for DELETE /api/profiles/{id}."""

    async def test_delete_profile_success(self, client, sample_profile_data):
        """Should delete an existing profile."""
        # Create profile
        create_response = await client.post("/api/profiles", json=sample_profile_data)
        profile_id = create_response.json()["id"]

        # Delete profile
        response = await client.delete(f"/api/profiles/{profile_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/profiles/{profile_id}")
        assert get_response.status_code == 404

    async def test_delete_profile_not_found(self, client):
        """Should return 404 for non-existent profile."""
        response = await client.delete("/api/profiles/nonexistent-id")
        assert response.status_code == 404
