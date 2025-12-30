"""
Evaluator Simulator Agent

Adversarial agent that simulates the perspective of a government Source Selection
Evaluation Board (SSEB) to identify weaknesses, deficiencies, and compliance gaps.
"""

import time
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import uuid

from agents.base import RedTeamAgent, SwarmContext, AgentOutput
from agents.config import AgentConfig
from agents.types import AgentRole, AgentCategory

from models.critique import Critique, ChallengeType, Severity, CritiqueSummary

from .evaluation_criteria import (
    EvaluationFactor,
    EvaluationRating,
    Rating,
    RatingLevel,
    Weakness,
    WeaknessType,
    Strength,
    EvaluationFactorResult,
    ConfidenceLevel,
    AcceptabilityStatus,
    COMMON_TECHNICAL_FACTORS,
    COMMON_PAST_PERFORMANCE_FACTORS,
    COMMON_COST_FACTORS,
)

from .prompts.evaluator_simulator_prompts import (
    EVALUATOR_SIMULATOR_SYSTEM_PROMPT,
    get_evaluation_prompt,
    get_section_evaluation_prompt,
    get_compliance_check_prompt,
    get_past_performance_evaluation_prompt,
    get_mock_evaluation_prompt,
)


@dataclass
class EvaluatorFinding:
    """A finding from the government evaluator perspective."""

    finding_type: WeaknessType  # Deficiency, Significant Weakness, Weakness, Risk
    factor: str
    title: str
    description: str
    requirement_affected: str = ""
    evidence_location: str = ""
    impact: str = ""
    recommendation: str = ""
    evaluator_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "finding_type": self.finding_type.value,
            "factor": self.factor,
            "title": self.title,
            "description": self.description,
            "requirement_affected": self.requirement_affected,
            "evidence_location": self.evidence_location,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "evaluator_notes": self.evaluator_notes,
        }

    def to_critique(
        self,
        agent: str,
        round_number: int = 1,
        document_id: str = "",
    ) -> Critique:
        """Convert finding to standard Critique format."""
        # Map weakness types to challenge types
        challenge_type_map = {
            WeaknessType.DEFICIENCY: ChallengeType.COMPLIANCE,
            WeaknessType.SIGNIFICANT_WEAKNESS: ChallengeType.RISK,
            WeaknessType.WEAKNESS: ChallengeType.COMPLETENESS,
            WeaknessType.RISK: ChallengeType.RISK,
        }

        # Map weakness types to severity
        severity_map = {
            WeaknessType.DEFICIENCY: Severity.CRITICAL,
            WeaknessType.SIGNIFICANT_WEAKNESS: Severity.MAJOR,
            WeaknessType.WEAKNESS: Severity.MAJOR,
            WeaknessType.RISK: Severity.MINOR,
        }

        return Critique(
            agent=agent,
            round_number=round_number,
            target_document_id=document_id,
            target_section=self.factor,
            target_content=self.evidence_location,
            challenge_type=challenge_type_map.get(self.finding_type, ChallengeType.COMPLIANCE),
            severity=severity_map.get(self.finding_type, Severity.MAJOR),
            title=f"[SSEB] {self.title}",
            argument=self.description,
            evidence=f"Requirement: {self.requirement_affected}. Impact: {self.impact}",
            suggested_remedy=self.recommendation,
            references=[self.requirement_affected] if self.requirement_affected else [],
        )


@dataclass
class EvaluatorStrength:
    """A strength identified from the evaluator perspective."""

    factor: str
    title: str
    description: str
    benefit_to_government: str = ""
    exceeds_requirements: bool = False
    location: str = ""

    def to_dict(self) -> dict:
        return {
            "factor": self.factor,
            "title": self.title,
            "description": self.description,
            "benefit_to_government": self.benefit_to_government,
            "exceeds_requirements": self.exceeds_requirements,
            "location": self.location,
        }


@dataclass
class FactorEvaluation:
    """Evaluation result for a single factor."""

    factor_name: str
    rating: RatingLevel
    rating_rationale: str = ""
    strengths: List[EvaluatorStrength] = field(default_factory=list)
    findings: List[EvaluatorFinding] = field(default_factory=list)
    evaluator_notes: List[str] = field(default_factory=list)

    @property
    def has_deficiency(self) -> bool:
        return any(f.finding_type == WeaknessType.DEFICIENCY for f in self.findings)

    @property
    def is_acceptable(self) -> bool:
        return self.rating.is_acceptable and not self.has_deficiency

    def to_dict(self) -> dict:
        return {
            "factor_name": self.factor_name,
            "rating": self.rating.value,
            "rating_rationale": self.rating_rationale,
            "strengths": [s.to_dict() for s in self.strengths],
            "findings": [f.to_dict() for f in self.findings],
            "evaluator_notes": self.evaluator_notes,
            "has_deficiency": self.has_deficiency,
            "is_acceptable": self.is_acceptable,
        }


