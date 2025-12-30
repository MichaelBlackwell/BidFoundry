"""Pytest configuration and shared fixtures for server tests."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from server.main import app
from server.models.database import (
    Base,
    CompanyProfile,
    Document,
    GenerationRequest,
    ShareLink,
    engine,
    async_session_maker,
)


# ============================================================================
# Event Loop Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest_asyncio.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ============================================================================
# HTTP Client Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_profile_data() -> dict:
    """Sample company profile data for testing."""
    return {
        "name": "Acme Federal",
        "description": "IT services provider specializing in government contracts",
        "naicsCodes": ["541512", "541519"],
        "certifications": ["8(a)", "SDVOSB"],
        "pastPerformance": ["Contract A", "Contract B"],
    }


@pytest.fixture
def sample_document_data() -> dict:
    """Sample document data for testing."""
    return {
        "type": "capability-statement",
        "title": "Acme Federal Capability Statement",
        "status": "draft",
        "confidence": 85.5,
        "content": {
            "sections": [
                {
                    "id": "sec-1",
                    "title": "Executive Summary",
                    "content": "Acme Federal provides enterprise IT solutions...",
                    "confidence": 90.0,
                    "unresolvedCritiques": 0,
                },
                {
                    "id": "sec-2",
                    "title": "Core Capabilities",
                    "content": "Our core capabilities include...",
                    "confidence": 85.0,
                    "unresolvedCritiques": 1,
                },
            ],
            "overallConfidence": 85.5,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        },
        "confidenceReport": {
            "overall": 85.5,
            "sections": {"sec-1": 90.0, "sec-2": 85.0},
        },
        "redTeamReport": {
            "entries": [
                {
                    "agentId": "devils_advocate",
                    "targetSection": "sec-2",
                    "severity": "minor",
                    "critique": "Consider adding more specific metrics",
                    "resolution": None,
                    "status": "pending",
                }
            ],
            "summary": "One minor issue identified",
        },
        "metrics": {
            "roundsCompleted": 3,
            "totalCritiques": 5,
            "criticalCount": 0,
            "majorCount": 1,
            "minorCount": 4,
            "acceptedCount": 4,
            "rebuttedCount": 1,
            "acknowledgedCount": 0,
            "timeElapsedMs": 45000,
        },
    }


@pytest.fixture
def sample_generation_config() -> dict:
    """Sample generation configuration for testing."""
    return {
        "intensity": "medium",
        "rounds": 3,
        "consensus": "majority",
        "blueTeam": {
            "strategyArchitect": True,
            "marketAnalyst": False,
            "complianceNavigator": True,
            "captureStrategist": False,
        },
        "redTeam": {
            "devilsAdvocate": True,
            "competitorSimulator": False,
            "evaluatorSimulator": True,
            "riskAssessor": False,
        },
        "specialists": {},
        "riskTolerance": "balanced",
        "escalationThresholds": {
            "confidenceMin": 70,
            "criticalUnresolved": True,
            "complianceUncertainty": True,
        },
    }


# ============================================================================
# Database Model Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def created_profile(client: AsyncClient, sample_profile_data: dict) -> dict:
    """Create a company profile and return its data."""
    response = await client.post("/api/profiles", json=sample_profile_data)
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def db_profile(db_session: AsyncSession, sample_profile_data: dict) -> CompanyProfile:
    """Create a company profile directly in the database."""
    profile = CompanyProfile(
        id=str(uuid.uuid4()),
        name=sample_profile_data["name"],
        description=sample_profile_data["description"],
        naics_codes=sample_profile_data["naicsCodes"],
        certifications=sample_profile_data["certifications"],
        past_performance=sample_profile_data["pastPerformance"],
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest_asyncio.fixture
async def db_document(
    db_session: AsyncSession, db_profile: CompanyProfile, sample_document_data: dict
) -> Document:
    """Create a document directly in the database."""
    document = Document(
        id=str(uuid.uuid4()),
        type=sample_document_data["type"],
        title=sample_document_data["title"],
        status=sample_document_data["status"],
        confidence=sample_document_data["confidence"],
        company_profile_id=db_profile.id,
        content=sample_document_data["content"],
        confidence_report=sample_document_data["confidenceReport"],
        red_team_report=sample_document_data["redTeamReport"],
        metrics=sample_document_data["metrics"],
        requires_human_review=False,
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    return document


@pytest_asyncio.fixture
async def db_documents(
    db_session: AsyncSession, db_profile: CompanyProfile
) -> list[Document]:
    """Create multiple documents in the database."""
    documents = []
    statuses = ["draft", "approved", "rejected", "draft", "approved"]
    types = [
        "capability-statement",
        "proposal",
        "capability-statement",
        "proposal",
        "capability-statement",
    ]

    for i, (status, doc_type) in enumerate(zip(statuses, types)):
        doc = Document(
            id=str(uuid.uuid4()),
            type=doc_type,
            title=f"Test Document {i + 1}",
            status=status,
            confidence=70.0 + i * 5,
            company_profile_id=db_profile.id,
            requires_human_review=(i % 2 == 0),
        )
        db_session.add(doc)
        documents.append(doc)

    await db_session.commit()
    for doc in documents:
        await db_session.refresh(doc)
    return documents


# ============================================================================
# WebSocket Test Helpers
# ============================================================================


class WebSocketTestClient:
    """Helper class for WebSocket testing."""

    def __init__(self, client: AsyncClient):
        self.client = client
        self.messages: list[dict] = []
        self.connection_id: str | None = None

    async def connect(self) -> str:
        """Connect to the WebSocket endpoint."""
        # Note: For full WebSocket testing, use websockets library
        # This is a placeholder for the WebSocket test infrastructure
        self.connection_id = str(uuid.uuid4())
        return self.connection_id


@pytest.fixture
def ws_test_client(client: AsyncClient) -> WebSocketTestClient:
    """Create a WebSocket test client helper."""
    return WebSocketTestClient(client)


# ============================================================================
# Utility Functions
# ============================================================================


def assert_datetime_recent(dt: datetime | str, seconds: int = 60) -> None:
    """Assert that a datetime is within the last N seconds."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = (now - dt).total_seconds()
    assert abs(delta) < seconds, f"Datetime {dt} is not within {seconds}s of now"


def assert_valid_uuid(value: str) -> None:
    """Assert that a string is a valid UUID."""
    try:
        uuid.UUID(value)
    except ValueError:
        pytest.fail(f"'{value}' is not a valid UUID")
