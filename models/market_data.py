"""
Market Data Models

Defines data structures for government market intelligence,
including agency budgets, contract awards, forecasts, and
incumbent performance data used by the Market Analyst agent.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional, Dict
import json
import uuid


class BudgetTrend(str, Enum):
    """Agency budget trend indicators."""

    INCREASING = "Increasing"
    STABLE = "Stable"
    DECREASING = "Decreasing"
    UNCERTAIN = "Uncertain"


class ForecastConfidence(str, Enum):
    """Confidence level for forecasted opportunities."""

    HIGH = "High"  # Published in agency forecast
    MEDIUM = "Medium"  # Rumored or expected based on patterns
    LOW = "Low"  # Speculative


class PerformanceRatingLevel(str, Enum):
    """CPARS performance rating levels."""

    EXCEPTIONAL = "Exceptional"
    VERY_GOOD = "Very Good"
    SATISFACTORY = "Satisfactory"
    MARGINAL = "Marginal"
    UNSATISFACTORY = "Unsatisfactory"


class MarketOpportunityStatus(str, Enum):
    """Status of opportunities in the market pipeline."""

    FORECASTED = "Forecasted"
    PRE_SOLICITATION = "Pre-Solicitation"
    ACTIVE = "Active"
    AWARDED = "Awarded"


@dataclass
class BudgetInfo:
    """
    Agency budget information for market analysis.

    Tracks budget levels and trends for specific agencies
    or programs to support market sizing and timing decisions.
    """

    agency: str
    sub_agency: Optional[str] = None
    fiscal_year: int = 0
    total_budget: float = 0.0  # In millions
    discretionary_budget: Optional[float] = None
    contracting_budget: Optional[float] = None

    # Trends
    budget_trend: BudgetTrend = BudgetTrend.STABLE
    yoy_change_percent: Optional[float] = None  # Year-over-year change

    # Focus areas
    priority_areas: List[str] = field(default_factory=list)
    budget_highlights: List[str] = field(default_factory=list)

    # Source
    source: Optional[str] = None  # e.g., "FY2025 President's Budget"
    last_updated: Optional[date] = None

    def to_dict(self) -> dict:
        return {
            "agency": self.agency,
            "sub_agency": self.sub_agency,
            "fiscal_year": self.fiscal_year,
            "total_budget": self.total_budget,
            "discretionary_budget": self.discretionary_budget,
            "contracting_budget": self.contracting_budget,
            "budget_trend": self.budget_trend.value,
            "yoy_change_percent": self.yoy_change_percent,
            "priority_areas": self.priority_areas,
            "budget_highlights": self.budget_highlights,
            "source": self.source,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BudgetInfo":
        return cls(
            agency=data.get("agency", ""),
            sub_agency=data.get("sub_agency"),
            fiscal_year=data.get("fiscal_year", 0),
            total_budget=data.get("total_budget", 0.0),
            discretionary_budget=data.get("discretionary_budget"),
            contracting_budget=data.get("contracting_budget"),
            budget_trend=BudgetTrend(data.get("budget_trend", "Stable")),
            yoy_change_percent=data.get("yoy_change_percent"),
            priority_areas=data.get("priority_areas", []),
            budget_highlights=data.get("budget_highlights", []),
            source=data.get("source"),
            last_updated=date.fromisoformat(data["last_updated"]) if data.get("last_updated") else None,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "BudgetInfo":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ContractAward:
    """
    Recent contract award data from FPDS or USASpending.

    Used for competitive intelligence and market pattern analysis.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    contract_number: str = ""
    title: str = ""

    # Award details
    award_date: Optional[date] = None
    award_amount: float = 0.0
    ceiling_amount: Optional[float] = None
    contract_type: str = ""  # FFP, T&M, etc.

    # Agency
    agency: str = ""
    sub_agency: Optional[str] = None
    contracting_office: Optional[str] = None

    # Awardee
    awardee_name: str = ""
    awardee_uei: Optional[str] = None
    awardee_cage: Optional[str] = None

    # Classification
    naics_code: str = ""
    psc_code: Optional[str] = None
    set_aside: Optional[str] = None  # Small Business, 8(a), etc.

    # Context
    is_incumbent: bool = False
    is_recompete: bool = False
    previous_contract: Optional[str] = None

    # Performance info (if available)
    period_of_performance: Optional[str] = None
    place_of_performance: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "contract_number": self.contract_number,
            "title": self.title,
            "award_date": self.award_date.isoformat() if self.award_date else None,
            "award_amount": self.award_amount,
            "ceiling_amount": self.ceiling_amount,
            "contract_type": self.contract_type,
            "agency": self.agency,
            "sub_agency": self.sub_agency,
            "contracting_office": self.contracting_office,
            "awardee_name": self.awardee_name,
            "awardee_uei": self.awardee_uei,
            "awardee_cage": self.awardee_cage,
            "naics_code": self.naics_code,
            "psc_code": self.psc_code,
            "set_aside": self.set_aside,
            "is_incumbent": self.is_incumbent,
            "is_recompete": self.is_recompete,
            "previous_contract": self.previous_contract,
            "period_of_performance": self.period_of_performance,
            "place_of_performance": self.place_of_performance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContractAward":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            contract_number=data.get("contract_number", ""),
            title=data.get("title", ""),
            award_date=date.fromisoformat(data["award_date"]) if data.get("award_date") else None,
            award_amount=data.get("award_amount", 0.0),
            ceiling_amount=data.get("ceiling_amount"),
            contract_type=data.get("contract_type", ""),
            agency=data.get("agency", ""),
            sub_agency=data.get("sub_agency"),
            contracting_office=data.get("contracting_office"),
            awardee_name=data.get("awardee_name", ""),
            awardee_uei=data.get("awardee_uei"),
            awardee_cage=data.get("awardee_cage"),
            naics_code=data.get("naics_code", ""),
            psc_code=data.get("psc_code"),
            set_aside=data.get("set_aside"),
            is_incumbent=data.get("is_incumbent", False),
            is_recompete=data.get("is_recompete", False),
            previous_contract=data.get("previous_contract"),
            period_of_performance=data.get("period_of_performance"),
            place_of_performance=data.get("place_of_performance"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ContractAward":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ForecastOpportunity:
    """
    Forecasted opportunity from agency procurement forecasts.

    Represents upcoming opportunities identified through agency
    forecasts, SAM.gov, or market intelligence.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""

    # Agency
    agency: str = ""
    sub_agency: Optional[str] = None
    contracting_office: Optional[str] = None

    # Timing
    estimated_solicitation_date: Optional[date] = None
    estimated_award_date: Optional[date] = None
    fiscal_quarter: Optional[str] = None  # e.g., "FY25 Q2"

    # Value
    estimated_value: Optional[float] = None
    value_range_low: Optional[float] = None
    value_range_high: Optional[float] = None

    # Classification
    naics_code: Optional[str] = None
    psc_code: Optional[str] = None
    set_aside: Optional[str] = None
    contract_type: Optional[str] = None

    # Context
    is_recompete: bool = False
    incumbent: Optional[str] = None
    current_contract_number: Optional[str] = None
    current_contract_end: Optional[date] = None

    # Status and confidence
    status: MarketOpportunityStatus = MarketOpportunityStatus.FORECASTED
    confidence: ForecastConfidence = ForecastConfidence.MEDIUM

    # Source
    source: Optional[str] = None  # e.g., "DoD Procurement Forecast FY25"
    last_updated: Optional[date] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "agency": self.agency,
            "sub_agency": self.sub_agency,
            "contracting_office": self.contracting_office,
            "estimated_solicitation_date": self.estimated_solicitation_date.isoformat() if self.estimated_solicitation_date else None,
            "estimated_award_date": self.estimated_award_date.isoformat() if self.estimated_award_date else None,
            "fiscal_quarter": self.fiscal_quarter,
            "estimated_value": self.estimated_value,
            "value_range_low": self.value_range_low,
            "value_range_high": self.value_range_high,
            "naics_code": self.naics_code,
            "psc_code": self.psc_code,
            "set_aside": self.set_aside,
            "contract_type": self.contract_type,
            "is_recompete": self.is_recompete,
            "incumbent": self.incumbent,
            "current_contract_number": self.current_contract_number,
            "current_contract_end": self.current_contract_end.isoformat() if self.current_contract_end else None,
            "status": self.status.value,
            "confidence": self.confidence.value,
            "source": self.source,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastOpportunity":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            agency=data.get("agency", ""),
            sub_agency=data.get("sub_agency"),
            contracting_office=data.get("contracting_office"),
            estimated_solicitation_date=date.fromisoformat(data["estimated_solicitation_date"]) if data.get("estimated_solicitation_date") else None,
            estimated_award_date=date.fromisoformat(data["estimated_award_date"]) if data.get("estimated_award_date") else None,
            fiscal_quarter=data.get("fiscal_quarter"),
            estimated_value=data.get("estimated_value"),
            value_range_low=data.get("value_range_low"),
            value_range_high=data.get("value_range_high"),
            naics_code=data.get("naics_code"),
            psc_code=data.get("psc_code"),
            set_aside=data.get("set_aside"),
            contract_type=data.get("contract_type"),
            is_recompete=data.get("is_recompete", False),
            incumbent=data.get("incumbent"),
            current_contract_number=data.get("current_contract_number"),
            current_contract_end=date.fromisoformat(data["current_contract_end"]) if data.get("current_contract_end") else None,
            status=MarketOpportunityStatus(data.get("status", "Forecasted")),
            confidence=ForecastConfidence(data.get("confidence", "Medium")),
            source=data.get("source"),
            last_updated=date.fromisoformat(data["last_updated"]) if data.get("last_updated") else None,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ForecastOpportunity":
        return cls.from_dict(json.loads(json_str))


@dataclass
class IncumbentPerformance:
    """
    Performance data for incumbent contractors.

    Aggregates performance information to assess incumbent strength
    and likelihood of successful recompete.
    """

    contractor_name: str = ""
    contractor_uei: Optional[str] = None

    # Contract being assessed
    contract_number: Optional[str] = None
    agency: str = ""

    # Performance ratings (from CPARS or other sources)
    overall_rating: Optional[PerformanceRatingLevel] = None
    quality_rating: Optional[PerformanceRatingLevel] = None
    schedule_rating: Optional[PerformanceRatingLevel] = None
    cost_control_rating: Optional[PerformanceRatingLevel] = None
    management_rating: Optional[PerformanceRatingLevel] = None

    # Performance indicators
    contract_modifications: int = 0
    option_years_exercised: int = 0
    total_option_years: int = 0
    has_stop_work_orders: bool = False
    has_cure_notices: bool = False
    has_show_cause_notices: bool = False

    # Relationship strength
    years_with_agency: int = 0
    other_contracts_with_agency: int = 0
    relationship_strength: str = "Unknown"  # Strong, Moderate, Weak

    # Assessment
    recompete_likelihood: str = "Unknown"  # High, Medium, Low
    vulnerabilities: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "contractor_name": self.contractor_name,
            "contractor_uei": self.contractor_uei,
            "contract_number": self.contract_number,
            "agency": self.agency,
            "overall_rating": self.overall_rating.value if self.overall_rating else None,
            "quality_rating": self.quality_rating.value if self.quality_rating else None,
            "schedule_rating": self.schedule_rating.value if self.schedule_rating else None,
            "cost_control_rating": self.cost_control_rating.value if self.cost_control_rating else None,
            "management_rating": self.management_rating.value if self.management_rating else None,
            "contract_modifications": self.contract_modifications,
            "option_years_exercised": self.option_years_exercised,
            "total_option_years": self.total_option_years,
            "has_stop_work_orders": self.has_stop_work_orders,
            "has_cure_notices": self.has_cure_notices,
            "has_show_cause_notices": self.has_show_cause_notices,
            "years_with_agency": self.years_with_agency,
            "other_contracts_with_agency": self.other_contracts_with_agency,
            "relationship_strength": self.relationship_strength,
            "recompete_likelihood": self.recompete_likelihood,
            "vulnerabilities": self.vulnerabilities,
            "strengths": self.strengths,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IncumbentPerformance":
        def parse_rating(val):
            return PerformanceRatingLevel(val) if val else None

        return cls(
            contractor_name=data.get("contractor_name", ""),
            contractor_uei=data.get("contractor_uei"),
            contract_number=data.get("contract_number"),
            agency=data.get("agency", ""),
            overall_rating=parse_rating(data.get("overall_rating")),
            quality_rating=parse_rating(data.get("quality_rating")),
            schedule_rating=parse_rating(data.get("schedule_rating")),
            cost_control_rating=parse_rating(data.get("cost_control_rating")),
            management_rating=parse_rating(data.get("management_rating")),
            contract_modifications=data.get("contract_modifications", 0),
            option_years_exercised=data.get("option_years_exercised", 0),
            total_option_years=data.get("total_option_years", 0),
            has_stop_work_orders=data.get("has_stop_work_orders", False),
            has_cure_notices=data.get("has_cure_notices", False),
            has_show_cause_notices=data.get("has_show_cause_notices", False),
            years_with_agency=data.get("years_with_agency", 0),
            other_contracts_with_agency=data.get("other_contracts_with_agency", 0),
            relationship_strength=data.get("relationship_strength", "Unknown"),
            recompete_likelihood=data.get("recompete_likelihood", "Unknown"),
            vulnerabilities=data.get("vulnerabilities", []),
            strengths=data.get("strengths", []),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "IncumbentPerformance":
        return cls.from_dict(json.loads(json_str))


@dataclass
class MarketData:
    """
    Aggregated market data for the Market Analyst agent.

    Contains all market intelligence inputs for analysis,
    including agency budgets, recent awards, forecasts,
    and incumbent performance data.
    """

    # Budget information by agency
    agency_budgets: Dict[str, BudgetInfo] = field(default_factory=dict)

    # Recent contract awards for pattern analysis
    recent_awards: List[ContractAward] = field(default_factory=list)

    # Forecasted opportunities
    forecast_opportunities: List[ForecastOpportunity] = field(default_factory=list)

    # Incumbent performance data
    incumbent_performance: Dict[str, IncumbentPerformance] = field(default_factory=dict)

    # Market summary statistics
    total_addressable_market: Optional[float] = None  # In millions
    target_market_size: Optional[float] = None
    market_growth_rate: Optional[float] = None  # Percentage

    # Data freshness
    data_as_of: Optional[date] = None
    sources: List[str] = field(default_factory=list)

    def get_budget_for_agency(self, agency: str) -> Optional[BudgetInfo]:
        """Get budget info for a specific agency."""
        return self.agency_budgets.get(agency)

    def get_awards_by_naics(self, naics_code: str) -> List[ContractAward]:
        """Filter awards by NAICS code."""
        return [a for a in self.recent_awards if a.naics_code == naics_code]

    def get_awards_by_agency(self, agency: str) -> List[ContractAward]:
        """Filter awards by agency."""
        return [a for a in self.recent_awards if agency.lower() in a.agency.lower()]

    def get_forecasts_by_naics(self, naics_code: str) -> List[ForecastOpportunity]:
        """Filter forecasts by NAICS code."""
        return [f for f in self.forecast_opportunities if f.naics_code == naics_code]

    def get_forecasts_by_agency(self, agency: str) -> List[ForecastOpportunity]:
        """Filter forecasts by agency."""
        return [f for f in self.forecast_opportunities if agency.lower() in f.agency.lower()]

    def get_upcoming_forecasts(self, days: int = 180) -> List[ForecastOpportunity]:
        """Get forecasts with estimated solicitation within the specified days."""
        from datetime import timedelta

        cutoff = date.today() + timedelta(days=days)
        return [
            f for f in self.forecast_opportunities
            if f.estimated_solicitation_date and f.estimated_solicitation_date <= cutoff
        ]

    def get_incumbent_performance(self, contractor: str) -> Optional[IncumbentPerformance]:
        """Get performance data for a specific incumbent."""
        return self.incumbent_performance.get(contractor)

    def to_dict(self) -> dict:
        return {
            "agency_budgets": {k: v.to_dict() for k, v in self.agency_budgets.items()},
            "recent_awards": [a.to_dict() for a in self.recent_awards],
            "forecast_opportunities": [f.to_dict() for f in self.forecast_opportunities],
            "incumbent_performance": {k: v.to_dict() for k, v in self.incumbent_performance.items()},
            "total_addressable_market": self.total_addressable_market,
            "target_market_size": self.target_market_size,
            "market_growth_rate": self.market_growth_rate,
            "data_as_of": self.data_as_of.isoformat() if self.data_as_of else None,
            "sources": self.sources,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarketData":
        return cls(
            agency_budgets={k: BudgetInfo.from_dict(v) for k, v in data.get("agency_budgets", {}).items()},
            recent_awards=[ContractAward.from_dict(a) for a in data.get("recent_awards", [])],
            forecast_opportunities=[ForecastOpportunity.from_dict(f) for f in data.get("forecast_opportunities", [])],
            incumbent_performance={k: IncumbentPerformance.from_dict(v) for k, v in data.get("incumbent_performance", {}).items()},
            total_addressable_market=data.get("total_addressable_market"),
            target_market_size=data.get("target_market_size"),
            market_growth_rate=data.get("market_growth_rate"),
            data_as_of=date.fromisoformat(data["data_as_of"]) if data.get("data_as_of") else None,
            sources=data.get("sources", []),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "MarketData":
        return cls.from_dict(json.loads(json_str))


@dataclass
class MarketAnalysis:
    """
    Output structure for Market Analyst agent's analysis.

    Contains the synthesized market intelligence and recommendations
    produced by the Market Analyst agent.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Market sizing
    total_addressable_market: Optional[float] = None
    serviceable_addressable_market: Optional[float] = None
    target_market: Optional[float] = None
    market_sizing_assumptions: List[str] = field(default_factory=list)

    # Opportunity rankings
    ranked_opportunities: List[Dict] = field(default_factory=list)  # Top opportunities with rationale
    opportunity_count: int = 0

    # Competitive landscape
    competitive_density: str = "Unknown"  # Low, Medium, High
    incumbent_strength_assessment: str = ""
    market_barriers: List[str] = field(default_factory=list)
    market_enablers: List[str] = field(default_factory=list)

    # Timing recommendations
    timing_recommendations: List[str] = field(default_factory=list)
    fiscal_year_considerations: List[str] = field(default_factory=list)
    recompete_windows: List[Dict] = field(default_factory=list)

    # Trends
    market_trends: List[str] = field(default_factory=list)
    budget_outlook: str = ""
    technology_shifts: List[str] = field(default_factory=list)

    # Agency-specific insights
    agency_insights: Dict[str, str] = field(default_factory=dict)

    # Confidence
    analysis_confidence: str = "Medium"  # Low, Medium, High
    data_limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "total_addressable_market": self.total_addressable_market,
            "serviceable_addressable_market": self.serviceable_addressable_market,
            "target_market": self.target_market,
            "market_sizing_assumptions": self.market_sizing_assumptions,
            "ranked_opportunities": self.ranked_opportunities,
            "opportunity_count": self.opportunity_count,
            "competitive_density": self.competitive_density,
            "incumbent_strength_assessment": self.incumbent_strength_assessment,
            "market_barriers": self.market_barriers,
            "market_enablers": self.market_enablers,
            "timing_recommendations": self.timing_recommendations,
            "fiscal_year_considerations": self.fiscal_year_considerations,
            "recompete_windows": self.recompete_windows,
            "market_trends": self.market_trends,
            "budget_outlook": self.budget_outlook,
            "technology_shifts": self.technology_shifts,
            "agency_insights": self.agency_insights,
            "analysis_confidence": self.analysis_confidence,
            "data_limitations": self.data_limitations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarketAnalysis":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "MarketAnalysis":
        return cls.from_dict(json.loads(json_str))
