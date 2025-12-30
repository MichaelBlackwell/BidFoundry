"""
Devil's Advocate Agent

Systematic contrarian agent that challenges blue team outputs to surface
logical flaws, unsupported assumptions, and alternative interpretations.
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

from .prompts.devils_advocate_prompts import (
    DEVILS_ADVOCATE_SYSTEM_PROMPT,
    get_critique_generation_prompt,
    get_section_critique_prompt,
    get_assumption_challenge_prompt,
    get_counterargument_generation_prompt,
    get_logic_analysis_prompt,
    get_response_evaluation_prompt,
)


@dataclass
class AssumptionAnalysis:
    """Analysis of an assumption's validity."""

    statement: str
    source_section: str = ""
    validity: str = "Questionable"  # Valid, Questionable, Unsupported, False
    challenge: str = ""
    alternative_scenario: str = ""
    evidence_needed: str = ""
    recommendation: str = ""  # Keep, Strengthen, Revise, Remove

    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "source_section": self.source_section,
            "validity": self.validity,
            "challenge": self.challenge,
            "alternative_scenario": self.alternative_scenario,
            "evidence_needed": self.evidence_needed,
            "recommendation": self.recommendation,
        }


@dataclass
class Counterargument:
    """A counterargument to a strategy claim."""

    original_claim: str
    section: str = ""
    counterargument: str = ""
    weakness_exposed: str = ""
    recommended_response: str = ""

    def to_dict(self) -> dict:
        return {
            "original_claim": self.original_claim,
            "section": self.section,
            "counterargument": self.counterargument,
            "weakness_exposed": self.weakness_exposed,
            "recommended_response": self.recommended_response,
        }


@dataclass
class LogicalIssue:
    """A logical issue identified in content."""

    issue_type: str
    location: str
    flawed_reasoning: str
    explanation: str
    correction: str
    severity: str = "major"

    def to_dict(self) -> dict:
        return {
            "issue_type": self.issue_type,
            "location": self.location,
            "flawed_reasoning": self.flawed_reasoning,
            "explanation": self.explanation,
            "correction": self.correction,
            "severity": self.severity,
        }


@dataclass
class ResponseEvaluation:
    """Evaluation of a blue team's response to a critique."""

    critique_id: str
    verdict: str = "Insufficient"  # Acceptable, Insufficient, Partially Acceptable
    reasoning: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    follow_up_required: bool = False
    follow_up_details: str = ""
    resolution_status: str = "Needs Further Work"  # Resolved, Needs Further Work, Escalate

    def to_dict(self) -> dict:
        return {
            "critique_id": self.critique_id,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "follow_up_required": self.follow_up_required,
            "follow_up_details": self.follow_up_details,
            "resolution_status": self.resolution_status,
        }


@dataclass
class DevilsAdvocateResult:
    """Result of Devil's Advocate analysis operations."""

    # Primary outputs
    critiques: List[Critique] = field(default_factory=list)
    assumption_analyses: List[AssumptionAnalysis] = field(default_factory=list)
    counterarguments: List[Counterargument] = field(default_factory=list)
    logical_issues: List[LogicalIssue] = field(default_factory=list)
    response_evaluations: List[ResponseEvaluation] = field(default_factory=list)

    # Summary
    critique_summary: Optional[CritiqueSummary] = None
    overall_assessment: str = ""

    # Meta
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "critiques": [c.to_dict() for c in self.critiques],
            "assumption_analyses": [a.to_dict() for a in self.assumption_analyses],
            "counterarguments": [c.to_dict() for c in self.counterarguments],
            "logical_issues": [l.to_dict() for l in self.logical_issues],
            "response_evaluations": [r.to_dict() for r in self.response_evaluations],
            "critique_summary": self.critique_summary.to_dict() if self.critique_summary else None,
            "overall_assessment": self.overall_assessment,
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "token_usage": self.token_usage,
        }