@dataclass
class EvaluatorSimulatorResult:
    """Complete result from Evaluator Simulator analysis."""

    # Evaluation type
    evaluation_type: str = "Best Value"  # "LPTA" or "Best Value"

    # Overall assessment
    overall_rating: RatingLevel = RatingLevel.ACCEPTABLE
    overall_rationale: str = ""
    in_competitive_range: bool = True
    competitive_range_rationale: str = ""

    # Factor evaluations
    factor_evaluations: List[FactorEvaluation] = field(default_factory=list)

    # Past performance
    past_performance_confidence: Optional[ConfidenceLevel] = None
    past_performance_narrative: str = ""

    # Consolidated findings
    all_findings: List[EvaluatorFinding] = field(default_factory=list)
    all_strengths: List[EvaluatorStrength] = field(default_factory=list)

    # Evaluator perspective
    margin_notes: List[str] = field(default_factory=list)
    clarification_questions: List[str] = field(default_factory=list)
    competitive_assessment: str = ""

    # Standard critiques
    critiques: List[Critique] = field(default_factory=list)
    critique_summary: Optional[CritiqueSummary] = None

    # Meta
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)

    @property
    def deficiency_count(self) -> int:
        return sum(1 for f in self.all_findings if f.finding_type == WeaknessType.DEFICIENCY)

    @property
    def significant_weakness_count(self) -> int:
        return sum(
            1 for f in self.all_findings
            if f.finding_type in {WeaknessType.DEFICIENCY, WeaknessType.SIGNIFICANT_WEAKNESS}
        )

    @property
    def weakness_count(self) -> int:
        return len(self.all_findings)

    @property
    def strength_count(self) -> int:
        return len(self.all_strengths)

    def to_dict(self) -> dict:
        return {
            "evaluation_type": self.evaluation_type,
            "overall_rating": self.overall_rating.value,
            "overall_rationale": self.overall_rationale,
            "in_competitive_range": self.in_competitive_range,
            "competitive_range_rationale": self.competitive_range_rationale,
            "factor_evaluations": [fe.to_dict() for fe in self.factor_evaluations],
            "past_performance_confidence": self.past_performance_confidence.value if self.past_performance_confidence else None,
            "past_performance_narrative": self.past_performance_narrative,
            "all_findings": [f.to_dict() for f in self.all_findings],
            "all_strengths": [s.to_dict() for s in self.all_strengths],
            "margin_notes": self.margin_notes,
            "clarification_questions": self.clarification_questions,
            "competitive_assessment": self.competitive_assessment,
            "critiques": [c.to_dict() for c in self.critiques],
            "critique_summary": self.critique_summary.to_dict() if self.critique_summary else None,
            "deficiency_count": self.deficiency_count,
            "significant_weakness_count": self.significant_weakness_count,
            "weakness_count": self.weakness_count,
            "strength_count": self.strength_count,
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "token_usage": self.token_usage,
        }


