"""
Lowest Price Technically Acceptable (LPTA) Evaluation

Implements LPTA evaluation logic per FAR 15.101-2. In LPTA evaluations,
technical factors are assessed only for acceptability (pass/fail),
and award goes to the lowest priced proposal that is technically acceptable.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import json

from .factors import (
    EvaluationFactor,
    EvaluationRating,
    Rating,
    RatingLevel,
    Weakness,
    WeaknessType,
    Strength,
)


class AcceptabilityStatus(str, Enum):
    """
    Technical acceptability status for LPTA evaluation.
    """

    ACCEPTABLE = "Acceptable"
    UNACCEPTABLE = "Unacceptable"
    PENDING_CLARIFICATION = "Pending Clarification"

    @property
    def is_acceptable(self) -> bool:
        return self == AcceptabilityStatus.ACCEPTABLE


@dataclass
class TechnicalAcceptability:
    """
    Technical acceptability determination for a factor.
    """

    factor_name: str
    status: AcceptabilityStatus
    rationale: str = ""
    deficiencies: List[Weakness] = field(default_factory=list)
    clarifications_needed: List[str] = field(default_factory=list)

    @property
    def is_acceptable(self) -> bool:
        return self.status.is_acceptable

    def to_dict(self) -> dict:
        return {
            "factor_name": self.factor_name,
            "status": self.status.value,
            "rationale": self.rationale,
            "deficiencies": [d.to_dict() for d in self.deficiencies],
            "clarifications_needed": self.clarifications_needed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TechnicalAcceptability":
        return cls(
            factor_name=data.get("factor_name", ""),
            status=AcceptabilityStatus(data.get("status", "Unacceptable")),
            rationale=data.get("rationale", ""),
            deficiencies=[
                Weakness.from_dict(d) for d in data.get("deficiencies", [])
            ],
            clarifications_needed=data.get("clarifications_needed", []),
        )


@dataclass
class LPTAEvaluationResult:
    """
    Complete LPTA evaluation result.
    """

    # Overall determination
    overall_acceptable: bool = False
    overall_rationale: str = ""

    # Factor-by-factor acceptability
    factor_acceptability: List[TechnicalAcceptability] = field(default_factory=list)

    # Price
    proposed_price: Optional[float] = None
    price_reasonable: bool = False
    price_analysis: str = ""

    # Evaluation notes
    evaluator_narrative: str = ""
    clarification_questions: List[str] = field(default_factory=list)

    # All identified issues
    all_deficiencies: List[Weakness] = field(default_factory=list)

    @property
    def unacceptable_factors(self) -> List[str]:
        """Get names of unacceptable factors."""
        return [
            fa.factor_name
            for fa in self.factor_acceptability
            if not fa.is_acceptable
        ]

    @property
    def deficiency_count(self) -> int:
        """Total number of deficiencies."""
        return len(self.all_deficiencies)

    @property
    def is_in_competitive_range(self) -> bool:
        """
        Determine if proposal is in competitive range.
        For LPTA, this means technically acceptable.
        """
        return self.overall_acceptable

    def to_dict(self) -> dict:
        return {
            "overall_acceptable": self.overall_acceptable,
            "overall_rationale": self.overall_rationale,
            "factor_acceptability": [fa.to_dict() for fa in self.factor_acceptability],
            "proposed_price": self.proposed_price,
            "price_reasonable": self.price_reasonable,
            "price_analysis": self.price_analysis,
            "evaluator_narrative": self.evaluator_narrative,
            "clarification_questions": self.clarification_questions,
            "all_deficiencies": [d.to_dict() for d in self.all_deficiencies],
            "unacceptable_factors": self.unacceptable_factors,
            "deficiency_count": self.deficiency_count,
        }


class LPTAEvaluator:
    """
    Evaluator for LPTA procurements.

    In LPTA evaluations:
    - Technical factors are assessed for acceptability only (pass/fail)
    - A deficiency in any factor makes the proposal unacceptable
    - Award goes to lowest priced acceptable proposal
    - Trade-offs between technical and price are NOT permitted
    """

    LPTA_GUIDANCE = """
    LPTA Evaluation Standards (FAR 15.101-2):

    1. ACCEPTABILITY DETERMINATION
       - Each technical factor is evaluated only for acceptability
       - Proposal either meets minimum requirements (Acceptable) or does not (Unacceptable)
       - No credit given for exceeding requirements
       - A single deficiency makes the factor Unacceptable

    2. DEFICIENCY = UNACCEPTABLE
       - A deficiency is a material failure to meet a Government requirement
       - Any proposal with a deficiency in any factor is Unacceptable overall
       - Cannot be included in competitive range

    3. PRICE EVALUATION
       - Price is evaluated for reasonableness
       - Award to lowest priced Acceptable proposal
       - No trade-off between price and non-price factors

    4. EVALUATION STANDARDS
       Acceptable: Proposal meets all minimum requirements of the factor
       Unacceptable: Proposal fails to meet one or more requirements (deficiency)
    """

    def __init__(self, factors: List[EvaluationFactor]):
        """
        Initialize the LPTA evaluator.

        Args:
            factors: List of evaluation factors from the solicitation
        """
        self.factors = factors

    def evaluate_factor_acceptability(
        self,
        factor: EvaluationFactor,
        proposal_content: str,
        requirements: List[str],
    ) -> TechnicalAcceptability:
        """
        Evaluate a single factor for technical acceptability.

        Args:
            factor: The evaluation factor
            proposal_content: Relevant proposal content for this factor
            requirements: Specific requirements that must be met

        Returns:
            TechnicalAcceptability determination
        """
        # Placeholder - actual evaluation would use LLM
        return TechnicalAcceptability(
            factor_name=factor.name,
            status=AcceptabilityStatus.ACCEPTABLE,
            rationale="Meets minimum requirements.",
        )

    def evaluate_proposal(
        self,
        proposal_sections: Dict[str, str],
        requirements: Dict[str, List[str]],
        proposed_price: Optional[float] = None,
    ) -> LPTAEvaluationResult:
        """
        Perform complete LPTA evaluation.

        Args:
            proposal_sections: Map of section names to content
            requirements: Map of factor names to their requirements
            proposed_price: The offeror's proposed price

        Returns:
            Complete LPTA evaluation result
        """
        result = LPTAEvaluationResult(proposed_price=proposed_price)

        # Evaluate each factor
        for factor in self.factors:
            factor_content = proposal_sections.get(factor.name, "")
            factor_requirements = requirements.get(factor.name, [])

            acceptability = self.evaluate_factor_acceptability(
                factor=factor,
                proposal_content=factor_content,
                requirements=factor_requirements,
            )

            result.factor_acceptability.append(acceptability)
            result.all_deficiencies.extend(acceptability.deficiencies)

        # Overall determination
        result.overall_acceptable = all(
            fa.is_acceptable for fa in result.factor_acceptability
        )

        if result.overall_acceptable:
            result.overall_rationale = (
                "Proposal is technically acceptable. All factors meet minimum requirements."
            )
        else:
            unacceptable = result.unacceptable_factors
            result.overall_rationale = (
                f"Proposal is technically unacceptable. "
                f"Deficiencies found in: {', '.join(unacceptable)}"
            )

        return result

    @staticmethod
    def get_evaluation_prompt_guidance() -> str:
        """Get guidance for LLM evaluation prompts."""
        return LPTAEvaluator.LPTA_GUIDANCE
