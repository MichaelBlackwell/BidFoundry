"""Pydantic request/response schemas for API validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Company Profile Schemas
# ============================================================================


class CompanyProfileBase(BaseModel):
    """Base schema for company profile data."""

    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    description: Optional[str] = Field(None, max_length=2000, description="Company description")
    naics_codes: list[str] = Field(default_factory=list, alias="naicsCodes", description="NAICS codes")
    certifications: list[str] = Field(default_factory=list, description="Company certifications")
    past_performance: list[str] = Field(
        default_factory=list, alias="pastPerformance", description="Past performance references"
    )

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class CompanyProfileCreate(CompanyProfileBase):
    """Schema for creating a new company profile."""

    full_profile: Optional[dict] = Field(None, alias="fullProfile", description="Full profile data")


class CompanyProfileUpdate(BaseModel):
    """Schema for updating a company profile (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    naics_codes: Optional[list[str]] = Field(None, alias="naicsCodes")
    certifications: Optional[list[str]] = None
    past_performance: Optional[list[str]] = Field(None, alias="pastPerformance")
    full_profile: Optional[dict] = Field(None, alias="fullProfile")

    model_config = ConfigDict(populate_by_name=True)


class CompanyProfileResponse(CompanyProfileBase):
    """Schema for company profile response."""

    id: str
    full_profile: Optional[dict] = Field(None, alias="fullProfile")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)


class CompanyProfileListResponse(BaseModel):
    """Schema for list of company profiles."""

    profiles: list[CompanyProfileResponse]
    total: int


# ============================================================================
# Document Schemas
# ============================================================================


class DocumentSectionSchema(BaseModel):
    """Schema for a document section."""

    id: str
    title: str
    content: str
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    unresolved_critiques: int = Field(default=0, alias="unresolvedCritiques")

    model_config = ConfigDict(populate_by_name=True)


class DocumentContentSchema(BaseModel):
    """Schema for document content."""

    id: str
    sections: list[DocumentSectionSchema] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.0, alias="overallConfidence")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class ConfidenceReportSchema(BaseModel):
    """Schema for confidence scores."""

    overall: float = Field(default=0.0)
    sections: dict[str, float] = Field(default_factory=dict)


class DebateEntrySchema(BaseModel):
    """Schema for debate log entry.

    Aligned with frontend DebateEntry type for WebSocket events.
    """

    id: Optional[str] = None
    round: int
    phase: str  # 'blue-build' | 'red-attack' | 'blue-defense' | 'synthesis'
    agent_id: Optional[str] = Field(None, alias="agentId")
    type: str  # 'critique' | 'response' | 'synthesis'
    content: str
    timestamp: datetime | str  # Allow string for flexibility
    severity: str | None = None  # For critiques: 'critical' | 'major' | 'minor'
    status: str | None = None  # For critiques: 'pending' | 'accepted' | 'rebutted' | 'acknowledged'

    model_config = ConfigDict(populate_by_name=True)


class RedTeamReportSchema(BaseModel):
    """Schema for red team report.

    Aligned with frontend RedTeamReport type for WebSocket events.
    """

    entries: list[DebateEntrySchema] = Field(default_factory=list)
    summary: str = ""
    critiques_by_severity: dict[str, int] = Field(default_factory=dict, alias="critiquesBySeverity")
    responses_by_disposition: dict[str, int] = Field(default_factory=dict, alias="responsesByDisposition")

    class Config:
        populate_by_name = True


class GenerationMetricsSchema(BaseModel):
    """Schema for generation metrics."""

    rounds_completed: int = Field(default=0, alias="roundsCompleted")
    total_critiques: int = Field(default=0, alias="totalCritiques")
    critical_count: int = Field(default=0, alias="criticalCount")
    major_count: int = Field(default=0, alias="majorCount")
    minor_count: int = Field(default=0, alias="minorCount")
    accepted_count: int = Field(default=0, alias="acceptedCount")
    rebutted_count: int = Field(default=0, alias="rebuttedCount")
    acknowledged_count: int = Field(default=0, alias="acknowledgedCount")
    time_elapsed_ms: int = Field(default=0, alias="timeElapsedMs")

    model_config = ConfigDict(populate_by_name=True)


