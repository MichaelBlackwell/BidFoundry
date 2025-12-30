"""
Best Value Tradeoff Evaluation

Implements Best Value tradeoff evaluation logic per FAR 15.101-1.
In Best Value evaluations, the Government may select a higher-priced
proposal if the non-price benefits justify the additional cost.
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
    FactorImportance,
    EvaluationFactorResult,
)


class ConfidenceLevel(str, Enum):
    """
    Past performance confidence assessment levels.
    """

    SUBSTANTIAL_CONFIDENCE = "Substantial Confidence"
    SATISFACTORY_CONFIDENCE = "Satisfactory Confidence"
    NEUTRAL_CONFIDENCE = "Neutral Confidence"  # No/limited record
    LIMITED_CONFIDENCE = "Limited Confidence"
    NO_CONFIDENCE = "No Confidence"

    @property
    def is_favorable(self) -> bool:
        return self in {
            ConfidenceLevel.SUBSTANTIAL_CONFIDENCE,
            ConfidenceLevel.SATISFACTORY_CONFIDENCE,
            ConfidenceLevel.NEUTRAL_CONFIDENCE,
        }


class TradeoffDecision(str, Enum):
    """
    Possible tradeoff decisions for Best Value analysis.
    """

    BEST_VALUE = "Best Value"  # Selected as best value
    LOWER_PRICE_SUFFICIENT = "Lower Price Sufficient"  # Lower priced offer provides adequate value
    NOT_IN_RANGE = "Not In Competitive Range"  # Too many deficiencies
    PENDING = "Pending Tradeoff"  # Further analysis needed


@dataclass
class TradeoffAnalysis:
    """
    Analysis of the cost-technical tradeoff.
    """

    # Price comparison
    price_rank: int = 0  # 1 = lowest
    price_delta: float = 0.0  # Difference from lowest price
    price_delta_percent: float = 0.0  # Percentage above lowest

    # Technical superiority
    technical_advantages: List[str] = field(default_factory=list)
    technical_disadvantages: List[str] = field(default_factory=list)

    # Tradeoff rationale
    is_premium_justified: bool = False
    tradeoff_rationale: str = ""

    # Decision
    decision: TradeoffDecision = TradeoffDecision.PENDING

    def to_dict(self) -> dict:
        return {
            "price_rank": self.price_rank,
            "price_delta": self.price_delta,
            "price_delta_percent": self.price_delta_percent,
            "technical_advantages": self.technical_advantages,
            "technical_disadvantages": self.technical_disadvantages,
            "is_premium_justified": self.is_premium_justified,
            "tradeoff_rationale": self.tradeoff_rationale,
            "decision": self.decision.value,
        }


@dataclass
class BestValueEvaluationResult:
    """
    Complete Best Value tradeoff evaluation result.
    """

    # Overall assessment
    overall_rating: RatingLevel = RatingLevel.ACCEPTABLE
    overall_narrative: str = ""

    # Factor ratings
    factor_results: List[EvaluationFactorResult] = field(default_factory=list)

    # Past performance confidence
    past_performance_confidence: ConfidenceLevel = ConfidenceLevel.NEUTRAL_CONFIDENCE
    past_performance_narrative: str = ""

    # Price evaluation
    proposed_price: Optional[float] = None
    price_reasonable: bool = False
    price_realistic: bool = False
    price_analysis: str = ""

    # Tradeoff analysis
    tradeoff: Optional[TradeoffAnalysis] = None

    # Competitive range determination
    in_competitive_range: bool = True
    competitive_range_rationale: str = ""

    # All findings
    all_strengths: List[Strength] = field(default_factory=list)
    all_weaknesses: List[Weakness] = field(default_factory=list)

    # Evaluator notes
    evaluator_margin_notes: List[str] = field(default_factory=list)
    clarification_questions: List[str] = field(default_factory=list)

    @property
    def strength_count(self) -> int:
        return len(self.all_strengths)

    @property
    def weakness_count(self) -> int:
        return len(self.all_weaknesses)

    @property
    def deficiency_count(self) -> int:
        return sum(
            1 for w in self.all_weaknesses
            if w.weakness_type == WeaknessType.DEFICIENCY
        )

    @property
    def significant_weakness_count(self) -> int:
        return sum(
            1 for w in self.all_weaknesses
            if w.weakness_type in {WeaknessType.DEFICIENCY, WeaknessType.SIGNIFICANT_WEAKNESS}
        )

    @property
    def has_deficiency(self) -> bool:
        return self.deficiency_count > 0

    def get_factor_rating(self, factor_name: str) -> Optional[RatingLevel]:
        """Get rating for a specific factor."""
        for fr in self.factor_results:
            if fr.factor.name == factor_name:
                return fr.rating.rating.level
        return None

    def to_dict(self) -> dict:
        return {
            "overall_rating": self.overall_rating.value,
            "overall_narrative": self.overall_narrative,
            "factor_results": [fr.to_dict() for fr in self.factor_results],
            "past_performance_confidence": self.past_performance_confidence.value,
            "past_performance_narrative": self.past_performance_narrative,
            "proposed_price": self.proposed_price,
            "price_reasonable": self.price_reasonable,
            "price_realistic": self.price_realistic,
            "price_analysis": self.price_analysis,
            "tradeoff": self.tradeoff.to_dict() if self.tradeoff else None,
            "in_competitive_range": self.in_competitive_range,
            "competitive_range_rationale": self.competitive_range_rationale,
            "all_strengths": [s.to_dict() for s in self.all_strengths],
            "all_weaknesses": [w.to_dict() for w in self.all_weaknesses],
            "evaluator_margin_notes": self.evaluator_margin_notes,
            "clarification_questions": self.clarification_questions,
            "strength_count": self.strength_count,
            "weakness_count": self.weakness_count,
            "deficiency_count": self.deficiency_count,
        }


class BestValueEvaluator:
    """
    Evaluator for Best Value tradeoff procurements.

    In Best Value evaluations:
    - Technical and non-price factors are rated and scored
    - Price is evaluated for reasonableness and realism
    - Trade-offs between price and non-price factors are permitted
    - Government may pay a premium for superior technical approaches
    """

    BEST_VALUE_GUIDANCE = """
    Best Value Tradeoff Evaluation Standards (FAR 15.101-1):

    1. TECHNICAL RATING SCALE
       Outstanding: Proposal significantly exceeds requirements in ways beneficial to Government
       Good: Proposal exceeds some requirements with beneficial outcomes
       Acceptable: Proposal meets all requirements
       Marginal: Proposal fails to meet some requirements but is correctable
       Unacceptable: Proposal fails to meet requirements; deficiencies cannot be corrected

    2. PAST PERFORMANCE CONFIDENCE
       Substantial Confidence: Strong record of relevant, successful performance
       Satisfactory Confidence: Record supports successful performance expectation
       Neutral Confidence: No/limited relevant record; neither positive nor negative
       Limited Confidence: Record raises doubt about successful performance
       No Confidence: Record shows significant performance problems

    3. STRENGTHS AND WEAKNESSES
       Strength: Aspect that exceeds requirements and provides benefit to Government
       Weakness: Flaw that increases risk of unsuccessful performance
       Significant Weakness: Flaw that appreciably increases risk of unsuccessful performance
       Deficiency: Material failure to meet a requirement; makes proposal unacceptable
       Risk: Potential for disruption of schedule, cost, or performance

    4. TRADEOFF ANALYSIS
       - Compare higher-priced proposals' technical superiority to price difference
       - Document what specific benefits justify paying more
       - Benefits must be worth the additional cost
       - Consider all evaluation factors in the tradeoff

    5. COMPETITIVE RANGE
       - Include proposals that have a reasonable chance of being selected
       - Proposals with deficiencies may still be included if correctable
       - Consider relative standings on all factors
    """

    RATING_DEFINITIONS = {
        RatingLevel.OUTSTANDING: (
            "Proposal significantly exceeds requirements in ways that are beneficial "
            "to the Government. The proposal contains multiple significant strengths "
            "with no weaknesses or only minor weaknesses."
        ),
        RatingLevel.GOOD: (
            "Proposal exceeds some requirements in ways beneficial to the Government. "
            "The proposal contains strengths which outweigh any weaknesses."
        ),
        RatingLevel.ACCEPTABLE: (
            "Proposal meets all requirements. Strengths and weaknesses are balanced "
            "or the proposal contains minor weaknesses that do not significantly "
            "detract from the proposal."
        ),
        RatingLevel.MARGINAL: (
            "Proposal fails to meet some requirements but deficiencies are minor "
            "and can be corrected. One or more weaknesses that significantly "
            "detract from the proposal but do not render it unacceptable."
        ),
        RatingLevel.UNACCEPTABLE: (
            "Proposal fails to meet requirements and contains one or more deficiencies "
            "that cannot be corrected without major proposal revisions. "
            "Not eligible for award in current form."
        ),
    }

    def __init__(
        self,
        factors: List[EvaluationFactor],
        factor_weights: Optional[Dict[str, float]] = None,
        price_weight: float = 30.0,
    ):
        """
        Initialize the Best Value evaluator.

        Args:
            factors: List of evaluation factors from the solicitation
            factor_weights: Optional weight percentages for each factor
            price_weight: Weight of price in overall evaluation
        """
        self.factors = factors
        self.factor_weights = factor_weights or {}
        self.price_weight = price_weight

    def evaluate_factor(
        self,
        factor: EvaluationFactor,
        proposal_content: str,
        requirements: List[str],
    ) -> EvaluationFactorResult:
        """
        Evaluate a single factor.

        Args:
            factor: The evaluation factor
            proposal_content: Relevant proposal content for this factor
            requirements: Specific requirements from the solicitation

        Returns:
            EvaluationFactorResult with rating and findings
        """
        # Placeholder - actual evaluation would use LLM
        return EvaluationFactorResult(
            factor=factor,
            rating=EvaluationRating(
                rating=Rating(
                    level=RatingLevel.ACCEPTABLE,
                    justification="Meets requirements.",
                )
            ),
        )

    def evaluate_proposal(
        self,
        proposal_sections: Dict[str, str],
        requirements: Dict[str, List[str]],
        proposed_price: Optional[float] = None,
        past_performance_refs: Optional[List[Dict[str, Any]]] = None,
    ) -> BestValueEvaluationResult:
        """
        Perform complete Best Value evaluation.

        Args:
            proposal_sections: Map of section names to content
            requirements: Map of factor names to their requirements
            proposed_price: The offeror's proposed price
            past_performance_refs: Past performance references

        Returns:
            Complete Best Value evaluation result
        """
        result = BestValueEvaluationResult(proposed_price=proposed_price)

        # Evaluate each factor
        for factor in self.factors:
            factor_content = proposal_sections.get(factor.name, "")
            factor_requirements = requirements.get(factor.name, [])

            factor_result = self.evaluate_factor(
                factor=factor,
                proposal_content=factor_content,
                requirements=factor_requirements,
            )

            result.factor_results.append(factor_result)
            result.all_strengths.extend(factor_result.rating.strengths)
            result.all_weaknesses.extend(factor_result.rating.weaknesses)

        # Determine overall rating
        result.overall_rating = self._calculate_overall_rating(result.factor_results)

        # Check competitive range
        result.in_competitive_range = not result.has_deficiency
        if not result.in_competitive_range:
            result.competitive_range_rationale = (
                f"Proposal contains {result.deficiency_count} deficiency(ies) "
                "that make it ineligible for competitive range."
            )

        return result

    def _calculate_overall_rating(
        self,
        factor_results: List[EvaluationFactorResult],
    ) -> RatingLevel:
        """Calculate overall rating from factor ratings."""
        if not factor_results:
            return RatingLevel.ACCEPTABLE

        # Check for any unacceptable ratings
        for fr in factor_results:
            if fr.rating.rating.level == RatingLevel.UNACCEPTABLE:
                return RatingLevel.UNACCEPTABLE

        # Calculate weighted average if weights available
        ratings = [fr.rating.rating.level for fr in factor_results]
        scores = [r.numeric_score for r in ratings]
        avg_score = sum(scores) / len(scores)

        if avg_score >= 4.5:
            return RatingLevel.OUTSTANDING
        elif avg_score >= 3.5:
            return RatingLevel.GOOD
        elif avg_score >= 2.5:
            return RatingLevel.ACCEPTABLE
        elif avg_score >= 1.5:
            return RatingLevel.MARGINAL
        else:
            return RatingLevel.UNACCEPTABLE

    def perform_tradeoff(
        self,
        proposals: List[BestValueEvaluationResult],
    ) -> List[TradeoffAnalysis]:
        """
        Perform tradeoff analysis across multiple proposals.

        Args:
            proposals: List of evaluation results for all proposals

        Returns:
            Tradeoff analysis for each proposal
        """
        if not proposals:
            return []

        # Sort by price
        proposals_with_price = [p for p in proposals if p.proposed_price is not None]
        proposals_with_price.sort(key=lambda p: p.proposed_price or 0)

        lowest_price = proposals_with_price[0].proposed_price if proposals_with_price else 0

        tradeoffs = []
        for i, proposal in enumerate(proposals_with_price):
            price = proposal.proposed_price or 0
            tradeoff = TradeoffAnalysis(
                price_rank=i + 1,
                price_delta=price - (lowest_price or 0),
                price_delta_percent=(
                    ((price - lowest_price) / lowest_price * 100) if lowest_price else 0
                ),
            )
            tradeoffs.append(tradeoff)

        return tradeoffs

    @staticmethod
    def get_evaluation_prompt_guidance() -> str:
        """Get guidance for LLM evaluation prompts."""
        return BestValueEvaluator.BEST_VALUE_GUIDANCE

    @staticmethod
    def get_rating_definition(rating: RatingLevel) -> str:
        """Get the definition for a rating level."""
        return BestValueEvaluator.RATING_DEFINITIONS.get(rating, "")
