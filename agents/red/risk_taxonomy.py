"""
Risk Taxonomy for GovCon

Defines risk categories, probability levels, and impact scales specific to
Government Contracting (GovCon) capture and proposal strategy.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, ClassVar, Set
import json
import uuid

from agents.utils import DataclassMixin


class RiskCategory(str, Enum):
    """Categories of risks in GovCon strategy and capture."""

    # Execution Risks
    EXECUTION = "Execution"  # Ability to deliver on promises
    STAFFING = "Staffing"  # Personnel availability and qualification
    TECHNICAL = "Technical"  # Technical feasibility and approach
    SCHEDULE = "Schedule"  # Timeline and milestone risks
    TRANSITION = "Transition"  # Transition/phase-in risks

    # Compliance Risks
    COMPLIANCE = "Compliance"  # FAR/DFAR regulatory compliance
    ELIGIBILITY = "Eligibility"  # Set-aside and certification eligibility
    OCI = "OCI"  # Organizational Conflict of Interest
    SECURITY = "Security"  # Clearance and security requirements

    # Competitive Risks
    COMPETITIVE = "Competitive"  # Competitive positioning risks
    INCUMBENT = "Incumbent"  # Incumbent advantage/relationship
    PRICING = "Pricing"  # Price-to-win and affordability
    TEAMING = "Teaming"  # Teaming arrangement risks

    # Financial Risks
    FINANCIAL = "Financial"  # Cost estimation and financial capacity
    CASH_FLOW = "Cash Flow"  # Cash flow and funding risks
    PROFITABILITY = "Profitability"  # Margin and profitability risks

    # External Risks
    POLITICAL = "Political"  # Political and budgetary environment
    PROTEST = "Protest"  # Bid protest risks
    RECOMPETE = "Recompete"  # Recompete timing and incumbency
    MARKET = "Market"  # Market condition changes

    # Strategic Risks
    STRATEGIC = "Strategic"  # Alignment with company strategy
    REPUTATION = "Reputation"  # Brand and reputation risks
    OPPORTUNITY_COST = "Opportunity Cost"  # Resource allocation trade-offs


class Probability(str, Enum):
    """Probability levels for risk occurrence."""

    RARE = "Rare"  # < 10% chance
    LOW = "Low"  # 10-30% chance
    MEDIUM = "Medium"  # 30-60% chance
    HIGH = "High"  # 60-90% chance
    ALMOST_CERTAIN = "Almost Certain"  # > 90% chance

    @property
    def numeric_value(self) -> float:
        """Get numeric probability for calculations."""
        mapping = {
            "Rare": 0.05,
            "Low": 0.20,
            "Medium": 0.45,
            "High": 0.75,
            "Almost Certain": 0.95,
        }
        return mapping.get(self.value, 0.5)


class Impact(str, Enum):
    """Impact levels for risk consequences."""

    NEGLIGIBLE = "Negligible"  # Minimal impact on outcomes
    LOW = "Low"  # Minor impact, easily recoverable
    MEDIUM = "Medium"  # Moderate impact, requires mitigation
    HIGH = "High"  # Significant impact on win probability or execution
    CATASTROPHIC = "Catastrophic"  # Could cause proposal rejection or contract failure

    @property
    def numeric_value(self) -> float:
        """Get numeric impact for calculations."""
        mapping = {
            "Negligible": 0.1,
            "Low": 0.3,
            "Medium": 0.5,
            "High": 0.7,
            "Catastrophic": 0.9,
        }
        return mapping.get(self.value, 0.5)


class MitigationStatus(str, Enum):
    """Status of risk mitigation efforts."""

    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    IMPLEMENTED = "Implemented"
    VERIFIED = "Verified"
    NOT_APPLICABLE = "Not Applicable"


@dataclass
class Risk(DataclassMixin):
    """
    A structured risk identified in strategy assessment.

    Follows standard risk management framework with GovCon-specific
    categorization and mitigation requirements.
    """

    # Include computed properties in to_dict() output
    _include_properties: ClassVar[Set[str]] = {"risk_score", "risk_level", "is_acceptable"}

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Classification
    category: RiskCategory = RiskCategory.EXECUTION
    subcategory: str = ""  # More specific classification

    # Description
    title: str = ""
    description: str = ""
    trigger: str = ""  # What would cause this risk to materialize
    consequence: str = ""  # What happens if the risk occurs

    # Assessment
    probability: Probability = Probability.MEDIUM
    impact: Impact = Impact.MEDIUM
    velocity: str = ""  # How quickly the risk could materialize

    # Context
    source_section: str = ""  # Document section where risk was identified
    source_content: str = ""  # Specific content that triggered the risk

    # Mitigation
    mitigation_required: bool = True
    suggested_mitigation: str = ""
    mitigation_owner: str = ""
    mitigation_status: MitigationStatus = MitigationStatus.NOT_STARTED
    mitigation_cost: str = ""  # Estimated cost/effort of mitigation
    residual_risk: str = ""  # Risk remaining after mitigation

    # Metadata
    identified_by: str = "Risk Assessor"
    round_number: int = 1
    requires_human_review: bool = False
    related_risks: List[str] = field(default_factory=list)  # IDs of related risks
    references: List[str] = field(default_factory=list)  # External references

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate and set derived fields."""
        # Require mitigation for high-severity risks
        if self.risk_score >= 0.4:
            self.mitigation_required = True

        # Flag for human review if critical
        if self.probability in {Probability.HIGH, Probability.ALMOST_CERTAIN} and \
           self.impact in {Impact.HIGH, Impact.CATASTROPHIC}:
            self.requires_human_review = True

    @property
    def risk_score(self) -> float:
        """Calculate risk score (probability * impact)."""
        return self.probability.numeric_value * self.impact.numeric_value

    @property
    def risk_level(self) -> str:
        """Determine overall risk level from score."""
        score = self.risk_score
        if score >= 0.6:
            return "critical"
        elif score >= 0.4:
            return "high"
        elif score >= 0.2:
            return "medium"
        elif score >= 0.1:
            return "low"
        else:
            return "negligible"

    @property
    def is_acceptable(self) -> bool:
        """Check if risk is within acceptable tolerance."""
        # Risks with critical impact are never acceptable without mitigation
        if self.impact == Impact.CATASTROPHIC:
            return self.mitigation_status in {
                MitigationStatus.IMPLEMENTED,
                MitigationStatus.VERIFIED,
            }
        # High risks need at least in-progress mitigation
        if self.risk_level in {"critical", "high"}:
            return self.mitigation_status not in {
                MitigationStatus.NOT_STARTED,
                MitigationStatus.NOT_APPLICABLE,
            }
        return True

    def update_mitigation(
        self,
        status: MitigationStatus,
        residual_risk: Optional[str] = None,
    ) -> None:
        """Update mitigation status and residual risk."""
        self.mitigation_status = status
        if residual_risk:
            self.residual_risk = residual_risk
        self.updated_at = datetime.utcnow()

    @classmethod
    def from_dict(cls, data: dict) -> "Risk":
        risk = cls.__new__(cls)
        risk.id = data.get("id", str(uuid.uuid4()))
        risk.category = RiskCategory(data.get("category", "Execution"))
        risk.subcategory = data.get("subcategory", "")
        risk.title = data.get("title", "")
        risk.description = data.get("description", "")
        risk.trigger = data.get("trigger", "")
        risk.consequence = data.get("consequence", "")
        risk.probability = Probability(data.get("probability", "Medium"))
        risk.impact = Impact(data.get("impact", "Medium"))
        risk.velocity = data.get("velocity", "")
        risk.source_section = data.get("source_section", "")
        risk.source_content = data.get("source_content", "")
        risk.mitigation_required = data.get("mitigation_required", True)
        risk.suggested_mitigation = data.get("suggested_mitigation", "")
        risk.mitigation_owner = data.get("mitigation_owner", "")
        risk.mitigation_status = MitigationStatus(
            data.get("mitigation_status", "Not Started")
        )
        risk.mitigation_cost = data.get("mitigation_cost", "")
        risk.residual_risk = data.get("residual_risk", "")
        risk.identified_by = data.get("identified_by", "Risk Assessor")
        risk.round_number = data.get("round_number", 1)
        risk.requires_human_review = data.get("requires_human_review", False)
        risk.related_risks = data.get("related_risks", [])
        risk.references = data.get("references", [])
        risk.created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow()
        )
        risk.updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.utcnow()
        )
        return risk

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Risk":
        return cls.from_dict(json.loads(json_str))