class DocumentBase(BaseModel):
    """Base schema for document data."""

    type: str = Field(..., description="Document type (e.g., capability-statement)")
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    status: str = Field(default="draft", description="Document status: draft, approved, rejected")
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)

    model_config = ConfigDict(populate_by_name=True)


class DocumentListItemSchema(BaseModel):
    """Schema for document in list response (summary view)."""

    id: str
    type: str
    title: str
    status: str
    confidence: float
    company_profile_id: Optional[str] = Field(None, alias="companyProfileId")
    requires_human_review: bool = Field(default=False, alias="requiresHumanReview")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_validator("confidence", mode="before")
    @classmethod
    def convert_confidence_to_percentage(cls, v: float) -> float:
        """Convert confidence from 0-1 to 0-100 format if needed."""
        if v is None:
            return 0.0
        # If value is <= 1.0, it's in 0-1 format, convert to percentage
        if v <= 1.0:
            return round(v * 100, 2)
        # Already in 0-100 format
        return round(v, 2)


class AgentInsightsSummarySchema(BaseModel):
    """Schema for agent insights summary."""

    agents_contributed: list[dict] = Field(default_factory=list, alias="agentsContributed")
    key_findings: list[str] = Field(default_factory=list, alias="keyFindings")

    model_config = ConfigDict(populate_by_name=True)


class AgentInsightsSchema(BaseModel):
    """Schema for consolidated agent insights from blue team agents."""

    market_intelligence: dict = Field(default_factory=dict, alias="marketIntelligence")
    capture_strategy: dict = Field(default_factory=dict, alias="captureStrategy")
    compliance_status: dict = Field(default_factory=dict, alias="complianceStatus")
    summary: AgentInsightsSummarySchema = Field(default_factory=AgentInsightsSummarySchema)

    model_config = ConfigDict(populate_by_name=True)


class DocumentResponse(BaseModel):
    """Schema for full document response."""

    document_id: str = Field(alias="documentId")
    content: Optional[DocumentContentSchema] = None
    confidence: Optional[ConfidenceReportSchema] = None
    red_team_report: Optional[RedTeamReportSchema] = Field(None, alias="redTeamReport")
    debate_log: list[DebateEntrySchema] = Field(default_factory=list, alias="debateLog")
    metrics: Optional[GenerationMetricsSchema] = None
    requires_human_review: bool = Field(default=False, alias="requiresHumanReview")
    agent_insights: Optional[AgentInsightsSchema] = Field(None, alias="agentInsights")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentListResponse(BaseModel):
    """Schema for list of documents."""

    documents: list[DocumentListItemSchema]
    total: int


class DocumentStatusUpdate(BaseModel):
    """Schema for updating document status (approve/reject)."""

    review_notes: Optional[str] = Field(None, alias="reviewNotes", max_length=2000)


class DocumentDuplicateRequest(BaseModel):
    """Schema for duplicating a document."""

    new_title: Optional[str] = Field(None, alias="newTitle", max_length=500)


# ============================================================================
# Generation Schemas
# ============================================================================


class EscalationThresholdsSchema(BaseModel):
    """Schema for escalation threshold configuration."""

    confidence_min: int = Field(default=70, alias="confidenceMin", ge=0, le=100)
    critical_unresolved: bool = Field(default=True, alias="criticalUnresolved")
    compliance_uncertainty: bool = Field(default=True, alias="complianceUncertainty")

    model_config = ConfigDict(populate_by_name=True)


class BlueTeamConfigSchema(BaseModel):
    """Schema for blue team agent configuration."""

    strategy_architect: bool = Field(default=True, alias="strategyArchitect")
    market_analyst: bool = Field(default=False, alias="marketAnalyst")
    compliance_navigator: bool = Field(default=True, alias="complianceNavigator")
    capture_strategist: bool = Field(default=False, alias="captureStrategist")

    model_config = ConfigDict(populate_by_name=True)


class RedTeamConfigSchema(BaseModel):
    """Schema for red team agent configuration."""

    devils_advocate: bool = Field(default=True, alias="devilsAdvocate")
    competitor_simulator: bool = Field(default=False, alias="competitorSimulator")
    evaluator_simulator: bool = Field(default=True, alias="evaluatorSimulator")
    risk_assessor: bool = Field(default=False, alias="riskAssessor")

    model_config = ConfigDict(populate_by_name=True)