class DevilsAdvocateAgent(RedTeamAgent):
    """
    The Devil's Advocate systematically challenges blue team outputs.

    Responsibilities:
    - Challenge every major assumption in blue team output
    - Identify logical gaps or unsupported claims
    - Propose alternative interpretations of data
    - Rate severity of each critique
    - Evaluate blue team responses to critiques

    The Devil's Advocate is:
    - Skeptical but constructive
    - Rigorous in identifying flaws
    - Fair in acknowledging strengths
    - Focused on strengthening the final output
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Devil's Advocate agent.

        Args:
            config: Optional agent configuration. If not provided, uses defaults.
        """
        if config is None:
            from agents.config import get_default_config
            config = get_default_config(AgentRole.DEVILS_ADVOCATE)

        super().__init__(config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.DEVILS_ADVOCATE

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.RED

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and generate critiques.

        The processing mode depends on the context:
        - Full document critique
        - Section-specific critique
        - Assumption challenge
        - Response evaluation

        Args:
            context: SwarmContext containing document content to critique

        Returns:
            AgentOutput with critiques and analysis
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
            analysis_type = context.custom_data.get("analysis_type", "full_critique")

            if analysis_type == "section_critique":
                result = await self._critique_section(context)
            elif analysis_type == "assumption_challenge":
                result = await self._challenge_assumptions(context)
            elif analysis_type == "counterargument":
                result = await self._generate_counterarguments(context)
            elif analysis_type == "logic_analysis":
                result = await self._analyze_logic(context)
            elif analysis_type == "response_evaluation":
                result = await self._evaluate_responses(context)
            else:
                # Full document critique
                result = await self._generate_full_critique(context)

            processing_time = int((time.time() - start_time) * 1000)
            result.processing_time_ms = processing_time

            # Generate summary
            if result.critiques:
                result.critique_summary = CritiqueSummary.from_critiques(
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
                    "critique_count": len(result.critiques),
                    "critical_count": sum(1 for c in result.critiques if c.severity == Severity.CRITICAL),
                    "major_count": sum(1 for c in result.critiques if c.severity == Severity.MAJOR),
                    "minor_count": sum(1 for c in result.critiques if c.severity == Severity.MINOR),
                    "assumption_count": len(result.assumption_analyses),
                    "logical_issue_count": len(result.logical_issues),
                },
            )

        except Exception as e:
            self.log_error(f"Error in Devil's Advocate processing: {e}")
            return self._create_output(
                success=False,
                error_message=f"Processing error: {str(e)}",
            )

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate the context for Devil's Advocate processing.

        Args:
            context: The SwarmContext to validate

        Returns:
            List of validation error messages
        """
        errors = super().validate_context(context)

        # Need either section drafts or current draft to critique
        if not context.section_drafts and not context.current_draft:
            errors.append("No document content provided to critique")

        return errors

    async def critique_section(
        self,
        context: SwarmContext,
        section_name: str,
        section_content: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate critiques for a specific section.

        Implementation of RedTeamAgent abstract method.

        Args:
            context: The swarm context
            section_name: Name of the section to critique
            section_content: Current content of the section

        Returns:
            List of critique dictionaries
        """
        # Set up context for section critique
        context.custom_data["analysis_type"] = "section_critique"
        context.custom_data["target_section"] = section_name
        context.section_drafts = {section_name: section_content}

        result = await self._critique_section(context)
        return [c.to_dict() for c in result.critiques]

    async def evaluate_response(
        self,
        context: SwarmContext,
        critique: Dict[str, Any],
        response: Dict[str, Any],
    ) -> bool:
        """
        Evaluate whether a blue team response adequately addresses a critique.

        Implementation of RedTeamAgent abstract method.

        Args:
            context: The swarm context
            critique: The original critique
            response: The blue team's response

        Returns:
            True if the response is acceptable, False otherwise
        """
        # Set up context for response evaluation
        context.custom_data["analysis_type"] = "response_evaluation"
        context.custom_data["critiques_to_evaluate"] = [critique]
        context.custom_data["responses"] = [response]

        result = await self._evaluate_responses(context)

        if result.response_evaluations:
            evaluation = result.response_evaluations[0]
            return evaluation.verdict == "Acceptable"

        return False

    async def _generate_full_critique(
        self,
        context: SwarmContext,
    ) -> DevilsAdvocateResult:
        """
        Generate critiques for an entire document.

        Args:
            context: SwarmContext with document content

        Returns:
            DevilsAdvocateResult with all critiques
        """
        result = DevilsAdvocateResult()

        # Collect document content
        document_content = context.section_drafts.copy()
        if context.current_draft and isinstance(context.current_draft, dict):
            if "sections" in context.current_draft:
                document_content.update(context.current_draft["sections"])

        if not document_content:
            result.success = False
            result.errors.append("No document content to critique")
            return result

        # Generate critique prompt
        focus_areas = context.custom_data.get("focus_areas", [])

        prompt = get_critique_generation_prompt(
            document_type=context.document_type or "Strategy Document",
            document_content=document_content,
            company_profile=context.company_profile,
            opportunity=context.opportunity,
            focus_areas=focus_areas if focus_areas else None,
        )

        llm_response = await self._call_llm(
            system_prompt=DEVILS_ADVOCATE_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.critiques = self._parse_critiques(
            content,
            document_id=context.document_id or "",
            round_number=context.round_number,
        )
        result.token_usage = llm_response.get("usage", {})

        # Generate overall assessment
        result.overall_assessment = self._generate_overall_assessment(result.critiques)

        return result

    async def _critique_section(
        self,
        context: SwarmContext,
    ) -> DevilsAdvocateResult:
        """
        Generate critiques for a specific section.

        Args:
            context: SwarmContext with section content

        Returns:
            DevilsAdvocateResult with section critiques
        """
        result = DevilsAdvocateResult()

        target_section = context.custom_data.get("target_section")
        if target_section:
            sections_to_critique = {target_section: context.section_drafts.get(target_section, "")}
        else:
            sections_to_critique = context.section_drafts

        for section_name, section_content in sections_to_critique.items():
            if not section_content:
                result.warnings.append(f"Section '{section_name}' is empty, skipping")
                continue

            prompt = get_section_critique_prompt(
                section_name=section_name,
                section_content=section_content,
                document_type=context.document_type or "Strategy Document",
                company_profile=context.company_profile,
                opportunity=context.opportunity,
            )

            llm_response = await self._call_llm(
                system_prompt=DEVILS_ADVOCATE_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            if llm_response.get("success"):
                content = llm_response.get("content", "")
                section_critiques = self._parse_critiques(
                    content,
                    document_id=context.document_id or "",
                    round_number=context.round_number,
                    default_section=section_name,
                )
                result.critiques.extend(section_critiques)

                # Update token usage
                for key, value in llm_response.get("usage", {}).items():
                    result.token_usage[key] = result.token_usage.get(key, 0) + value
            else:
                result.warnings.append(f"Failed to critique section '{section_name}'")

        return result

    async def _challenge_assumptions(
        self,
        context: SwarmContext,
    ) -> DevilsAdvocateResult:
        """
        Challenge identified assumptions.

        Args:
            context: SwarmContext with assumptions to challenge

        Returns:
            DevilsAdvocateResult with assumption analyses
        """
        result = DevilsAdvocateResult()

        assumptions = context.custom_data.get("assumptions", [])
        if not assumptions:
            # Try to extract assumptions from document content
            assumptions = self._extract_assumptions(context.section_drafts)

        if not assumptions:
            result.warnings.append("No assumptions identified to challenge")
            return result

        analysis_context = {}
        if context.opportunity:
            analysis_context["opportunity"] = context.opportunity
        if context.custom_data.get("market_conditions"):
            analysis_context["market_conditions"] = context.custom_data.get("market_conditions")

        prompt = get_assumption_challenge_prompt(
            assumptions=assumptions,
            context=analysis_context if analysis_context else None,
        )

        llm_response = await self._call_llm(
            system_prompt=DEVILS_ADVOCATE_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.assumption_analyses = self._parse_assumption_analyses(content)
        result.token_usage = llm_response.get("usage", {})

        # Convert questionable/unsupported assumptions to critiques
        for analysis in result.assumption_analyses:
            if analysis.validity in ["Unsupported", "False"]:
                critique = Critique(
                    agent=self.role.value,
                    round_number=context.round_number,
                    target_document_id=context.document_id or "",
                    target_section=analysis.source_section,
                    target_content=analysis.statement,
                    challenge_type=ChallengeType.EVIDENCE if analysis.validity == "Unsupported" else ChallengeType.LOGIC,
                    severity=Severity.MAJOR if analysis.validity == "Unsupported" else Severity.CRITICAL,
                    title=f"Unsupported Assumption: {analysis.statement[:50]}...",
                    argument=analysis.challenge,
                    evidence=f"Alternative scenario: {analysis.alternative_scenario}",
                    suggested_remedy=f"{analysis.recommendation}. Evidence needed: {analysis.evidence_needed}",
                )
                result.critiques.append(critique)

        return result

    async def _generate_counterarguments(
        self,
        context: SwarmContext,
    ) -> DevilsAdvocateResult:
        """
        Generate counterarguments to claims.

        Args:
            context: SwarmContext with claims to counter

        Returns:
            DevilsAdvocateResult with counterarguments
        """
        result = DevilsAdvocateResult()

        claims = context.custom_data.get("claims", [])
        if not claims:
            # Try to extract claims from document content
            claims = self._extract_claims(context.section_drafts)

        if not claims:
            result.warnings.append("No claims identified to counter")
            return result

        perspective = context.custom_data.get("opponent_perspective", "Government Evaluator")

        prompt = get_counterargument_generation_prompt(
            claims=claims,
            opponent_perspective=perspective,
        )

        llm_response = await self._call_llm(
            system_prompt=DEVILS_ADVOCATE_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.counterarguments = self._parse_counterarguments(content)
        result.token_usage = llm_response.get("usage", {})

        # Convert significant counterarguments to critiques
        for counter in result.counterarguments:
            if counter.weakness_exposed:
                critique = Critique(
                    agent=self.role.value,
                    round_number=context.round_number,
                    target_document_id=context.document_id or "",
                    target_section=counter.section,
                    target_content=counter.original_claim,
                    challenge_type=ChallengeType.LOGIC,
                    severity=Severity.MAJOR,
                    title=f"Claim Vulnerability: {counter.original_claim[:50]}...",
                    argument=counter.counterargument,
                    evidence=counter.weakness_exposed,
                    suggested_remedy=counter.recommended_response,
                )
                result.critiques.append(critique)

        return result

    async def _analyze_logic(
        self,
        context: SwarmContext,
    ) -> DevilsAdvocateResult:
        """
        Perform logical analysis of content.

        Args:
            context: SwarmContext with content to analyze

        Returns:
            DevilsAdvocateResult with logical issues
        """
        result = DevilsAdvocateResult()

        # Analyze each section
        for section_name, section_content in context.section_drafts.items():
            if not section_content:
                continue

            prompt = get_logic_analysis_prompt(
                content=section_content,
                section_name=section_name,
            )

            llm_response = await self._call_llm(
                system_prompt=DEVILS_ADVOCATE_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            if llm_response.get("success"):
                content = llm_response.get("content", "")
                issues = self._parse_logical_issues(content, section_name)
                result.logical_issues.extend(issues)

                # Update token usage
                for key, value in llm_response.get("usage", {}).items():
                    result.token_usage[key] = result.token_usage.get(key, 0) + value

        # Convert logical issues to critiques
        for issue in result.logical_issues:
            severity = Severity.CRITICAL if issue.severity == "critical" else (
                Severity.MAJOR if issue.severity == "major" else Severity.MINOR
            )
            critique = Critique(
                agent=self.role.value,
                round_number=context.round_number,
                target_document_id=context.document_id or "",
                target_section=issue.location,
                target_content=issue.flawed_reasoning,
                challenge_type=ChallengeType.LOGIC,
                severity=severity,
                title=f"Logical Issue: {issue.issue_type}",
                argument=issue.explanation,
                evidence=f"Found in: {issue.location}",
                suggested_remedy=issue.correction,
            )
            result.critiques.append(critique)

        return result

    async def _evaluate_responses(
        self,
        context: SwarmContext,
    ) -> DevilsAdvocateResult:
        """
        Evaluate blue team responses to critiques.

        Args:
            context: SwarmContext with critiques and responses

        Returns:
            DevilsAdvocateResult with response evaluations
        """
        result = DevilsAdvocateResult()

        critiques_to_evaluate = context.custom_data.get("critiques_to_evaluate", [])
        responses = context.custom_data.get("responses", [])

        # Match critiques to responses
        response_map = {r.get("critique_id"): r for r in responses}

        for critique in critiques_to_evaluate:
            critique_id = critique.get("id", "")
            response = response_map.get(critique_id)

            if not response:
                result.warnings.append(f"No response found for critique {critique_id}")
                continue

            prompt = get_response_evaluation_prompt(
                critique=critique,
                response=response,
            )

            llm_response = await self._call_llm(
                system_prompt=DEVILS_ADVOCATE_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            if llm_response.get("success"):
                content = llm_response.get("content", "")
                evaluation = self._parse_response_evaluation(content, critique_id)
                result.response_evaluations.append(evaluation)

                # Update token usage
                for key, value in llm_response.get("usage", {}).items():
                    result.token_usage[key] = result.token_usage.get(key, 0) + value
            else:
                result.warnings.append(f"Failed to evaluate response for critique {critique_id}")

        return result

    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock critique content for testing."""
        prompt_lower = prompt.lower()

        # More specific matches first to avoid false positives
        if "task: assumption challenge" in prompt_lower:
            return """### Assumption 1 Analysis

**Statement**: "Our team has the deepest federal experience in this market"

**Validity Assessment**: Questionable

**Challenge**: This claim is relative and unsubstantiated. "Deepest" implies comparison to all competitors, but no data is provided to support this ranking.

**Alternative Scenario**: If a competitor has longer tenure or more relevant contracts, evaluators may view this claim as exaggerated, potentially damaging credibility.

**Evidence Needed**: Quantified comparison of years of experience, number of similar contracts, or key personnel tenure versus known competitors.

**Recommendation**: Revise - Replace superlative with specific, provable metrics.

---

### Assumption 2 Analysis

**Statement**: "The agency will prioritize innovation over cost in this evaluation"

**Validity Assessment**: Unsupported

**Challenge**: While the RFP mentions innovation, it also explicitly states Best Value tradeoff with price as a significant factor. The assumption ignores the stated evaluation methodology.

**Alternative Scenario**: If price is weighted more heavily than assumed, our premium pricing strategy could eliminate us from the competitive range.

**Evidence Needed**: Explicit RFP language about tradeoff tolerance, historical award data for similar procurements at this agency.

**Recommendation**: Strengthen with evidence - Cite specific RFP language and adjust strategy if evidence contradicts assumption.

---

### Assumption 3 Analysis

**Statement**: "The incumbent will not significantly improve their approach for the recompete"

**Validity Assessment**: Unsupported

**Challenge**: This assumes the incumbent is complacent. In reality, incumbents typically invest heavily in recompete preparation and often address known weaknesses.

**Alternative Scenario**: If the incumbent has been gathering customer feedback and addressing performance gaps, our ghost team analysis underestimates their competitiveness.

**Evidence Needed**: Intelligence on incumbent's recompete preparation activities, recent performance trends, key personnel retention.

**Recommendation**: Revise - Assume the incumbent will present their strongest possible bid and plan accordingly."""

        elif "task: counterargument generation" in prompt_lower:
            return """### Claim 1 Counterargument

**Original Claim**: "Our CloudBridge platform reduces migration time by 50%"

**Counterargument**: As an evaluator, I've seen similar claims from many offerors. Where is the evidence? A 50% reduction compared to what baseline? Your own manual processes or industry standards? Show me the independent validation, customer testimonials, or documented case studies. Without them, this is marketing language, not a discriminator.

**Weakness Exposed**: The claim lacks specificity and validation. It sounds impressive but provides no verifiable proof.

**How Blue Team Should Respond**: Provide specific case study with dates, customer name, and measured metrics. Include before/after timeline data. Reference any third-party validation or awards.

---

### Claim 2 Counterargument

**Original Claim**: "Our team has unmatched understanding of agency mission priorities"

**Counterargument**: Every offeror claims this. The incumbent has been working with us for 5 years - how can you claim to understand our mission better than they do? What specific mission knowledge do you have that they don't? Have you actually worked on our programs, or are you inferring from public documents?

**Weakness Exposed**: "Unmatched" is an unprovable superlative. Without specific evidence of mission knowledge the incumbent lacks, this claim invites unfavorable comparison.

**How Blue Team Should Respond**: Replace with specific examples of mission-relevant work. If proposing personnel who formerly worked at the agency, cite that directly. Avoid comparatives that can't be proven.

---

### Claim 3 Counterargument

**Original Claim**: "We offer the lowest risk transition approach"

**Counterargument**: Zero transition is lower risk than any transition. As evaluators, we know that bringing in a new contractor always involves risk. What specifically makes your transition "lowest risk"? Have you done this exact transition before? What's your mitigation for knowledge transfer gaps?

**Weakness Exposed**: The claim ignores the inherent incumbent advantage and doesn't acknowledge any transition risks.

**How Blue Team Should Respond**: Acknowledge that transition has inherent risks, then quantify how your approach mitigates specific risks. Provide evidence from previous transitions of similar complexity. Be honest about residual risks and how you'll manage them."""

        elif "task: logical analysis" in prompt_lower:
            return """### Logical Issue 1: Non Sequitur

**Location**: Win Theme 2 - Competitive Advantage section

**The Flawed Reasoning**: "We have 50 engineers with AWS certifications, therefore we are the best positioned to win this cloud migration contract."

**Why It's Flawed**: Having certified engineers does not automatically make a company the best positioned. Other factors like relevant past performance, understanding of agency-specific requirements, pricing, and management approach also determine competitive position. The conclusion is a non sequitur - it doesn't follow from the premise.

**Correct Reasoning Would Be**: "Our 50 AWS-certified engineers demonstrate deep cloud expertise, which directly addresses the technical capability requirements. Combined with our [other factors], this positions us competitively for this opportunity."

**Severity**: Major

---

### Logical Issue 2: False Dichotomy

**Location**: Price-to-Win Analysis - Strategy Recommendations

**The Flawed Reasoning**: "We must either price aggressively to beat the incumbent or price premium to differentiate on quality. There is no middle ground."

**Why It's Flawed**: This presents only two options when the evaluation methodology (Best Value) explicitly allows for moderate pricing with technical superiority. The analysis ignores the actual tradeoff space defined by the procurement.

**Correct Reasoning Would Be**: "Our pricing strategy exists on a spectrum. Given the Best Value methodology, we should identify the optimal price point where our technical advantages justify any price premium without exceeding the agency's tradeoff tolerance."

**Severity**: Major

---

### Logical Issue 3: Circular Reasoning

**Location**: Discriminator 3 - Personnel Discriminator

**The Flawed Reasoning**: "Our Program Manager is uniquely qualified because she has unique qualifications for this program."

**Why It's Flawed**: This statement is tautological - it assumes what it's trying to prove. What specifically makes her qualifications unique? This provides no actual evidence for the discriminator claim.

**Correct Reasoning Would Be**: "Our Program Manager is uniquely qualified because she served as the government PM for this program for three years, achieving Exceptional CPARS ratings. No competitor can offer personnel with direct government-side experience managing this specific program."

**Severity**: Minor"""

        elif "task: response evaluation" in prompt_lower:
            return """### Evaluation Result

**Verdict**: Partially Acceptable

**Reasoning**: The Blue Team's response addresses the substance of the critique and provides some supporting evidence, but falls short of fully resolving the issue. The rebuttal attempts to defend the original claim but the evidence provided is circumstantial rather than direct.

**Strengths of Response**:
- Acknowledged the validity of the concern
- Provided some quantitative data to support the claim
- Proposed specific revision language
- Identified additional evidence that could be gathered

**Weaknesses of Response**:
- The evidence provided (internal metrics) may not be credible to evaluators
- The rebuttal doesn't address the evaluator's perspective adequately
- The proposed revision still uses relative language ("superior") without quantified comparison
- Residual risk of credibility concern is not fully mitigated

**Follow-Up Required**: Yes - The Blue Team should:
1. Obtain independent validation or customer testimonial for the claimed improvement
2. Revise language to use specific, verifiable metrics rather than comparatives
3. Consider whether the claim is essential or if a more conservative statement would suffice

**Resolution Status**: Needs Further Work"""

        else:
            # Full critique
            return """### Critique 1: Unsupported Performance Claim

**Challenge Type**: Evidence

**Severity**: Critical

**Target Section**: Win Theme 1 - Mission-Proven Excellence

**Challenged Content**: "Our team has successfully migrated over 50 federal agency systems to cloud environments, delivering 40% cost savings and 99.9% uptime."

**Argument**: This claim makes three quantified assertions (50+ systems, 40% savings, 99.9% uptime) but provides no source or verification. Evaluators will scrutinize such specific claims and may penalize unsupported statistics. If challenged during discussions, the company would need to produce documentation.

**Evidence**: The document provides no contract references, CPARS citations, or customer testimonials to validate these metrics. The 99.9% uptime claim is particularly aggressive - this represents only 8.76 hours of downtime per year.

**Impact If Not Addressed**: Evaluators may rate the Past Performance section as "Unsupported" or "Unverifiable," which could result in a Weakness finding in the Technical Evaluation.

**Suggested Remedy**: Either reduce claims to verifiable levels with cited sources, or add specific contract references that can be validated. Example: "Achieved 99.8% uptime on the VA EHR Cloud Migration (Contract #XYZ) as documented in FY2023 CPARS."

---

### Critique 2: Missing Competitive Risk Acknowledgment

**Challenge Type**: Completeness

**Severity**: Major

**Target Section**: Competitive Analysis

**Challenged Content**: [The entire Competitive Analysis section]

**Argument**: The analysis extensively covers competitor weaknesses but fails to acknowledge any areas where competitors may have legitimate advantages over us. This one-sided analysis lacks credibility and suggests either insufficient competitive intelligence or deliberate omission.

**Evidence**: No section addresses "our vulnerabilities" or "areas for improvement." Every competitor is positioned as weaker across all factors, which is statistically unlikely and suggests confirmation bias.

**Impact If Not Addressed**: Experienced evaluators recognize when an analysis is too optimistic. This can undermine the credibility of the entire competitive assessment and, by extension, the capture strategy.

**Suggested Remedy**: Add a balanced "Our Vulnerabilities" subsection that honestly addresses 2-3 areas where we are at a disadvantage, along with mitigation strategies. This actually strengthens credibility.

---

### Critique 3: Logical Gap in Price Positioning

**Challenge Type**: Logic

**Severity**: Major

**Target Section**: Price-to-Win Analysis

**Challenged Content**: "Recommended Position: MODERATE ($20.5-21.5M annually) ... Our discriminators justify modest premium."

**Argument**: The recommendation to price at moderate-to-premium is inconsistent with earlier analysis showing the incumbent can match or undercut our pricing (they have "lower transition costs"). If the incumbent is likely to price aggressively and price is 30% of the evaluation, how does moderate pricing lead to a win?

**Evidence**: The same document states: "TechCorp (Incumbent): Low-Mid ($19-21M) - Defending position, low transition costs, willing to compress margin." This directly contradicts the recommendation to price in the same range without superior technical scores.

**Impact If Not Addressed**: The pricing strategy may be misaligned with competitive reality, resulting in a price that is neither competitive enough to win on cost nor premium enough to signal superior value.

**Suggested Remedy**: Resolve the logical tension by either: (1) lowering target price to ensure price competitiveness, (2) significantly strengthening technical approach to justify premium, or (3) explicitly stating the win probability given this pricing risk.

---

### Critique 4: Overly Optimistic Win Probability

**Challenge Type**: Risk

**Severity**: Major

**Target Section**: Executive Summary

**Challenged Content**: "Overall Win Probability: 55-65% (Medium-High)"

**Argument**: This probability assessment appears optimistic given the identified challenges: strong incumbent with transition advantage, aggressive competitor pricing, and our acknowledged weaker position on price. The confidence interval is narrow for what should be an uncertain assessment.

**Evidence**: The risk table shows "Incumbent price matching" as High probability/High impact, yet this doesn't appear to materially reduce the win probability estimate. A High/High risk should have significant downward impact on probability.

**Impact If Not Addressed**: Overly optimistic probability assessments can lead to inappropriate resource allocation decisions by leadership and failure to implement aggressive enough capture activities.

**Suggested Remedy**: Either: (1) lower the probability estimate to reflect identified High risks, (2) expand the confidence interval (e.g., 45-65%), or (3) explicitly condition the estimate on mitigation of the High/High risks.

---

### Critique 5: Missing Evaluation Criteria Mapping

**Challenge Type**: Completeness

**Severity**: Minor

**Target Section**: Win Themes

**Challenged Content**: Win Theme evaluation alignment statements

**Argument**: The evaluation criteria alignment statements reference approximate percentages ("Technical Approach (40%)") but the document doesn't show a complete mapping ensuring all evaluation factors are covered by at least one win theme or discriminator.

**Evidence**: Evaluation Factor "Cost/Price Realism (30%)" mentioned in opportunity requirements is not explicitly addressed in any win theme's evaluation alignment section.

**Impact If Not Addressed**: Evaluators may find gaps in addressing evaluation criteria. Even if unintentional, missing coverage could result in lower scores on unaddressed factors.

**Suggested Remedy**: Create a traceability matrix showing each evaluation factor mapped to corresponding win themes and discriminators. Address any gaps identified."""

    def _parse_critiques(
        self,
        content: str,
        document_id: str = "",
        round_number: int = 1,
        default_section: str = "",
    ) -> List[Critique]:
        """Parse critiques from LLM response."""
        critiques = []

        # Split by critique sections
        critique_sections = re.split(r'###\s*Critique\s*\d+', content, flags=re.IGNORECASE)

        for section in critique_sections[1:]:  # Skip first split (before first critique)
            try:
                # Extract title
                title_match = re.search(r'^[:\s]*([^\n]+)', section.strip())
                title = title_match.group(1).strip() if title_match else "Untitled Critique"

                # Extract challenge type
                type_match = re.search(
                    r'\*\*Challenge Type\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                challenge_type_str = type_match.group(1).strip() if type_match else "Logic"
                challenge_type = self._map_challenge_type(challenge_type_str)

                # Extract severity
                severity_match = re.search(
                    r'\*\*Severity\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                severity_str = severity_match.group(1).strip().lower() if severity_match else "major"
                severity = self._map_severity(severity_str)

                # Extract target section
                section_match = re.search(
                    r'\*\*Target Section\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                target_section = section_match.group(1).strip() if section_match else default_section

                # Extract challenged content
                content_match = re.search(
                    r'\*\*Challenged Content\*\*[:\s]*["\']?([^"\']+)["\']?',
                    section,
                    re.IGNORECASE
                )
                target_content = content_match.group(1).strip() if content_match else ""

                # Extract argument
                arg_match = re.search(
                    r'\*\*Argument\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                argument = arg_match.group(1).strip() if arg_match else "No argument provided"

                # Extract evidence
                evidence_match = re.search(
                    r'\*\*Evidence\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                evidence = evidence_match.group(1).strip() if evidence_match else ""

                # Extract remedy
                remedy_match = re.search(
                    r'\*\*Suggested Remedy\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                suggested_remedy = remedy_match.group(1).strip() if remedy_match else "No remedy provided"

                critique = Critique(
                    agent=self.role.value,
                    round_number=round_number,
                    target_document_id=document_id,
                    target_section=target_section,
                    target_content=target_content,
                    challenge_type=challenge_type,
                    severity=severity,
                    title=title,
                    argument=argument,
                    evidence=evidence,
                    suggested_remedy=suggested_remedy,
                )
                critiques.append(critique)

            except Exception as e:
                self.log_warning(f"Failed to parse critique section: {e}")
                continue

        return critiques

    def _map_challenge_type(self, type_str: str) -> ChallengeType:
        """Map string to ChallengeType enum."""
        type_lower = type_str.lower()
        if "logic" in type_lower:
            return ChallengeType.LOGIC
        elif "evidence" in type_lower:
            return ChallengeType.EVIDENCE
        elif "complete" in type_lower:
            return ChallengeType.COMPLETENESS
        elif "risk" in type_lower:
            return ChallengeType.RISK
        elif "compliance" in type_lower:
            return ChallengeType.COMPLIANCE
        elif "feasibility" in type_lower:
            return ChallengeType.FEASIBILITY
        elif "clarity" in type_lower:
            return ChallengeType.CLARITY
        elif "competitive" in type_lower:
            return ChallengeType.COMPETITIVE
        else:
            return ChallengeType.LOGIC

    def _map_severity(self, severity_str: str) -> Severity:
        """Map string to Severity enum."""
        severity_lower = severity_str.lower()
        if "critical" in severity_lower:
            return Severity.CRITICAL
        elif "major" in severity_lower:
            return Severity.MAJOR
        elif "minor" in severity_lower:
            return Severity.MINOR
        elif "observation" in severity_lower:
            return Severity.OBSERVATION
        else:
            return Severity.MAJOR

    def _parse_assumption_analyses(self, content: str) -> List[AssumptionAnalysis]:
        """Parse assumption analyses from LLM response."""
        analyses = []

        # Split by assumption sections
        assumption_sections = re.split(r'###\s*Assumption\s*\d+', content, flags=re.IGNORECASE)

        for section in assumption_sections[1:]:
            try:
                # Extract statement
                statement_match = re.search(
                    r'\*\*Statement\*\*[:\s]*["\']?([^"\']+)["\']?',
                    section,
                    re.IGNORECASE
                )
                statement = statement_match.group(1).strip() if statement_match else ""

                # Extract validity
                validity_match = re.search(
                    r'\*\*Validity.*?\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                validity = validity_match.group(1).strip() if validity_match else "Questionable"

                # Extract challenge
                challenge_match = re.search(
                    r'\*\*Challenge\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                challenge = challenge_match.group(1).strip() if challenge_match else ""

                # Extract alternative scenario
                alt_match = re.search(
                    r'\*\*Alternative Scenario\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                alternative = alt_match.group(1).strip() if alt_match else ""

                # Extract evidence needed
                evidence_match = re.search(
                    r'\*\*Evidence Needed\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                evidence_needed = evidence_match.group(1).strip() if evidence_match else ""

                # Extract recommendation
                rec_match = re.search(
                    r'\*\*Recommendation\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                recommendation = rec_match.group(1).strip() if rec_match else ""

                analysis = AssumptionAnalysis(
                    statement=statement,
                    validity=validity,
                    challenge=challenge,
                    alternative_scenario=alternative,
                    evidence_needed=evidence_needed,
                    recommendation=recommendation,
                )
                analyses.append(analysis)

            except Exception as e:
                self.log_warning(f"Failed to parse assumption analysis: {e}")
                continue

        return analyses

    def _parse_counterarguments(self, content: str) -> List[Counterargument]:
        """Parse counterarguments from LLM response."""
        counterarguments = []

        # Split by claim sections
        claim_sections = re.split(r'###\s*Claim\s*\d+', content, flags=re.IGNORECASE)

        for section in claim_sections[1:]:
            try:
                # Extract original claim
                claim_match = re.search(
                    r'\*\*Original Claim\*\*[:\s]*["\']?([^"\']+)["\']?',
                    section,
                    re.IGNORECASE
                )
                original_claim = claim_match.group(1).strip() if claim_match else ""

                # Extract counterargument
                counter_match = re.search(
                    r'\*\*Counterargument\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                counterargument = counter_match.group(1).strip() if counter_match else ""

                # Extract weakness exposed
                weakness_match = re.search(
                    r'\*\*Weakness Exposed\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                weakness = weakness_match.group(1).strip() if weakness_match else ""

                # Extract recommended response
                response_match = re.search(
                    r'\*\*How.*?Respond\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                recommended_response = response_match.group(1).strip() if response_match else ""

                counter = Counterargument(
                    original_claim=original_claim,
                    counterargument=counterargument,
                    weakness_exposed=weakness,
                    recommended_response=recommended_response,
                )
                counterarguments.append(counter)

            except Exception as e:
                self.log_warning(f"Failed to parse counterargument: {e}")
                continue

        return counterarguments

    def _parse_logical_issues(self, content: str, section_name: str) -> List[LogicalIssue]:
        """Parse logical issues from LLM response."""
        issues = []

        # Split by issue sections
        issue_sections = re.split(r'###\s*Logical Issue\s*\d+', content, flags=re.IGNORECASE)

        for section in issue_sections[1:]:
            try:
                # Extract issue type
                type_match = re.search(r'^[:\s]*([^\n]+)', section.strip())
                issue_type = type_match.group(1).strip() if type_match else "Unknown"

                # Extract location
                location_match = re.search(
                    r'\*\*Location\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                location = location_match.group(1).strip() if location_match else section_name

                # Extract flawed reasoning
                flawed_match = re.search(
                    r'\*\*(?:The\s+)?Flawed Reasoning\*\*[:\s]*["\']?([^"\']+)["\']?',
                    section,
                    re.IGNORECASE
                )
                flawed_reasoning = flawed_match.group(1).strip() if flawed_match else ""

                # Extract explanation
                explain_match = re.search(
                    r'\*\*Why.*?Flawed\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    section,
                    re.IGNORECASE
                )
                explanation = explain_match.group(1).strip() if explain_match else ""

                # Extract correction
                correct_match = re.search(
                    r'\*\*Correct.*?\*\*[:\s]*["\']?([^"\']+)["\']?',
                    section,
                    re.IGNORECASE
                )
                correction = correct_match.group(1).strip() if correct_match else ""

                # Extract severity
                severity_match = re.search(
                    r'\*\*Severity\*\*[:\s]*([^\n]+)',
                    section,
                    re.IGNORECASE
                )
                severity = severity_match.group(1).strip().lower() if severity_match else "major"

                issue = LogicalIssue(
                    issue_type=issue_type,
                    location=location,
                    flawed_reasoning=flawed_reasoning,
                    explanation=explanation,
                    correction=correction,
                    severity=severity,
                )
                issues.append(issue)

            except Exception as e:
                self.log_warning(f"Failed to parse logical issue: {e}")
                continue

        return issues

    def _parse_response_evaluation(self, content: str, critique_id: str) -> ResponseEvaluation:
        """Parse response evaluation from LLM response."""
        evaluation = ResponseEvaluation(critique_id=critique_id)

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

        # Extract strengths
        strengths_match = re.search(
            r'\*\*Strengths.*?\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
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
            r'\*\*Weaknesses.*?\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
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

    def _extract_claims(self, section_drafts: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract key claims from document content."""
        claims = []

        # Common strong claim indicators
        claim_patterns = [
            r'we are the (only|best|most|leading)',
            r'we have (proven|demonstrated|achieved)',
            r'we offer (unique|unmatched|superior)',
            r'our (team|solution|approach) (is|has|provides)',
            r'\d+%\s+(improvement|reduction|increase|savings)',
            r'no competitor',
            r'unlike (any|other)',
        ]

        for section_name, content in section_drafts.items():
            for pattern in claim_patterns:
                matches = re.finditer(
                    rf'([^.]*{pattern}[^.]*\.)',
                    content,
                    re.IGNORECASE
                )
                for match in matches:
                    claims.append({
                        "claim": match.group(1).strip(),
                        "section": section_name,
                    })

        return claims[:10]  # Limit to 10 claims

    def _generate_overall_assessment(self, critiques: List[Critique]) -> str:
        """Generate an overall assessment based on critiques."""
        if not critiques:
            return "No significant issues identified. Document appears sound."

        critical_count = sum(1 for c in critiques if c.severity == Severity.CRITICAL)
        major_count = sum(1 for c in critiques if c.severity == Severity.MAJOR)
        minor_count = sum(1 for c in critiques if c.severity == Severity.MINOR)

        # Count by type
        type_counts = {}
        for c in critiques:
            type_name = c.challenge_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        assessment_parts = []

        if critical_count > 0:
            assessment_parts.append(
                f"**{critical_count} CRITICAL issues** require immediate attention before this document can be approved."
            )
        if major_count > 0:
            assessment_parts.append(
                f"**{major_count} Major issues** should be addressed to strengthen the document."
            )
        if minor_count > 0:
            assessment_parts.append(
                f"**{minor_count} Minor issues** identified for optional improvement."
            )

        # Most common issue types
        if type_counts:
            top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:2]
            type_summary = ", ".join(f"{t[0]} ({t[1]})" for t in top_types)
            assessment_parts.append(f"Primary concern areas: {type_summary}")

        return " ".join(assessment_parts)

    def _format_result_content(
        self,
        result: DevilsAdvocateResult,
        analysis_type: str,
    ) -> str:
        """Format result as content string."""
        parts = ["# Devil's Advocate Analysis", ""]

        # Overall assessment
        if result.overall_assessment:
            parts.append("## Overall Assessment")
            parts.append("")
            parts.append(result.overall_assessment)
            parts.append("")

        # Critique summary
        if result.critique_summary:
            summary = result.critique_summary
            parts.append("## Critique Summary")
            parts.append("")
            parts.append(f"- **Total Critiques**: {summary.total}")
            parts.append(f"- **Critical**: {summary.critical}")
            parts.append(f"- **Major**: {summary.major}")
            parts.append(f"- **Minor**: {summary.minor}")
            parts.append(f"- **Blocking Issues**: {len(summary.blocking_critiques)}")
            parts.append("")

        # Detailed critiques
        if result.critiques:
            parts.append("## Detailed Critiques")
            parts.append("")

            for i, critique in enumerate(result.critiques, 1):
                parts.append(f"### Critique {i}: {critique.title}")
                parts.append("")
                parts.append(f"**Challenge Type**: {critique.challenge_type.value}")
                parts.append(f"**Severity**: {critique.severity.value}")
                parts.append(f"**Target Section**: {critique.target_section}")
                parts.append("")

                if critique.target_content:
                    parts.append(f"**Challenged Content**: \"{critique.target_content[:200]}...\"")
                    parts.append("")

                parts.append(f"**Argument**: {critique.argument}")
                parts.append("")

                if critique.evidence:
                    parts.append(f"**Evidence**: {critique.evidence}")
                    parts.append("")

                parts.append(f"**Suggested Remedy**: {critique.suggested_remedy}")
                parts.append("")
                parts.append("---")
                parts.append("")

        # Assumption analyses
        if result.assumption_analyses:
            parts.append("## Assumption Analysis")
            parts.append("")

            for analysis in result.assumption_analyses:
                parts.append(f"### {analysis.statement[:50]}...")
                parts.append("")
                parts.append(f"**Validity**: {analysis.validity}")
                parts.append(f"**Challenge**: {analysis.challenge}")
                parts.append(f"**Recommendation**: {analysis.recommendation}")
                parts.append("")
                parts.append("---")
                parts.append("")

        # Logical issues
        if result.logical_issues:
            parts.append("## Logical Issues")
            parts.append("")

            for issue in result.logical_issues:
                parts.append(f"### {issue.issue_type}")
                parts.append("")
                parts.append(f"**Location**: {issue.location}")
                parts.append(f"**Severity**: {issue.severity}")
                parts.append(f"**Explanation**: {issue.explanation}")
                parts.append(f"**Correction**: {issue.correction}")
                parts.append("")
                parts.append("---")
                parts.append("")

        # Response evaluations
        if result.response_evaluations:
            parts.append("## Response Evaluations")
            parts.append("")

            for eval in result.response_evaluations:
                parts.append(f"### Critique {eval.critique_id}")
                parts.append("")
                parts.append(f"**Verdict**: {eval.verdict}")
                parts.append(f"**Resolution Status**: {eval.resolution_status}")
                if eval.reasoning:
                    parts.append(f"**Reasoning**: {eval.reasoning}")
                parts.append("")
                parts.append("---")
                parts.append("")

        return "\n".join(parts)
