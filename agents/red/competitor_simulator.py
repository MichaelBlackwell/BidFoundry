"""
Competitor Simulator Agent

Adversarial agent that role-plays likely competitors to expose vulnerabilities
in the blue team's strategy from competitive perspectives.
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

from .prompts.competitor_simulator_prompts import (
    COMPETITOR_SIMULATOR_SYSTEM_PROMPT,
    get_competitor_simulation_prompt,
    get_single_competitor_prompt,
    get_competitive_response_prompt,
    get_incumbent_defense_prompt,
    get_vulnerability_synthesis_prompt,
)


class CompetitorChallengeType:
    """Challenge types specific to competitive analysis."""
    COMPETITIVE = "Competitive"
    TECHNICAL = "Technical"
    EXPERIENCE = "Experience"
    PRICING = "Pricing"
    RISK = "Risk"
    INCUMBENT = "Incumbent"


@dataclass
class CompetitorPerspective:
    """A competitor's perspective on the client's strategy."""

    competitor_name: str
    is_incumbent: bool = False
    estimated_strength: str = "Unknown"

    # Competitor's self-view
    self_assessment: str = ""
    key_strengths: List[str] = field(default_factory=list)

    # View of client
    client_threat_level: str = "Unknown"  # High, Medium, Low
    client_perceived_weaknesses: List[str] = field(default_factory=list)

    # Win strategy
    predicted_strategy: str = ""
    key_differentiators: List[str] = field(default_factory=list)
    pricing_approach: str = ""

    def to_dict(self) -> dict:
        return {
            "competitor_name": self.competitor_name,
            "is_incumbent": self.is_incumbent,
            "estimated_strength": self.estimated_strength,
            "self_assessment": self.self_assessment,
            "key_strengths": self.key_strengths,
            "client_threat_level": self.client_threat_level,
            "client_perceived_weaknesses": self.client_perceived_weaknesses,
            "predicted_strategy": self.predicted_strategy,
            "key_differentiators": self.key_differentiators,
            "pricing_approach": self.pricing_approach,
        }


@dataclass
class CompetitiveVulnerability:
    """A vulnerability identified from a competitor's perspective."""

    competitor_name: str
    title: str
    target_section: str = ""
    target_content: str = ""

    # Classification
    challenge_type: str = CompetitorChallengeType.COMPETITIVE
    severity: str = "major"

    # Competitive analysis
    competitor_attack: str = ""
    competitive_advantage: str = ""
    evidence: str = ""

    # Defensive guidance
    defensive_recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "competitor_name": self.competitor_name,
            "title": self.title,
            "target_section": self.target_section,
            "target_content": self.target_content,
            "challenge_type": self.challenge_type,
            "severity": self.severity,
            "competitor_attack": self.competitor_attack,
            "competitive_advantage": self.competitive_advantage,
            "evidence": self.evidence,
            "defensive_recommendation": self.defensive_recommendation,
        }

    def to_critique(
        self,
        agent: str,
        round_number: int = 1,
        document_id: str = "",
    ) -> Critique:
        """Convert vulnerability to standard Critique format."""
        # Map competitive challenge types to standard ChallengeType
        challenge_type_map = {
            CompetitorChallengeType.COMPETITIVE: ChallengeType.COMPETITIVE,
            CompetitorChallengeType.TECHNICAL: ChallengeType.FEASIBILITY,
            CompetitorChallengeType.EXPERIENCE: ChallengeType.EVIDENCE,
            CompetitorChallengeType.PRICING: ChallengeType.RISK,
            CompetitorChallengeType.RISK: ChallengeType.RISK,
            CompetitorChallengeType.INCUMBENT: ChallengeType.COMPETITIVE,
        }

        severity_map = {
            "critical": Severity.CRITICAL,
            "major": Severity.MAJOR,
            "minor": Severity.MINOR,
            "observation": Severity.OBSERVATION,
        }

        return Critique(
            agent=agent,
            round_number=round_number,
            target_document_id=document_id,
            target_section=self.target_section,
            target_content=self.target_content,
            challenge_type=challenge_type_map.get(self.challenge_type, ChallengeType.COMPETITIVE),
            severity=severity_map.get(self.severity, Severity.MAJOR),
            title=f"[{self.competitor_name}] {self.title}",
            argument=self.competitor_attack,
            evidence=f"Competitive advantage: {self.competitive_advantage}. {self.evidence}",
            suggested_remedy=self.defensive_recommendation,
        )


@dataclass
class CompetitorAnalysis:
    """Complete analysis from a single competitor's perspective."""

    competitor_name: str
    is_incumbent: bool = False

    # Perspective
    perspective: Optional[CompetitorPerspective] = None

    # Vulnerabilities identified
    vulnerabilities: List[CompetitiveVulnerability] = field(default_factory=list)

    # Win strategy
    win_strategy: str = ""

    # Defensive recommendations
    defensive_recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "competitor_name": self.competitor_name,
            "is_incumbent": self.is_incumbent,
            "perspective": self.perspective.to_dict() if self.perspective else None,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "win_strategy": self.win_strategy,
            "defensive_recommendations": self.defensive_recommendations,
        }


