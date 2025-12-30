"""
Core Data Models for Adversarial Agentic Swarm

This package contains all shared data structures used across agents
for GovCon strategy document generation.
"""

from .company_profile import (
    CompanyProfile,
    NAICSCode,
    Certification,
    CertificationType,
    PastPerformance,
    PerformanceRating,
    TeamMember,
    CoreCapability,
)
from .opportunity import (
    Opportunity,
    Agency,
    SetAsideType,
    ContractType,
    EvaluationType,
    Competitor,
    CompetitorIntel,
)
from .document_types import (
    DocumentType,
    DocumentSection,
    DocumentMetadata,
)
from .critique import (
    Critique,
    ChallengeType,
    Severity,
)
from .response import (
    Response,
    Disposition,
)
from .confidence import (
    ConfidenceScore,
    SectionConfidence,
    ConfidenceThresholds,
)
from .market_data import (
    MarketData,
    BudgetInfo,
    BudgetTrend,
    ContractAward,
    ForecastOpportunity,
    ForecastConfidence,
    IncumbentPerformance,
    PerformanceRatingLevel,
    MarketOpportunityStatus,
    MarketAnalysis,
)

__all__ = [
    # Company Profile
    "CompanyProfile",
    "NAICSCode",
    "Certification",
    "CertificationType",
    "PastPerformance",
    "PerformanceRating",
    "TeamMember",
    "CoreCapability",
    # Opportunity
    "Opportunity",
    "Agency",
    "SetAsideType",
    "ContractType",
    "EvaluationType",
    "Competitor",
    "CompetitorIntel",
    # Document Types
    "DocumentType",
    "DocumentSection",
    "DocumentMetadata",
    # Critique
    "Critique",
    "ChallengeType",
    "Severity",
    # Response
    "Response",
    "Disposition",
    # Confidence
    "ConfidenceScore",
    "SectionConfidence",
    "ConfidenceThresholds",
    # Market Data
    "MarketData",
    "BudgetInfo",
    "BudgetTrend",
    "ContractAward",
    "ForecastOpportunity",
    "ForecastConfidence",
    "IncumbentPerformance",
    "PerformanceRatingLevel",
    "MarketOpportunityStatus",
    "MarketAnalysis",
]