class EvaluatorSimulatorAgent(RedTeamAgent):
    """
    The Evaluator Simulator simulates government SSEB evaluation perspective.

    Responsibilities:
    - Score strategy against likely evaluation factors
    - Identify weaknesses, deficiencies, and risks (FAR terminology)
    - Simulate evaluator margin notes
    - Flag compliance gaps
    - Distinguish between LPTA and Best Value evaluations

    The Evaluator Simulator:
    - Applies FAR source selection standards
    - Uses correct FAR weakness/deficiency terminology
    - Maps critiques to specific evaluation factors
    - Provides evaluator-perspective feedback
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Evaluator Simulator agent.

        Args:
            config: Optional agent configuration. If not provided, uses defaults.
        """
        if config is None:
            from agents.config import get_default_config
            config = get_default_config(AgentRole.EVALUATOR_SIMULATOR)

        super().__init__(config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.EVALUATOR_SIMULATOR

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.RED

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and generate evaluator perspective analysis.

        The processing mode depends on the context:
        - Full proposal evaluation (Best Value or LPTA)
        - Section-specific evaluation
        - Compliance check
        - Past performance evaluation
        - Quick mock evaluation

        Args:
            context: SwarmContext containing document content to evaluate

        Returns:
            AgentOutput with evaluator findings and ratings
        """
        start_time = time.time()

        # Validate context
        validation_errors = self.validate_context(context)
        if validation_errors:
            return self._create_output(
                success=False,
                error_message="; ".join(validation_errors),
            )

        try:
            # Determine analysis type from context
            analysis_type = context.custom_data.get("analysis_type", "full_evaluation")
            evaluation_type = context.custom_data.get("evaluation_type", "Best Value")

            if analysis_type == "section_evaluation":
                result = await self._evaluate_section(context)
            elif analysis_type == "compliance_check":
                result = await self._check_compliance(context)
            elif analysis_type == "past_performance":
                result = await self._evaluate_past_performance(context)
            elif analysis_type == "mock_evaluation":
                result = await self._mock_evaluation(context)
            else:
                # Full proposal evaluation
                result = await self._full_evaluation(context, evaluation_type)

            processing_time = int((time.time() - start_time) * 1000)
            result.processing_time_ms = processing_time

            # Generate critique summary
            if result.critiques:
                result.critique_summary = CritiqueSummary.from_critiques(
                    result.critiques,
                    document_id=context.document_id or "",
                    round_number=context.round_number,
                )

            # Build output content
            content = self._format_result_content(result)

            # Convert critiques to dict format
            critiques_dict = [c.to_dict() for c in result.critiques]

            return self._create_output(
                content=content,
                success=result.success,
                error_message=result.errors[0] if result.errors else None,
                warnings=result.warnings,
                processing_time_ms=processing_time,
                token_usage=result.token_usage,
                critiques=critiques_dict,
                metadata={
                    "analysis_type": analysis_type,
                    "evaluation_type": result.evaluation_type,
                    "overall_rating": result.overall_rating.value,
                    "in_competitive_range": result.in_competitive_range,
                    "deficiency_count": result.deficiency_count,
                    "weakness_count": result.weakness_count,
                    "strength_count": result.strength_count,
                    "factors_evaluated": len(result.factor_evaluations),
                },
            )

        except Exception as e:
            self.log_error(f"Error in Evaluator Simulator processing: {e}")
            return self._create_output(
                success=False,
                error_message=f"Processing error: {str(e)}",
            )

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate the context for Evaluator Simulator processing.

        Args:
            context: The SwarmContext to validate

        Returns:
            List of validation error messages
        """
        errors = super().validate_context(context)

        # Need document content to evaluate
        if not context.section_drafts and not context.current_draft:
            errors.append("No document content provided to evaluate")

        return errors

    async def critique_section(
        self,
        context: SwarmContext,
        section_name: str,
        section_content: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate evaluator critiques for a specific section.

        Implementation of RedTeamAgent abstract method.

        Args:
            context: The swarm context
            section_name: Name of the section to critique
            section_content: Current content of the section

        Returns:
            List of critique dictionaries
        """
        context.custom_data["analysis_type"] = "section_evaluation"
        context.custom_data["target_section"] = section_name
        context.section_drafts = {section_name: section_content}

        result = await self._evaluate_section(context)
        return [c.to_dict() for c in result.critiques]

    async def evaluate_response(
        self,
        context: SwarmContext,
        critique: Dict[str, Any],
        response: Dict[str, Any],
    ) -> bool:
        """
        Evaluate whether a blue team response adequately addresses an evaluator critique.

        Implementation of RedTeamAgent abstract method.

        Args:
            context: The swarm context
            critique: The original critique
            response: The blue team's response

        Returns:
            True if the response adequately addresses the critique
        """
        disposition = response.get("disposition", "")
        action = response.get("action", "")
        evidence = response.get("evidence", "")

        # For evaluator findings, we're strict about deficiencies
        finding_type = critique.get("severity", "")

        if "critical" in finding_type.lower() or "Deficiency" in critique.get("title", ""):
            # Deficiencies require full acceptance with action
            if disposition == "Accept" and action:
                return True
            # Cannot rebut a deficiency - it's a failure to meet requirements
            return False

        # For weaknesses, acceptance or strong rebuttal with evidence is acceptable
        if disposition == "Accept":
            return bool(action)
        elif disposition == "Rebut":
            return bool(evidence) and len(evidence) > 50
        elif disposition == "Acknowledge":
            return bool(response.get("residual_risk"))

        return False

    async def _full_evaluation(
        self,
        context: SwarmContext,
        evaluation_type: str,
    ) -> EvaluatorSimulatorResult:
        """
        Perform full proposal evaluation.

        Args:
            context: SwarmContext with document content
            evaluation_type: "LPTA" or "Best Value"

        Returns:
            EvaluatorSimulatorResult with complete evaluation
        """
        result = EvaluatorSimulatorResult(evaluation_type=evaluation_type)

        # Collect document content
        document_content = context.section_drafts.copy()
        if context.current_draft and isinstance(context.current_draft, dict):
            if "sections" in context.current_draft:
                document_content.update(context.current_draft["sections"])

        if not document_content:
            result.success = False
            result.errors.append("No document content to evaluate")
            return result

        # Get evaluation factors
        evaluation_factors = self._get_evaluation_factors(context)

        # Generate evaluation prompt
        prompt = get_evaluation_prompt(
            document_type=context.document_type or "Proposal Strategy",
            document_content=document_content,
            evaluation_type=evaluation_type,
            evaluation_factors=[f.to_dict() for f in evaluation_factors],
            company_profile=context.company_profile,
            opportunity=context.opportunity,
        )

        llm_response = await self._call_llm(
            system_prompt=EVALUATOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse the evaluation response
        self._parse_evaluation_response(content, result, evaluation_factors)

        # Convert findings to critiques
        for finding in result.all_findings:
            critique = finding.to_critique(
                agent=self.role.value,
                round_number=context.round_number,
                document_id=context.document_id or "",
            )
            result.critiques.append(critique)

        return result

    async def _evaluate_section(
        self,
        context: SwarmContext,
    ) -> EvaluatorSimulatorResult:
        """
        Evaluate a specific section.

        Args:
            context: SwarmContext with section content

        Returns:
            EvaluatorSimulatorResult with section evaluation
        """
        result = EvaluatorSimulatorResult()

        target_section = context.custom_data.get("target_section", "")
        evaluation_type = context.custom_data.get("evaluation_type", "Best Value")
        result.evaluation_type = evaluation_type

        section_content = context.section_drafts.get(target_section, "")
        if not section_content:
            result.success = False
            result.errors.append(f"No content found for section: {target_section}")
            return result

        # Find matching evaluation factor
        evaluation_factors = self._get_evaluation_factors(context)
        matching_factor = None
        for factor in evaluation_factors:
            if factor.name.lower() in target_section.lower() or target_section.lower() in factor.name.lower():
                matching_factor = factor
                break

        if not matching_factor:
            matching_factor = EvaluationFactor(name=target_section)

        # Get requirements for section
        requirements = context.custom_data.get("requirements", [])

        prompt = get_section_evaluation_prompt(
            section_name=target_section,
            section_content=section_content,
            evaluation_factor=matching_factor.to_dict(),
            evaluation_type=evaluation_type,
            requirements=requirements,
        )

        llm_response = await self._call_llm(
            system_prompt=EVALUATOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse section evaluation
        factor_eval = self._parse_section_evaluation(content, target_section)
        result.factor_evaluations = [factor_eval]
        result.all_findings = factor_eval.findings
        result.all_strengths = factor_eval.strengths
        result.overall_rating = factor_eval.rating

        # Convert to critiques
        for finding in result.all_findings:
            critique = finding.to_critique(
                agent=self.role.value,
                round_number=context.round_number,
                document_id=context.document_id or "",
            )
            result.critiques.append(critique)

        return result

    async def _check_compliance(
        self,
        context: SwarmContext,
    ) -> EvaluatorSimulatorResult:
        """
        Perform compliance check.

        Args:
            context: SwarmContext with document and requirements

        Returns:
            EvaluatorSimulatorResult with compliance findings
        """
        result = EvaluatorSimulatorResult()
        result.evaluation_type = "Compliance Check"

        document_content = context.section_drafts.copy()
        requirements = context.custom_data.get("solicitation_requirements", [])

        if not requirements:
            result.warnings.append("No solicitation requirements provided - using generic compliance check")

        prompt = get_compliance_check_prompt(
            document_content=document_content,
            solicitation_requirements=requirements,
        )

        llm_response = await self._call_llm(
            system_prompt=EVALUATOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse compliance findings
        self._parse_compliance_response(content, result)

        # Convert to critiques
        for finding in result.all_findings:
            critique = finding.to_critique(
                agent=self.role.value,
                round_number=context.round_number,
                document_id=context.document_id or "",
            )
            result.critiques.append(critique)

        return result

    async def _evaluate_past_performance(
        self,
        context: SwarmContext,
    ) -> EvaluatorSimulatorResult:
        """
        Evaluate past performance references.

        Args:
            context: SwarmContext with past performance data

        Returns:
            EvaluatorSimulatorResult with past performance evaluation
        """
        result = EvaluatorSimulatorResult()
        result.evaluation_type = "Past Performance"

        past_perf_refs = context.custom_data.get("past_performance_refs", [])
        if not past_perf_refs and context.company_profile:
            past_perf_refs = context.company_profile.get("past_performance", [])

        if not past_perf_refs:
            result.past_performance_confidence = ConfidenceLevel.NEUTRAL_CONFIDENCE
            result.past_performance_narrative = "No past performance references provided."
            result.warnings.append("No past performance references to evaluate")
            return result

        requirements = context.custom_data.get("current_requirements", {})

        prompt = get_past_performance_evaluation_prompt(
            past_performance_refs=past_perf_refs,
            requirements=requirements,
        )

        llm_response = await self._call_llm(
            system_prompt=EVALUATOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse past performance evaluation
        self._parse_past_performance_response(content, result)

        return result

    async def _mock_evaluation(
        self,
        context: SwarmContext,
    ) -> EvaluatorSimulatorResult:
        """
        Perform quick mock evaluation.

        Args:
            context: SwarmContext with document content

        Returns:
            EvaluatorSimulatorResult with quick assessment
        """
        result = EvaluatorSimulatorResult()
        result.evaluation_type = "Mock Evaluation"

        document_content = context.section_drafts.copy()
        evaluation_factors = self._get_evaluation_factors(context)

        prompt = get_mock_evaluation_prompt(
            document_content=document_content,
            evaluation_factors=[f.to_dict() for f in evaluation_factors],
        )

        llm_response = await self._call_llm(
            system_prompt=EVALUATOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse mock evaluation
        self._parse_mock_evaluation_response(content, result)

        # Convert to critiques
        for finding in result.all_findings:
            critique = finding.to_critique(
                agent=self.role.value,
                round_number=context.round_number,
                document_id=context.document_id or "",
            )
            result.critiques.append(critique)

        return result

    def _get_evaluation_factors(self, context: SwarmContext) -> List[EvaluationFactor]:
        """Get evaluation factors from context or use defaults."""
        # Check custom_data first
        custom_factors = context.custom_data.get("evaluation_factors", [])
        if custom_factors:
            return [EvaluationFactor.from_dict(f) for f in custom_factors]

        # Check opportunity
        if context.opportunity:
            opp_factors = context.opportunity.get("evaluation_factors", [])
            if opp_factors:
                return [
                    EvaluationFactor(
                        name=f.get("name", f) if isinstance(f, dict) else f,
                        weight=f.get("weight") if isinstance(f, dict) else None,
                    )
                    for f in opp_factors
                ]

        # Use default factors
        return COMMON_TECHNICAL_FACTORS + COMMON_PAST_PERFORMANCE_FACTORS

    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock evaluation content for testing."""
        prompt_lower = prompt.lower()

        if "section evaluation" in prompt_lower:
            return """### Technical Approach Evaluation

**Rating**: Acceptable

**Rating Rationale**: The proposal meets the minimum requirements for the Technical Approach factor. The solution description is adequate but lacks the level of detail and innovation that would merit a higher rating.

**Strengths**:

**Strength 1: Clear Methodology**
- **Description**: The proposal articulates a clear 5-phase methodology for system migration
- **Location**: Technical Approach, Page 3-4
- **Benefit**: Provides Government visibility into approach and milestones

**Weaknesses/Deficiencies**:

**Finding 1: Vague Risk Mitigation**
- **Type**: Weakness
- **Description**: Risk mitigation strategies are generic and not tailored to the specific system complexity
- **Requirement Affected**: PWS Section 4.2 - Risk Management Plan
- **Evidence**: "We will apply best practices" without specific identification of key risks
- **Impact**: Reduces confidence in successful execution
- **Recommendation**: Develop specific risk identification tied to system architecture with tailored mitigations

**Finding 2: Missing Performance Metrics**
- **Type**: Significant Weakness
- **Description**: No quantitative performance metrics or SLA commitments provided
- **Requirement Affected**: PWS Section 3.1 - Performance Standards
- **Evidence**: Section lacks any measurable commitments
- **Impact**: Unable to assess whether offeror understands performance expectations
- **Recommendation**: Add specific SLA commitments with measurable targets

**Evaluator Notes**:
- Need clarification on team size assumptions
- Should ask about toolset specifics
- Migration timeline seems aggressive - worth questioning in discussions"""

        elif "compliance" in prompt_lower:
            return """### Compliance Matrix

| Req # | Requirement | Compliant | Evidence/Gap | Risk |
|-------|-------------|-----------|--------------|------|
| 1 | FedRAMP High Authorization | Partial | Claims FedRAMP Moderate, not High | Deficiency |
| 2 | Key Personnel Qualifications | Yes | PM and Tech Lead resumes provided | None |
| 3 | Transition Plan | Partial | Plan provided but missing Phase 2 details | Weakness |
| 4 | Security Clearances | Yes | All personnel have required clearances | None |
| 5 | Past Performance References | Partial | Only 2 of 3 required references | Weakness |

### Non-Compliant Items

**Requirement 1: FedRAMP High Authorization**

- **Status**: Non-Compliant
- **Gap Description**: The proposed cloud environment has FedRAMP Moderate authorization but the solicitation requires FedRAMP High. This is a material failure to meet a mandatory requirement.
- **Impact**: Deficiency - This is a Go/No-Go requirement
- **Remediation Required**: Must demonstrate FedRAMP High authorization or provide approved path to authorization

**Requirement 3: Transition Plan**

- **Status**: Partially Compliant
- **Gap Description**: Transition Plan Section 2.3 (Data Migration) lacks specific validation procedures
- **Impact**: Weakness - Increases risk of data integrity issues
- **Remediation Required**: Add data validation and rollback procedures for migration

### Overall Compliance Assessment

- **Total Requirements**: 5
- **Fully Compliant**: 2
- **Partially Compliant**: 2
- **Non-Compliant**: 1
- **Recommendation**: Unacceptable for compliance - contains 1 Deficiency (FedRAMP High requirement)"""

        elif "past performance" in prompt_lower:
            return """### Reference-by-Reference Assessment

**Reference 1: DHS Cloud Migration Program**

- **Relevance Rating**: Very Relevant
- **Relevance Justification**: Similar scope (cloud migration), similar complexity, same agency (DHS). Contract value ($15M) is comparable to current requirement.
- **Quality Assessment**: CPARS rating of Exceptional indicates strong performance. Specific achievements cited (99.9% uptime, on-schedule delivery).
- **Concerns**: None identified.

**Reference 2: VA EHR Support Services**

- **Relevance Rating**: Relevant
- **Relevance Justification**: Different agency but similar technical scope. Smaller scale ($8M) reduces direct comparability but demonstrates core capability.
- **Quality Assessment**: CPARS rating of Very Good. One noted schedule issue that was resolved.
- **Concerns**: Schedule issue noted - should inquire about cause and corrective actions.

**Reference 3: DOD Network Modernization**

- **Relevance Rating**: Somewhat Relevant
- **Relevance Justification**: Different technical scope (network vs. cloud) but demonstrates large-scale federal IT experience. Value ($22M) exceeds current requirement.
- **Quality Assessment**: CPARS rating of Satisfactory. Cost control issues noted.
- **Concerns**: Cost overruns on fixed-price portion are concerning for a similar contract type.

### Overall Past Performance Assessment

**Confidence Rating**: Satisfactory Confidence

**Confidence Rationale**:
- One Very Relevant reference with Exceptional performance
- One Relevant reference with Very Good performance
- One Somewhat Relevant reference with Satisfactory performance and cost concerns
- Overall record supports expectation of successful performance, though cost control concerns warrant attention

**Evaluator Observations**:
- Would benefit from additional cloud-specific references
- Should explore cause of cost issues on DOD contract
- No references provided for subcontractor's past performance"""

        else:
            # Full evaluation
            return """### 1. Overall Evaluation Summary

**Overall Rating**: Acceptable

**In Competitive Range**: Yes

**Key Concerns**:
1. Weak risk management approach lacks specificity
2. Past performance references only partially relevant
3. Key personnel qualifications meet but don't exceed requirements

**Key Strengths**:
1. Clear understanding of agency mission and priorities
2. Proven migration methodology
3. Strong security credentials and approach

### 2. Factor-by-Factor Evaluation

**Technical Approach**

- **Rating**: Acceptable
- **Rationale**: Proposal demonstrates understanding of requirements and presents a feasible approach. However, lacks the innovation and exceeds-requirement features that would merit a higher rating.

**Strengths Identified**:
- Well-structured methodology with clear phases
- Appropriate use of automation tools
- Alignment with agency architecture standards

**Weaknesses/Deficiencies Identified**:

**Finding 1: Generic Risk Management**
- **Type**: Weakness
- **Description**: Risk management plan uses boilerplate language without tailoring to specific project risks
- **Requirement Affected**: Section L.4.2.3 - Risk Management Approach
- **Evidence**: "We will follow industry best practices" without identifying specific risks
- **Impact**: Reduces confidence in proactive risk identification
- **Recommendation**: Identify top 5 project-specific risks with tailored mitigation strategies

**Finding 2: Missing Transition Timeline**
- **Type**: Significant Weakness
- **Description**: Transition approach lacks detailed timeline with specific milestones
- **Requirement Affected**: Section L.4.3 - Transition Plan
- **Evidence**: Only high-level phases described, no week-by-week plan
- **Impact**: Unable to assess realism of transition schedule
- **Recommendation**: Provide detailed 90-day transition timeline with milestones

**Finding 3: Unsubstantiated Performance Claims**
- **Type**: Deficiency
- **Description**: Claims 99.9% uptime achievement but no supporting evidence provided
- **Requirement Affected**: Section M.2 - Verifiable Performance Claims
- **Evidence**: "We consistently achieve 99.9% uptime" with no contract reference or CPARS citation
- **Impact**: Unsubstantiated material claim - cannot be credited
- **Recommendation**: Provide specific contract references with verified performance metrics

---

**Management Approach**

- **Rating**: Good
- **Rationale**: Strong organizational structure with clear roles. Quality management approach exceeds typical proposals.

**Strengths Identified**:
- Comprehensive quality management system (ISO 9001 certified)
- Clear escalation procedures
- Dedicated QA lead with relevant certifications

**Weaknesses/Deficiencies Identified**:

**Finding 4: Subcontractor Management Gap**
- **Type**: Weakness
- **Description**: Limited detail on subcontractor oversight and integration
- **Requirement Affected**: Section L.4.4 - Subcontract Management
- **Evidence**: Only one paragraph addresses subcontractor management
- **Impact**: Unclear how subcontractor performance will be monitored
- **Recommendation**: Expand subcontractor management section with specific oversight mechanisms

---

**Past Performance**

- **Rating**: Satisfactory Confidence
- **Rationale**: References demonstrate relevant experience but quality is mixed. One Exceptional reference offset by one with noted issues.

**Strengths Identified**:
- Strong DHS reference with directly relevant scope
- Consistent schedule performance across references

**Weaknesses/Deficiencies Identified**:

**Finding 5: Cost Control Concerns**
- **Type**: Risk
- **Description**: One reference shows cost overruns on fixed-price portion
- **Requirement Affected**: Past Performance evaluation criteria
- **Evidence**: DOD contract CPARS notes "cost control challenges"
- **Impact**: Raises question about cost realism on similar contract type
- **Recommendation**: Address cost control improvements implemented since that contract

### 3. Evaluator Margin Notes

- "Show me the data" - lots of claims, limited proof
- Why only 2.5 references? Missing 3rd required reference?
- PM resume is thin on agency-specific experience
- Transition plan needs work before discussions
- Ask about the DOD cost overrun in discussions
- Innovation section feels like it was written for a different RFP

### 4. Clarification Questions

1. Please provide supporting documentation for the claimed 99.9% uptime achievement, including specific contract references and CPARS ratings.
2. Clarify the transition timeline: provide week-by-week milestones for the first 90 days.
3. Describe corrective actions implemented to address cost control issues noted in the DOD past performance reference.
4. Provide the third required past performance reference or explain why only two were submitted.
5. Detail the specific tools and automation to be used in the migration process.

### 5. Competitive Assessment

From an evaluator perspective:
- This proposal is competitive but not outstanding
- Likely in the middle of the pack on technical factors
- Deficiency in unsubstantiated claims must be resolved in discussions
- Strong competitors would have more specific, verifiable proof points
- To achieve Outstanding: add specific metrics, detailed plans, and innovation that clearly benefits Government"""

    def _parse_evaluation_response(
        self,
        content: str,
        result: EvaluatorSimulatorResult,
        factors: List[EvaluationFactor],
    ) -> None:
        """Parse full evaluation response from LLM."""
        # Parse overall rating
        rating_match = re.search(
            r'\*\*Overall Rating\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if rating_match:
            result.overall_rating = self._map_rating(rating_match.group(1).strip())

        # Parse competitive range
        range_match = re.search(
            r'\*\*In Competitive Range\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if range_match:
            result.in_competitive_range = "yes" in range_match.group(1).lower()

        # Parse factor evaluations
        for factor in factors:
            factor_eval = self._parse_factor_section(content, factor.name)
            if factor_eval:
                result.factor_evaluations.append(factor_eval)
                result.all_findings.extend(factor_eval.findings)
                result.all_strengths.extend(factor_eval.strengths)

        # Parse margin notes
        notes_match = re.search(
            r'###\s*3\.\s*Evaluator Margin Notes\s*([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )
        if notes_match:
            notes_text = notes_match.group(1)
            result.margin_notes = [
                line.strip().lstrip('-•').strip()
                for line in notes_text.split('\n')
                if line.strip() and line.strip().startswith(('-', '•', '"'))
            ]

        # Parse clarification questions
        questions_match = re.search(
            r'###\s*4\.\s*Clarification Questions\s*([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )
        if questions_match:
            questions_text = questions_match.group(1)
            result.clarification_questions = [
                re.sub(r'^\d+\.\s*', '', line.strip())
                for line in questions_text.split('\n')
                if line.strip() and re.match(r'\d+\.', line.strip())
            ]

        # Parse competitive assessment
        assessment_match = re.search(
            r'###\s*5\.\s*Competitive Assessment\s*([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )
        if assessment_match:
            result.competitive_assessment = assessment_match.group(1).strip()

        # Determine overall rationale
        if result.deficiency_count > 0:
            result.overall_rationale = (
                f"Proposal contains {result.deficiency_count} deficiency(ies) that must be "
                "resolved. Currently not acceptable for award without correction."
            )
            result.in_competitive_range = False
        elif result.significant_weakness_count > 0:
            result.overall_rationale = (
                f"Proposal has {result.significant_weakness_count} significant weakness(es) "
                "that increase risk of unsuccessful performance."
            )
        else:
            result.overall_rationale = (
                f"Proposal rated {result.overall_rating.value}. "
                f"Identified {result.strength_count} strengths and {result.weakness_count} weaknesses."
            )

    def _parse_factor_section(
        self,
        content: str,
        factor_name: str,
    ) -> Optional[FactorEvaluation]:
        """Parse evaluation for a specific factor."""
        # Find factor section
        pattern = rf'\*\*{re.escape(factor_name)}\*\*\s*([\s\S]*?)(?=\*\*[A-Z]|---|\n\n###|$)'
        match = re.search(pattern, content, re.IGNORECASE)

        if not match:
            return None

        section = match.group(1)

        # Extract rating
        rating_match = re.search(r'\*\*Rating\*\*[:\s]*([^\n]+)', section, re.IGNORECASE)
        rating = self._map_rating(rating_match.group(1).strip()) if rating_match else RatingLevel.ACCEPTABLE

        # Extract rationale
        rationale_match = re.search(r'\*\*Rationale\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)', section, re.IGNORECASE)
        rationale = rationale_match.group(1).strip() if rationale_match else ""

        factor_eval = FactorEvaluation(
            factor_name=factor_name,
            rating=rating,
            rating_rationale=rationale,
        )

        # Parse findings
        finding_sections = re.split(r'\*\*Finding\s*\d+[:\s]*', section, flags=re.IGNORECASE)
        for finding_section in finding_sections[1:]:
            finding = self._parse_finding(finding_section, factor_name)
            if finding:
                factor_eval.findings.append(finding)

        # Parse strengths (simpler structure)
        strength_match = re.search(
            r'\*\*Strengths?\s*(?:Identified)?\*\*[:\s]*([\s\S]*?)(?=\*\*(?:Weakness|Finding)|$)',
            section,
            re.IGNORECASE
        )
        if strength_match:
            strength_lines = re.findall(r'[-•]\s*([^\n]+)', strength_match.group(1))
            for line in strength_lines:
                factor_eval.strengths.append(EvaluatorStrength(
                    factor=factor_name,
                    title=line[:50],
                    description=line,
                ))

        return factor_eval

    def _parse_finding(
        self,
        section: str,
        factor_name: str,
    ) -> Optional[EvaluatorFinding]:
        """Parse a single finding from section content."""
        try:
            # Extract title
            title_match = re.match(r'^([^\n]+)', section.strip())
            title = title_match.group(1).strip() if title_match else "Finding"

            # Extract type
            type_match = re.search(r'\*\*Type\*\*[:\s]*([^\n]+)', section, re.IGNORECASE)
            finding_type_str = type_match.group(1).strip() if type_match else "Weakness"
            finding_type = self._map_weakness_type(finding_type_str)

            # Extract description
            desc_match = re.search(r'\*\*Description\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)', section, re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else ""

            # Extract requirement
            req_match = re.search(r'\*\*Requirement.*?\*\*[:\s]*([^\n]+)', section, re.IGNORECASE)
            requirement = req_match.group(1).strip() if req_match else ""

            # Extract evidence
            evidence_match = re.search(r'\*\*Evidence.*?\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)', section, re.IGNORECASE)
            evidence = evidence_match.group(1).strip() if evidence_match else ""

            # Extract impact
            impact_match = re.search(r'\*\*Impact\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)', section, re.IGNORECASE)
            impact = impact_match.group(1).strip() if impact_match else ""

            # Extract recommendation
            rec_match = re.search(r'\*\*Recommendation\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)', section, re.IGNORECASE)
            recommendation = rec_match.group(1).strip() if rec_match else ""

            return EvaluatorFinding(
                finding_type=finding_type,
                factor=factor_name,
                title=title,
                description=description,
                requirement_affected=requirement,
                evidence_location=evidence,
                impact=impact,
                recommendation=recommendation,
            )

        except Exception as e:
            self.log_warning(f"Failed to parse finding: {e}")
            return None

    def _parse_section_evaluation(
        self,
        content: str,
        section_name: str,
    ) -> FactorEvaluation:
        """Parse section-specific evaluation response."""
        # Extract rating
        rating_match = re.search(r'\*\*Rating\*\*[:\s]*([^\n]+)', content, re.IGNORECASE)
        rating = self._map_rating(rating_match.group(1).strip()) if rating_match else RatingLevel.ACCEPTABLE

        # Extract rationale
        rationale_match = re.search(r'\*\*Rating Rationale\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)', content, re.IGNORECASE)
        rationale = rationale_match.group(1).strip() if rationale_match else ""

        factor_eval = FactorEvaluation(
            factor_name=section_name,
            rating=rating,
            rating_rationale=rationale,
        )

        # Parse findings
        finding_sections = re.split(r'\*\*Finding\s*\d+[:\s]*', content, flags=re.IGNORECASE)
        for finding_section in finding_sections[1:]:
            finding = self._parse_finding(finding_section, section_name)
            if finding:
                factor_eval.findings.append(finding)

        # Parse strengths
        strength_match = re.search(
            r'\*\*Strength\s*\d+[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if strength_match:
            factor_eval.strengths.append(EvaluatorStrength(
                factor=section_name,
                title=strength_match.group(1).strip()[:50],
                description=strength_match.group(1).strip(),
            ))

        # Parse evaluator notes
        notes_match = re.search(
            r'\*\*Evaluator Notes\*\*[:\s]*([\s\S]*?)(?=\n\n|$)',
            content,
            re.IGNORECASE
        )
        if notes_match:
            notes_text = notes_match.group(1)
            factor_eval.evaluator_notes = [
                line.strip().lstrip('-•').strip()
                for line in notes_text.split('\n')
                if line.strip().startswith(('-', '•'))
            ]

        return factor_eval

    def _parse_compliance_response(
        self,
        content: str,
        result: EvaluatorSimulatorResult,
    ) -> None:
        """Parse compliance check response."""
        # Find non-compliant items section
        non_compliant_match = re.search(
            r'###\s*Non-Compliant Items\s*([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )

        if non_compliant_match:
            section = non_compliant_match.group(1)

            # Parse each non-compliant requirement
            req_sections = re.split(r'\*\*Requirement\s*\d+[:\s]*', section, flags=re.IGNORECASE)

            for req_section in req_sections[1:]:
                title_match = re.match(r'^([^\n]+)', req_section.strip())
                title = title_match.group(1).strip() if title_match else "Requirement"

                # Determine finding type
                if "deficiency" in req_section.lower():
                    finding_type = WeaknessType.DEFICIENCY
                elif "non-compliant" in req_section.lower():
                    finding_type = WeaknessType.DEFICIENCY
                else:
                    finding_type = WeaknessType.WEAKNESS

                # Extract gap description
                gap_match = re.search(r'\*\*Gap Description\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)', req_section, re.IGNORECASE)
                description = gap_match.group(1).strip() if gap_match else ""

                # Extract remediation
                rem_match = re.search(r'\*\*Remediation.*?\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)', req_section, re.IGNORECASE)
                recommendation = rem_match.group(1).strip() if rem_match else ""

                finding = EvaluatorFinding(
                    finding_type=finding_type,
                    factor="Compliance",
                    title=f"Compliance: {title}",
                    description=description,
                    requirement_affected=title,
                    recommendation=recommendation,
                )
                result.all_findings.append(finding)

        # Determine overall compliance
        if result.deficiency_count > 0:
            result.overall_rating = RatingLevel.UNACCEPTABLE
            result.in_competitive_range = False
        else:
            result.overall_rating = RatingLevel.ACCEPTABLE

    def _parse_past_performance_response(
        self,
        content: str,
        result: EvaluatorSimulatorResult,
    ) -> None:
        """Parse past performance evaluation response."""
        # Extract confidence rating
        confidence_match = re.search(
            r'\*\*Confidence Rating\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if confidence_match:
            confidence_text = confidence_match.group(1).strip().lower()
            if "substantial" in confidence_text:
                result.past_performance_confidence = ConfidenceLevel.SUBSTANTIAL_CONFIDENCE
            elif "satisfactory" in confidence_text:
                result.past_performance_confidence = ConfidenceLevel.SATISFACTORY_CONFIDENCE
            elif "neutral" in confidence_text:
                result.past_performance_confidence = ConfidenceLevel.NEUTRAL_CONFIDENCE
            elif "limited" in confidence_text:
                result.past_performance_confidence = ConfidenceLevel.LIMITED_CONFIDENCE
            elif "no confidence" in confidence_text:
                result.past_performance_confidence = ConfidenceLevel.NO_CONFIDENCE

        # Extract rationale
        rationale_match = re.search(
            r'\*\*Confidence Rationale\*\*[:\s]*([\s\S]*?)(?=\*\*|###|$)',
            content,
            re.IGNORECASE
        )
        if rationale_match:
            result.past_performance_narrative = rationale_match.group(1).strip()

    def _parse_mock_evaluation_response(
        self,
        content: str,
        result: EvaluatorSimulatorResult,
    ) -> None:
        """Parse mock evaluation response."""
        # Parse top concerns as findings
        concerns_match = re.search(
            r'###\s*Top 3 Concerns.*?\n([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )
        if concerns_match:
            concerns_text = concerns_match.group(1)
            concern_lines = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*[:\s]*([^-\n]+)(?:\s*-\s*\[?([^\]\n]+)\]?)?', concerns_text)

            for title, description, classification in concern_lines:
                finding_type = self._map_weakness_type(classification or "Weakness")
                result.all_findings.append(EvaluatorFinding(
                    finding_type=finding_type,
                    factor="Overall",
                    title=title.strip(),
                    description=description.strip(),
                ))

        # Parse strengths
        strengths_match = re.search(
            r'###\s*Top 3 Strengths.*?\n([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )
        if strengths_match:
            strengths_text = strengths_match.group(1)
            strength_lines = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*[:\s]*([^\n]+)', strengths_text)

            for title, description in strength_lines:
                result.all_strengths.append(EvaluatorStrength(
                    factor="Overall",
                    title=title.strip(),
                    description=description.strip(),
                ))

    def _map_rating(self, rating_str: str) -> RatingLevel:
        """Map string to RatingLevel enum."""
        rating_lower = rating_str.lower()
        if "outstanding" in rating_lower or "exceptional" in rating_lower:
            return RatingLevel.OUTSTANDING
        elif "good" in rating_lower or "very good" in rating_lower:
            return RatingLevel.GOOD
        # Check unacceptable BEFORE acceptable since "unacceptable" contains "acceptable"
        elif "unacceptable" in rating_lower or "unsatisfactory" in rating_lower:
            return RatingLevel.UNACCEPTABLE
        elif "acceptable" in rating_lower or "satisfactory" in rating_lower:
            return RatingLevel.ACCEPTABLE
        elif "marginal" in rating_lower:
            return RatingLevel.MARGINAL
        else:
            return RatingLevel.ACCEPTABLE

    def _map_weakness_type(self, type_str: str) -> WeaknessType:
        """Map string to WeaknessType enum."""
        type_lower = type_str.lower()
        if "deficiency" in type_lower:
            return WeaknessType.DEFICIENCY
        elif "significant" in type_lower:
            return WeaknessType.SIGNIFICANT_WEAKNESS
        elif "risk" in type_lower:
            return WeaknessType.RISK
        else:
            return WeaknessType.WEAKNESS

    def _format_result_content(self, result: EvaluatorSimulatorResult) -> str:
        """Format result as content string."""
        parts = ["# Government Evaluator Simulation", ""]

        # Evaluation type
        parts.append(f"**Evaluation Type**: {result.evaluation_type}")
        parts.append("")

        # Overall assessment
        parts.append("## Overall Assessment")
        parts.append("")
        parts.append(f"**Rating**: {result.overall_rating.value}")
        parts.append(f"**In Competitive Range**: {'Yes' if result.in_competitive_range else 'No'}")
        parts.append("")
        parts.append(result.overall_rationale)
        parts.append("")

        # Summary stats
        parts.append("## Evaluation Summary")
        parts.append("")
        parts.append(f"- **Deficiencies**: {result.deficiency_count}")
        parts.append(f"- **Significant Weaknesses**: {result.significant_weakness_count - result.deficiency_count}")
        parts.append(f"- **Weaknesses**: {result.weakness_count - result.significant_weakness_count}")
        parts.append(f"- **Strengths**: {result.strength_count}")
        parts.append("")

        # Factor evaluations
        if result.factor_evaluations:
            parts.append("## Factor-by-Factor Evaluation")
            parts.append("")

            for factor_eval in result.factor_evaluations:
                parts.append(f"### {factor_eval.factor_name}")
                parts.append("")
                parts.append(f"**Rating**: {factor_eval.rating.value}")
                if factor_eval.rating_rationale:
                    parts.append(f"**Rationale**: {factor_eval.rating_rationale}")
                parts.append("")

                if factor_eval.strengths:
                    parts.append("**Strengths**:")
                    for strength in factor_eval.strengths:
                        parts.append(f"- {strength.description}")
                    parts.append("")

                if factor_eval.findings:
                    parts.append("**Findings**:")
                    for finding in factor_eval.findings:
                        parts.append(f"- **[{finding.finding_type.value}]** {finding.title}")
                        parts.append(f"  - {finding.description}")
                    parts.append("")

                parts.append("---")
                parts.append("")

        # Past performance
        if result.past_performance_confidence:
            parts.append("## Past Performance Assessment")
            parts.append("")
            parts.append(f"**Confidence**: {result.past_performance_confidence.value}")
            if result.past_performance_narrative:
                parts.append(f"**Narrative**: {result.past_performance_narrative}")
            parts.append("")

        # Evaluator margin notes
        if result.margin_notes:
            parts.append("## Evaluator Margin Notes")
            parts.append("")
            for note in result.margin_notes:
                parts.append(f"- {note}")
            parts.append("")

        # Clarification questions
        if result.clarification_questions:
            parts.append("## Clarification Questions")
            parts.append("")
            for i, question in enumerate(result.clarification_questions, 1):
                parts.append(f"{i}. {question}")
            parts.append("")

        # Competitive assessment
        if result.competitive_assessment:
            parts.append("## Competitive Assessment")
            parts.append("")
            parts.append(result.competitive_assessment)
            parts.append("")

        return "\n".join(parts)
