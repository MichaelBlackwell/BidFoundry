"""
Output Structures

Contains data structures for final documents, reports, and
other outputs from the adversarial swarm.
"""

from .final_document import (
    FinalDocument,
    DocumentSection,
    DocumentMetadata,
    DocumentFormat,
    DocumentStatus,
)
from .red_team_report import (
    RedTeamReport,
    CritiqueRecord,
    ResponseRecord,
    ExchangeRecord,
    RoundSummary,
    ExchangeOutcome,
)
from .confidence_report import (
    ConfidenceReport,
    SectionReport,
    ReviewItem,
    ReviewPriority,
)

__all__ = [
    # Final Document
    "FinalDocument",
    "DocumentSection",
    "DocumentMetadata",
    "DocumentFormat",
    "DocumentStatus",
    # Red Team Report
    "RedTeamReport",
    "CritiqueRecord",
    "ResponseRecord",
    "ExchangeRecord",
    "RoundSummary",
    "ExchangeOutcome",
    # Confidence Report
    "ConfidenceReport",
    "SectionReport",
    "ReviewItem",
    "ReviewPriority",
]