@dataclass
class WorstCaseScenario(DataclassMixin):
    """A worst-case scenario analysis for risk assessment."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Scenario description
    title: str = ""
    narrative: str = ""  # Detailed description of what could go wrong
    trigger_chain: List[str] = field(default_factory=list)  # Sequence of events

    # Impact analysis
    win_probability_impact: str = ""  # Effect on win probability
    financial_impact: str = ""  # Potential financial loss
    reputation_impact: str = ""  # Effect on company reputation
    strategic_impact: str = ""  # Long-term strategic consequences

    # Associated risks
    contributing_risks: List[str] = field(default_factory=list)  # Risk IDs

    # Prevention and recovery
    prevention_measures: List[str] = field(default_factory=list)
    recovery_options: List[str] = field(default_factory=list)
    early_warning_signs: List[str] = field(default_factory=list)

    # Assessment
    plausibility: str = "Medium"  # Low, Medium, High
    severity: str = "High"  # Medium, High, Catastrophic


@dataclass
class RiskRegister(DataclassMixin):
    """
    A register of all identified risks for an opportunity.

    Provides aggregation and analysis capabilities for risk management.
    """

    document_id: str = ""
    opportunity_id: str = ""

    # Risks
    risks: List[Risk] = field(default_factory=list)
    worst_case_scenarios: List[WorstCaseScenario] = field(default_factory=list)

    # Summary statistics
    total_risks: int = 0
    critical_risks: int = 0
    high_risks: int = 0
    medium_risks: int = 0
    low_risks: int = 0

    # Category breakdown
    risks_by_category: Dict[str, int] = field(default_factory=dict)

    # Overall assessment
    overall_risk_level: str = ""  # Aggregate assessment
    risk_appetite_status: str = ""  # Within/Exceeds risk appetite
    recommended_action: str = ""  # Proceed, Proceed with caution, Reconsider

    def __post_init__(self):
        """Calculate summary statistics."""
        if self.risks:
            self.calculate_summary()

    def add_risk(self, risk: Risk) -> None:
        """Add a risk and update statistics."""
        self.risks.append(risk)
        self.calculate_summary()

    def calculate_summary(self) -> None:
        """Calculate summary statistics from risks."""
        self.total_risks = len(self.risks)
        self.critical_risks = sum(1 for r in self.risks if r.risk_level == "critical")
        self.high_risks = sum(1 for r in self.risks if r.risk_level == "high")
        self.medium_risks = sum(1 for r in self.risks if r.risk_level == "medium")
        self.low_risks = sum(1 for r in self.risks if r.risk_level in {"low", "negligible"})

        # Category breakdown
        self.risks_by_category = {}
        for risk in self.risks:
            cat = risk.category.value
            self.risks_by_category[cat] = self.risks_by_category.get(cat, 0) + 1

        # Overall assessment
        if self.critical_risks > 0:
            self.overall_risk_level = "critical"
            self.risk_appetite_status = "Exceeds Appetite"
            self.recommended_action = "Reconsider unless critical risks can be mitigated"
        elif self.high_risks >= 3:
            self.overall_risk_level = "high"
            self.risk_appetite_status = "At Limit"
            self.recommended_action = "Proceed with caution; ensure mitigation plans"
        elif self.high_risks > 0:
            self.overall_risk_level = "medium-high"
            self.risk_appetite_status = "Within Appetite"
            self.recommended_action = "Proceed with active risk monitoring"
        elif self.medium_risks > 0:
            self.overall_risk_level = "medium"
            self.risk_appetite_status = "Within Appetite"
            self.recommended_action = "Proceed with standard risk management"
        else:
            self.overall_risk_level = "low"
            self.risk_appetite_status = "Well Within Appetite"
            self.recommended_action = "Proceed"

    def get_unmitigated_risks(self) -> List[Risk]:
        """Get all risks without mitigation plans."""
        return [
            r for r in self.risks
            if r.mitigation_required and
               r.mitigation_status == MitigationStatus.NOT_STARTED
        ]

    def get_risks_requiring_review(self) -> List[Risk]:
        """Get all risks flagged for human review."""
        return [r for r in self.risks if r.requires_human_review]

    def get_risks_by_category(self, category: RiskCategory) -> List[Risk]:
        """Get all risks in a specific category."""
        return [r for r in self.risks if r.category == category]

    def get_top_risks(self, n: int = 5) -> List[Risk]:
        """Get the top N risks by score."""
        return sorted(self.risks, key=lambda r: r.risk_score, reverse=True)[:n]

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# Risk indicators by category - patterns that suggest specific risks
RISK_INDICATORS: Dict[RiskCategory, List[str]] = {
    RiskCategory.EXECUTION: [
        "aggressive timeline",
        "limited experience",
        "first time",
        "complex integration",
        "new technology",
        "unproven approach",
    ],
    RiskCategory.STAFFING: [
        "key personnel",
        "clearance requirement",
        "specialized skill",
        "hard to fill",
        "recruitment",
        "retention",
    ],
    RiskCategory.COMPLIANCE: [
        "far requirement",
        "dfar",
        "regulation",
        "mandatory",
        "shall",
        "must comply",
    ],
    RiskCategory.COMPETITIVE: [
        "incumbent",
        "established relationship",
        "competitor strength",
        "market leader",
        "price pressure",
    ],
    RiskCategory.FINANCIAL: [
        "cost estimate",
        "budget constraint",
        "margin",
        "investment required",
        "cash flow",
    ],
    RiskCategory.PRICING: [
        "price-to-win",
        "cost realism",
        "labor rate",
        "aggressive pricing",
        "underbid",
    ],
    RiskCategory.TEAMING: [
        "subcontractor",
        "teaming partner",
        "joint venture",
        "mentor-protege",
        "work share",
    ],
    RiskCategory.TRANSITION: [
        "transition",
        "phase-in",
        "knowledge transfer",
        "onboarding",
        "handover",
    ],
}


def identify_risk_category(content: str) -> List[RiskCategory]:
    """
    Identify potential risk categories from content.

    Args:
        content: Text content to analyze

    Returns:
        List of potentially relevant risk categories
    """
    content_lower = content.lower()
    categories = []

    for category, indicators in RISK_INDICATORS.items():
        for indicator in indicators:
            if indicator in content_lower:
                if category not in categories:
                    categories.append(category)
                break

    return categories if categories else [RiskCategory.EXECUTION]
