"""
Opportunity Model

Defines the structure for capturing federal contracting opportunities,
including solicitation details, agency information, and competitor intelligence.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict
import json
import uuid


class SetAsideType(str, Enum):
    """Federal set-aside types for small business programs."""

    FULL_AND_OPEN = "Full and Open"
    SMALL_BUSINESS = "Small Business Set-Aside"
    SBA_8A = "8(a)"
    HUBZONE = "HUBZone"
    SDVOSB = "SDVOSB"
    VOSB = "VOSB"
    WOSB = "WOSB"
    EDWOSB = "EDWOSB"
    SOLE_SOURCE = "Sole Source"
    COMPETITIVE_8A = "Competitive 8(a)"


class ContractType(str, Enum):
    """Federal contract types."""

    FFP = "Firm Fixed Price"
    FPIF = "Fixed Price Incentive Firm"
    CPFF = "Cost Plus Fixed Fee"
    CPAF = "Cost Plus Award Fee"
    CPIF = "Cost Plus Incentive Fee"
    TM = "Time and Materials"
    LH = "Labor Hour"
    IDIQ = "Indefinite Delivery/Indefinite Quantity"
    BPA = "Blanket Purchase Agreement"


class EvaluationType(str, Enum):
    """Evaluation methodology types."""

    LPTA = "Lowest Price Technically Acceptable"
    BEST_VALUE = "Best Value Tradeoff"
    HIGHEST_RATED = "Highest Technically Rated with Fair and Reasonable Price"


class OpportunityStatus(str, Enum):
    """Opportunity lifecycle status."""

    FORECASTED = "Forecasted"
    PRESOLICITATION = "Pre-Solicitation"
    SOURCES_SOUGHT = "Sources Sought"
    RFI = "RFI"
    DRAFT_RFP = "Draft RFP"
    FINAL_RFP = "Final RFP"
    PROPOSAL_DUE = "Proposal Due"
    UNDER_EVALUATION = "Under Evaluation"
    AWARDED = "Awarded"
    CANCELLED = "Cancelled"


class OpportunityPriority(str, Enum):
    """Opportunity pursuit priority."""

    MUST_WIN = "Must Win"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    WATCHING = "Watching"


@dataclass
class Agency:
    """Federal agency information."""

    name: str
    abbreviation: str
    sub_agency: Optional[str] = None
    contracting_office: Optional[str] = None
    mission_areas: List[str] = field(default_factory=list)
    budget_trends: Optional[str] = None  # Increasing, Stable, Decreasing
    procurement_forecast_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "abbreviation": self.abbreviation,
            "sub_agency": self.sub_agency,
            "contracting_office": self.contracting_office,
            "mission_areas": self.mission_areas,
            "budget_trends": self.budget_trends,
            "procurement_forecast_url": self.procurement_forecast_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agency":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Agency":
        return cls.from_dict(json.loads(json_str))


@dataclass
class EvaluationFactor:
    """Evaluation factor with weight and subfactors."""

    name: str
    weight: Optional[float] = None  # Percentage or relative weight
    relative_importance: Optional[str] = None  # e.g., "More important than cost"
    subfactors: List[str] = field(default_factory=list)
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "weight": self.weight,
            "relative_importance": self.relative_importance,
            "subfactors": self.subfactors,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationFactor":
        return cls(**data)


@dataclass
class Competitor:
    """Known or suspected competitor information."""

    name: str
    duns_number: Optional[str] = None
    uei_number: Optional[str] = None
    is_incumbent: bool = False
    is_confirmed: bool = False  # Confirmed vs suspected
    estimated_strength: str = "Unknown"  # Strong, Moderate, Weak, Unknown

    # Competitive intelligence
    known_strengths: List[str] = field(default_factory=list)
    known_weaknesses: List[str] = field(default_factory=list)
    relevant_past_performance: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    likely_strategy: Optional[str] = None
    teaming_partners: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duns_number": self.duns_number,
            "uei_number": self.uei_number,
            "is_incumbent": self.is_incumbent,
            "is_confirmed": self.is_confirmed,
            "estimated_strength": self.estimated_strength,
            "known_strengths": self.known_strengths,
            "known_weaknesses": self.known_weaknesses,
            "relevant_past_performance": self.relevant_past_performance,
            "certifications": self.certifications,
            "likely_strategy": self.likely_strategy,
            "teaming_partners": self.teaming_partners,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Competitor":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Competitor":
        return cls.from_dict(json.loads(json_str))


@dataclass
class CompetitorIntel:
    """Aggregated competitive intelligence for an opportunity."""

    competitors: List[Competitor] = field(default_factory=list)
    competitive_density: str = "Unknown"  # Low (<5), Medium (5-10), High (>10)
    incumbent_advantage_level: str = "Unknown"  # Strong, Moderate, Weak, None
    market_assessment: Optional[str] = None

    @property
    def confirmed_competitors(self) -> List[Competitor]:
        return [c for c in self.competitors if c.is_confirmed]

    @property
    def incumbent(self) -> Optional[Competitor]:
        incumbents = [c for c in self.competitors if c.is_incumbent]
        return incumbents[0] if incumbents else None

    def to_dict(self) -> dict:
        return {
            "competitors": [c.to_dict() for c in self.competitors],
            "competitive_density": self.competitive_density,
            "incumbent_advantage_level": self.incumbent_advantage_level,
            "market_assessment": self.market_assessment,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompetitorIntel":
        return cls(
            competitors=[Competitor.from_dict(c) for c in data.get("competitors", [])],
            competitive_density=data.get("competitive_density", "Unknown"),
            incumbent_advantage_level=data.get("incumbent_advantage_level", "Unknown"),
            market_assessment=data.get("market_assessment"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CompetitorIntel":
        return cls.from_dict(json.loads(json_str))


@dataclass
class Opportunity:
    """
    Federal contracting opportunity.

    This is the primary input for opportunity-specific strategy generation,
    including proposal strategy, capture plans, and competitive analysis.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Identification
    title: str = ""
    solicitation_number: Optional[str] = None
    sam_gov_id: Optional[str] = None
    notice_id: Optional[str] = None

    # Agency
    agency: Optional[Agency] = None

    # Status and Timing
    status: OpportunityStatus = OpportunityStatus.FORECASTED
    priority: OpportunityPriority = OpportunityPriority.WATCHING
    posted_date: Optional[date] = None
    response_deadline: Optional[datetime] = None
    estimated_award_date: Optional[date] = None
    period_of_performance: Optional[str] = None  # e.g., "1 Base + 4 Option Years"

    # Value
    estimated_value: Optional[float] = None
    value_ceiling: Optional[float] = None
    value_floor: Optional[float] = None

    # Contract Structure
    set_aside: SetAsideType = SetAsideType.FULL_AND_OPEN
    contract_type: Optional[ContractType] = None
    naics_code: Optional[str] = None
    psc_code: Optional[str] = None  # Product Service Code
    place_of_performance: Optional[str] = None

    # Evaluation
    evaluation_type: Optional[EvaluationType] = None
    evaluation_factors: List[EvaluationFactor] = field(default_factory=list)

    # Requirements
    scope_summary: str = ""
    key_requirements: List[str] = field(default_factory=list)
    mandatory_qualifications: List[str] = field(default_factory=list)
    desired_qualifications: List[str] = field(default_factory=list)
    clearance_requirements: Optional[str] = None

    # Competitive Intelligence
    competitor_intel: Optional[CompetitorIntel] = None
    incumbent_contract_number: Optional[str] = None
    is_recompete: bool = False

    # Capture Information
    capture_manager: Optional[str] = None
    proposal_manager: Optional[str] = None
    go_no_go_decision: Optional[str] = None  # Go, No-Go, Pending
    go_no_go_date: Optional[date] = None
    notes: str = ""

    # Source Documents
    solicitation_url: Optional[str] = None
    attachments: List[str] = field(default_factory=list)

    @property
    def is_small_business_setaside(self) -> bool:
        """Check if this is a small business set-aside."""
        sb_setasides = {
            SetAsideType.SMALL_BUSINESS,
            SetAsideType.SBA_8A,
            SetAsideType.HUBZONE,
            SetAsideType.SDVOSB,
            SetAsideType.VOSB,
            SetAsideType.WOSB,
            SetAsideType.EDWOSB,
            SetAsideType.COMPETITIVE_8A,
        }
        return self.set_aside in sb_setasides

    @property
    def days_until_deadline(self) -> Optional[int]:
        """Calculate days remaining until response deadline."""
        if self.response_deadline is None:
            return None
        delta = self.response_deadline.date() - date.today()
        return delta.days

    @property
    def is_active(self) -> bool:
        """Check if opportunity is actively pursuable."""
        active_statuses = {
            OpportunityStatus.PRESOLICITATION,
            OpportunityStatus.SOURCES_SOUGHT,
            OpportunityStatus.RFI,
            OpportunityStatus.DRAFT_RFP,
            OpportunityStatus.FINAL_RFP,
            OpportunityStatus.PROPOSAL_DUE,
        }
        return self.status in active_statuses

    def get_primary_evaluation_factors(self) -> List[EvaluationFactor]:
        """Get evaluation factors, sorted by weight if available."""
        factors = self.evaluation_factors.copy()
        factors.sort(key=lambda f: f.weight or 0, reverse=True)
        return factors

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "solicitation_number": self.solicitation_number,
            "sam_gov_id": self.sam_gov_id,
            "notice_id": self.notice_id,
            "agency": self.agency.to_dict() if self.agency else None,
            "status": self.status.value,
            "priority": self.priority.value,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "response_deadline": self.response_deadline.isoformat() if self.response_deadline else None,
            "estimated_award_date": self.estimated_award_date.isoformat() if self.estimated_award_date else None,
            "period_of_performance": self.period_of_performance,
            "estimated_value": self.estimated_value,
            "value_ceiling": self.value_ceiling,
            "value_floor": self.value_floor,
            "set_aside": self.set_aside.value,
            "contract_type": self.contract_type.value if self.contract_type else None,
            "naics_code": self.naics_code,
            "psc_code": self.psc_code,
            "place_of_performance": self.place_of_performance,
            "evaluation_type": self.evaluation_type.value if self.evaluation_type else None,
            "evaluation_factors": [ef.to_dict() for ef in self.evaluation_factors],
            "scope_summary": self.scope_summary,
            "key_requirements": self.key_requirements,
            "mandatory_qualifications": self.mandatory_qualifications,
            "desired_qualifications": self.desired_qualifications,
            "clearance_requirements": self.clearance_requirements,
            "competitor_intel": self.competitor_intel.to_dict() if self.competitor_intel else None,
            "incumbent_contract_number": self.incumbent_contract_number,
            "is_recompete": self.is_recompete,
            "capture_manager": self.capture_manager,
            "proposal_manager": self.proposal_manager,
            "go_no_go_decision": self.go_no_go_decision,
            "go_no_go_date": self.go_no_go_date.isoformat() if self.go_no_go_date else None,
            "notes": self.notes,
            "solicitation_url": self.solicitation_url,
            "attachments": self.attachments,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Opportunity":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            solicitation_number=data.get("solicitation_number"),
            sam_gov_id=data.get("sam_gov_id"),
            notice_id=data.get("notice_id"),
            agency=Agency.from_dict(data["agency"]) if data.get("agency") else None,
            status=OpportunityStatus(data.get("status", "Forecasted")),
            priority=OpportunityPriority(data.get("priority", "Watching")),
            posted_date=date.fromisoformat(data["posted_date"]) if data.get("posted_date") else None,
            response_deadline=datetime.fromisoformat(data["response_deadline"]) if data.get("response_deadline") else None,
            estimated_award_date=date.fromisoformat(data["estimated_award_date"]) if data.get("estimated_award_date") else None,
            period_of_performance=data.get("period_of_performance"),
            estimated_value=data.get("estimated_value"),
            value_ceiling=data.get("value_ceiling"),
            value_floor=data.get("value_floor"),
            set_aside=SetAsideType(data.get("set_aside", "Full and Open")),
            contract_type=ContractType(data["contract_type"]) if data.get("contract_type") else None,
            naics_code=data.get("naics_code"),
            psc_code=data.get("psc_code"),
            place_of_performance=data.get("place_of_performance"),
            evaluation_type=EvaluationType(data["evaluation_type"]) if data.get("evaluation_type") else None,
            evaluation_factors=[EvaluationFactor.from_dict(ef) for ef in data.get("evaluation_factors", [])],
            scope_summary=data.get("scope_summary", ""),
            key_requirements=data.get("key_requirements", []),
            mandatory_qualifications=data.get("mandatory_qualifications", []),
            desired_qualifications=data.get("desired_qualifications", []),
            clearance_requirements=data.get("clearance_requirements"),
            competitor_intel=CompetitorIntel.from_dict(data["competitor_intel"]) if data.get("competitor_intel") else None,
            incumbent_contract_number=data.get("incumbent_contract_number"),
            is_recompete=data.get("is_recompete", False),
            capture_manager=data.get("capture_manager"),
            proposal_manager=data.get("proposal_manager"),
            go_no_go_decision=data.get("go_no_go_decision"),
            go_no_go_date=date.fromisoformat(data["go_no_go_date"]) if data.get("go_no_go_date") else None,
            notes=data.get("notes", ""),
            solicitation_url=data.get("solicitation_url"),
            attachments=data.get("attachments", []),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Opportunity":
        return cls.from_dict(json.loads(json_str))
