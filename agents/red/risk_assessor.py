"""
Risk Assessor Agent

Red team agent that identifies failure modes, stress-tests assumptions,
and develops worst-case scenarios for GovCon strategy documents.
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
from agents.utils import DataclassMixin

from models.critique import Critique, ChallengeType, Severity, CritiqueSummary

from .risk_taxonomy import (
    Risk,
    RiskCategory,
    Probability,
    Impact,
    MitigationStatus,
    WorstCaseScenario,
    RiskRegister,
    identify_risk_category,
)

from .prompts.risk_assessor_prompts import (
    RISK_ASSESSOR_SYSTEM_PROMPT,
    get_risk_assessment_prompt,
    get_section_risk_prompt,
    get_worst_case_scenario_prompt,
    get_stress_test_prompt,
    get_mitigation_evaluation_prompt,
    get_risk_response_evaluation_prompt,
)


@dataclass
class StressTestResult(DataclassMixin):
    """Result of stress-testing an assumption."""

    assumption: str
    source: str = ""
    stress_scenario: str = ""
    strategy_impact: str = ""
    win_probability_effect: str = ""
    vulnerability_level: str = "Medium"  # Low, Medium, High, Critical
    early_warning_indicators: List[str] = field(default_factory=list)
    contingency_recommendation: str = ""


@dataclass
class MitigationEvaluation(DataclassMixin):
    """Evaluation of a proposed risk mitigation."""

    risk_id: str
    verdict: str = "Insufficient"  # Adequate, Insufficient, Partially Adequate
    effectiveness_assessment: str = ""
    feasibility_assessment: str = ""
    new_probability: str = ""
    new_impact: str = ""
    gaps_identified: List[str] = field(default_factory=list)
    improvement_recommendations: List[str] = field(default_factory=list)
    new_risks_created: List[str] = field(default_factory=list)


@dataclass
class ResponseEvaluation(DataclassMixin):
    """Evaluation of a blue team's response to a risk."""

    risk_id: str
    verdict: str = "Insufficient"  # Acceptable, Insufficient, Partially Acceptable
    reasoning: str = ""
    residual_probability: str = ""
    residual_impact: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    follow_up_required: bool = False
    follow_up_details: str = ""
    resolution_status: str = "Needs Further Work"  # Resolved, Needs Further Work, Escalate


@dataclass
class RiskAssessorResult(DataclassMixin):
    """Result of Risk Assessor analysis operations."""

    # Primary outputs
    risks: List[Risk] = field(default_factory=list)
    worst_case_scenarios: List[WorstCaseScenario] = field(default_factory=list)
    stress_test_results: List[StressTestResult] = field(default_factory=list)
    mitigation_evaluations: List[MitigationEvaluation] = field(default_factory=list)
    response_evaluations: List[ResponseEvaluation] = field(default_factory=list)

    # Critiques generated from risks
    critiques: List[Critique] = field(default_factory=list)

    # Summary
    risk_register: Optional[RiskRegister] = None
    overall_assessment: str = ""

    # Meta
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)


