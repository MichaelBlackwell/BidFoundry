"""
Evaluation Factors

Defines the structure and common evaluation factors used in federal
government source selection. Based on FAR Part 15 evaluation standards.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import json


class FactorImportance(str, Enum):
    """Relative importance levels for evaluation factors."""

    SIGNIFICANTLY_MORE_IMPORTANT = "Significantly More Important"
    MORE_IMPORTANT = "More Important"
    APPROXIMATELY_EQUAL = "Approximately Equal"
    LESS_IMPORTANT = "Less Important"
    SIGNIFICANTLY_LESS_IMPORTANT = "Significantly Less Important"


class RatingLevel(str, Enum):
    """
    Standard adjectival rating levels per FAR guidance.

    These ratings are used for technical and past performance factors.
    """

    # Technical/Management ratings
    OUTSTANDING = "Outstanding"
    GOOD = "Good"
    ACCEPTABLE = "Acceptable"
    MARGINAL = "Marginal"
    UNACCEPTABLE = "Unacceptable"

    # Past performance specific ratings
    EXCEPTIONAL = "Exceptional"
    VERY_GOOD = "Very Good"
    SATISFACTORY = "Satisfactory"
    # MARGINAL also used
    UNSATISFACTORY = "Unsatisfactory"
    NEUTRAL = "Neutral"  # No past performance or not relevant

    @property
    def is_acceptable(self) -> bool:
        """Check if this rating is considered acceptable."""
        return self in {
            RatingLevel.OUTSTANDING,
            RatingLevel.EXCEPTIONAL,
            RatingLevel.GOOD,
            RatingLevel.VERY_GOOD,
            RatingLevel.ACCEPTABLE,
            RatingLevel.SATISFACTORY,
        }

    @property
    def numeric_score(self) -> int:
        """Convert to numeric score for comparison."""
        score_map = {
            RatingLevel.OUTSTANDING: 5,
            RatingLevel.EXCEPTIONAL: 5,
            RatingLevel.GOOD: 4,
            RatingLevel.VERY_GOOD: 4,
            RatingLevel.ACCEPTABLE: 3,
            RatingLevel.SATISFACTORY: 3,
            RatingLevel.MARGINAL: 2,
            RatingLevel.UNACCEPTABLE: 1,
            RatingLevel.UNSATISFACTORY: 1,
            RatingLevel.NEUTRAL: 3,  # Neutral is treated as acceptable
        }
        return score_map.get(self, 3)


class WeaknessType(str, Enum):
    """
    Types of weaknesses per FAR 15.305 definitions.
    """

    DEFICIENCY = "Deficiency"  # Material failure to meet requirements
    SIGNIFICANT_WEAKNESS = "Significant Weakness"  # Appreciably lessens likelihood of success
    WEAKNESS = "Weakness"  # Lessens likelihood of success
    RISK = "Risk"  # Potential for disruption of performance

    @property
    def severity_order(self) -> int:
        """Get severity order (higher = more severe)."""
        order_map = {
            WeaknessType.DEFICIENCY: 4,
            WeaknessType.SIGNIFICANT_WEAKNESS: 3,
            WeaknessType.WEAKNESS: 2,
            WeaknessType.RISK: 1,
        }
        return order_map.get(self, 0)


@dataclass
class Rating:
    """
    A rating for an evaluation factor with justification.
    """

    level: RatingLevel
    justification: str = ""
    evaluator_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "justification": self.justification,
            "evaluator_notes": self.evaluator_notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Rating":
        return cls(
            level=RatingLevel(data.get("level", "Acceptable")),
            justification=data.get("justification", ""),
            evaluator_notes=data.get("evaluator_notes", ""),
        )


@dataclass
class EvaluationRating:
    """
    Complete rating with strengths and weaknesses.
    """

    rating: Rating
    strengths: List["Strength"] = field(default_factory=list)
    weaknesses: List["Weakness"] = field(default_factory=list)

    @property
    def has_deficiency(self) -> bool:
        """Check if any weakness is a deficiency."""
        return any(w.weakness_type == WeaknessType.DEFICIENCY for w in self.weaknesses)

    @property
    def has_significant_weakness(self) -> bool:
        """Check if any weakness is significant."""
        return any(
            w.weakness_type in {WeaknessType.DEFICIENCY, WeaknessType.SIGNIFICANT_WEAKNESS}
            for w in self.weaknesses
        )

    @property
    def weakness_count(self) -> int:
        return len(self.weaknesses)

    @property
    def strength_count(self) -> int:
        return len(self.strengths)

    def to_dict(self) -> dict:
        return {
            "rating": self.rating.to_dict(),
            "strengths": [s.to_dict() for s in self.strengths],
            "weaknesses": [w.to_dict() for w in self.weaknesses],
        }


@dataclass
class Weakness:
    """
    A weakness identified in evaluation per FAR definitions.
    """

    weakness_type: WeaknessType
    factor: str  # Which factor this weakness applies to
    description: str
    location: str = ""  # Where in the proposal this was found
    requirement_reference: str = ""  # Which requirement is affected
    impact: str = ""  # Impact on evaluation or performance
    recommendation: str = ""  # How to address

    def to_dict(self) -> dict:
        return {
            "weakness_type": self.weakness_type.value,
            "factor": self.factor,
            "description": self.description,
            "location": self.location,
            "requirement_reference": self.requirement_reference,
            "impact": self.impact,
            "recommendation": self.recommendation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Weakness":
        return cls(
            weakness_type=WeaknessType(data.get("weakness_type", "Weakness")),
            factor=data.get("factor", ""),
            description=data.get("description", ""),
            location=data.get("location", ""),
            requirement_reference=data.get("requirement_reference", ""),
            impact=data.get("impact", ""),
            recommendation=data.get("recommendation", ""),
        )


@dataclass
class Strength:
    """
    A strength identified in evaluation.
    """

    factor: str  # Which factor this strength applies to
    description: str
    location: str = ""  # Where in the proposal this was found
    benefit: str = ""  # How this benefits the government
    exceeds_requirements: bool = False  # Whether this exceeds minimum requirements

    def to_dict(self) -> dict:
        return {
            "factor": self.factor,
            "description": self.description,
            "location": self.location,
            "benefit": self.benefit,
            "exceeds_requirements": self.exceeds_requirements,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Strength":
        return cls(
            factor=data.get("factor", ""),
            description=data.get("description", ""),
            location=data.get("location", ""),
            benefit=data.get("benefit", ""),
            exceeds_requirements=data.get("exceeds_requirements", False),
        )


@dataclass
class EvaluationSubFactor:
    """
    A sub-factor within a main evaluation factor.
    """

    name: str
    description: str = ""
    weight: Optional[float] = None  # Percentage weight within parent factor
    importance: Optional[FactorImportance] = None  # Relative importance

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "importance": self.importance.value if self.importance else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationSubFactor":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            weight=data.get("weight"),
            importance=FactorImportance(data["importance"]) if data.get("importance") else None,
        )


@dataclass
class EvaluationFactor:
    """
    A main evaluation factor from the solicitation.
    """

    name: str
    description: str = ""
    weight: Optional[float] = None  # Percentage weight in overall evaluation
    importance: Optional[FactorImportance] = None  # Relative importance
    sub_factors: List[EvaluationSubFactor] = field(default_factory=list)
    evaluation_criteria: List[str] = field(default_factory=list)  # Specific criteria

    # Source selection context
    order_of_importance: Optional[int] = None  # 1 = most important

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "importance": self.importance.value if self.importance else None,
            "sub_factors": [sf.to_dict() for sf in self.sub_factors],
            "evaluation_criteria": self.evaluation_criteria,
            "order_of_importance": self.order_of_importance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationFactor":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            weight=data.get("weight"),
            importance=FactorImportance(data["importance"]) if data.get("importance") else None,
            sub_factors=[
                EvaluationSubFactor.from_dict(sf) for sf in data.get("sub_factors", [])
            ],
            evaluation_criteria=data.get("evaluation_criteria", []),
            order_of_importance=data.get("order_of_importance"),
        )


@dataclass
class EvaluationFactorResult:
    """
    Evaluation result for a single factor.
    """

    factor: EvaluationFactor
    rating: EvaluationRating
    sub_factor_ratings: Dict[str, EvaluationRating] = field(default_factory=dict)
    evaluator_narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "factor": self.factor.to_dict(),
            "rating": self.rating.to_dict(),
            "sub_factor_ratings": {
                k: v.to_dict() for k, v in self.sub_factor_ratings.items()
            },
            "evaluator_narrative": self.evaluator_narrative,
        }


# Common evaluation factors used in federal procurements

COMMON_TECHNICAL_FACTORS = [
    EvaluationFactor(
        name="Technical Approach",
        description="The offeror's approach to meeting the technical requirements of the PWS/SOW.",
        sub_factors=[
            EvaluationSubFactor(
                name="Understanding of Requirements",
                description="Demonstrated understanding of the work to be performed.",
            ),
            EvaluationSubFactor(
                name="Technical Solution",
                description="Quality and feasibility of the proposed technical solution.",
            ),
            EvaluationSubFactor(
                name="Innovation",
                description="Innovative approaches that add value.",
            ),
        ],
        evaluation_criteria=[
            "Clear demonstration of understanding of the requirements",
            "Feasible and effective technical approach",
            "Innovative solutions that provide benefit",
            "Risk mitigation strategies",
        ],
    ),
    EvaluationFactor(
        name="Management Approach",
        description="The offeror's approach to managing the contract.",
        sub_factors=[
            EvaluationSubFactor(
                name="Program Management",
                description="Organizational structure and program management approach.",
            ),
            EvaluationSubFactor(
                name="Quality Control",
                description="Quality assurance and quality control processes.",
            ),
            EvaluationSubFactor(
                name="Risk Management",
                description="Approach to identifying and mitigating risks.",
            ),
        ],
        evaluation_criteria=[
            "Sound organizational structure",
            "Effective quality control processes",
            "Proactive risk management",
            "Clear communication and reporting plans",
        ],
    ),
    EvaluationFactor(
        name="Staffing/Key Personnel",
        description="Qualifications and experience of proposed key personnel.",
        sub_factors=[
            EvaluationSubFactor(
                name="Program Manager",
                description="Qualifications of the proposed Program Manager.",
            ),
            EvaluationSubFactor(
                name="Technical Leads",
                description="Qualifications of technical leads and subject matter experts.",
            ),
            EvaluationSubFactor(
                name="Staffing Plan",
                description="Approach to staffing including recruitment and retention.",
            ),
        ],
        evaluation_criteria=[
            "Relevant experience for key personnel",
            "Appropriate qualifications and certifications",
            "Realistic staffing plan",
            "Personnel retention strategies",
        ],
    ),
]

COMMON_PAST_PERFORMANCE_FACTORS = [
    EvaluationFactor(
        name="Past Performance",
        description="Relevance and quality of past performance on similar contracts.",
        sub_factors=[
            EvaluationSubFactor(
                name="Relevance",
                description="How relevant the past performance is to the current requirement.",
            ),
            EvaluationSubFactor(
                name="Quality",
                description="Quality of performance on past contracts.",
            ),
            EvaluationSubFactor(
                name="Recency",
                description="How recent the past performance is.",
            ),
        ],
        evaluation_criteria=[
            "Work of similar size, scope, and complexity",
            "Positive CPARS ratings",
            "Demonstrated ability to meet schedules and cost controls",
            "Satisfactory resolution of past performance issues",
        ],
    ),
]

COMMON_COST_FACTORS = [
    EvaluationFactor(
        name="Cost/Price",
        description="Evaluation of the proposed cost or price.",
        sub_factors=[
            EvaluationSubFactor(
                name="Price Reasonableness",
                description="Whether the price is reasonable for the work proposed.",
            ),
            EvaluationSubFactor(
                name="Price Realism",
                description="Whether the price reflects a clear understanding of requirements.",
            ),
            EvaluationSubFactor(
                name="Cost Control",
                description="Approach to managing and controlling costs.",
            ),
        ],
        evaluation_criteria=[
            "Price is fair and reasonable",
            "Cost is realistic for the proposed approach",
            "Effective cost control mechanisms",
            "Clear basis of estimate",
        ],
    ),
]