@dataclass
class CompetitorSimulatorResult:
    """Result of Competitor Simulator analysis operations."""

    # Primary outputs
    competitor_analyses: List[CompetitorAnalysis] = field(default_factory=list)
    critiques: List[Critique] = field(default_factory=list)

    # Synthesis
    cross_competitor_patterns: List[str] = field(default_factory=list)
    prioritized_vulnerabilities: List[CompetitiveVulnerability] = field(default_factory=list)
    integrated_recommendations: List[str] = field(default_factory=list)

    # Summary
    critique_summary: Optional[CritiqueSummary] = None
    overall_competitive_assessment: str = ""

    # Meta
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "competitor_analyses": [a.to_dict() for a in self.competitor_analyses],
            "critiques": [c.to_dict() for c in self.critiques],
            "cross_competitor_patterns": self.cross_competitor_patterns,
            "prioritized_vulnerabilities": [v.to_dict() for v in self.prioritized_vulnerabilities],
            "integrated_recommendations": self.integrated_recommendations,
            "critique_summary": self.critique_summary.to_dict() if self.critique_summary else None,
            "overall_competitive_assessment": self.overall_competitive_assessment,
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "token_usage": self.token_usage,
        }


class CompetitorSimulatorAgent(RedTeamAgent):
    """
    The Competitor Simulator role-plays as competitors to expose vulnerabilities.

    Responsibilities:
    - Adopt persona of each major competitor
    - Predict their likely bid strategy
    - Identify where client is vulnerable to competitor strengths
    - Suggest defensive positioning

    The Competitor Simulator:
    - Takes a hostile, competitive perspective
    - Grounds assessments in available competitive intelligence
    - Provides actionable defensive recommendations
    - Simulates 2-3 competitor personas per engagement
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Competitor Simulator agent.

        Args:
            config: Optional agent configuration. If not provided, uses defaults.
        """
        if config is None:
            from agents.config import get_default_config
            config = get_default_config(AgentRole.COMPETITOR_SIMULATOR)

        super().__init__(config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.COMPETITOR_SIMULATOR

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.RED

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and generate competitive vulnerability analysis.

        The processing mode depends on the context:
        - Full competitive analysis (multiple competitors)
        - Single competitor deep dive
        - Incumbent defense analysis
        - Claim-specific counter-positioning

        Args:
            context: SwarmContext containing document content and competitor intel

        Returns:
            AgentOutput with vulnerabilities and competitive analysis
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
            analysis_type = context.custom_data.get("analysis_type", "full_simulation")

            if analysis_type == "single_competitor":
                result = await self._simulate_single_competitor(context)
            elif analysis_type == "incumbent_defense":
                result = await self._simulate_incumbent_defense(context)
            elif analysis_type == "claim_counter":
                result = await self._generate_claim_counter(context)
            else:
                # Full multi-competitor simulation
                result = await self._simulate_all_competitors(context)

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
                    "competitors_analyzed": len(result.competitor_analyses),
                    "vulnerabilities_found": sum(
                        len(a.vulnerabilities) for a in result.competitor_analyses
                    ),
                    "critique_count": len(result.critiques),
                    "critical_count": sum(1 for c in result.critiques if c.severity == Severity.CRITICAL),
                    "major_count": sum(1 for c in result.critiques if c.severity == Severity.MAJOR),
                    "minor_count": sum(1 for c in result.critiques if c.severity == Severity.MINOR),
                },
            )

        except Exception as e:
            self.log_error(f"Error in Competitor Simulator processing: {e}")
            return self._create_output(
                success=False,
                error_message=f"Processing error: {str(e)}",
            )

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate the context for Competitor Simulator processing.

        Args:
            context: The SwarmContext to validate

        Returns:
            List of validation error messages
        """
        errors = super().validate_context(context)

        # Need document content to analyze
        if not context.section_drafts and not context.current_draft:
            errors.append("No document content provided to analyze")

        # Need competitor intelligence (either from opportunity or custom_data)
        competitors = self._get_competitors(context)
        if not competitors:
            errors.append("No competitor intelligence provided. Add competitors to opportunity.competitor_intel or context.custom_data['competitors']")

        return errors

    def _get_competitors(self, context: SwarmContext) -> List[Dict[str, Any]]:
        """Extract competitor list from context."""
        # Check custom_data first (explicit override)
        if context.custom_data.get("competitors"):
            return context.custom_data["competitors"]

        # Check opportunity for competitor intel
        if context.opportunity:
            competitor_intel = context.opportunity.get("competitor_intel", {})
            if competitor_intel and competitor_intel.get("competitors"):
                return competitor_intel["competitors"]

        return []

    async def critique_section(
        self,
        context: SwarmContext,
        section_name: str,
        section_content: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate competitive critiques for a specific section.

        Implementation of RedTeamAgent abstract method.

        Args:
            context: The swarm context
            section_name: Name of the section to critique
            section_content: Current content of the section

        Returns:
            List of critique dictionaries
        """
        # Set up context for section-focused analysis
        context.custom_data["focus_section"] = section_name
        context.section_drafts = {section_name: section_content}

        result = await self._simulate_all_competitors(context)
        return [c.to_dict() for c in result.critiques]

    async def evaluate_response(
        self,
        context: SwarmContext,
        critique: Dict[str, Any],
        response: Dict[str, Any],
    ) -> bool:
        """
        Evaluate whether a blue team response adequately addresses a competitive critique.

        Implementation of RedTeamAgent abstract method.

        Args:
            context: The swarm context
            critique: The original critique
            response: The blue team's response

        Returns:
            True if the response adequately addresses the competitive vulnerability
        """
        # For competitive vulnerabilities, we're stricter about evaluation
        disposition = response.get("disposition", "")
        action = response.get("action", "")
        evidence = response.get("evidence", "")

        # Accept is acceptable if they provide evidence
        if disposition == "Accept" and (action or evidence):
            return True

        # Rebut needs strong evidence for competitive claims
        if disposition == "Rebut":
            # Need substantial evidence to rebut a competitive vulnerability
            if evidence and len(evidence) > 100:
                return True
            return False

        # Acknowledge means they see the issue but can't fully address it
        if disposition == "Acknowledge":
            # Acceptable only if they have a mitigation plan
            return bool(response.get("residual_risk"))

        return False

    async def _simulate_all_competitors(
        self,
        context: SwarmContext,
    ) -> CompetitorSimulatorResult:
        """
        Simulate all known competitors and identify vulnerabilities.

        Args:
            context: SwarmContext with document content and competitor intel

        Returns:
            CompetitorSimulatorResult with all analyses
        """
        result = CompetitorSimulatorResult()

        # Get competitors to simulate
        competitors = self._get_competitors(context)
        if not competitors:
            result.success = False
            result.errors.append("No competitors to simulate")
            return result

        # Limit to top 3 competitors
        competitors_to_simulate = competitors[:3]

        # Collect document content
        document_content = context.section_drafts.copy()
        if context.current_draft and isinstance(context.current_draft, dict):
            if "sections" in context.current_draft:
                document_content.update(context.current_draft["sections"])

        if not document_content:
            result.success = False
            result.errors.append("No document content to analyze")
            return result

        # Generate simulation prompt
        prompt = get_competitor_simulation_prompt(
            document_type=context.document_type or "Strategy Document",
            document_content=document_content,
            competitors=competitors_to_simulate,
            company_profile=context.company_profile,
            opportunity=context.opportunity,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPETITOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse the response into competitor analyses
        result.competitor_analyses = self._parse_competitor_analyses(
            content,
            competitors_to_simulate,
        )

        # Convert vulnerabilities to critiques
        for analysis in result.competitor_analyses:
            for vuln in analysis.vulnerabilities:
                critique = vuln.to_critique(
                    agent=self.role.value,
                    round_number=context.round_number,
                    document_id=context.document_id or "",
                )
                result.critiques.append(critique)

        # Generate overall competitive assessment
        result.overall_competitive_assessment = self._generate_competitive_assessment(
            result.competitor_analyses
        )

        # Identify cross-competitor patterns
        result.cross_competitor_patterns = self._identify_cross_competitor_patterns(
            result.competitor_analyses
        )

        # Generate integrated recommendations
        result.integrated_recommendations = self._generate_integrated_recommendations(
            result.competitor_analyses
        )

        return result

    async def _simulate_single_competitor(
        self,
        context: SwarmContext,
    ) -> CompetitorSimulatorResult:
        """
        Perform deep simulation of a single competitor.

        Args:
            context: SwarmContext with target competitor in custom_data

        Returns:
            CompetitorSimulatorResult with single competitor analysis
        """
        result = CompetitorSimulatorResult()

        # Get the target competitor
        target_competitor = context.custom_data.get("target_competitor")
        if not target_competitor:
            # Fall back to first competitor
            competitors = self._get_competitors(context)
            if competitors:
                target_competitor = competitors[0]
            else:
                result.success = False
                result.errors.append("No target competitor specified")
                return result

        # Get document content
        document_content = context.section_drafts.copy()
        if context.current_draft and isinstance(context.current_draft, dict):
            if "sections" in context.current_draft:
                document_content.update(context.current_draft["sections"])

        prompt = get_single_competitor_prompt(
            competitor=target_competitor,
            document_content=document_content,
            document_type=context.document_type or "Strategy Document",
            company_profile=context.company_profile,
            opportunity=context.opportunity,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPETITOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse the single competitor analysis
        analysis = self._parse_single_competitor_analysis(
            content,
            target_competitor,
        )
        result.competitor_analyses = [analysis]

        # Convert to critiques
        for vuln in analysis.vulnerabilities:
            critique = vuln.to_critique(
                agent=self.role.value,
                round_number=context.round_number,
                document_id=context.document_id or "",
            )
            result.critiques.append(critique)

        return result

    async def _simulate_incumbent_defense(
        self,
        context: SwarmContext,
    ) -> CompetitorSimulatorResult:
        """
        Simulate the incumbent's defense strategy.

        Args:
            context: SwarmContext with incumbent info

        Returns:
            CompetitorSimulatorResult with incumbent defense analysis
        """
        result = CompetitorSimulatorResult()

        # Get incumbent
        competitors = self._get_competitors(context)
        incumbent = None
        for comp in competitors:
            if comp.get("is_incumbent"):
                incumbent = comp
                break

        if not incumbent:
            result.success = False
            result.errors.append("No incumbent found in competitor intelligence")
            return result

        # Get document content (this is the challenger's strategy)
        document_content = context.section_drafts.copy()

        prompt = get_incumbent_defense_prompt(
            incumbent=incumbent,
            challenger_strategy=document_content,
            opportunity=context.opportunity,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPETITOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse incumbent analysis
        analysis = self._parse_incumbent_defense_analysis(content, incumbent)
        result.competitor_analyses = [analysis]

        # Convert to critiques
        for vuln in analysis.vulnerabilities:
            critique = vuln.to_critique(
                agent=self.role.value,
                round_number=context.round_number,
                document_id=context.document_id or "",
            )
            result.critiques.append(critique)

        return result

    async def _generate_claim_counter(
        self,
        context: SwarmContext,
    ) -> CompetitorSimulatorResult:
        """
        Generate counter-positioning for a specific claim.

        Args:
            context: SwarmContext with claim details in custom_data

        Returns:
            CompetitorSimulatorResult with claim counter-analysis
        """
        result = CompetitorSimulatorResult()

        claim = context.custom_data.get("claim")
        claim_section = context.custom_data.get("claim_section", "Unknown")
        competitor = context.custom_data.get("target_competitor")

        if not claim:
            result.success = False
            result.errors.append("No claim provided to counter")
            return result

        if not competitor:
            competitors = self._get_competitors(context)
            if competitors:
                competitor = competitors[0]
            else:
                result.success = False
                result.errors.append("No competitor specified for counter-positioning")
                return result

        prompt = get_competitive_response_prompt(
            competitor=competitor,
            client_claim=claim,
            claim_section=claim_section,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPETITOR_SIMULATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.token_usage = llm_response.get("usage", {})

        # Parse counter-positioning
        vuln = self._parse_claim_counter(content, competitor, claim, claim_section)

        analysis = CompetitorAnalysis(
            competitor_name=competitor.get("name", "Unknown"),
            is_incumbent=competitor.get("is_incumbent", False),
            vulnerabilities=[vuln] if vuln else [],
        )
        result.competitor_analyses = [analysis]

        if vuln:
            critique = vuln.to_critique(
                agent=self.role.value,
                round_number=context.round_number,
                document_id=context.document_id or "",
            )
            result.critiques.append(critique)

        return result

    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock competitor analysis content for testing."""
        prompt_lower = prompt.lower()

        if "deep competitor simulation" in prompt_lower or "single competitor" in prompt_lower:
            return """### 1. Initial Threat Assessment

This competitor presents a **moderate threat** to our position. While they have relevant experience, their approach appears generic and lacks the specific proof points needed to unseat us.

### 2. Target Weaknesses You Will Exploit

**Vulnerability 1: Transition Risk Underestimation**

- **Challenge Type**: Incumbent
- **Severity**: Critical
- **Target Section**: Win Themes
- **Competitor's Attack**: They claim seamless transition but provide no transition plan details or risk mitigation. We have zero transition risk as incumbent.
- **Competitive Advantage**: 5 years of institutional knowledge and zero disruption risk
- **Evidence**: Our 5-year track record with zero service disruptions
- **Defensive Recommendation**: Add detailed 90-day transition plan with specific risk mitigation strategies

**Vulnerability 2: Vague Past Performance**

- **Challenge Type**: Experience
- **Severity**: Major
- **Target Section**: Past Performance
- **Competitor's Attack**: They cite "multiple federal cloud migrations" but provide no specific metrics or contract references
- **Competitive Advantage**: We can cite specific CPARS ratings and contract values
- **Evidence**: DHS Contract #GS-35F-0001X - Exceptional rating, $12.5M value
- **Defensive Recommendation**: Add specific contract references with CPARS ratings and quantified outcomes

**Vulnerability 3: Overstated Technical Capabilities**

- **Challenge Type**: Technical
- **Severity**: Major
- **Target Section**: Technical Approach
- **Competitor's Attack**: "Best-in-class" is unprovable marketing language that evaluators will discount
- **Competitive Advantage**: We have documented platform capabilities with third-party validation
- **Evidence**: FedRAMP High authorization, AWS GovCloud certification
- **Defensive Recommendation**: Replace superlatives with quantified, verifiable technical claims

**Vulnerability 4: Pricing Disconnect**

- **Challenge Type**: Pricing
- **Severity**: Major
- **Target Section**: Pricing Strategy
- **Competitor's Attack**: Premium pricing with unsubstantiated claims is a losing combination
- **Competitive Advantage**: We can price competitively with proven performance to back it up
- **Evidence**: Historical pricing data from current contract
- **Defensive Recommendation**: Consider more competitive pricing or strengthen value justification

### 3. Your Win Strategy Against This Target

**Key Differentiators**:
- Zero transition risk (incumbent advantage)
- Proven performance track record with this customer
- Established relationships with key stakeholders
- Competitive pricing based on known cost structure

**Weaknesses to Highlight**:
- Their lack of specific agency experience
- Transition risk they represent
- Unsubstantiated claims throughout their proposal

**Pricing Strategy**:
- Price aggressively to remove price as a differentiator
- Emphasize value of continuity and reduced risk

### 4. Recommendations for Target's Defense

To counter our attack, they should:
- Add specific contract references with metrics to Past Performance
- Develop detailed transition plan with risk mitigation
- Replace superlatives with quantified, provable claims
- Consider more competitive pricing given their challenger position
- Acknowledge transition risk openly and address it directly"""

        elif "counter-positioning" in prompt_lower or "counter this client claim" in prompt_lower:
            return """### Claim Analysis

**Claim Strength**: Moderate - the claim has some merit but lacks supporting evidence

**Vulnerabilities in Claim**: The claim of 50% reduction lacks specific metrics, timeframes, or client references

### Your Counter-Positioning

**Your Counter-Claim**: While the competitor touts a "50% reduction," our proven methodology delivers documented results with specific metrics across multiple federal agencies.

**Your Evidence**: We have achieved 45% average migration time reduction across 5 federal contracts, with documented CPARS ratings of Exceptional.

**Attack Angle**: Evaluators should ask: where's the proof? Generic claims without specific contract references suggest marketing language rather than proven capability.

### Recommendation for Client

**How to Defend**: Add specific contract references showing the 50% reduction, including agency names, contract values, and independent validation of the claimed improvement."""

        elif "incumbent defense" in prompt_lower:
            return """### 1. Transition Risk Narrative

As the incumbent, we will emphasize:

**Vulnerability 1: Knowledge Transfer Risk**

- **Challenge Type**: Incumbent
- **Severity**: Critical
- **Target Section**: Transition Approach
- **Competitor's Attack**: Any new contractor will face 6-12 months of learning curve. Our team knows the undocumented requirements, the stakeholder preferences, and the system quirks.
- **Competitive Advantage**: Zero knowledge transfer risk - we already have the knowledge
- **Evidence**: 5 years of institutional knowledge; key personnel with agency relationships
- **Defensive Recommendation**: Challenger should provide detailed knowledge capture plan and accelerated onboarding approach

**Vulnerability 2: Service Continuity Risk**

- **Challenge Type**: Risk
- **Severity**: Critical
- **Target Section**: Technical Approach
- **Competitor's Attack**: Transitions always carry risk of service disruption. Are you willing to risk mission-critical services?
- **Competitive Advantage**: Proven continuity - we've maintained 99.9% uptime
- **Evidence**: Documented uptime metrics and CPARS ratings
- **Defensive Recommendation**: Include service level guarantees and penalties in proposal

### 2. Challenger Weaknesses to Highlight

**Vulnerability 3: Unproven with This Agency**

- **Challenge Type**: Experience
- **Severity**: Major
- **Target Section**: Past Performance
- **Competitor's Attack**: They may have cloud experience, but not with our specific agency. We know DHS requirements.
- **Competitive Advantage**: Agency-specific experience and relationships
- **Evidence**: 5-year performance history with DHS
- **Defensive Recommendation**: Emphasize any DHS sub-work or personnel with DHS experience

### 3. Your Differentiators to Emphasize

- Proven track record on this exact requirement
- Established team with security clearances in place
- Deep understanding of agency culture and priorities
- Zero mobilization time required

### 4. Pricing Strategy

We will price at or slightly below the challenger to remove price as a factor and make this a pure incumbent-advantage decision.

### 5. Recommendations for Challenger's Defense

The challenger should:
- Provide detailed transition plan with specific milestones
- Offer service level guarantees with financial penalties
- Cite personnel with direct agency experience
- Address incumbent advantages directly rather than ignoring them
- Consider aggressive pricing to offset transition risk premium"""

        else:
            # Full multi-competitor simulation
            return """### Competitor Analysis: TechCorp Federal (INCUMBENT)

#### Competitor Perspective

**Competitor's Self-Assessment**: TechCorp sees themselves as the natural choice. They have the relationships, the track record, and zero transition risk. They're confident but will price aggressively to defend.

**Competitor's View of Client**: They view the challenger as a threat but believe the transition risk narrative will win. They see the challenger's generic claims as weak points.

**Predicted Win Strategy**: Emphasize continuity, highlight transition risks, price competitively, leverage relationships.

#### Vulnerabilities Identified

**Vulnerability 1: Incumbent Transition Risk Narrative**

- **Challenge Type**: Incumbent
- **Severity**: Critical
- **Target Section**: Transition Approach
- **Competitor's Attack**: The incumbent will hammer the transition risk message. "Why take a chance on disruption when we're performing well?"
- **Competitive Advantage**: TechCorp has zero transition risk and 5 years of institutional knowledge
- **Evidence**: Incumbent recompete win rates are historically 60-70%
- **Defensive Recommendation**: Develop detailed transition plan with risk mitigation. Acknowledge transition as a real factor and address it head-on.

**Vulnerability 2: Relationship Disadvantage**

- **Challenge Type**: Competitive
- **Severity**: Major
- **Target Section**: Win Themes
- **Competitor's Attack**: TechCorp's Program Manager has direct relationships with agency leadership. They'll leverage this during orals.
- **Competitive Advantage**: Established trust and communication channels
- **Evidence**: 5 years of joint collaboration
- **Defensive Recommendation**: Identify any personnel with agency relationships. Emphasize customer references from similar agencies.

**Vulnerability 3: Pricing Pressure**

- **Challenge Type**: Pricing
- **Severity**: Major
- **Target Section**: Pricing Strategy
- **Competitor's Attack**: TechCorp knows the true cost structure and can price aggressively to defend. Challenger's premium pricing strategy is vulnerable.
- **Competitive Advantage**: Lower risk premium required; known cost drivers
- **Evidence**: Incumbent typically has 10-15% cost advantage
- **Defensive Recommendation**: Reconsider premium pricing. May need to price more competitively to offset transition risk perception.

---

### Competitor Analysis: CloudFirst Solutions (CHALLENGER)

#### Competitor Perspective

**Competitor's Self-Assessment**: CloudFirst believes their modern technology and innovative approach will differentiate them. They're aggressive and willing to invest in winning.

**Competitor's View of Client**: They see us as a peer competitor but believe they have superior technology and are willing to price aggressively.

**Predicted Win Strategy**: Lead with innovation, attack incumbent's legacy approach, price to win.

#### Vulnerabilities Identified

**Vulnerability 1: Technical Differentiation Gap**

- **Challenge Type**: Technical
- **Severity**: Major
- **Target Section**: Technical Approach
- **Competitor's Attack**: CloudFirst has AWS Premier Partner status and a proprietary migration accelerator. They'll position our approach as generic.
- **Competitive Advantage**: CloudFirst's accelerator reduces migration time by 40% (documented)
- **Evidence**: AWS partner tier and case studies
- **Defensive Recommendation**: Strengthen technical differentiators. If we have tools or methodologies, document them with metrics.

**Vulnerability 2: Aggressive Pricing**

- **Challenge Type**: Pricing
- **Severity**: Major
- **Target Section**: Pricing Strategy
- **Competitor's Attack**: CloudFirst is willing to price below market to win. They view this as a strategic footprint opportunity.
- **Competitive Advantage**: Willingness to absorb lower margins for market entry
- **Evidence**: Pattern of aggressive bids in new markets
- **Defensive Recommendation**: Be prepared for significant price competition. May need to offer added value rather than compete on price alone.

---

### Cross-Competitor Patterns

1. **Transition Risk**: Both incumbent TechCorp and CloudFirst will use different transition narratives. TechCorp says "don't risk change," CloudFirst says "legacy is risk."

2. **Pricing Pressure**: Both competitors are positioned to price aggressively - incumbent to defend, challenger to win. Our premium strategy is vulnerable from both directions.

3. **Technical Proof Points**: Both competitors have concrete, documented capabilities. Our claims need equivalent evidence.

### Integrated Defensive Recommendations

1. **Must Address (Critical)**:
   - Develop comprehensive transition plan with risk mitigation
   - Add specific, quantified proof points to technical claims
   - Reconsider pricing strategy given competitive pressure

2. **Should Address (Major)**:
   - Strengthen personnel value proposition
   - Add customer references and testimonials
   - Document any proprietary tools or methodologies

3. **Consider Addressing (Minor)**:
   - Add competitive positioning that acknowledges and addresses competitor strengths
   - Develop specific counter-narratives for likely competitor attacks"""

    def _parse_competitor_analyses(
        self,
        content: str,
        competitors: List[Dict[str, Any]],
    ) -> List[CompetitorAnalysis]:
        """Parse competitor analyses from LLM response."""
        analyses = []

        # Split by competitor sections
        competitor_sections = re.split(
            r'###\s*Competitor Analysis[:\s]*',
            content,
            flags=re.IGNORECASE
        )

        for section in competitor_sections[1:]:  # Skip first split
            # Extract competitor name
            name_match = re.match(r'([^\n(]+)', section.strip())
            if not name_match:
                continue

            competitor_name = name_match.group(1).strip()

            # Find matching competitor
            matching_competitor = None
            for comp in competitors:
                if comp.get("name", "").lower() in competitor_name.lower():
                    matching_competitor = comp
                    break

            is_incumbent = matching_competitor.get("is_incumbent", False) if matching_competitor else "incumbent" in competitor_name.lower()

            analysis = CompetitorAnalysis(
                competitor_name=competitor_name,
                is_incumbent=is_incumbent,
            )

            # Parse perspective
            perspective = self._parse_competitor_perspective(section, competitor_name)
            analysis.perspective = perspective

            # Parse vulnerabilities
            analysis.vulnerabilities = self._parse_vulnerabilities(section, competitor_name)

            # Parse win strategy
            strategy_match = re.search(
                r'\*\*Predicted Win Strategy\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                section,
                re.IGNORECASE
            )
            if strategy_match:
                analysis.win_strategy = strategy_match.group(1).strip()

            analyses.append(analysis)

        return analyses

    def _parse_competitor_perspective(
        self,
        section: str,
        competitor_name: str,
    ) -> CompetitorPerspective:
        """Parse competitor perspective from section."""
        perspective = CompetitorPerspective(competitor_name=competitor_name)

        # Self-assessment
        self_match = re.search(
            r'\*\*Competitor\'s Self-Assessment\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
            section,
            re.IGNORECASE
        )
        if self_match:
            perspective.self_assessment = self_match.group(1).strip()

        # View of client
        view_match = re.search(
            r'\*\*Competitor\'s View of Client\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
            section,
            re.IGNORECASE
        )
        if view_match:
            text = view_match.group(1).strip()
            perspective.client_perceived_weaknesses = [text]

            # Infer threat level
            if "significant" in text.lower() or "major" in text.lower():
                perspective.client_threat_level = "High"
            elif "weak" in text.lower() or "minor" in text.lower():
                perspective.client_threat_level = "Low"
            else:
                perspective.client_threat_level = "Medium"

        return perspective

    def _parse_vulnerabilities(
        self,
        section: str,
        competitor_name: str,
    ) -> List[CompetitiveVulnerability]:
        """Parse vulnerabilities from a competitor section."""
        vulnerabilities = []

        # Split by vulnerability markers
        vuln_sections = re.split(
            r'\*\*Vulnerability\s*\d*[:\s]*',
            section,
            flags=re.IGNORECASE
        )

        for vuln_section in vuln_sections[1:]:
            try:
                # Extract title
                title_match = re.match(r'([^\n*]+)', vuln_section.strip())
                title = title_match.group(1).strip() if title_match else "Untitled"

                # Extract challenge type
                type_match = re.search(
                    r'\*\*Challenge Type\*\*[:\s]*([^\n]+)',
                    vuln_section,
                    re.IGNORECASE
                )
                challenge_type = type_match.group(1).strip() if type_match else CompetitorChallengeType.COMPETITIVE

                # Extract severity
                severity_match = re.search(
                    r'\*\*Severity\*\*[:\s]*([^\n]+)',
                    vuln_section,
                    re.IGNORECASE
                )
                severity = severity_match.group(1).strip().lower() if severity_match else "major"

                # Extract target section
                section_match = re.search(
                    r'\*\*Target Section\*\*[:\s]*([^\n]+)',
                    vuln_section,
                    re.IGNORECASE
                )
                target_section = section_match.group(1).strip() if section_match else ""

                # Extract competitor attack
                attack_match = re.search(
                    r'\*\*(?:Competitor\'s Attack|Your attack angle)\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    vuln_section,
                    re.IGNORECASE
                )
                competitor_attack = attack_match.group(1).strip() if attack_match else ""

                # Extract competitive advantage
                advantage_match = re.search(
                    r'\*\*(?:Competitive Advantage|Your advantage)\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    vuln_section,
                    re.IGNORECASE
                )
                competitive_advantage = advantage_match.group(1).strip() if advantage_match else ""

                # Extract evidence
                evidence_match = re.search(
                    r'\*\*(?:Evidence|Your proof points)\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    vuln_section,
                    re.IGNORECASE
                )
                evidence = evidence_match.group(1).strip() if evidence_match else ""

                # Extract defensive recommendation
                defense_match = re.search(
                    r'\*\*Defensive Recommendation\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                    vuln_section,
                    re.IGNORECASE
                )
                defensive_recommendation = defense_match.group(1).strip() if defense_match else ""

                vuln = CompetitiveVulnerability(
                    competitor_name=competitor_name,
                    title=title,
                    target_section=target_section,
                    challenge_type=challenge_type,
                    severity=severity,
                    competitor_attack=competitor_attack,
                    competitive_advantage=competitive_advantage,
                    evidence=evidence,
                    defensive_recommendation=defensive_recommendation,
                )
                vulnerabilities.append(vuln)

            except Exception as e:
                self.log_warning(f"Failed to parse vulnerability: {e}")
                continue

        return vulnerabilities

    def _parse_single_competitor_analysis(
        self,
        content: str,
        competitor: Dict[str, Any],
    ) -> CompetitorAnalysis:
        """Parse analysis for a single competitor deep-dive."""
        competitor_name = competitor.get("name", "Unknown")

        analysis = CompetitorAnalysis(
            competitor_name=competitor_name,
            is_incumbent=competitor.get("is_incumbent", False),
        )

        # Parse vulnerabilities from "Target Weaknesses" section
        analysis.vulnerabilities = self._parse_vulnerabilities(content, competitor_name)

        # Parse win strategy
        strategy_match = re.search(
            r'###\s*3\.\s*Your Win Strategy.*?\n([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )
        if strategy_match:
            analysis.win_strategy = strategy_match.group(1).strip()

        # Parse defensive recommendations
        defense_match = re.search(
            r'###\s*4\.\s*Recommendations.*?\n([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )
        if defense_match:
            rec_text = defense_match.group(1)
            # Extract bullet points
            recs = re.findall(r'[-•]\s*([^\n]+)', rec_text)
            analysis.defensive_recommendations = recs

        return analysis

    def _parse_incumbent_defense_analysis(
        self,
        content: str,
        incumbent: Dict[str, Any],
    ) -> CompetitorAnalysis:
        """Parse incumbent defense analysis."""
        incumbent_name = incumbent.get("name", "Incumbent")

        analysis = CompetitorAnalysis(
            competitor_name=incumbent_name,
            is_incumbent=True,
        )

        # Parse vulnerabilities from the various sections
        analysis.vulnerabilities = self._parse_vulnerabilities(content, incumbent_name)

        # Add recommendations
        rec_match = re.search(
            r'###\s*5\.\s*Recommendations.*?\n([\s\S]*?)(?=###|$)',
            content,
            re.IGNORECASE
        )
        if rec_match:
            rec_text = rec_match.group(1)
            recs = re.findall(r'[-•]\s*([^\n]+)', rec_text)
            analysis.defensive_recommendations = recs

        return analysis

    def _parse_claim_counter(
        self,
        content: str,
        competitor: Dict[str, Any],
        claim: str,
        claim_section: str,
    ) -> Optional[CompetitiveVulnerability]:
        """Parse counter-positioning for a specific claim."""
        try:
            # Extract counter-claim
            counter_match = re.search(
                r'\*\*Your Counter-Claim\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                content,
                re.IGNORECASE
            )
            counter_claim = counter_match.group(1).strip() if counter_match else ""

            # Extract attack angle
            attack_match = re.search(
                r'\*\*Attack Angle\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                content,
                re.IGNORECASE
            )
            attack_angle = attack_match.group(1).strip() if attack_match else ""

            # Extract evidence
            evidence_match = re.search(
                r'\*\*Your Evidence\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                content,
                re.IGNORECASE
            )
            evidence = evidence_match.group(1).strip() if evidence_match else ""

            # Extract defense recommendation
            defense_match = re.search(
                r'\*\*How to Defend\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                content,
                re.IGNORECASE
            )
            defense = defense_match.group(1).strip() if defense_match else ""

            # Determine severity based on claim strength assessment
            strength_match = re.search(
                r'\*\*Claim Strength\*\*[:\s]*([^\n]+)',
                content,
                re.IGNORECASE
            )
            if strength_match:
                strength = strength_match.group(1).strip().lower()
                if "weak" in strength:
                    severity = "critical"
                elif "moderate" in strength:
                    severity = "major"
                else:
                    severity = "minor"
            else:
                severity = "major"

            return CompetitiveVulnerability(
                competitor_name=competitor.get("name", "Unknown"),
                title=f"Counter to: {claim[:50]}...",
                target_section=claim_section,
                target_content=claim,
                challenge_type=CompetitorChallengeType.COMPETITIVE,
                severity=severity,
                competitor_attack=f"{counter_claim} {attack_angle}",
                competitive_advantage="",
                evidence=evidence,
                defensive_recommendation=defense,
            )

        except Exception as e:
            self.log_warning(f"Failed to parse claim counter: {e}")
            return None

    def _generate_competitive_assessment(
        self,
        analyses: List[CompetitorAnalysis],
    ) -> str:
        """Generate overall competitive assessment."""
        if not analyses:
            return "No competitors analyzed."

        total_vulnerabilities = sum(len(a.vulnerabilities) for a in analyses)
        critical_count = sum(
            1 for a in analyses
            for v in a.vulnerabilities
            if v.severity == "critical"
        )
        major_count = sum(
            1 for a in analyses
            for v in a.vulnerabilities
            if v.severity == "major"
        )

        incumbent_count = sum(1 for a in analyses if a.is_incumbent)

        parts = [
            f"Analyzed **{len(analyses)} competitors** ({incumbent_count} incumbent{'s' if incumbent_count != 1 else ''}).",
        ]

        if critical_count > 0:
            parts.append(
                f"**{critical_count} Critical vulnerabilities** require immediate defensive action."
            )

        if major_count > 0:
            parts.append(
                f"**{major_count} Major vulnerabilities** should be addressed to strengthen competitive position."
            )

        parts.append(f"Total of {total_vulnerabilities} competitive vulnerabilities identified.")

        return " ".join(parts)

    def _identify_cross_competitor_patterns(
        self,
        analyses: List[CompetitorAnalysis],
    ) -> List[str]:
        """Identify patterns that appear across multiple competitors."""
        patterns = []

        if len(analyses) < 2:
            return patterns

        # Collect all target sections
        section_counts: Dict[str, int] = {}
        for analysis in analyses:
            for vuln in analysis.vulnerabilities:
                section = vuln.target_section
                section_counts[section] = section_counts.get(section, 0) + 1

        # Find sections targeted by multiple competitors
        for section, count in section_counts.items():
            if count > 1 and section:
                patterns.append(
                    f"**{section}** is targeted by {count} competitors - high priority for defense"
                )

        # Check for common challenge types
        type_counts: Dict[str, int] = {}
        for analysis in analyses:
            for vuln in analysis.vulnerabilities:
                ctype = vuln.challenge_type
                type_counts[ctype] = type_counts.get(ctype, 0) + 1

        for ctype, count in type_counts.items():
            if count > 2:
                patterns.append(
                    f"**{ctype}** vulnerabilities appear {count} times - systemic issue to address"
                )

        return patterns

    def _generate_integrated_recommendations(
        self,
        analyses: List[CompetitorAnalysis],
    ) -> List[str]:
        """Generate integrated defensive recommendations."""
        recommendations = []

        # Collect all recommendations
        all_recs: List[str] = []
        for analysis in analyses:
            all_recs.extend(analysis.defensive_recommendations)
            for vuln in analysis.vulnerabilities:
                if vuln.defensive_recommendation:
                    all_recs.append(vuln.defensive_recommendation)

        # Deduplicate and prioritize (simple approach)
        seen = set()
        for rec in all_recs:
            rec_lower = rec.lower().strip()
            if rec_lower not in seen and len(rec) > 10:
                seen.add(rec_lower)
                recommendations.append(rec)

        return recommendations[:10]  # Limit to top 10

    def _format_result_content(
        self,
        result: CompetitorSimulatorResult,
        analysis_type: str,
    ) -> str:
        """Format result as content string."""
        parts = ["# Competitor Simulation Analysis", ""]

        # Overall assessment
        if result.overall_competitive_assessment:
            parts.append("## Competitive Assessment")
            parts.append("")
            parts.append(result.overall_competitive_assessment)
            parts.append("")

        # Cross-competitor patterns
        if result.cross_competitor_patterns:
            parts.append("## Cross-Competitor Patterns")
            parts.append("")
            for pattern in result.cross_competitor_patterns:
                parts.append(f"- {pattern}")
            parts.append("")

        # Competitor analyses
        for analysis in result.competitor_analyses:
            parts.append(f"## {analysis.competitor_name}")
            if analysis.is_incumbent:
                parts.append("**(INCUMBENT)**")
            parts.append("")

            if analysis.perspective and analysis.perspective.self_assessment:
                parts.append(f"**Perspective**: {analysis.perspective.self_assessment}")
                parts.append("")

            if analysis.win_strategy:
                parts.append(f"**Win Strategy**: {analysis.win_strategy}")
                parts.append("")

            if analysis.vulnerabilities:
                parts.append("### Vulnerabilities")
                parts.append("")
                for vuln in analysis.vulnerabilities:
                    parts.append(f"#### {vuln.title}")
                    parts.append("")
                    parts.append(f"- **Type**: {vuln.challenge_type}")
                    parts.append(f"- **Severity**: {vuln.severity}")
                    parts.append(f"- **Target**: {vuln.target_section}")
                    parts.append(f"- **Attack**: {vuln.competitor_attack}")
                    parts.append(f"- **Defense**: {vuln.defensive_recommendation}")
                    parts.append("")

            parts.append("---")
            parts.append("")

        # Integrated recommendations
        if result.integrated_recommendations:
            parts.append("## Integrated Defensive Recommendations")
            parts.append("")
            for i, rec in enumerate(result.integrated_recommendations, 1):
                parts.append(f"{i}. {rec}")
            parts.append("")

        # Critique summary
        if result.critique_summary:
            parts.append("## Summary")
            parts.append("")
            summary = result.critique_summary
            parts.append(f"- **Total Critiques**: {summary.total}")
            parts.append(f"- **Critical**: {summary.critical}")
            parts.append(f"- **Major**: {summary.major}")
            parts.append(f"- **Minor**: {summary.minor}")
            parts.append("")

        return "\n".join(parts)
