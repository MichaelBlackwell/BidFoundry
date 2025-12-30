# Backend Server Design Document

## Adversarial Swarm API Server v1.1

> **Implementation Status:** ✅ Backend fully operational with REST API, WebSocket streaming, document export, and multi-provider LLM support.

---

## 1. Executive Summary

This document specifies the FastAPI backend server that bridges the React frontend with the Python agent orchestration system. The server provides REST endpoints for CRUD operations and WebSocket connections for real-time agent streaming during document generation.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          React Frontend                                  │
│                    (localhost:5173 in dev)                               │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │         HTTP/WS             │
              ▼                             ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│      REST API           │    │     WebSocket           │
│   /api/documents/*      │    │     /ws                 │
│   /api/profiles/*       │    │                         │
│   /api/generation/*     │    │  Real-time streaming    │
└─────────────────────────┘    └─────────────────────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │      Service Layer          │
              │   OrchestratorService       │
              │   ProfilesService           │
              │   DocumentsService          │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │      Agent System           │
              │   ArbiterAgent              │
              │   MessageBus                │
              │   Blue/Red Team Agents      │
              └─────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │      Data Layer             │
              │   SQLite (dev) / Postgres   │
              │   File Storage              │
              └─────────────────────────────┘
```

---

## 3. Project Structure

```
d:\ShawarmAgen\
├── server/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Server configuration
│   ├── dependencies.py            # Dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py              # Main API router
│   │   ├── documents.py           # Document endpoints
│   │   ├── profiles.py            # Company profile endpoints
│   │   └── generation.py          # Generation endpoints
│   │
│   ├── websocket/
│   │   ├── __init__.py
│   │   ├── manager.py             # Connection manager
│   │   ├── handler.py             # WebSocket message handler
│   │   └── events.py              # Event type definitions
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # Generation orchestration
│   │   ├── profiles.py            # Profile management
│   │   ├── documents.py           # Document management
│   │   └── export.py              # Document export service
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy models
│   │   └── schemas.py             # Pydantic request/response schemas
│   │
│   └── utils/
│       ├── __init__.py
│       └── converters.py          # Data conversion utilities
│
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── run_server.py                  # Server startup script
```

---

## 4. Dependencies

### requirements.txt

```
# Web Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# WebSocket
websockets>=12.0

# Database
sqlalchemy>=2.0.25
aiosqlite>=0.19.0        # Async SQLite for dev
asyncpg>=0.29.0          # Async Postgres for prod

# Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0
email-validator>=2.1.0

# Document Export
python-docx>=1.1.0       # Word export
reportlab>=4.0.0         # PDF export
markdown>=3.5.0          # Markdown processing

# Utilities
python-dotenv>=1.0.0
aiofiles>=23.2.0

# Development
pytest>=7.4.0
pytest-asyncio>=0.23.0
httpx>=0.26.0            # Async HTTP client for testing
```

---

## 5. REST API Specification

### 5.1 Company Profiles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profiles` | List all company profiles |
| GET | `/api/profiles/{id}` | Get profile by ID |
| POST | `/api/profiles` | Create new profile |
| PUT | `/api/profiles/{id}` | Update profile |
| DELETE | `/api/profiles/{id}` | Delete profile |

#### Request/Response Schemas

```python
# GET /api/profiles
# Response
{
    "profiles": [
        {
            "id": "uuid",
            "name": "Acme Federal",
            "description": "IT services provider",
            "naicsCodes": ["541512", "541519"],
            "certifications": ["8(a)", "SDVOSB"],
            "pastPerformance": ["Contract A", "Contract B"],
            "createdAt": "2025-01-15T10:00:00Z",
            "updatedAt": "2025-01-15T10:00:00Z"
        }
    ],
    "total": 1
}

# POST /api/profiles
# Request
{
    "name": "Acme Federal",
    "description": "IT services provider",
    "naicsCodes": ["541512"],
    "certifications": ["8(a)"],
    "pastPerformance": []
}
```

---

### 5.2 Document Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/generate` | Start document generation |
| GET | `/api/documents/generate/{requestId}/status` | Get generation status |

#### Start Generation

```python
# POST /api/documents/generate
# Request
{
    "documentType": "capability-statement",
    "companyProfileId": "uuid",
    "opportunityContext": {
        "solicitationNumber": "W911QY-24-R-0001",
        "targetAgency": "Department of Defense",
        "knownCompetitors": ["Competitor A"],
        "budgetMin": 1000000,
        "budgetMax": 5000000,
        "dueDate": "2025-03-01"
    },
    "config": {
        "intensity": "medium",
        "rounds": 3,
        "consensus": "majority",
        "blueTeam": {
            "strategy_architect": true,
            "compliance_navigator": true
        },
        "redTeam": {
            "devils_advocate": true,
            "evaluator_simulator": true
        },
        "specialists": {},
        "riskTolerance": "balanced",
        "escalationThresholds": {
            "confidenceMin": 70,
            "criticalUnresolved": true,
            "complianceUncertainty": true
        }
    }
}

# Response
{
    "requestId": "req_123abc",
    "status": "started",
    "estimatedDuration": 60000
}
```

---

### 5.3 Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents` | List documents with filtering |
| GET | `/api/documents/{id}` | Get document by ID |
| DELETE | `/api/documents/{id}` | Delete document |
| POST | `/api/documents/{id}/duplicate` | Duplicate document |
| POST | `/api/documents/{id}/approve` | Approve after review |
| POST | `/api/documents/{id}/reject` | Reject after review |
| POST | `/api/documents/{id}/regenerate` | Regenerate with new config |
| GET | `/api/documents/{id}/export` | Export document |
| POST | `/api/documents/{id}/share` | Create share link |

#### List Documents Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max results (default: 20) |
| `offset` | int | Pagination offset |
| `status` | string | Filter: draft, approved, rejected |
| `type` | string | Filter by document type |
| `search` | string | Search in title |
| `sortBy` | string | createdAt, updatedAt, title, confidence |
| `sortOrder` | string | asc, desc |

#### Get Document Response (Full Output)

```python
{
    "documentId": "doc_123",
    "content": {
        "id": "doc_123",
        "sections": [
            {
                "id": "sec-1",
                "title": "Executive Summary",
                "content": "...",
                "confidence": 85,
                "unresolvedCritiques": 0
            }
        ],
        "overallConfidence": 82,
        "updatedAt": "2025-01-15T12:00:00Z"
    },
    "confidence": {
        "overall": 82,
        "sections": {
            "sec-1": 85,
            "sec-2": 78
        }
    },
    "redTeamReport": {
        "entries": [...],
        "summary": "Red team analysis complete..."
    },
    "debateLog": [...],
    "metrics": {
        "roundsCompleted": 3,
        "totalCritiques": 15,
        "criticalCount": 2,
        "majorCount": 5,
        "minorCount": 8,
        "acceptedCount": 10,
        "rebuttedCount": 3,
        "acknowledgedCount": 2,
        "timeElapsedMs": 180000
    },
    "requiresHumanReview": false
}
```

---

## 6. WebSocket Protocol

### 6.1 Connection

```
WebSocket URL: ws://localhost:8000/ws
```

### 6.2 Message Format

All messages follow this structure:

```python
{
    "type": "event_type",
    "payload": { ... },
    "timestamp": 1705312800000,
    "requestId": "req_123abc"
}
```

### 6.3 Client → Server Events

| Event | Payload | Description |
|-------|---------|-------------|
| `generation:start` | `{ requestId, config }` | Begin generation |
| `generation:pause` | `{ requestId }` | Pause workflow |
| `generation:resume` | `{ requestId }` | Resume workflow |
| `generation:cancel` | `{ requestId }` | Cancel generation |

### 6.4 Server → Client Events

| Event | Payload | Description |
|-------|---------|-------------|
| `round:start` | `{ round, totalRounds, phase, agents[] }` | Round beginning |
| `round:end` | `{ round, summary }` | Round complete |
| `phase:change` | `{ phase, round }` | Workflow phase changed |
| `agent:registered` | `{ agents[] }` | Available agents list |
| `agent:thinking` | `{ agentId, target? }` | Agent processing |
| `agent:streaming` | `{ agentId, chunk }` | Streaming output chunk |
| `agent:complete` | `{ agentId, critique?, response? }` | Agent finished |
| `draft:update` | `{ draft, changedSections[] }` | Document updated |
| `confidence:update` | `{ overall, sections }` | Confidence scores |
| `escalation:triggered` | `{ reasons[], disputes[] }` | Human review needed |
| `generation:complete` | `{ result: FinalOutput }` | Generation finished |
| `generation:error` | `{ error, code?, recoverable? }` | Error occurred |

---

## 7. Service Layer Design

### 7.1 OrchestratorService

The central service that bridges WebSocket events to the agent system.

```python
# server/services/orchestrator.py

class OrchestratorService:
    """
    Manages document generation workflows.

    Responsibilities:
    - Creates and configures ArbiterAgent instances
    - Subscribes to MessageBus events
    - Translates agent messages to WebSocket events
    - Tracks active generation requests
    - Handles pause/resume/cancel operations
    """

    def __init__(
        self,
        ws_manager: ConnectionManager,
        db: AsyncSession
    ):
        self.ws_manager = ws_manager
        self.db = db
        self.active_requests: Dict[str, GenerationContext] = {}

    async def start_generation(
        self,
        request_id: str,
        request: DocumentGenerationRequest
    ) -> None:
        """
        Start a new document generation workflow.

        1. Load company profile from database
        2. Create SwarmContext with request data
        3. Configure ArbiterAgent based on request.config
        4. Subscribe to MessageBus with event forwarder
        5. Run arbiter.generate_document() in background task
        6. Stream events to WebSocket as they occur
        """
        pass

    async def pause_generation(self, request_id: str) -> bool:
        """Pause an active generation."""
        pass

    async def resume_generation(self, request_id: str) -> bool:
        """Resume a paused generation."""
        pass

    async def cancel_generation(self, request_id: str) -> bool:
        """Cancel an active generation."""
        pass

    async def _on_message_bus_event(
        self,
        message: Message,
        request_id: str
    ) -> None:
        """
        Handle messages from the agent MessageBus.

        Converts internal Message objects to WebSocket events:
        - DRAFT messages → draft:update
        - CRITIQUE messages → agent:complete (with critique)
        - RESPONSE messages → agent:complete (with response)
        - CONTROL messages → round:start, round:end, etc.
        """
        pass
```

### 7.2 Event Mapping

| MessageBus Event | WebSocket Event |
|------------------|-----------------|
| `MessageType.CONTROL` (round_start) | `round:start` |
| `MessageType.CONTROL` (round_end) | `round:end` |
| `MessageType.DRAFT` | `draft:update` |
| `MessageType.CRITIQUE` | `agent:complete` with critique |
| `MessageType.RESPONSE` | `agent:complete` with response |
| WorkflowPhase change | `phase:change` |
| Confidence recalculation | `confidence:update` |
| Human escalation triggered | `escalation:triggered` |

---

## 8. Database Schema

### 8.1 SQLAlchemy Models

```python
# server/models/database.py

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    naics_codes = Column(JSON, default=list)       # List[str]
    certifications = Column(JSON, default=list)    # List[str]
    past_performance = Column(JSON, default=list)  # List[str]

    # Full company profile data (from models/company_profile.py)
    full_profile = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="company_profile")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)  # DocumentType enum value
    title = Column(String, nullable=False)
    status = Column(String, default="draft")  # draft, approved, rejected
    confidence = Column(Float, default=0.0)

    company_profile_id = Column(String, ForeignKey("company_profiles.id"))
    company_profile = relationship("CompanyProfile", back_populates="documents")

    # Full output data (FinalOutput structure)
    content = Column(JSON)  # Document sections
    confidence_report = Column(JSON)
    red_team_report = Column(JSON)
    debate_log = Column(JSON)
    metrics = Column(JSON)

    # Generation config used
    generation_config = Column(JSON)

    # Review tracking
    requires_human_review = Column(Boolean, default=False)
    review_notes = Column(Text)
    reviewed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GenerationRequest(Base):
    __tablename__ = "generation_requests"

    id = Column(String, primary_key=True)  # request_id
    document_id = Column(String, ForeignKey("documents.id"))
    status = Column(String, default="queued")  # queued, running, complete, error

    # Progress tracking
    current_round = Column(Integer, default=0)
    total_rounds = Column(Integer)
    current_phase = Column(String)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Error tracking
    error_message = Column(Text)
    error_code = Column(String)


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"))
    token = Column(String, unique=True)
    password_hash = Column(String)  # Optional password protection
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 9. Configuration

### 9.1 Environment Variables

```bash
# .env.example

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/swarm.db
# For production: postgresql+asyncpg://user:pass@host:5432/dbname

# LLM Configuration (for agents)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Export
EXPORT_TEMP_DIR=./data/exports
MAX_EXPORT_SIZE_MB=50
```

### 9.2 Server Config

```python
# server/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/swarm.db"

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100

    # Generation
    max_concurrent_generations: int = 5
    generation_timeout_seconds: int = 600

    # Export
    export_temp_dir: str = "./data/exports"
    max_export_size_mb: int = 50

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 10. Implementation Status

### Phase 1: Core Server Setup ✅
- [x] Create project structure
- [x] Set up FastAPI app with CORS
- [x] Configure async SQLite database
- [x] Implement health check endpoint
- [x] Add structured logging (JSON in prod, human-readable in dev)
- [x] Custom exception handlers
- [x] Request ID middleware
- [x] Metrics endpoint

### Phase 2: Profiles API ✅
- [x] Create CompanyProfile model
- [x] Implement CRUD endpoints
- [x] Add validation schemas
- [x] Write tests (`tests/test_profiles_api.py`)

### Phase 3: Documents API ✅
- [x] Create Document model
- [x] Implement list/get/delete endpoints
- [x] Add filtering and pagination
- [x] Implement status updates (approve/reject)
- [x] Document duplication endpoint
- [x] Write tests (`tests/test_documents_api.py`)

### Phase 4: WebSocket Infrastructure ✅
- [x] Create ConnectionManager with heartbeat
- [x] Implement message handler with event routing
- [x] Add connection lifecycle management
- [x] Handle reconnection scenarios
- [x] Write tests (`tests/test_websocket.py`)

### Phase 5: Generation Integration ✅
- [x] Create OrchestratorService
- [x] Bridge MessageBus to WebSocket
- [x] Implement start/pause/resume/cancel
- [x] Handle errors and recovery
- [x] Real-time agent streaming
- [x] Write tests (`tests/test_generation_api.py`)

### Phase 6: Document Export ✅
- [x] Implement Word export (.docx)
- [x] Implement PDF export (with tables, styling)
- [x] Implement Markdown export
- [x] Create share link functionality (with password protection and expiration)

### Phase 7: Testing & Polish ✅
- [x] Integration tests
- [x] Error handling improvements
- [x] Logging and monitoring
- [ ] Load testing (pending)

---

## 11. Key Integration Points

### 11.1 Connecting to ArbiterAgent

```python
# In OrchestratorService.start_generation()

from agents import ArbiterAgent, DocumentRequest, get_registry
from comms.bus import MessageBus

async def start_generation(self, request_id: str, request: DocumentGenerationRequest):
    # 1. Load company profile
    profile = await self.db.get(CompanyProfile, request.company_profile_id)

    # 2. Create DocumentRequest for arbiter
    doc_request = DocumentRequest(
        id=request_id,
        document_type=request.document_type,
        company_profile=profile.full_profile,
        opportunity=request.opportunity_context,
        max_adversarial_rounds=request.config.rounds,
        consensus_threshold=0.80,
        confidence_threshold=request.config.escalation_thresholds.confidence_min / 100,
    )

    # 3. Create and initialize arbiter
    arbiter = ArbiterAgent()
    message_bus = MessageBus()

    # 4. Subscribe to message bus for streaming
    await message_bus.subscribe(
        agent_role="websocket_bridge",
        message_types=[MessageType.DRAFT, MessageType.CRITIQUE, MessageType.RESPONSE, MessageType.CONTROL],
        handler=lambda msg: self._on_message_bus_event(msg, request_id)
    )

    await arbiter.initialize(registry=get_registry(), message_bus=message_bus)

    # 5. Run generation in background
    self.active_requests[request_id] = GenerationContext(
        arbiter=arbiter,
        message_bus=message_bus,
        task=asyncio.create_task(self._run_generation(request_id, arbiter, doc_request))
    )

async def _run_generation(self, request_id: str, arbiter: ArbiterAgent, request: DocumentRequest):
    try:
        # Notify start
        await self.ws_manager.broadcast(request_id, {
            "type": "generation:started",
            "payload": {"requestId": request_id}
        })

        # Run the workflow
        result = await arbiter.generate_document(request)

        # Save to database
        await self._save_document(request_id, result)

        # Notify complete
        await self.ws_manager.broadcast(request_id, {
            "type": "generation:complete",
            "payload": {"result": self._format_final_output(result)}
        })

    except Exception as e:
        await self.ws_manager.broadcast(request_id, {
            "type": "generation:error",
            "payload": {"error": str(e), "recoverable": False}
        })
```

### 11.2 Mapping Agent Roles to Frontend

| Python AgentRole | Frontend agentId | Category |
|------------------|------------------|----------|
| `STRATEGY_ARCHITECT` | `strategy_architect` | blue |
| `MARKET_ANALYST` | `market_analyst` | blue |
| `COMPLIANCE_NAVIGATOR` | `compliance_navigator` | blue |
| `CAPTURE_STRATEGIST` | `capture_strategist` | blue |
| `DEVILS_ADVOCATE` | `devils_advocate` | red |
| `COMPETITOR_SIMULATOR` | `competitor_simulator` | red |
| `EVALUATOR_SIMULATOR` | `evaluator_simulator` | red |
| `RISK_ASSESSOR` | `risk_assessor` | red |

---

## 12. Running the Server

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python run_server.py
# or
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# With gunicorn
gunicorn server.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### With Frontend

```bash
# Terminal 1: Backend
cd d:\ShawarmAgen
python run_server.py

# Terminal 2: Frontend
cd d:\ShawarmAgen\frontend
npm run dev
```

Then open http://localhost:5173 and the frontend will connect to the backend at http://localhost:8000.

---

## 13. Error Handling

### 13.1 HTTP Error Responses

```python
{
    "code": "PROFILE_NOT_FOUND",
    "message": "Company profile not found: abc123",
    "details": {
        "profileId": "abc123"
    }
}
```

### 13.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PROFILE_NOT_FOUND` | 404 | Company profile doesn't exist |
| `DOCUMENT_NOT_FOUND` | 404 | Document doesn't exist |
| `GENERATION_IN_PROGRESS` | 409 | Request already generating |
| `GENERATION_NOT_FOUND` | 404 | Generation request not found |
| `INVALID_CONFIG` | 400 | Invalid swarm configuration |
| `EXPORT_FAILED` | 500 | Document export failed |
| `WS_CONNECTION_FAILED` | 500 | WebSocket connection error |

---

## Appendix A: Frontend Type Alignment

The backend response schemas are designed to match the frontend TypeScript types in `frontend/src/types/index.ts`:

| Frontend Type | Backend Schema |
|---------------|----------------|
| `CompanyProfile` | `CompanyProfileSchema` |
| `DocumentRequest` | `GenerationRequestSchema` |
| `SwarmConfig` | `SwarmConfigSchema` |
| `FinalOutput` | `FinalOutputSchema` |
| `GeneratedDocument` | `DocumentListItemSchema` |

All datetime fields are serialized as ISO 8601 strings.

---

---

## 14. Additional Implemented Features

### 14.1 Settings API ✅

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get current LLM settings and available providers |
| PUT | `/api/settings` | Update LLM provider and model (session-level) |
| GET | `/api/settings/models` | Get available models per provider |

**Supported LLM Providers:**
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus
- **Groq**: Llama 3.1 70B, Llama 3.1 8B, Mixtral 8x7B, Gemma2 9B

### 14.2 Enhanced Document Endpoints ✅

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/{id}/duplicate` | Duplicate a document |
| GET | `/api/documents/{id}/export` | Export document (word/pdf/markdown) |
| POST | `/api/documents/{id}/share` | Create share link |
| GET | `/api/documents/{id}/share` | List share links for document |
| DELETE | `/api/documents/{id}/share/{link_id}` | Delete share link |
| GET | `/api/documents/shared/{token}` | Access shared document |

### 14.3 WebSocket Stats Endpoint ✅

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ws/stats` | Get WebSocket connection statistics |

### 14.4 Metrics & Health ✅

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check endpoint |
| GET | `/metrics` | Application metrics (request counts, latencies) |

---

*Document Version: 1.1*
*Status: Implementation Complete*
*Last Updated: 2025-01-15*