class RiskAssessorAgent(RedTeamAgent):
    """
    The Risk Assessor identifies failure modes and stress-tests assumptions.

    Responsibilities:
    - Identify risks across categories (execution, compliance, competitive, financial)
    - Assess probability and impact of each risk
    - Require mitigation strategies for high risks
    - Develop worst-case scenarios
    - Stress-test key assumptions
    - Evaluate proposed mitigations and responses

    The Risk Assessor is:
    - Cautiously pessimistic but not paranoid
    - Thorough in risk identification
    - Practical about mitigation requirements
    - Focused on actionable risk management
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Risk Assessor agent.

        Args:
            config: Optional agent configuration. If not provided, uses defaults.
        """
        if config is None:
            from agents.config import get_default_config
            config = get_default_config(AgentRole.RISK_ASSESSOR)

        super().__init__(config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.RISK_ASSESSOR

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.RED

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and perform risk assessment.

        The processing mode depends on the context:
        - Full risk assessment
        - Section-specific risk assessment
        - Worst-case scenario development
        - Assumption stress testing
        - Mitigation evaluation
        - Response evaluation

        Args:
            context: SwarmContext containing document content to assess

        Returns:
            AgentOutput with risks and analysis
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
            analysis_type = context.custom_data.get("analysis_type", "full_assessment")

            if analysis_type == "section_assessment":
                result = await self._assess_section_risks(context)
            elif analysis_type == "worst_case":
                result = await self._develop_worst_case_scenarios(context)
            elif analysis_type == "stress_test":
                result = await self._stress_test_assumptions(context)
            elif analysis_type == "mitigation_evaluation":
                result = await self._evaluate_mitigations(context)
            elif analysis_type == "response_evaluation":
                result = await self._evaluate_responses(context)
            else:
                # Full risk assessment
                result = await self._perform_full_assessment(context)

            processing_time = int((time.time() - start_time) * 1000)
            result.processing_time_ms = processing_time

            # Generate risk register
            if result.risks:
                result.risk_register = RiskRegister(
                    document_id=context.document_id or "",
                    opportunity_id=context.opportunity.get("id", "") if context.opportunity else "",
                    risks=result.risks,
                    worst_case_scenarios=result.worst_case_scenarios,
                )

            # Convert risks to critiques for integration with debate workflow
            result.critiques = self._risks_to_critiques(result.risks, context)

            # Generate critique summary if we have critiques
            critique_summary = None
            if result.critiques:
                critique_summary = CritiqueSummary.from_critiques(
                    result.critiques,
                    document_id=context.document_id or "",
                    round_number=context.round_number,
                )

            # Build output content
            content = self._format_result_content(result, analysis_type)

            # Convert critiques to dict format for AgentOutput
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
                    "total_risks": len(result.risks),
                    "critical_risks": sum(1 for r in result.risks if r.risk_level == "critical"),
                    "high_risks": sum(1 for r in result.risks if r.risk_level == "high"),
                    "medium_risks": sum(1 for r in result.risks if r.risk_level == "medium"),
                    "worst_case_count": len(result.worst_case_scenarios),
                    "stress_test_count": len(result.stress_test_results),
                    "risks_requiring_mitigation": sum(
                        1 for r in result.risks if r.mitigation_required
                    ),
                    "risks_requiring_human_review": sum(
                        1 for r in result.risks if r.requires_human_review
                    ),
                    "overall_risk_level": (
                        result.risk_register.overall_risk_level
                        if result.risk_register
                        else "Unknown"
                    ),
                },
            )

        except Exception as e:
            self.log_error(f"Error in Risk Assessor processing: {e}")
            return self._create_output(
                success=False,
                error_message=f"Processing error: {str(e)}",
            )

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate the context for Risk Assessor processing.

        Args:
            context: The SwarmContext to validate

        Returns:
            List of validation error messages
        """
        errors = super().validate_context(context)

        # Need either section drafts or current draft to assess
        if not context.section_drafts and not context.current_draft:
            errors.append("No document content provided to assess")

        return errors

    async def critique_section(
        self,
        context: SwarmContext,
        section_name: str,
        section_content: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate risk-based critiques for a specific section.

        Implementation of RedTeamAgent abstract method.

        Args:
            context: The swarm context
            section_name: Name of the section to assess
            section_content: Current content of the section

        Returns:
            List of critique dictionaries
        """
        # Set up context for section assessment
        context.custom_data["analysis_type"] = "section_assessment"
        context.custom_data["target_section"] = section_name
        context.section_drafts = {section_name: section_content}

        result = await self._assess_section_risks(context)
        return [c.to_dict() for c in result.critiques]

    async def evaluate_response(
        self,
        context: SwarmContext,
        critique: Dict[str, Any],
        response: Dict[str, Any],
    ) -> bool:
        """
        Evaluate whether a blue team response adequately addresses a risk critique.

        Implementation of RedTeamAgent abstract method.

        Args:
            context: The swarm context
            critique: The original critique (risk-based)
            response: The blue team's response

        Returns:
            True if the response is acceptable, False otherwise
        """
        # Set up context for response evaluation
        context.custom_data["analysis_type"] = "response_evaluation"
        context.custom_data["risks_to_evaluate"] = [critique]
        context.custom_data["responses"] = [response]

        result = await self._evaluate_responses(context)

        if result.response_evaluations:
            evaluation = result.response_evaluations[0]
            return evaluation.verdict == "Acceptable"

        return False

    async def _perform_full_assessment(
        self,
        context: SwarmContext,
    ) -> RiskAssessorResult:
        """
        Perform comprehensive risk assessment of the document.

        Args:
            context: SwarmContext with document content

        Returns:
            RiskAssessorResult with all identified risks
        """
        result = RiskAssessorResult()

        # Collect document content
        document_content = context.section_drafts.copy()
        if context.current_draft and isinstance(context.current_draft, dict):
            if "sections" in context.current_draft:
                document_content.update(context.current_draft["sections"])

        if not document_content:
            result.success = False
            result.errors.append("No document content to assess")
            return result

        # Get focus categories if specified
        focus_categories = context.custom_data.get("focus_categories", [])

        prompt = get_risk_assessment_prompt(
            document_type=context.document_type or "Strategy Document",
            document_content=document_content,
            company_profile=context.company_profile,
            opportunity=context.opportunity,
            focus_categories=focus_categories if focus_categories else None,
        )

        llm_response = await self._call_llm(
            system_prompt=RISK_ASSESSOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.risks = self._parse_risks(
            content,
            document_id=context.document_id or "",
            round_number=context.round_number,
        )
        result.token_usage = llm_response.get("usage", {})

        # Generate overall assessment
        result.overall_assessment = self._generate_overall_assessment(result.risks)

        # If we have high-severity risks, develop worst-case scenarios
        high_risks = [r for r in result.risks if r.risk_level in {"critical", "high"}]
        if high_risks and context.custom_data.get("include_worst_case", True):
            scenarios = await self._generate_worst_case_scenarios(
                high_risks,
                context.opportunity,
            )
            result.worst_case_scenarios = scenarios

        return result

    async def _assess_section_risks(
        self,
        context: SwarmContext,
    ) -> RiskAssessorResult:
        """
        Assess risks for specific sections.

        Args:
            context: SwarmContext with section content

        Returns:
            RiskAssessorResult with section risks
        """
        result = RiskAssessorResult()

        target_section = context.custom_data.get("target_section")
        if target_section:
            sections_to_assess = {target_section: context.section_drafts.get(target_section, "")}
        else:
            sections_to_assess = context.section_drafts

        for section_name, section_content in sections_to_assess.items():
            if not section_content:
                result.warnings.append(f"Section '{section_name}' is empty, skipping")
                continue

            prompt = get_section_risk_prompt(
                section_name=section_name,
                section_content=section_content,
                document_type=context.document_type or "Strategy Document",
                opportunity=context.opportunity,
            )

            llm_response = await self._call_llm(
                system_prompt=RISK_ASSESSOR_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            if llm_response.get("success"):
                content = llm_response.get("content", "")
                section_risks = self._parse_risks(
                    content,
                    document_id=context.document_id or "",
                    round_number=context.round_number,
                    default_section=section_name,
                )
                result.risks.extend(section_risks)

                # Update token usage
                for key, value in llm_response.get("usage", {}).items():
                    result.token_usage[key] = result.token_usage.get(key, 0) + value
            else:
                result.warnings.append(f"Failed to assess section '{section_name}'")

        return result

    async def _develop_worst_case_scenarios(
        self,
        context: SwarmContext,
    ) -> RiskAssessorResult:
        """
        Develop worst-case scenarios from identified risks.

        Args:
            context: SwarmContext with risks

        Returns:
            RiskAssessorResult with worst-case scenarios
        """
        result = RiskAssessorResult()

        risks = context.custom_data.get("risks", [])
        if not risks:
            # First perform risk assessment
            assessment = await self._perform_full_assessment(context)
            result.risks = assessment.risks
            risks = [r.to_dict() for r in assessment.risks]

        if not risks:
            result.warnings.append("No risks identified for scenario development")
            return result

        scenarios = await self._generate_worst_case_scenarios(
            risks if isinstance(risks[0], Risk) else [Risk.from_dict(r) for r in risks],
            context.opportunity,
        )
        result.worst_case_scenarios = scenarios

        return result

    async def _generate_worst_case_scenarios(
        self,
        risks: List[Risk],
        opportunity: Optional[Dict[str, Any]],
    ) -> List[WorstCaseScenario]:
        """
        Generate worst-case scenarios from risks.

        Args:
            risks: List of identified risks
            opportunity: Optional opportunity context

        Returns:
            List of worst-case scenarios
        """
        prompt = get_worst_case_scenario_prompt(
            risks=[r.to_dict() if isinstance(r, Risk) else r for r in risks],
            opportunity=opportunity,
        )

        llm_response = await self._call_llm(
            system_prompt=RISK_ASSESSOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            return []

        content = llm_response.get("content", "")
        return self._parse_worst_case_scenarios(content)

    async def _stress_test_assumptions(
        self,
        context: SwarmContext,
    ) -> RiskAssessorResult:
        """
        Stress-test strategy assumptions.

        Args:
            context: SwarmContext with assumptions

        Returns:
            RiskAssessorResult with stress test results
        """
        result = RiskAssessorResult()

        assumptions = context.custom_data.get("assumptions", [])
        if not assumptions:
            # Extract assumptions from document
            assumptions = self._extract_assumptions(context.section_drafts)

        if not assumptions:
            result.warnings.append("No assumptions identified for stress testing")
            return result

        # Get strategy summary
        strategy_summary = context.custom_data.get(
            "strategy_summary",
            self._extract_strategy_summary(context.section_drafts),
        )

        prompt = get_stress_test_prompt(
            assumptions=assumptions,
            strategy_summary=strategy_summary,
            opportunity=context.opportunity,
        )

        llm_response = await self._call_llm(
            system_prompt=RISK_ASSESSOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.stress_test_results = self._parse_stress_tests(content)
        result.token_usage = llm_response.get("usage", {})

        # Convert high-vulnerability stress tests to risks
        for stress_test in result.stress_test_results:
            if stress_test.vulnerability_level in {"high", "critical"}:
                risk = Risk(
                    category=RiskCategory.STRATEGIC,
                    title=f"Assumption Vulnerability: {stress_test.assumption[:50]}...",
                    description=stress_test.stress_scenario,
                    consequence=stress_test.strategy_impact,
                    probability=Probability.MEDIUM,
                    impact=Impact.HIGH if stress_test.vulnerability_level == "high" else Impact.CATASTROPHIC,
                    source_content=stress_test.assumption,
                    suggested_mitigation=stress_test.contingency_recommendation,
                    identified_by=self.role.value,
                    round_number=context.round_number,
                )
                result.risks.append(risk)

        return result

    async def _evaluate_mitigations(
        self,
        context: SwarmContext,
    ) -> RiskAssessorResult:
        """
        Evaluate proposed risk mitigations.

        Args:
            context: SwarmContext with risks and mitigations

        Returns:
            RiskAssessorResult with mitigation evaluations
        """
        result = RiskAssessorResult()

        risks_to_evaluate = context.custom_data.get("risks_to_evaluate", [])
        mitigations = context.custom_data.get("mitigations", [])

        # Match risks to mitigations
        mitigation_map = {m.get("risk_id"): m for m in mitigations}

        for risk in risks_to_evaluate:
            risk_id = risk.get("id", "")
            mitigation = mitigation_map.get(risk_id)

            if not mitigation:
                result.warnings.append(f"No mitigation found for risk {risk_id}")
                continue

            prompt = get_mitigation_evaluation_prompt(
                risk=risk,
                proposed_mitigation=mitigation,
            )

            llm_response = await self._call_llm(
                system_prompt=RISK_ASSESSOR_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            if llm_response.get("success"):
                content = llm_response.get("content", "")
                evaluation = self._parse_mitigation_evaluation(content, risk_id)
                result.mitigation_evaluations.append(evaluation)

                # Update token usage
                for key, value in llm_response.get("usage", {}).items():
                    result.token_usage[key] = result.token_usage.get(key, 0) + value
            else:
                result.warnings.append(f"Failed to evaluate mitigation for risk {risk_id}")

        return result

    async def _evaluate_responses(
        self,
        context: SwarmContext,
    ) -> RiskAssessorResult:
        """
        Evaluate blue team responses to risks.

        Args:
            context: SwarmContext with risks and responses

        Returns:
            RiskAssessorResult with response evaluations
        """
        result = RiskAssessorResult()

        risks_to_evaluate = context.custom_data.get("risks_to_evaluate", [])
        responses = context.custom_data.get("responses", [])

        # Match risks to responses
        response_map = {r.get("risk_id", r.get("critique_id")): r for r in responses}

        for risk in risks_to_evaluate:
            risk_id = risk.get("id", "")
            response = response_map.get(risk_id)

            if not response:
                result.warnings.append(f"No response found for risk {risk_id}")
                continue

            prompt = get_risk_response_evaluation_prompt(
                risk=risk,
                response=response,
            )

            llm_response = await self._call_llm(
                system_prompt=RISK_ASSESSOR_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            if llm_response.get("success"):
                content = llm_response.get("content", "")
                evaluation = self._parse_response_evaluation(content, risk_id)
                result.response_evaluations.append(evaluation)

                # Update token usage
                for key, value in llm_response.get("usage", {}).items():
                    result.token_usage[key] = result.token_usage.get(key, 0) + value
            else:
                result.warnings.append(f"Failed to evaluate response for risk {risk_id}")

        return result

    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock risk content for testing."""
        prompt_lower = prompt.lower()

        if "task: worst-case scenario" in prompt_lower:
            return """### Worst-Case Scenario 1: Incumbent Price War with Staffing Crisis

**Narrative**: The incumbent, sensing our competitive threat, dramatically underprices their recompete bid while simultaneously poaching our key proposed personnel. Our PM accepts a counter-offer two weeks before proposal submission, forcing a last-minute substitution that weakens our Management approach. Meanwhile, the incumbent's aggressive pricing creates a 15% gap that our technical advantages cannot overcome in the Best Value tradeoff. We lose the competition and the invested BD resources, while also losing key personnel to a competitor.

**Trigger Chain**:
1. Incumbent learns of our aggressive capture efforts and responds with defensive pricing
2. Our key personnel become targets for competitive recruiting
3. Proposed PM receives attractive counter-offer from incumbent
4. PM departure forces emergency personnel substitution
5. Substitute PM has weaker qualifications, reducing technical score
6. Combined with price gap, we fall outside the competitive range

**Contributing Risks**: Risk 1, Risk 3, Risk 5

**Impacts**:
- **Win Probability**: Reduced from 55% to <15%
- **Financial**: ~$150K in BD costs with no return; potential loss of key performer permanently
- **Reputation**: Internal perception of inability to retain talent; market perception as non-competitive bidder
- **Strategic**: Sets back agency relationship building by 2-3 years

**Early Warning Signs**:
- Incumbent increases engagement with agency ahead of RFP
- Key personnel receive unexpected retention bonuses at current employers
- Market intelligence suggests incumbent preparing aggressive bid
- Personnel express concerns about opportunity timing or company commitment

**Prevention Measures**:
- Secure written commitments from key personnel with financial incentives
- Monitor incumbent activity and have pricing contingency plans
- Build relationships with multiple qualified candidates for critical positions
- Develop "Plan B" technical approach that doesn't rely on specific individuals

**Recovery Options** (if worst case occurs):
- Preserve agency relationship for future opportunities
- Document lessons learned for future captures
- Retain remaining team for next opportunity
- Consider protest if procurement irregularities are identified

**Plausibility**: Medium

**Severity**: High

---

### Worst-Case Scenario 2: Compliance Disqualification

**Narrative**: During proposal preparation, we discover that our 8(a) certification is set to expire 60 days after contract award, and the SBA has signaled they will not extend. Rather than addressing this proactively, we submit the proposal hoping for clarification during discussions. The Contracting Officer issues a determination that we are ineligible for the set-aside, and our proposal is rejected without evaluation. The opportunity, which we had positioned as our top pursuit, is lost before any substantive evaluation of our merits.

**Trigger Chain**:
1. 8(a) certification approaching expiration is not surfaced during opportunity qualification
2. Capture team proceeds without validating set-aside eligibility timeline
3. Proposal is submitted with certification status unclear
4. CO requests eligibility documentation
5. We cannot demonstrate eligibility for full period of performance
6. Proposal is rejected as non-responsive to set-aside requirement

**Contributing Risks**: Risk 2, Risk 4

**Impacts**:
- **Win Probability**: Reduced to 0% - complete disqualification
- **Financial**: Total loss of BD investment; potential penalties if misrepresentation is alleged
- **Reputation**: Damaged credibility with agency; questions about our compliance rigor
- **Strategic**: Loss of key agency relationship; internal trust in BD/compliance processes

**Early Warning Signs**:
- Certification status not reviewed during pursuit qualification
- Set-aside requirements not validated against company eligibility timeline
- Compliance Navigator not engaged early in capture process
- Questions about eligibility are deferred rather than resolved

**Prevention Measures**:
- Mandatory compliance review at opportunity qualification gate
- Track all certification expirations with 12-month early warning
- Engage SBA proactively on any certification concerns
- Develop contingency teaming arrangements with eligible primes

**Recovery Options** (if worst case occurs):
- File for reconsideration if procedural errors occurred
- Transition to subcontractor role with eligible prime
- Pursue debriefing to understand exact disqualification rationale
- Document and address compliance gaps for future opportunities

**Plausibility**: Low

**Severity**: Catastrophic"""

        elif "task: strategy stress test" in prompt_lower:
            return """### Assumption 1 Stress Test

**Assumption**: "The agency will prioritize innovation over cost in this evaluation"

**Stress Scenario**: The agency faces unexpected budget cuts in Q3, forcing a reprioritization toward lowest-price technically acceptable (LPTA) evaluation or a much tighter price/technical tradeoff tolerance. Our premium pricing based on innovation becomes a liability rather than a differentiator.

**Strategy Impact**: Our entire win strategy is built on technical differentiation at a price premium. If price becomes the dominant factor, we would need to: (1) significantly reduce proposed staffing, (2) descope optional innovations, (3) accept lower margins or potential losses.

**Win Probability Effect**: Decrease from estimated 55% to approximately 25-30%. Our price-competitive positioning is weak, and rapid cost reduction would likely also reduce our technical scores.

**Vulnerability Level**: High

**Early Warning Indicators**:
- Agency budget announcements or continuing resolution impacts
- Shift in RFP language emphasizing cost over innovation in amendments
- Informal customer feedback indicating price sensitivity
- Competitive intelligence suggesting incumbent is pricing aggressively

**Contingency Recommendation**: Develop a "shadow" pricing model at 15% below current target that maintains core capabilities but removes premium innovations. Prepare to pivot messaging from "best" to "best value" if price signals change.

---

### Assumption 2 Stress Test

**Assumption**: "The incumbent will not significantly improve their approach for the recompete"

**Stress Scenario**: The incumbent has quietly been addressing all known performance issues, has hired a new program manager with outstanding credentials, and is preparing to propose a significantly enhanced technical approach that leapfrogs our innovations. They've also been improving their customer relationship and addressing all concerns raised in contract reviews.

**Strategy Impact**: Our ghost team analysis becomes obsolete. Discriminators based on "fixing incumbent problems" lose relevance. We may be proposing solutions to problems that no longer exist, appearing out of touch with current performance realities.

**Win Probability Effect**: Decrease from estimated 55% to approximately 40%. The incumbent advantage (lower transition risk, proven relationship) would compound with their improved approach.

**Vulnerability Level**: High

**Early Warning Indicators**:
- Incumbent personnel changes (new PM, technical leads)
- Customer feedback indicating improved incumbent performance
- Incumbent hiring activity aligned with opportunity requirements
- Intelligence suggesting incumbent is investing heavily in recompete

**Contingency Recommendation**: Develop capture intelligence focused on incumbent recompete preparation. Ensure our discriminators are not solely based on incumbent weaknesses but also on unique strengths they cannot easily replicate. Prepare alternative messaging that acknowledges improved performance while demonstrating superior value.

---

### Assumption 3 Stress Test

**Assumption**: "Our teaming partner will remain committed through proposal submission"

**Stress Scenario**: Our key teaming partner, who provides 30% of the proposed work and critical past performance, receives an attractive prime offer from a competitor and withdraws from our team 45 days before proposal deadline.

**Strategy Impact**: We lose critical capabilities and past performance. Our technical approach has significant gaps. We must either find a replacement partner quickly (with associated learning curve and potential compliance issues) or significantly restructure our approach. Either path degrades proposal quality.

**Win Probability Effect**: Decrease from estimated 55% to approximately 30% if we find adequate replacement, or 10-15% if we cannot fill the capability gap.

**Vulnerability Level**: Critical

**Early Warning Indicators**:
- Partner receiving prime opportunities in same timeframe
- Reduced partner engagement in solution development
- Partner personnel assigned to other pursuits
- Delayed responses to teaming communications

**Contingency Recommendation**: Immediately secure binding teaming agreement with meaningful exclusivity provisions. Identify backup partners who could provide similar capabilities. Ensure our approach is not critically dependent on a single partner for more than 20% of scope. Develop relationship at multiple levels in partner organization."""

        elif "task: mitigation evaluation" in prompt_lower:
            return """### Mitigation Evaluation

**Verdict**: Partially Adequate

**Effectiveness Assessment**: The proposed mitigation addresses the symptom (personnel availability) but not the root cause (competitive compensation and opportunity attractiveness). Retention bonuses may delay departures but do not fundamentally change the competitive dynamic for key personnel.

**Feasibility Assessment**: The mitigation is implementable within the proposed timeline and budget. However, it requires HR and Finance approvals that may not be routine, and the timing (45 days before proposal) may be too late if competitors have already made offers.

**Residual Risk After Mitigation**:
- **New Probability**: Medium (reduced from High, but not eliminated)
- **New Impact**: High (unchanged - if key personnel still depart, impact is the same)

**Gaps Identified**:
- No contingency for if retention bonuses are declined
- No monitoring mechanism to detect competitor recruiting activity
- No backup personnel identification or development
- Timeline for implementation is aggressive

**Improvement Recommendations**:
- Add proactive outreach to personnel to understand concerns before offering retention
- Develop formal backup candidate pipeline for all key positions
- Include non-financial retention elements (role clarity, growth opportunities)
- Implement competitive intelligence on competitor recruiting activities
- Move retention conversations earlier in capture timeline

**New Risks Created**:
- Retention bonuses may create expectations for future opportunities
- Other personnel may feel undervalued if not offered similar incentives
- Financial commitment increases if opportunity is lost"""

        elif "task: risk response evaluation" in prompt_lower:
            return """### Evaluation Result

**Verdict**: Partially Acceptable

**Reasoning**: The Blue Team has acknowledged the risk and proposed a mitigation plan, but the plan lacks specificity and timeline. The response demonstrates understanding of the issue but does not provide confidence that the mitigation will be effectively implemented before proposal submission.

**Risk Status After Response**:
- **Residual Probability**: Medium (reduced from High through awareness, but execution is uncertain)
- **Residual Impact**: High (unchanged - consequences remain severe if risk materializes)

**Strengths**:
- Acknowledged the legitimacy of the risk concern
- Identified appropriate mitigation approach (retention incentives)
- Assigned ownership to Capture Manager
- Recognized the urgency of addressing the risk

**Weaknesses**:
- No specific timeline for mitigation implementation
- No metrics or success criteria defined
- Backup plan if primary mitigation fails is vague
- Does not address root cause of personnel vulnerability
- Budget for retention incentives not confirmed

**Follow-Up Required**: Yes - The Blue Team should provide:
1. Specific timeline with milestones for retention conversations
2. Confirmed budget allocation for retention incentives
3. Named backup candidates for each key position
4. Criteria for determining if mitigation is working
5. Trigger points for escalation if mitigation appears to be failing

**Resolution Status**: Needs Further Work"""

        else:
            # Full risk assessment
            return """### Risk 1: Key Personnel Vulnerability

**Category**: Staffing

**Description**: Proposed Program Manager has received indications of interest from competitor organizations. If recruited away before proposal submission or contract award, the technical approach and management plan would require significant revision with less qualified personnel.

**Trigger**: Competitor makes attractive offer; current employer counter-offers; personal circumstances change.

**Consequence**: Forced personnel substitution could weaken technical evaluation scores by 1-2 adjective ratings. May also impact customer confidence if PM has established relationship with agency.

**Probability**: Medium

**Impact**: High

**Source**: Management Approach - Personnel Section

**Mitigation Required**: Yes

**Suggested Mitigation**: Secure written letter of commitment with retention incentive. Identify and develop backup PM candidate who could step in if needed. Ensure technical approach is not overly dependent on any single individual.

**Residual Risk**: Even with commitment, personnel can still be recruited. Backup candidates may not be as strong.

---

### Risk 2: 8(a) Certification Timeline

**Category**: Eligibility

**Description**: Company's 8(a) certification is scheduled to expire 18 months into the base period of performance. While graduation is expected to be orderly, any issues with the transition could create eligibility challenges for option years.

**Trigger**: SBA questions about program graduation; contract modification delays; competitor protest on eligibility grounds.

**Consequence**: Potential ineligibility for option year awards under the set-aside. Could require novation or bridge contract arrangements that complicate performance and profitability.

**Probability**: Low

**Impact**: Medium

**Source**: Compliance section, Set-aside requirements

**Mitigation Required**: Yes

**Suggested Mitigation**: Engage SBA proactively on graduation timeline and transition planning. Ensure contract structure accommodates potential graduation. Consider teaming arrangement that provides eligibility backup.

**Residual Risk**: SBA processes are not fully controllable; competitor protests are always possible.

---

### Risk 3: Incumbent Relationship Strength

**Category**: Competitive

**Description**: Current incumbent has 7 years of relationship with agency program office and has received consistently positive CPARS ratings. Our capture efforts have not yet achieved equivalent access or demonstrated understanding of agency priorities.

**Trigger**: Incumbent leverages relationship for favorable RFP shaping; evaluators give benefit of doubt on proposal ambiguities; informal customer feedback favors incumbent.

**Consequence**: All else being equal, incumbent receives higher confidence ratings. Our proposals must be demonstrably superior to overcome relationship disadvantage, which may not be achievable.

**Probability**: High

**Impact**: Medium

**Source**: Competitive Analysis section

**Mitigation Required**: Yes

**Suggested Mitigation**: Intensify agency engagement over remaining capture period. Identify opportunities for demonstrations or pilots that build relationship. Leverage any current contracts with adjacent offices. Prepare proposal messaging that addresses transition risk directly.

**Residual Risk**: 7 years of relationship cannot be replicated in months. Some evaluators will prefer known quantity.

---

### Risk 4: Price-to-Win Uncertainty

**Category**: Pricing

**Description**: PTW analysis is based on limited market data and assumptions about competitor pricing strategies. Actual competitive bids could vary significantly from estimates, placing us outside the competitive range or in an unfavorable price/technical tradeoff position.

**Trigger**: Competitor prices more aggressively than expected; incumbent accepts margin compression to defend position; our cost estimates prove too high.

**Consequence**: If we price too high, we may be excluded from competitive range. If we price too low, we may win an unprofitable contract. Either outcome damages our business position.

**Probability**: Medium

**Impact**: High

**Source**: Price-to-Win Analysis section

**Mitigation Required**: Yes

**Suggested Mitigation**: Develop pricing scenarios at multiple points (aggressive, target, conservative). Conduct sensitivity analysis on key cost drivers. Build in pricing flexibility for negotiations. Monitor market signals for competitor pricing intentions.

**Residual Risk**: Competitive pricing is inherently uncertain until bids are opened.

---

### Risk 5: Technical Approach Complexity

**Category**: Execution

**Description**: Proposed technical solution involves integration of three commercial products that have not previously been integrated in a federal environment. While technically feasible, execution complexity creates schedule and performance risk during transition.

**Trigger**: Integration issues during development; vendor support gaps; performance problems under federal security requirements; longer-than-planned testing cycles.

**Consequence**: Delayed transition could trigger penalties or customer dissatisfaction. Performance issues in production could result in poor CPARS and recompete disadvantage. Cost overruns from extended development could eliminate profit margin.

**Probability**: Medium

**Impact**: High

**Source**: Technical Approach section - Integration subsection

**Mitigation Required**: Yes

**Suggested Mitigation**: Conduct proof-of-concept integration before proposal submission if possible. Build schedule contingency into transition plan. Ensure firm vendor commitments for support. Include experienced integration engineers on proposed team.

**Residual Risk**: Novel integrations always carry some execution uncertainty. Proof-of-concept reduces but does not eliminate risk.

---

### Risk 6: Teaming Partner Commitment

**Category**: Teaming

**Description**: Primary teaming partner is also pursuing prime opportunities that would require their key personnel. If they win a prime opportunity, they may reduce commitment to our team or withdraw entirely.

**Trigger**: Partner wins prime contract; partner resources are reassigned; partner experiences financial difficulties; competitive intelligence reveals partner engagement with competitors.

**Consequence**: Loss of critical capabilities and past performance. Proposal revision under time pressure. Potential need to find replacement partner or restructure approach.

**Probability**: Low

**Impact**: Catastrophic

**Source**: Teaming Strategy section

**Mitigation Required**: Yes

**Suggested Mitigation**: Secure exclusive teaming agreement for this opportunity. Identify backup partners with similar capabilities. Ensure our proposal can be modified if partner circumstances change. Maintain regular communication with partner leadership.

**Residual Risk**: Even with agreements, partners can exit with appropriate notice and penalties.

---

### Risk 7: Cost Realism Challenge

**Category**: Financial

**Description**: Our proposed labor rates are 8-12% below current GSA schedule rates for comparable positions. While we believe this reflects our efficient operations, evaluators may question whether rates are realistic and sustainable.

**Trigger**: Evaluator applies cost realism analysis; rates compared unfavorably to market surveys; questions during discussions about rate justification.

**Consequence**: Cost realism findings could increase evaluated price above actual price, negating pricing advantage. Severe findings could result in downgraded ratings or discussions about capability to perform.

**Probability**: Medium

**Impact**: Medium

**Source**: Pricing Strategy section

**Mitigation Required**: Yes

**Suggested Mitigation**: Prepare comprehensive cost realism documentation showing how rates are achievable. Include efficiency factors and overhead improvements that support rates. Ensure rates are consistent with past performance on similar work.

**Residual Risk**: Evaluator discretion in cost realism is significant; not all justifications are accepted.

---

### Risk 8: Transition Period Compressed

**Category**: Schedule

**Description**: The solicitation specifies a 60-day transition period, but our detailed transition plan requires 75-80 days for full operational capability. Compressing the timeline could result in incomplete knowledge transfer or operational gaps.

**Trigger**: Strict enforcement of 60-day transition requirement; incumbent provides minimal transition support; personnel onboarding delays; security clearance processing delays.

**Consequence**: Operational gaps during transition could impact service delivery and customer satisfaction. Early performance issues could damage relationship and future CPARS. Rushed transition could also create security or compliance vulnerabilities.

**Probability**: Medium

**Impact**: Medium

**Source**: Transition Plan section

**Mitigation Required**: Yes

**Suggested Mitigation**: Re-examine transition plan to identify compression opportunities. Build in parallel activities where possible. Pre-position key resources before transition begins. Develop contingency support arrangements for any gaps.

**Residual Risk**: Transition timelines are often optimistic; some compression may simply not be possible without risk.

---

### Risk 9: Past Performance Relevance

**Category**: Competitive

**Description**: Our most relevant past performance is on a contract that is 4 years old. While we have current work, it is in an adjacent domain that may not be viewed as directly comparable by evaluators.

**Trigger**: Evaluators rate past performance as "limited relevance"; competitors have more recent and directly relevant experience; questions during discussions about capability gaps.

**Consequence**: Weaker past performance ratings could offset technical advantages. In a tight competition, past performance tie-breaker could favor competitor with more relevant recent work.

**Probability**: Medium

**Impact**: Medium

**Source**: Past Performance volume planning

**Mitigation Required**: Yes

**Suggested Mitigation**: Strengthen past performance narrative to emphasize transferable experience. Include detailed capability mapping from past work to current requirements. Consider highlighting key personnel experience from relevant projects at other companies.

**Residual Risk**: Evaluator judgment on relevance is subjective; even strong narratives may not fully close gap.

---

### Risk 10: Protest Potential

**Category**: External

**Description**: Given the competitive sensitivity of this opportunity and the incumbent's investment in the relationship, there is elevated risk of bid protest regardless of outcome. Either winner or losers may file to delay or reverse the award.

**Trigger**: Any perceived procurement irregularity; close evaluation scores; relationship between evaluators and offerors; novel evaluation approaches.

**Consequence**: Award delay of 3-6 months if protest filed. Additional legal costs. Potential for award reversal if protest sustained. Resource distraction during protest period.

**Probability**: Medium

**Impact**: Medium

**Source**: Competitive landscape analysis

**Mitigation Required**: No (external risk outside our control)

**Suggested Mitigation**: Ensure our proposal creates no protestable issues. Document all customer interactions carefully. Prepare for protest scenario with legal counsel. Build protest timeline into planning assumptions.

**Residual Risk**: Protest risk is inherent in competitive federal procurements; cannot be eliminated."""

    def _parse_risks(
        self,
        content: str,
        document_id: str = "",
        round_number: int = 1,
        default_section: str = "",
    ) -> List[Risk]:
        """Parse risks from LLM response."""
        risks = []

        # DEBUG: Log the content we're trying to parse
        content_preview = content[:500] + "..." if len(content) > 500 else content
        self.log_debug(f"_parse_risks: Parsing content ({len(content)} chars): {content_preview}")

        # Split by risk sections - support both ### and ## headers
        risk_sections = re.split(r'#{2,3}\s*Risk\s*\d+', content, flags=re.IGNORECASE)

        # DEBUG: Log how many sections we found
        self.log_debug(f"_parse_risks: Found {len(risk_sections) - 1} risk sections (regex split)")

        # If no sections found, try alternative patterns
        if len(risk_sections) <= 1:
            self.log_warning(f"_parse_risks: No '### Risk N' or '## Risk N' patterns found. Trying alternative patterns...")
            # Try "Risk 1:", "Risk 2:", etc.
            risk_sections = re.split(r'\n\s*Risk\s+\d+\s*[:\-]', content, flags=re.IGNORECASE)
            self.log_debug(f"_parse_risks: Alternative pattern found {len(risk_sections) - 1} sections")

        for section in risk_sections[1:]:  # Skip first split (before first risk)
            try:
                # Extract title
                title_match = re.search(r'^[:\s]*([^\n]+)', section.strip())
                title = title_match.group(1).strip() if title_match else "Untitled Risk"

                # Extract category
                category_match = re.search(
                    r'\*\*Category\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                category_str = category_match.group(1).strip() if category_match else "Execution"
                category = self._map_risk_category(category_str)

                # Extract description
                desc_match = re.search(
                    r'\*\*Description\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                description = desc_match.group(1).strip() if desc_match else ""

                # Extract trigger
                trigger_match = re.search(
                    r'\*\*Trigger\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                trigger = trigger_match.group(1).strip() if trigger_match else ""

                # Extract consequence
                consequence_match = re.search(
                    r'\*\*Consequence\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                consequence = consequence_match.group(1).strip() if consequence_match else ""

                # Extract probability
                prob_match = re.search(
                    r'\*\*Probability\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                prob_str = prob_match.group(1).strip() if prob_match else "Medium"
                probability = self._map_probability(prob_str)

                # Extract impact
                impact_match = re.search(
                    r'\*\*Impact\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                impact_str = impact_match.group(1).strip() if impact_match else "Medium"
                impact = self._map_impact(impact_str)

                # Extract source section
                source_match = re.search(
                    r'\*\*Source\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                source_section = source_match.group(1).strip() if source_match else default_section

                # Extract mitigation required
                mit_req_match = re.search(
                    r'\*\*Mitigation Required\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                mitigation_required = True
                if mit_req_match:
                    mitigation_required = "yes" in mit_req_match.group(1).lower()

                # Extract suggested mitigation
                mitigation_match = re.search(
                    r'\*\*Suggested Mitigation\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                suggested_mitigation = mitigation_match.group(1).strip() if mitigation_match else ""

                # Extract residual risk
                residual_match = re.search(
                    r'\*\*Residual Risk\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                residual_risk = residual_match.group(1).strip() if residual_match else ""

                risk = Risk(
                    category=category,
                    title=title,
                    description=description,
                    trigger=trigger,
                    consequence=consequence,
                    probability=probability,
                    impact=impact,
                    source_section=source_section,
                    mitigation_required=mitigation_required,
                    suggested_mitigation=suggested_mitigation,
                    residual_risk=residual_risk,
                    identified_by=self.role.value,
                    round_number=round_number,
                )
                risks.append(risk)

            except Exception as e:
                self.log_warning(f"Failed to parse risk section: {e}")
                continue

        return risks

    def _map_risk_category(self, category_str: str) -> RiskCategory:
        """Map string to RiskCategory enum."""
        category_lower = category_str.lower()

        mapping = {
            "execution": RiskCategory.EXECUTION,
            "staffing": RiskCategory.STAFFING,
            "technical": RiskCategory.TECHNICAL,
            "schedule": RiskCategory.SCHEDULE,
            "transition": RiskCategory.TRANSITION,
            "compliance": RiskCategory.COMPLIANCE,
            "eligibility": RiskCategory.ELIGIBILITY,
            "oci": RiskCategory.OCI,
            "security": RiskCategory.SECURITY,
            "competitive": RiskCategory.COMPETITIVE,
            "incumbent": RiskCategory.INCUMBENT,
            "pricing": RiskCategory.PRICING,
            "teaming": RiskCategory.TEAMING,
            "financial": RiskCategory.FINANCIAL,
            "cash flow": RiskCategory.CASH_FLOW,
            "profitability": RiskCategory.PROFITABILITY,
            "political": RiskCategory.POLITICAL,
            "protest": RiskCategory.PROTEST,
            "recompete": RiskCategory.RECOMPETE,
            "market": RiskCategory.MARKET,
            "external": RiskCategory.POLITICAL,  # Map external to political
            "strategic": RiskCategory.STRATEGIC,
            "reputation": RiskCategory.REPUTATION,
            "opportunity cost": RiskCategory.OPPORTUNITY_COST,
        }

        for key, value in mapping.items():
            if key in category_lower:
                return value

        return RiskCategory.EXECUTION

    def _map_probability(self, prob_str: str) -> Probability:
        """Map string to Probability enum."""
        prob_lower = prob_str.lower()

        if "rare" in prob_lower:
            return Probability.RARE
        elif "low" in prob_lower:
            return Probability.LOW
        elif "medium" in prob_lower or "moderate" in prob_lower:
            return Probability.MEDIUM
        elif "almost" in prob_lower or "certain" in prob_lower:
            return Probability.ALMOST_CERTAIN
        elif "high" in prob_lower:
            return Probability.HIGH
        else:
            return Probability.MEDIUM

    def _map_impact(self, impact_str: str) -> Impact:
        """Map string to Impact enum."""
        impact_lower = impact_str.lower()

        if "negligible" in impact_lower:
            return Impact.NEGLIGIBLE
        elif "catastrophic" in impact_lower:
            return Impact.CATASTROPHIC
        elif "high" in impact_lower:
            return Impact.HIGH
        elif "medium" in impact_lower or "moderate" in impact_lower:
            return Impact.MEDIUM
        elif "low" in impact_lower:
            return Impact.LOW
        else:
            return Impact.MEDIUM

    def _parse_worst_case_scenarios(self, content: str) -> List[WorstCaseScenario]:
        """Parse worst-case scenarios from LLM response."""
        scenarios = []

        # Split by scenario sections
        scenario_sections = re.split(
            r'###\s*Worst-Case Scenario\s*\d+',
            content,
            flags=re.IGNORECASE
        )

        for section in scenario_sections[1:]:
            try:
                # Extract title
                title_match = re.search(r'^[:\s]*([^\n]+)', section.strip())
                title = title_match.group(1).strip() if title_match else "Untitled Scenario"

                # Extract narrative
                narrative_match = re.search(
                    r'\*\*Narrative\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                narrative = narrative_match.group(1).strip() if narrative_match else ""

                # Extract trigger chain
                trigger_chain = []
                trigger_match = re.search(
                    r'\*\*Trigger Chain\*\*[:\s]*((?:\d+\.[^\n]+\n?)+)',
                    section,
                    re.IGNORECASE
                )
                if trigger_match:
                    trigger_chain = [
                        re.sub(r'^\d+\.\s*', '', line.strip())
                        for line in trigger_match.group(1).strip().split('\n')
                        if line.strip()
                    ]

                # Extract contributing risks
                contributing_match = re.search(
                    r'\*\*Contributing Risks\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                contributing = contributing_match.group(1).strip() if contributing_match else ""
                contributing_risks = [c.strip() for c in contributing.split(',') if c.strip()]

                # Extract impacts
                win_impact_match = re.search(
                    r'\*\*Win Probability\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                financial_impact_match = re.search(
                    r'\*\*Financial\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                reputation_impact_match = re.search(
                    r'\*\*Reputation\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                strategic_impact_match = re.search(
                    r'\*\*Strategic\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )

                # Extract early warning signs
                warning_signs = []
                warning_match = re.search(
                    r'\*\*Early Warning Signs\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
                    section,
                    re.IGNORECASE
                )
                if warning_match:
                    warning_signs = [
                        line.strip().lstrip('-•').strip()
                        for line in warning_match.group(1).strip().split('\n')
                        if line.strip()
                    ]

                # Extract prevention measures
                prevention = []
                prevention_match = re.search(
                    r'\*\*Prevention Measures\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
                    section,
                    re.IGNORECASE
                )
                if prevention_match:
                    prevention = [
                        line.strip().lstrip('-•').strip()
                        for line in prevention_match.group(1).strip().split('\n')
                        if line.strip()
                    ]

                # Extract recovery options
                recovery = []
                recovery_match = re.search(
                    r'\*\*Recovery Options\*\*[^:]*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
                    section,
                    re.IGNORECASE
                )
                if recovery_match:
                    recovery = [
                        line.strip().lstrip('-•').strip()
                        for line in recovery_match.group(1).strip().split('\n')
                        if line.strip()
                    ]

                # Extract plausibility and severity
                plausibility_match = re.search(
                    r'\*\*Plausibility\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                severity_match = re.search(
                    r'\*\*Severity\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )

                scenario = WorstCaseScenario(
                    title=title,
                    narrative=narrative,
                    trigger_chain=trigger_chain,
                    win_probability_impact=win_impact_match.group(1).strip() if win_impact_match else "",
                    financial_impact=financial_impact_match.group(1).strip() if financial_impact_match else "",
                    reputation_impact=reputation_impact_match.group(1).strip() if reputation_impact_match else "",
                    strategic_impact=strategic_impact_match.group(1).strip() if strategic_impact_match else "",
                    contributing_risks=contributing_risks,
                    prevention_measures=prevention,
                    recovery_options=recovery,
                    early_warning_signs=warning_signs,
                    plausibility=plausibility_match.group(1).strip() if plausibility_match else "Medium",
                    severity=severity_match.group(1).strip() if severity_match else "High",
                )
                scenarios.append(scenario)

            except Exception as e:
                self.log_warning(f"Failed to parse worst-case scenario: {e}")
                continue

        return scenarios

    def _parse_stress_tests(self, content: str) -> List[StressTestResult]:
        """Parse stress test results from LLM response."""
        results = []

        # Split by assumption sections
        test_sections = re.split(
            r'###\s*Assumption\s*\d+\s*Stress Test',
            content,
            flags=re.IGNORECASE
        )

        for section in test_sections[1:]:
            try:
                # Extract assumption
                assumption_match = re.search(
                    r'\*\*Assumption\*\*[:\s]*["\']?([^"\']+)["\']?',
                    section,
                    re.IGNORECASE
                )
                assumption = assumption_match.group(1).strip() if assumption_match else ""

                # Extract stress scenario
                scenario_match = re.search(
                    r'\*\*Stress Scenario\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                stress_scenario = scenario_match.group(1).strip() if scenario_match else ""

                # Extract strategy impact
                impact_match = re.search(
                    r'\*\*Strategy Impact\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                strategy_impact = impact_match.group(1).strip() if impact_match else ""

                # Extract win probability effect
                win_match = re.search(
                    r'\*\*Win Probability Effect\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                win_probability_effect = win_match.group(1).strip() if win_match else ""

                # Extract vulnerability level
                vuln_match = re.search(
                    r'\*\*Vulnerability Level\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                vulnerability_level = vuln_match.group(1).strip() if vuln_match else "Medium"

                # Extract early warning indicators
                indicators = []
                indicators_match = re.search(
                    r'\*\*Early Warning Indicators\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
                    section,
                    re.IGNORECASE
                )
                if indicators_match:
                    indicators = [
                        line.strip().lstrip('-•').strip()
                        for line in indicators_match.group(1).strip().split('\n')
                        if line.strip()
                    ]

                # Extract contingency recommendation
                contingency_match = re.search(
                    r'\*\*Contingency Recommendation\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                contingency = contingency_match.group(1).strip() if contingency_match else ""

                result = StressTestResult(
                    assumption=assumption,
                    stress_scenario=stress_scenario,
                    strategy_impact=strategy_impact,
                    win_probability_effect=win_probability_effect,
                    vulnerability_level=vulnerability_level,
                    early_warning_indicators=indicators,
                    contingency_recommendation=contingency,
                )
                results.append(result)

            except Exception as e:
                self.log_warning(f"Failed to parse stress test result: {e}")
                continue

        return results

    def _parse_mitigation_evaluation(
        self,
        content: str,
        risk_id: str,
    ) -> MitigationEvaluation:
        """Parse mitigation evaluation from LLM response."""
        evaluation = MitigationEvaluation(risk_id=risk_id)

        # Extract verdict
        verdict_match = re.search(
            r'\*\*Verdict\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if verdict_match:
            verdict_text = verdict_match.group(1).strip()
            if "adequate" in verdict_text.lower() and "partial" not in verdict_text.lower():
                evaluation.verdict = "Adequate"
            elif "partial" in verdict_text.lower():
                evaluation.verdict = "Partially Adequate"
            else:
                evaluation.verdict = "Insufficient"

        # Extract effectiveness assessment
        effectiveness_match = re.search(
            r'\*\*Effectiveness Assessment\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if effectiveness_match:
            evaluation.effectiveness_assessment = effectiveness_match.group(1).strip()

        # Extract feasibility assessment
        feasibility_match = re.search(
            r'\*\*Feasibility Assessment\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if feasibility_match:
            evaluation.feasibility_assessment = feasibility_match.group(1).strip()

        # Extract new probability
        new_prob_match = re.search(
            r'\*\*New Probability\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if new_prob_match:
            evaluation.new_probability = new_prob_match.group(1).strip()

        # Extract new impact
        new_impact_match = re.search(
            r'\*\*New Impact\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if new_impact_match:
            evaluation.new_impact = new_impact_match.group(1).strip()

        # Extract gaps identified
        gaps_match = re.search(
            r'\*\*Gaps Identified\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
            content,
            re.IGNORECASE
        )
        if gaps_match:
            evaluation.gaps_identified = [
                line.strip().lstrip('-•').strip()
                for line in gaps_match.group(1).strip().split('\n')
                if line.strip()
            ]

        # Extract improvement recommendations
        improvements_match = re.search(
            r'\*\*Improvement Recommendations\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
            content,
            re.IGNORECASE
        )
        if improvements_match:
            evaluation.improvement_recommendations = [
                line.strip().lstrip('-•').strip()
                for line in improvements_match.group(1).strip().split('\n')
                if line.strip()
            ]

        # Extract new risks created
        new_risks_match = re.search(
            r'\*\*New Risks Created\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
            content,
            re.IGNORECASE
        )
        if new_risks_match:
            evaluation.new_risks_created = [
                line.strip().lstrip('-•').strip()
                for line in new_risks_match.group(1).strip().split('\n')
                if line.strip()
            ]

        return evaluation

    def _parse_response_evaluation(
        self,
        content: str,
        risk_id: str,
    ) -> ResponseEvaluation:
        """Parse response evaluation from LLM response."""
        evaluation = ResponseEvaluation(risk_id=risk_id)

        # Extract verdict
        verdict_match = re.search(
            r'\*\*Verdict\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if verdict_match:
            verdict_text = verdict_match.group(1).strip()
            if "acceptable" in verdict_text.lower() and "partial" not in verdict_text.lower():
                evaluation.verdict = "Acceptable"
            elif "partial" in verdict_text.lower():
                evaluation.verdict = "Partially Acceptable"
            else:
                evaluation.verdict = "Insufficient"

        # Extract reasoning
        reasoning_match = re.search(
            r'\*\*Reasoning\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
            content,
            re.IGNORECASE
        )
        if reasoning_match:
            evaluation.reasoning = reasoning_match.group(1).strip()

        # Extract residual probability
        res_prob_match = re.search(
            r'\*\*Residual Probability\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if res_prob_match:
            evaluation.residual_probability = res_prob_match.group(1).strip()

        # Extract residual impact
        res_impact_match = re.search(
            r'\*\*Residual Impact\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if res_impact_match:
            evaluation.residual_impact = res_impact_match.group(1).strip()

        # Extract strengths
        strengths_match = re.search(
            r'\*\*Strengths\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
            content,
            re.IGNORECASE
        )
        if strengths_match:
            evaluation.strengths = [
                line.strip().lstrip('-•').strip()
                for line in strengths_match.group(1).strip().split('\n')
                if line.strip()
            ]

        # Extract weaknesses
        weaknesses_match = re.search(
            r'\*\*Weaknesses\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
            content,
            re.IGNORECASE
        )
        if weaknesses_match:
            evaluation.weaknesses = [
                line.strip().lstrip('-•').strip()
                for line in weaknesses_match.group(1).strip().split('\n')
                if line.strip()
            ]

        # Extract follow-up required
        followup_match = re.search(
            r'\*\*Follow-Up Required\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if followup_match:
            followup_text = followup_match.group(1).strip()
            evaluation.follow_up_required = "yes" in followup_text.lower()
            if "-" in followup_text:
                evaluation.follow_up_details = followup_text.split("-", 1)[1].strip()

        # Extract resolution status
        status_match = re.search(
            r'\*\*Resolution Status\*\*[:\s]*([^\n]+)',
            content,
            re.IGNORECASE
        )
        if status_match:
            evaluation.resolution_status = status_match.group(1).strip()

        return evaluation

    def _risks_to_critiques(
        self,
        risks: List[Risk],
        context: SwarmContext,
    ) -> List[Critique]:
        """Convert risks to critiques for debate workflow integration."""
        critiques = []

        for risk in risks:
            # Map risk level to severity
            severity_map = {
                "critical": Severity.CRITICAL,
                "high": Severity.MAJOR,
                "medium": Severity.MAJOR,
                "low": Severity.MINOR,
                "negligible": Severity.OBSERVATION,
            }
            severity = severity_map.get(risk.risk_level, Severity.MAJOR)

            critique = Critique(
                agent=self.role.value,
                round_number=context.round_number,
                target_document_id=context.document_id or "",
                target_section=risk.source_section,
                target_content=risk.source_content,
                challenge_type=ChallengeType.RISK,
                severity=severity,
                title=f"Risk: {risk.title}",
                argument=f"{risk.description}\n\nTrigger: {risk.trigger}\n\nConsequence: {risk.consequence}",
                evidence=f"Probability: {risk.probability.value}, Impact: {risk.impact.value}",
                suggested_remedy=risk.suggested_mitigation or "Address this risk through appropriate mitigation measures",
            )
            critiques.append(critique)

        return critiques

    def _extract_assumptions(self, section_drafts: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract implicit assumptions from document content."""
        assumptions = []

        # Common assumption indicator phrases
        assumption_patterns = [
            r'we expect',
            r'we anticipate',
            r'we believe',
            r'we assume',
            r'it is likely',
            r'presumably',
            r'the customer will',
            r'competitors will',
            r'the market will',
            r'based on our assessment',
            r'will prioritize',
            r'will not',
        ]

        for section_name, content in section_drafts.items():
            for pattern in assumption_patterns:
                matches = re.finditer(
                    rf'([^.]*{pattern}[^.]*\.)',
                    content,
                    re.IGNORECASE
                )
                for match in matches:
                    assumptions.append({
                        "statement": match.group(1).strip(),
                        "source": section_name,
                    })

        return assumptions[:10]  # Limit to 10 assumptions

    def _extract_strategy_summary(self, section_drafts: Dict[str, str]) -> str:
        """Extract a brief strategy summary from document content."""
        summary_parts = []

        # Look for executive summary or strategy overview
        for section_name, content in section_drafts.items():
            if any(keyword in section_name.lower() for keyword in ['executive', 'summary', 'overview', 'strategy']):
                # Take first 500 chars
                summary_parts.append(content[:500])

        if summary_parts:
            return "\n\n".join(summary_parts)

        # If no summary section, take first 200 chars from each section
        for section_name, content in list(section_drafts.items())[:3]:
            summary_parts.append(f"**{section_name}**: {content[:200]}...")

        return "\n\n".join(summary_parts) if summary_parts else "No strategy summary available."

    def _generate_overall_assessment(self, risks: List[Risk]) -> str:
        """Generate overall risk assessment based on identified risks."""
        if not risks:
            return "No material risks identified. Strategy appears low-risk."

        # Count by level
        critical = sum(1 for r in risks if r.risk_level == "critical")
        high = sum(1 for r in risks if r.risk_level == "high")
        medium = sum(1 for r in risks if r.risk_level == "medium")

        # Count requiring mitigation
        needs_mitigation = sum(1 for r in risks if r.mitigation_required and r.mitigation_status == MitigationStatus.NOT_STARTED)

        # Count requiring human review
        needs_review = sum(1 for r in risks if r.requires_human_review)

        # Category analysis
        category_counts: Dict[str, int] = {}
        for risk in risks:
            cat = risk.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        assessment_parts = []

        # Overall risk level
        if critical > 0:
            assessment_parts.append(
                f"**CRITICAL RISK LEVEL**: {critical} critical risk(s) require immediate attention."
            )
        elif high >= 3:
            assessment_parts.append(
                f"**HIGH RISK LEVEL**: {high} high-severity risks identified. Proceed with caution."
            )
        elif high > 0:
            assessment_parts.append(
                f"**MEDIUM-HIGH RISK LEVEL**: {high} high-severity risk(s) identified. Active monitoring required."
            )
        else:
            assessment_parts.append(
                "**MODERATE RISK LEVEL**: No critical or high-severity risks identified."
            )

        # Mitigation status
        if needs_mitigation > 0:
            assessment_parts.append(
                f"**{needs_mitigation} risks require mitigation plans** that have not yet been addressed."
            )

        # Human review
        if needs_review > 0:
            assessment_parts.append(
                f"**{needs_review} risks flagged for human review** due to severity or complexity."
            )

        # Top risk categories
        if category_counts:
            top_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            cat_summary = ", ".join(f"{c[0]} ({c[1]})" for c in top_cats)
            assessment_parts.append(f"**Primary risk areas**: {cat_summary}")

        return " ".join(assessment_parts)

    def _format_result_content(
        self,
        result: RiskAssessorResult,
        analysis_type: str,
    ) -> str:
        """Format result as content string."""
        parts = ["# Risk Assessment Report", ""]

        # Overall assessment
        if result.overall_assessment:
            parts.append("## Overall Assessment")
            parts.append("")
            parts.append(result.overall_assessment)
            parts.append("")

        # Risk register summary
        if result.risk_register:
            register = result.risk_register
            parts.append("## Risk Summary")
            parts.append("")
            parts.append(f"- **Total Risks**: {register.total_risks}")
            parts.append(f"- **Critical**: {register.critical_risks}")
            parts.append(f"- **High**: {register.high_risks}")
            parts.append(f"- **Medium**: {register.medium_risks}")
            parts.append(f"- **Low/Negligible**: {register.low_risks}")
            parts.append("")
            parts.append(f"**Overall Risk Level**: {register.overall_risk_level}")
            parts.append(f"**Risk Appetite Status**: {register.risk_appetite_status}")
            parts.append(f"**Recommended Action**: {register.recommended_action}")
            parts.append("")

        # Detailed risks
        if result.risks:
            parts.append("## Identified Risks")
            parts.append("")

            for i, risk in enumerate(result.risks, 1):
                parts.append(f"### Risk {i}: {risk.title}")
                parts.append("")
                parts.append(f"**Category**: {risk.category.value}")
                parts.append(f"**Probability**: {risk.probability.value}")
                parts.append(f"**Impact**: {risk.impact.value}")
                parts.append(f"**Risk Level**: {risk.risk_level}")
                parts.append("")
                parts.append(f"**Description**: {risk.description}")
                parts.append("")

                if risk.trigger:
                    parts.append(f"**Trigger**: {risk.trigger}")
                    parts.append("")

                if risk.consequence:
                    parts.append(f"**Consequence**: {risk.consequence}")
                    parts.append("")

                if risk.mitigation_required:
                    parts.append(f"**Mitigation Required**: Yes")
                    if risk.suggested_mitigation:
                        parts.append(f"**Suggested Mitigation**: {risk.suggested_mitigation}")
                    parts.append("")

                if risk.requires_human_review:
                    parts.append("**[REQUIRES HUMAN REVIEW]**")
                    parts.append("")

                parts.append("---")
                parts.append("")

        # Worst-case scenarios
        if result.worst_case_scenarios:
            parts.append("## Worst-Case Scenarios")
            parts.append("")

            for scenario in result.worst_case_scenarios:
                parts.append(f"### {scenario.title}")
                parts.append("")
                parts.append(f"**Plausibility**: {scenario.plausibility}")
                parts.append(f"**Severity**: {scenario.severity}")
                parts.append("")
                parts.append(f"**Narrative**: {scenario.narrative}")
                parts.append("")

                if scenario.trigger_chain:
                    parts.append("**Trigger Chain**:")
                    for i, trigger in enumerate(scenario.trigger_chain, 1):
                        parts.append(f"{i}. {trigger}")
                    parts.append("")

                if scenario.early_warning_signs:
                    parts.append("**Early Warning Signs**:")
                    for sign in scenario.early_warning_signs:
                        parts.append(f"- {sign}")
                    parts.append("")

                parts.append("---")
                parts.append("")

        # Stress test results
        if result.stress_test_results:
            parts.append("## Stress Test Results")
            parts.append("")

            for test in result.stress_test_results:
                parts.append(f"### Assumption: {test.assumption[:50]}...")
                parts.append("")
                parts.append(f"**Vulnerability Level**: {test.vulnerability_level}")
                parts.append(f"**Stress Scenario**: {test.stress_scenario}")
                parts.append(f"**Strategy Impact**: {test.strategy_impact}")
                parts.append(f"**Win Probability Effect**: {test.win_probability_effect}")
                parts.append("")

                if test.contingency_recommendation:
                    parts.append(f"**Contingency**: {test.contingency_recommendation}")
                    parts.append("")

                parts.append("---")
                parts.append("")

        # Response evaluations
        if result.response_evaluations:
            parts.append("## Response Evaluations")
            parts.append("")

            for eval in result.response_evaluations:
                parts.append(f"### Risk {eval.risk_id}")
                parts.append("")
                parts.append(f"**Verdict**: {eval.verdict}")
                parts.append(f"**Resolution Status**: {eval.resolution_status}")
                if eval.reasoning:
                    parts.append(f"**Reasoning**: {eval.reasoning}")
                parts.append("")
                parts.append("---")
                parts.append("")

        return "\n".join(parts)