class SwarmConfigSchema(BaseModel):
    """Schema for swarm configuration."""

    intensity: str = Field(default="medium", description="Debate intensity: light, medium, aggressive")
    rounds: int = Field(default=3, ge=1, le=10, description="Maximum adversarial rounds")
    consensus: str = Field(default="majority", description="Consensus mode: unanimous, majority, arbiter-decides")
    blue_team: BlueTeamConfigSchema = Field(default_factory=BlueTeamConfigSchema, alias="blueTeam")
    red_team: RedTeamConfigSchema = Field(default_factory=RedTeamConfigSchema, alias="redTeam")
    specialists: dict[str, bool] = Field(default_factory=dict)
    risk_tolerance: str = Field(default="balanced", alias="riskTolerance")
    escalation_thresholds: EscalationThresholdsSchema = Field(
        default_factory=EscalationThresholdsSchema, alias="escalationThresholds"
    )

    model_config = ConfigDict(populate_by_name=True)


class OpportunityContextSchema(BaseModel):
    """Schema for opportunity context in generation request."""

    solicitation_number: Optional[str] = Field(None, alias="solicitationNumber")
    target_agency: Optional[str] = Field(None, alias="targetAgency")
    known_competitors: list[str] = Field(default_factory=list, alias="knownCompetitors")
    budget_min: Optional[int] = Field(None, alias="budgetMin", ge=0)
    budget_max: Optional[int] = Field(None, alias="budgetMax", ge=0)
    due_date: Optional[str] = Field(None, alias="dueDate")

    model_config = ConfigDict(populate_by_name=True)


class DocumentGenerationRequest(BaseModel):
    """Schema for starting document generation."""

    document_type: str = Field(..., alias="documentType", description="Type of document to generate")
    company_profile_id: str = Field(..., alias="companyProfileId", description="ID of company profile to use")
    opportunity_context: Optional[OpportunityContextSchema] = Field(None, alias="opportunityContext")
    config: SwarmConfigSchema = Field(default_factory=SwarmConfigSchema)

    model_config = ConfigDict(populate_by_name=True)


class GenerationStartResponse(BaseModel):
    """Schema for generation start response."""

    request_id: str = Field(alias="requestId")
    status: str = Field(default="started")
    estimated_duration: int = Field(default=60000, alias="estimatedDuration", description="Estimated duration in ms")

    model_config = ConfigDict(populate_by_name=True)


class GenerationStatusResponse(BaseModel):
    """Schema for generation status response."""

    request_id: str = Field(alias="requestId")
    status: str = Field(description="Status: queued, running, complete, error, paused, cancelled")
    current_round: int = Field(default=0, alias="currentRound")
    total_rounds: int = Field(default=0, alias="totalRounds")
    current_phase: Optional[str] = Field(None, alias="currentPhase")
    document_id: Optional[str] = Field(None, alias="documentId")
    error_message: Optional[str] = Field(None, alias="errorMessage")
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Export Schemas
# ============================================================================


class ExportRequest(BaseModel):
    """Schema for document export request."""

    format: str = Field(
        ...,
        description="Export format: word, pdf, markdown",
        pattern="^(word|pdf|markdown)$",
    )


# ============================================================================
# Share Link Schemas
# ============================================================================


class ShareLinkCreateRequest(BaseModel):
    """Schema for creating a share link."""

    password: Optional[str] = Field(
        None,
        min_length=4,
        max_length=100,
        description="Optional password to protect the share link",
    )
    expires_in_days: Optional[int] = Field(
        None,
        alias="expiresInDays",
        ge=1,
        le=365,
        description="Number of days until the link expires (None = never)",
    )

    model_config = ConfigDict(populate_by_name=True)


class ShareLinkResponse(BaseModel):
    """Schema for share link response."""

    id: str
    document_id: str = Field(alias="documentId")
    token: str
    url: str = Field(description="Full shareable URL")
    has_password: bool = Field(alias="hasPassword")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ShareLinkListResponse(BaseModel):
    """Schema for list of share links."""

    share_links: list[ShareLinkResponse] = Field(alias="shareLinks")
    total: int

    model_config = ConfigDict(populate_by_name=True)


class ShareLinkAccessRequest(BaseModel):
    """Schema for accessing a shared document."""

    password: Optional[str] = Field(None, description="Password if required")
