"""
Capture Strategist Agent

Win strategy and competitive positioning agent for federal contracting.
Develops win themes, identifies discriminators, performs ghost team analysis,
and provides price-to-win guidance.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from agents.base import BlueTeamAgent, SwarmContext, AgentOutput
from agents.config import AgentConfig
from agents.types import AgentRole, AgentCategory
from agents.utils import DataclassMixin
from agents.utils.section_formatter import (
    format_win_themes_section,
    format_discriminators_section,
    format_ghost_team_section,
    format_price_to_win_section,
    format_capture_comprehensive_section,
)

from .prompts.capture_strategist_prompts import (
    CAPTURE_STRATEGIST_SYSTEM_PROMPT,
    get_win_theme_development_prompt,
    get_discriminator_identification_prompt,
    get_ghost_team_analysis_prompt,
    get_price_to_win_prompt,
    get_capture_strategy_summary_prompt,
    get_revision_prompt,
)


@dataclass
class WinTheme(DataclassMixin):
    """A win theme for the capture strategy."""

    title: str
    theme_statement: str
    supporting_evidence: List[str] = field(default_factory=list)
    customer_benefit: str = ""
    evaluation_criteria_alignment: List[str] = field(default_factory=list)
    competitive_advantage: str = ""
    priority: int = 0  # 1 = highest priority


@dataclass
class Discriminator(DataclassMixin):
    """A discriminator that sets the company apart from competitors."""

    title: str
    discriminator_type: str  # Technical, Management, Past Performance, Personnel, Corporate, Teaming
    description: str
    proof_point: str = ""
    evaluation_factor_link: List[str] = field(default_factory=list)
    competitor_gap: str = ""
    messaging_guidance: str = ""
    impact_score: int = 0  # 1-10, impact on evaluation


@dataclass
class GhostTeamAnalysis(DataclassMixin):
    """Ghost team analysis for a competitor."""

    competitor_name: str
    is_incumbent: bool = False
    predicted_win_themes: List[str] = field(default_factory=list)
    predicted_technical_approach: str = ""
    predicted_pricing_strategy: str = ""
    predicted_teaming_strategy: str = ""
    key_strengths_to_counter: List[str] = field(default_factory=list)
    vulnerabilities_to_exploit: List[str] = field(default_factory=list)
    counter_strategies: List[str] = field(default_factory=list)


@dataclass
class PriceToWinGuidance(DataclassMixin):
    """Price-to-win directional guidance."""

    recommended_positioning: str  # Aggressive, Moderate, Premium
    market_price_range: Dict[str, float] = field(default_factory=dict)  # low, mid, high
    competitor_predictions: Dict[str, str] = field(default_factory=dict)
    price_sensitivity_analysis: Dict[str, str] = field(default_factory=dict)
    risk_assessment: str = ""
    strategic_recommendations: List[str] = field(default_factory=list)


@dataclass
class CaptureStrategyResult(DataclassMixin):
    """Result of capture strategy analysis operations."""

    # Win themes
    win_themes: List[WinTheme] = field(default_factory=list)

    # Discriminators
    discriminators: List[Discriminator] = field(default_factory=list)

    # Ghost team analysis
    ghost_team_analyses: List[GhostTeamAnalysis] = field(default_factory=list)
    competitive_positioning_matrix: Dict[str, Dict[str, str]] = field(default_factory=dict)
    universal_counter_themes: List[str] = field(default_factory=list)

    # Price-to-win
    price_to_win: Optional[PriceToWinGuidance] = None

    # Overall strategy
    executive_summary: str = ""
    win_probability: str = "Unknown"  # High, Medium, Low
    critical_success_factors: List[str] = field(default_factory=list)
    risks: List[Dict[str, str]] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)

    # Meta
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)


class CaptureStrategistAgent(BlueTeamAgent):
    """
    The Capture Strategist develops win strategies and competitive positioning.

    Responsibilities:
    - Develop 3-5 win themes based on company strengths vs. opportunity requirements
    - Identify discriminators that set the company apart from competition
    - Anticipate competitor positioning through ghost team analysis
    - Provide directional price-to-win guidance
    - Align capture strategy with evaluation criteria

    The Capture Strategist focuses on:
    - Customer-centric value propositions
    - Evidence-based discriminators
    - Realistic competitive assessments
    - Actionable strategic recommendations
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Capture Strategist agent.

        Args:
            config: Optional agent configuration. If not provided, uses defaults.
        """
        if config is None:
            from agents.config import get_default_config
            config = get_default_config(AgentRole.CAPTURE_STRATEGIST)

        super().__init__(config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.CAPTURE_STRATEGIST

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.BLUE

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and generate capture strategy analysis.

        The processing mode depends on the context:
        - Win theme development
        - Discriminator identification
        - Ghost team analysis
        - Price-to-win guidance
        - Comprehensive capture strategy

        Args:
            context: SwarmContext containing company profile, opportunity, and competitor intel

        Returns:
            AgentOutput with capture strategy content
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
            # Ensure custom_data is a dict (defensive check)
            if not isinstance(context.custom_data, dict):
                self.log_warning(f"custom_data is not a dict: {type(context.custom_data)}, using empty dict")
                context.custom_data = {}
            analysis_type = context.custom_data.get("analysis_type", "comprehensive")

            if analysis_type == "win_themes":
                result = await self._develop_win_themes(context)
            elif analysis_type == "discriminators":
                result = await self._identify_discriminators(context)
            elif analysis_type == "ghost_team":
                result = await self._analyze_ghost_team(context)
            elif analysis_type == "price_to_win":
                result = await self._analyze_price_to_win(context)
            else:
                # Comprehensive capture strategy
                result = await self._comprehensive_analysis(context)

            processing_time = int((time.time() - start_time) * 1000)

            # Build output content
            content = self._format_analysis_content(result, analysis_type)

            return self._create_output(
                content=content,
                success=result.success,
                error_message=result.errors[0] if result.errors else None,
                warnings=result.warnings,
                processing_time_ms=processing_time,
                token_usage=result.token_usage,
                metadata={
                    "analysis_type": analysis_type,
                    "win_theme_count": len(result.win_themes),
                    "discriminator_count": len(result.discriminators),
                    "competitor_count": len(result.ghost_team_analyses),
                    "win_probability": result.win_probability,
                    "price_positioning": result.price_to_win.recommended_positioning if result.price_to_win else None,
                },
            )

        except Exception as e:
            self.log_error(f"Error in Capture Strategist processing: {e}")
            return self._create_output(
                success=False,
                error_message=f"Processing error: {str(e)}",
            )

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate the context for Capture Strategist processing.

        Args:
            context: The SwarmContext to validate

        Returns:
            List of validation error messages
        """
        errors = super().validate_context(context)

        # Require company profile for capture strategy
        if not context.company_profile:
            errors.append("Company profile is required for capture strategy development")

        # Require opportunity for most analyses
        if not context.opportunity:
            errors.append("Opportunity details are required for capture strategy development")

        return errors

    async def _comprehensive_analysis(
        self,
        context: SwarmContext,
    ) -> CaptureStrategyResult:
        """
        Perform comprehensive capture strategy analysis.

        Args:
            context: SwarmContext with company profile, opportunity, and competitor intel

        Returns:
            CaptureStrategyResult with full analysis
        """
        result = CaptureStrategyResult()

        # 1. Develop win themes
        win_themes_result = await self._develop_win_themes(context)
        result.win_themes = win_themes_result.win_themes

        # 2. Identify discriminators
        discriminators_result = await self._identify_discriminators(context)
        result.discriminators = discriminators_result.discriminators

        # 3. Ghost team analysis (if competitor intel available)
        competitor_intel = context.custom_data.get("competitor_intel")
        if competitor_intel and competitor_intel.get("competitors"):
            ghost_result = await self._analyze_ghost_team(context)
            result.ghost_team_analyses = ghost_result.ghost_team_analyses
            result.competitive_positioning_matrix = ghost_result.competitive_positioning_matrix
            result.universal_counter_themes = ghost_result.universal_counter_themes

        # 4. Price-to-win guidance
        ptw_result = await self._analyze_price_to_win(context)
        result.price_to_win = ptw_result.price_to_win

        # 5. Generate summary
        summary_result = await self._generate_strategy_summary(context, result)
        result.executive_summary = summary_result.executive_summary
        result.win_probability = summary_result.win_probability
        result.critical_success_factors = summary_result.critical_success_factors
        result.risks = summary_result.risks
        result.action_items = summary_result.action_items

        # Merge token usage
        for sub_result in [win_themes_result, discriminators_result, ptw_result]:
            for key, value in sub_result.token_usage.items():
                result.token_usage[key] = result.token_usage.get(key, 0) + value

        return result

    async def _develop_win_themes(
        self,
        context: SwarmContext,
    ) -> CaptureStrategyResult:
        """
        Develop win themes for the opportunity.

        Args:
            context: SwarmContext with company and opportunity data

        Returns:
            CaptureStrategyResult with win themes
        """
        result = CaptureStrategyResult()

        competitor_intel = context.custom_data.get("competitor_intel")

        prompt = get_win_theme_development_prompt(
            company_profile=context.company_profile or {},
            opportunity=context.opportunity or {},
            competitor_intel=competitor_intel,
        )

        llm_response = await self._call_llm(
            system_prompt=CAPTURE_STRATEGIST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.win_themes = self._parse_win_themes(content)
        result.token_usage = llm_response.get("usage", {})

        return result

    async def _identify_discriminators(
        self,
        context: SwarmContext,
    ) -> CaptureStrategyResult:
        """
        Identify discriminators for the opportunity.

        Args:
            context: SwarmContext with company and opportunity data

        Returns:
            CaptureStrategyResult with discriminators
        """
        result = CaptureStrategyResult()

        competitor_intel = context.custom_data.get("competitor_intel")

        prompt = get_discriminator_identification_prompt(
            company_profile=context.company_profile or {},
            opportunity=context.opportunity or {},
            competitor_intel=competitor_intel,
        )

        llm_response = await self._call_llm(
            system_prompt=CAPTURE_STRATEGIST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.discriminators = self._parse_discriminators(content)
        result.token_usage = llm_response.get("usage", {})

        return result

    async def _analyze_ghost_team(
        self,
        context: SwarmContext,
    ) -> CaptureStrategyResult:
        """
        Perform ghost team analysis of competitors.

        Args:
            context: SwarmContext with competitor intel

        Returns:
            CaptureStrategyResult with ghost team analyses
        """
        result = CaptureStrategyResult()

        competitor_intel = context.custom_data.get("competitor_intel", {})
        if not competitor_intel.get("competitors"):
            result.warnings.append("No competitor intelligence provided for ghost team analysis")
            return result

        prompt = get_ghost_team_analysis_prompt(
            company_profile=context.company_profile or {},
            opportunity=context.opportunity or {},
            competitor_intel=competitor_intel,
        )

        llm_response = await self._call_llm(
            system_prompt=CAPTURE_STRATEGIST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        parsed = self._parse_ghost_team_analysis(content)
        result.ghost_team_analyses = parsed.get("analyses", [])
        result.competitive_positioning_matrix = parsed.get("matrix", {})
        result.universal_counter_themes = parsed.get("universal_themes", [])
        result.token_usage = llm_response.get("usage", {})

        return result

    async def _analyze_price_to_win(
        self,
        context: SwarmContext,
    ) -> CaptureStrategyResult:
        """
        Analyze price-to-win positioning.

        Args:
            context: SwarmContext with opportunity and competitor data

        Returns:
            CaptureStrategyResult with price-to-win guidance
        """
        result = CaptureStrategyResult()

        competitor_intel = context.custom_data.get("competitor_intel", {})
        cost_data = context.custom_data.get("cost_data")

        prompt = get_price_to_win_prompt(
            company_profile=context.company_profile or {},
            opportunity=context.opportunity or {},
            competitor_intel=competitor_intel,
            cost_data=cost_data,
        )

        llm_response = await self._call_llm(
            system_prompt=CAPTURE_STRATEGIST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.price_to_win = self._parse_price_to_win(content)
        result.token_usage = llm_response.get("usage", {})

        return result

    async def _generate_strategy_summary(
        self,
        context: SwarmContext,
        prior_result: CaptureStrategyResult,
    ) -> CaptureStrategyResult:
        """
        Generate capture strategy summary.

        Args:
            context: SwarmContext with all inputs
            prior_result: Results from prior analysis steps

        Returns:
            CaptureStrategyResult with summary elements
        """
        result = CaptureStrategyResult()

        win_themes = [wt.title for wt in prior_result.win_themes]
        discriminators = [d.title for d in prior_result.discriminators]

        prompt = get_capture_strategy_summary_prompt(
            company_profile=context.company_profile or {},
            opportunity=context.opportunity or {},
            competitor_intel=context.custom_data.get("competitor_intel"),
            win_themes=win_themes,
            discriminators=discriminators,
        )

        llm_response = await self._call_llm(
            system_prompt=CAPTURE_STRATEGIST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.warnings.append("Could not generate strategy summary")
            return result

        content = llm_response.get("content", "")
        parsed = self._parse_strategy_summary(content)
        result.executive_summary = parsed.get("executive_summary", "")
        result.win_probability = parsed.get("win_probability", "Unknown")
        result.critical_success_factors = parsed.get("critical_success_factors", [])
        result.risks = parsed.get("risks", [])
        result.action_items = parsed.get("action_items", [])
        result.token_usage = llm_response.get("usage", {})

        return result

    async def draft_section(
        self,
        context: SwarmContext,
        section_name: str,
    ) -> str:
        """
        Draft capture strategy content for a specific section.

        Args:
            context: The swarm context
            section_name: Name of the section to draft

        Returns:
            The drafted content for the section
        """
        section_lower = section_name.lower()

        if "win" in section_lower and "theme" in section_lower:
            result = await self._develop_win_themes(context)
            return self._format_win_themes_section(result)

        elif "discriminator" in section_lower:
            result = await self._identify_discriminators(context)
            return self._format_discriminators_section(result)

        elif "ghost" in section_lower or "competitor" in section_lower:
            result = await self._analyze_ghost_team(context)
            return self._format_ghost_team_section(result)

        elif "price" in section_lower or "ptw" in section_lower:
            result = await self._analyze_price_to_win(context)
            return self._format_price_to_win_section(result)

        else:
            # Default to comprehensive analysis
            result = await self._comprehensive_analysis(context)
            return self._format_analysis_content(result, "comprehensive")

    async def revise_section(
        self,
        context: SwarmContext,
        section_name: str,
        critiques: List[Dict[str, Any]],
    ) -> str:
        """
        Revise capture strategy section based on critiques.

        Args:
            context: The swarm context
            section_name: Name of the section to revise
            critiques: List of critiques to address

        Returns:
            The revised content for the section
        """
        original = context.section_drafts.get(section_name, "")
        if not original:
            return await self.draft_section(context, section_name)

        prompt = get_revision_prompt(
            original_content=original,
            section_name=section_name,
            critiques=critiques,
        )

        llm_response = await self._call_llm(
            system_prompt=CAPTURE_STRATEGIST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            return llm_response.get("content", original)
        return original

    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock capture strategy content for testing."""
        prompt_lower = prompt.lower()

        if "win theme" in prompt_lower:
            return """## Win Themes

### Win Theme 1: Mission-Proven Cloud Migration Excellence

**Theme Statement**: Our team has successfully migrated over 50 federal agency systems to cloud environments, delivering 40% cost savings and 99.9% uptime, demonstrating the exact capabilities this mission requires.

**Supporting Evidence**:
- Completed DoD cloud migration of 200+ applications with zero data loss
- FedRAMP High authorization experience across 3 agencies
- AWS GovCloud certified architects on staff

**Customer Benefit**: Reduced risk of mission disruption through proven migration methodology and experienced team that understands agency-specific requirements.

**Evaluation Criteria Alignment**: Technical Approach (40%), Past Performance (30%)

**Competitive Advantage**: Only competitor with documented FedRAMP High migration experience at this scale in DoD environment.

---

### Win Theme 2: Agile Delivery with Measurable Outcomes

**Theme Statement**: Our Agile DevSecOps approach has delivered 30% faster time-to-value for federal clients, with built-in security controls that exceed NIST 800-53 requirements.

**Supporting Evidence**:
- Implemented CI/CD pipeline at VA reducing deployment time from weeks to hours
- SAFe 5.0 certified team with federal experience
- Automated security scanning integrated into development lifecycle

**Customer Benefit**: Faster delivery of mission capabilities with continuous security assurance, reducing both schedule and security risk.

**Evaluation Criteria Alignment**: Technical Approach (40%), Management Approach (20%)

**Competitive Advantage**: Proprietary DevSecOps toolkit specifically designed for federal compliance requirements.

---

### Win Theme 3: Deep Agency Mission Understanding

**Theme Statement**: Our team includes former agency personnel who understand the mission from the inside, enabling solutions that address real operational challenges rather than generic IT improvements.

**Supporting Evidence**:
- Key personnel with 50+ combined years at this agency
- Current contracts supporting adjacent agency offices
- Documented understanding of agency strategic plan priorities

**Customer Benefit**: Solutions designed by people who understand your mission, reducing requirements clarification cycles and ensuring alignment with agency priorities.

**Evaluation Criteria Alignment**: Past Performance (30%), Key Personnel (10%)

**Competitive Advantage**: Competitor personnel lack direct agency experience; our team has worked these exact mission sets."""

        elif "discriminator" in prompt_lower:
            return """## Discriminators

### Discriminator 1: Proprietary CloudBridge Migration Platform

**Type**: Technical

**Description**: Our proprietary CloudBridge platform automates 70% of cloud migration tasks, reducing migration time by 50% compared to manual approaches while ensuring compliance with federal security requirements.

**Proof Point**: Used CloudBridge to complete VA EHR migration 3 months ahead of schedule, saving $2.3M in labor costs.

**Evaluation Factor Link**: Technical Approach, Cost

**Competitor Gap**: No competitor has an equivalent automated migration platform with federal security certifications. Competitors rely on manual processes or commercial tools that require extensive customization.

**Messaging Guidance**: "Our CloudBridge platform has been purpose-built for federal cloud migrations, automating compliance verification and reducing migration risk through tested, repeatable processes."

---

### Discriminator 2: Cleared Workforce Ready to Deploy

**Type**: Corporate

**Description**: 85% of our proposed team holds active TS/SCI clearances with current BI/SSBI investigations, enabling immediate project start without clearance processing delays.

**Proof Point**: Started performance on DIA contract within 2 weeks of award versus 6-month industry average.

**Evaluation Factor Link**: Management Approach, Key Personnel

**Competitor Gap**: Competitor A has clearance processing backlog of 6+ months. Competitor B's cleared workforce is committed to other contracts.

**Messaging Guidance**: "Our cleared workforce is ready to begin Day One, eliminating the security processing delays that typically extend project timelines by 6-9 months."

---

### Discriminator 3: Integrated Cybersecurity Center of Excellence

**Type**: Technical

**Description**: Our in-house Cybersecurity Center of Excellence provides 24/7 threat monitoring and incident response capabilities, with dedicated federal sector specialists.

**Proof Point**: Achieved Zero breach incidents across 15 federal clients over 5 years. Identified and mitigated SolarWinds vulnerability 48 hours before public disclosure.

**Evaluation Factor Link**: Technical Approach, Past Performance

**Competitor Gap**: Competitors outsource security monitoring to third parties, creating response delays and information handoff risks.

**Messaging Guidance**: "Our integrated Cybersecurity Center of Excellence provides dedicated protection for your mission, with federal-sector specialists who understand agency-specific threat landscapes."

---

### Discriminator 4: Proven CMMC Level 3 Compliance

**Type**: Corporate

**Description**: Already achieved CMMC Level 3 certification, with documented processes and controls that exceed current DoD requirements.

**Proof Point**: One of only 47 companies with verified CMMC Level 3 certification. Passed certification assessment on first attempt.

**Evaluation Factor Link**: Technical Approach, Compliance

**Competitor Gap**: Competitors are still in CMMC assessment queue with 12-18 month estimated timelines.

**Messaging Guidance**: "Our proven CMMC Level 3 certification eliminates compliance risk for your program, ensuring uninterrupted contractor support regardless of evolving DoD requirements."

---

### Discriminator 5: Former Program Manager as Proposed PM

**Type**: Personnel

**Description**: Our proposed Program Manager previously served as the government Program Manager for this exact program, providing unmatched understanding of requirements, stakeholders, and success criteria.

**Proof Point**: Led the program to "Exceptional" CPARS ratings for 3 consecutive years. Maintains relationships with key agency stakeholders.

**Evaluation Factor Link**: Key Personnel, Management Approach

**Competitor Gap**: No competitor can offer personnel with direct program management experience from the government side.

**Messaging Guidance**: "Our Program Manager knows this program inside and out, having led it successfully for the government. She understands not just what you need, but why you need it."
"""

        elif "ghost team" in prompt_lower or "competitor" in prompt_lower:
            return """## Ghost Team Analysis

### TechCorp Solutions (INCUMBENT)

#### Predicted Win Themes
1. "Continuity of service with proven track record"
2. "Deep understanding of agency operations and culture"
3. "Minimal transition risk and immediate productivity"
4. "Established relationships with stakeholders"
5. "Knowledge of legacy systems and integration points"

#### Predicted Technical Approach
TechCorp will likely propose an evolution of their current approach rather than transformation. Expect emphasis on:
- Incremental improvements to existing systems
- Risk-averse technology selections
- Heavy reliance on institutional knowledge

#### Predicted Pricing Strategy
**Moderate to Aggressive**: TechCorp will likely price at or slightly below their current rates to defend the incumbent position. They have lower transition costs and can absorb margin compression.

#### Predicted Teaming Strategy
Likely to maintain current subcontractor relationships. May add a cloud specialist subcontractor to address modernization requirements.

#### Key Strengths to Counter
- Deep institutional knowledge
- Established customer relationships
- Zero transition risk
- Known quantity to evaluators

#### Vulnerabilities to Exploit
- CPARS shows declining schedule performance (Satisfactory in recent periods)
- Limited cloud migration experience
- Key personnel turnover on current contract
- Reactive rather than proactive approach to emerging requirements

#### Our Counter-Strategy
1. Emphasize need for fresh perspective and innovation
2. Highlight our superior cloud migration capabilities
3. Propose dedicated knowledge transfer approach that mitigates transition risk
4. Reference their declining performance in evaluation-appropriate manner

---

### GlobalTech Partners

#### Predicted Win Themes
1. "Enterprise-scale cloud expertise"
2. "Investment in automation and AI"
3. "Global delivery model with cost efficiency"
4. "Fortune 500 proven methodologies"

#### Predicted Technical Approach
GlobalTech will propose their standard commercial cloud migration framework, adapted for federal requirements. Expect:
- Heavy emphasis on commercial best practices
- Significant use of offshore resources
- Tool-centric approach with proprietary platforms

#### Predicted Pricing Strategy
**Aggressive**: GlobalTech typically underbids to win new federal business, planning to recover margin through change orders. Expect price 10-15% below market.

#### Predicted Teaming Strategy
Will likely team with a small business partner for set-aside requirements. May partner with major cloud provider for technical credibility.

#### Key Strengths to Counter
- Brand recognition and scale
- Deep technical bench
- Investment in emerging technologies
- Ability to absorb risk

#### Vulnerabilities to Exploit
- Limited federal past performance
- Offshore delivery model raises security concerns
- Commercial approach may not translate to federal context
- Large company bureaucracy slows responsiveness

#### Our Counter-Strategy
1. Emphasize federal-specific experience vs. commercial adaptation
2. Highlight cleared workforce and domestic delivery
3. Question their federal culture fit
4. Emphasize agility vs. bureaucratic processes

---

## Competitive Positioning Matrix

| Factor | Us | TechCorp (Incumbent) | GlobalTech |
|--------|-----|---------------------|------------|
| Cloud Migration | Strong | Weak | Strong |
| Federal Experience | Strong | Strong | Weak |
| Cleared Workforce | Strong | Moderate | Weak |
| Innovation | Strong | Weak | Moderate |
| Price Competitiveness | Moderate | Strong | Strong |
| Transition Risk | Moderate | None | High |

## Universal Counter-Themes

1. **Fresh Perspective Required**: The program needs transformation, not incremental improvement
2. **Federal-First Approach**: Commercial approaches require risky adaptation for federal environment
3. **Innovation with Stability**: We combine innovative solutions with proven federal execution
4. **Mission Understanding**: Deep agency knowledge cannot be replaced by commercial scale
5. **Proactive Partnership**: We anticipate and address needs before they become problems"""

        elif "price" in prompt_lower:
            return """## Price-to-Win Analysis

### Market Price Range Assessment

Based on competitive analysis and market conditions:

| Position | Annual Value | Total Contract |
|----------|-------------|----------------|
| **Low** | $18.5M | $92.5M (5-year) |
| **Mid** | $21.0M | $105.0M (5-year) |
| **High** | $24.5M | $122.5M (5-year) |

**Factors Driving Variance**:
- Labor mix (senior vs. junior ratio)
- Subcontractor percentage
- Profit margin expectations
- Investment in innovation/transition

### Evaluation Impact Analysis

**Evaluation Type**: Best Value Tradeoff

**Price Weight**: 30% (vs. 70% technical/management/past performance)

**Technical/Price Tradeoff Tolerance**: Based on evaluation language emphasizing "technical excellence," evaluators appear willing to pay 5-8% premium for demonstrably superior technical approach.

**Price Reasonableness Threshold**: Prices more than 15% above IGCE will likely trigger detailed cost analysis and potential elimination.

### Competitor Price Predictions

| Competitor | Predicted Position | Rationale |
|------------|-------------------|-----------|
| **TechCorp (Incumbent)** | Low-Mid ($19-21M) | Defending position, low transition costs, willing to compress margin |
| **GlobalTech** | Low ($18-19M) | Aggressive entry pricing, offshore delivery model enables lower costs |
| **CompetitorC** | Mid-High ($22-24M) | Premium positioning, limited cost flexibility |

### Price Positioning Recommendation

**Recommended Position: MODERATE ($20.5-21.5M annually)**

**Rationale**:
1. Best Value evaluation rewards technical superiority
2. Our discriminators justify modest premium
3. Going lower risks credibility and sustainability
4. Incumbent likely to match or beat aggressive pricing

**Technical Strength Requirements**:
To support moderate pricing, proposal must clearly demonstrate:
- Superior technical approach with measurable benefits
- Lower risk profile than incumbent
- Innovation value that justifies investment

### Price Sensitivity Analysis

| Scenario | Impact Assessment |
|----------|------------------|
| **5% Above Mid** | Low risk; within tradeoff tolerance if technical is strong |
| **10% Above Mid** | Moderate risk; requires clear discriminators to justify |
| **15% Above Mid** | High risk; approaching reasonableness threshold |
| **5% Below Mid** | May signal underbidding; questions about sustainability |
| **10% Below Mid** | Likely to trigger cost realism concerns |

### Risk Assessment

**Pricing Too Aggressively (Below $19M)**:
- Risk of cost realism challenge
- Questions about ability to deliver at proposed price
- Potential for unrealistic performance expectations
- May signal desperation to evaluators

**Pricing Too High (Above $23M)**:
- Risk of elimination from competitive range
- Must demonstrate exceptional value to justify
- Incumbent advantage at lower price becomes insurmountable
- May not survive initial price reasonableness review

### Strategic Recommendations

1. **Target $20.5-21.5M annual value** - competitive while supporting quality delivery
2. **Invest in transition** - allocate budget for comprehensive knowledge transfer to address incumbent advantage
3. **Optimize labor mix** - balance experience levels to manage cost while demonstrating capability
4. **Consider innovation investment** - strategic uncompensated effort in key areas may differentiate without inflating price
5. **Prepare price narrative** - document value proposition that justifies any premium over low bidders
6. **Monitor competitor pricing signals** - adjust strategy if market intelligence indicates different positioning

### Price-to-Win Summary

| Element | Recommendation |
|---------|---------------|
| **Target Price Range** | $20.5M - $21.5M annually |
| **Positioning** | Moderate - value-focused |
| **Key Message** | "Optimal value: proven capability at competitive price" |
| **Risk Level** | Low-Moderate |
| **Win Probability Impact** | Neutral to positive with strong technical |"""

        else:
            return """## Capture Strategy Summary

### Executive Summary

Based on comprehensive analysis of the opportunity, our competitive position, and market conditions, we assess a **Medium-High probability of winning** this opportunity. Our key advantages include superior cloud migration capabilities, a cleared workforce ready for immediate deployment, and unique discriminators that competitors cannot match.

The incumbent (TechCorp) presents the primary competitive challenge, but their declining performance ratings and limited modernization experience create openings. GlobalTech's aggressive pricing strategy poses a secondary threat that we counter with demonstrably superior federal experience.

**Critical Success Factors**:
1. Emphasize cloud migration excellence with specific proof points
2. Propose cleared, experienced workforce to minimize transition risk
3. Price competitively while emphasizing value over low-bid approach
4. Counter incumbent advantage through innovation narrative

### Win Probability Assessment

**Overall Win Probability: 55-65% (Medium-High)**

| Factor | Assessment | Impact |
|--------|------------|--------|
| Technical Capability | Strong | +15% |
| Past Performance | Strong | +10% |
| Key Personnel | Strong | +10% |
| Price Competitiveness | Moderate | Neutral |
| Incumbent Advantage | Headwind | -15% |
| Evaluation Alignment | Strong | +10% |

### Top Win Themes

1. **Mission-Proven Cloud Migration Excellence** - Demonstrated success at scale
2. **Agile Delivery with Measurable Outcomes** - Faster time-to-value
3. **Deep Agency Mission Understanding** - Insider knowledge of requirements

### Top Discriminators

1. **Proprietary CloudBridge Migration Platform** - Technical differentiation
2. **Cleared Workforce Ready to Deploy** - Immediate start capability
3. **Former Government PM as Our PM** - Unique personnel advantage
4. **CMMC Level 3 Certification** - Compliance leadership
5. **Integrated Cybersecurity Center** - Superior security posture

### Competitive Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Incumbent price matching | High | High | Emphasize technical superiority and innovation value |
| Transition concerns | Medium | High | Detailed transition plan with risk mitigation |
| GlobalTech underbidding | Medium | Medium | Focus on federal experience gap in their approach |
| Key personnel availability | Low | High | Secure commitments and identify backups |
| Clearance processing delays | Low | Medium | Pre-position cleared workforce |

### Action Items

#### Immediate (0-30 Days)
- [ ] Finalize teaming agreements with key subcontractors
- [ ] Secure written commitments from key personnel
- [ ] Develop detailed transition plan framework
- [ ] Initiate customer shaping meetings if allowable
- [ ] Complete competitive intelligence gathering

#### Near-Term (30-90 Days)
- [ ] Develop technical approach with clear discriminator emphasis
- [ ] Build win theme proof points with quantified evidence
- [ ] Refine pricing strategy based on updated market intelligence
- [ ] Prepare and review past performance narratives
- [ ] Conduct internal Red Team review of strategy

#### Pre-Proposal
- [ ] Final Go/No-Go decision with complete capture intelligence
- [ ] Proposal kickoff with fully briefed team
- [ ] Assign volume leads and establish review schedule
- [ ] Finalize price-to-win position
- [ ] Prepare oral presentation if required"""

    def _parse_win_themes(self, content: str) -> List[WinTheme]:
        """Parse win themes from LLM response."""
        import re

        themes = []
        theme_sections = re.split(r'###\s*Win Theme\s*\d+', content, flags=re.IGNORECASE)

        for i, section in enumerate(theme_sections[1:], 1):  # Skip first split (before first theme)
            title_match = re.search(r'^[:\s]*([^\n]+)', section.strip())
            title = title_match.group(1).strip() if title_match else f"Win Theme {i}"

            statement_match = re.search(
                r'\*\*Theme Statement\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                section,
                re.IGNORECASE
            )
            theme_statement = statement_match.group(1).strip() if statement_match else ""

            benefit_match = re.search(
                r'\*\*Customer Benefit\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                section,
                re.IGNORECASE
            )
            customer_benefit = benefit_match.group(1).strip() if benefit_match else ""

            advantage_match = re.search(
                r'\*\*Competitive Advantage\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                section,
                re.IGNORECASE
            )
            competitive_advantage = advantage_match.group(1).strip() if advantage_match else ""

            # Extract supporting evidence as list
            evidence_match = re.search(
                r'\*\*Supporting Evidence\*\*[:\s]*((?:[-•]\s*[^\n]+\n?)+)',
                section,
                re.IGNORECASE
            )
            evidence = []
            if evidence_match:
                evidence = [
                    line.strip().lstrip('-•').strip()
                    for line in evidence_match.group(1).strip().split('\n')
                    if line.strip()
                ]

            # Extract evaluation alignment as list
            eval_match = re.search(
                r'\*\*Evaluation.*?Alignment\*\*[:\s]*([^\n]+)',
                section,
                re.IGNORECASE
            )
            eval_alignment = []
            if eval_match:
                eval_text = eval_match.group(1)
                eval_alignment = [e.strip() for e in re.split(r'[,;]', eval_text) if e.strip()]

            theme = WinTheme(
                title=title,
                theme_statement=theme_statement,
                supporting_evidence=evidence,
                customer_benefit=customer_benefit,
                evaluation_criteria_alignment=eval_alignment,
                competitive_advantage=competitive_advantage,
                priority=i,
            )
            themes.append(theme)

        return themes

    def _parse_discriminators(self, content: str) -> List[Discriminator]:
        """Parse discriminators from LLM response."""
        import re

        discriminators = []
        disc_sections = re.split(r'###\s*Discriminator\s*\d+', content, flags=re.IGNORECASE)

        for i, section in enumerate(disc_sections[1:], 1):
            title_match = re.search(r'^[:\s]*([^\n]+)', section.strip())
            title = title_match.group(1).strip() if title_match else f"Discriminator {i}"

            type_match = re.search(r'\*\*Type\*\*[:\s]*([^\n]+)', section, re.IGNORECASE)
            disc_type = type_match.group(1).strip() if type_match else "Unknown"

            desc_match = re.search(
                r'\*\*Description\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                section,
                re.IGNORECASE
            )
            description = desc_match.group(1).strip() if desc_match else ""

            proof_match = re.search(
                r'\*\*Proof Point\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                section,
                re.IGNORECASE
            )
            proof_point = proof_match.group(1).strip() if proof_match else ""

            gap_match = re.search(
                r'\*\*Competitor Gap\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                section,
                re.IGNORECASE
            )
            competitor_gap = gap_match.group(1).strip() if gap_match else ""

            messaging_match = re.search(
                r'\*\*Messaging.*?\*\*[:\s]*([^\n]+(?:\n(?!\*\*)[^\n]+)*)',
                section,
                re.IGNORECASE
            )
            messaging = messaging_match.group(1).strip().strip('"') if messaging_match else ""

            # Extract evaluation factor links
            eval_match = re.search(
                r'\*\*Evaluation.*?Link\*\*[:\s]*([^\n]+)',
                section,
                re.IGNORECASE
            )
            eval_links = []
            if eval_match:
                eval_text = eval_match.group(1)
                eval_links = [e.strip() for e in re.split(r'[,;]', eval_text) if e.strip()]

            disc = Discriminator(
                title=title,
                discriminator_type=disc_type,
                description=description,
                proof_point=proof_point,
                evaluation_factor_link=eval_links,
                competitor_gap=competitor_gap,
                messaging_guidance=messaging,
                impact_score=10 - i + 1,  # Higher score for earlier discriminators
            )
            discriminators.append(disc)

        return discriminators

    def _parse_ghost_team_analysis(self, content: str) -> Dict[str, Any]:
        """Parse ghost team analysis from LLM response."""
        import re

        result = {
            "analyses": [],
            "matrix": {},
            "universal_themes": [],
        }

        # Split by competitor sections
        competitor_sections = re.split(r'###\s*(?:Competitor\s*\d+[:\s]*)?([A-Za-z\s]+(?:\([^)]+\))?)\s*\n', content)

        for i in range(1, len(competitor_sections), 2):
            if i + 1 >= len(competitor_sections):
                break

            name = competitor_sections[i].strip()
            section = competitor_sections[i + 1]

            is_incumbent = "incumbent" in name.lower()
            clean_name = re.sub(r'\s*\(incumbent\)\s*', '', name, flags=re.IGNORECASE).strip()

            # Extract predicted win themes
            themes_match = re.search(
                r'(?:Predicted\s+)?Win Themes[:\s]*((?:\d+\.\s*[^\n]+\n?)+)',
                section,
                re.IGNORECASE
            )
            predicted_themes = []
            if themes_match:
                predicted_themes = [
                    re.sub(r'^\d+\.\s*', '', line.strip()).strip('"')
                    for line in themes_match.group(1).strip().split('\n')
                    if line.strip()
                ]

            # Extract pricing strategy
            pricing_match = re.search(
                r'(?:Predicted\s+)?Pricing Strategy[:\s]*\*\*([^*]+)\*\*[:\s]*([^\n]+)',
                section,
                re.IGNORECASE
            )
            pricing = ""
            if pricing_match:
                pricing = f"{pricing_match.group(1)}: {pricing_match.group(2)}"

            # Extract counter strategies
            counter_match = re.search(
                r'(?:Our\s+)?Counter.?Strategy[:\s]*((?:\d+\.\s*[^\n]+\n?)+)',
                section,
                re.IGNORECASE
            )
            counter_strategies = []
            if counter_match:
                counter_strategies = [
                    re.sub(r'^\d+\.\s*', '', line.strip())
                    for line in counter_match.group(1).strip().split('\n')
                    if line.strip()
                ]

            analysis = GhostTeamAnalysis(
                competitor_name=clean_name,
                is_incumbent=is_incumbent,
                predicted_win_themes=predicted_themes,
                predicted_pricing_strategy=pricing,
                counter_strategies=counter_strategies,
            )
            result["analyses"].append(analysis)

        # Extract universal counter-themes
        universal_match = re.search(
            r'Universal Counter.?Themes[:\s]*((?:\d+\.\s*\*\*[^*]+\*\*[^\n]*\n?)+)',
            content,
            re.IGNORECASE
        )
        if universal_match:
            result["universal_themes"] = [
                re.sub(r'^\d+\.\s*\*\*([^*]+)\*\*.*', r'\1', line.strip())
                for line in universal_match.group(1).strip().split('\n')
                if line.strip()
            ]

        return result

    def _parse_price_to_win(self, content: str) -> PriceToWinGuidance:
        """Parse price-to-win guidance from LLM response."""
        import re

        ptw = PriceToWinGuidance(recommended_positioning="Moderate")

        # Extract recommended positioning
        position_match = re.search(
            r'Recommended Position[:\s]*\*\*([^*]+)\*\*',
            content,
            re.IGNORECASE
        )
        if position_match:
            pos_text = position_match.group(1).strip()
            if "aggressive" in pos_text.lower():
                ptw.recommended_positioning = "Aggressive"
            elif "premium" in pos_text.lower():
                ptw.recommended_positioning = "Premium"
            else:
                ptw.recommended_positioning = "Moderate"

        # Extract market price range
        low_match = re.search(r'\*\*Low\*\*\s*\|\s*\$?([\d.]+)', content)
        mid_match = re.search(r'\*\*Mid\*\*\s*\|\s*\$?([\d.]+)', content)
        high_match = re.search(r'\*\*High\*\*\s*\|\s*\$?([\d.]+)', content)

        if low_match:
            ptw.market_price_range["low"] = float(low_match.group(1).replace(',', ''))
        if mid_match:
            ptw.market_price_range["mid"] = float(mid_match.group(1).replace(',', ''))
        if high_match:
            ptw.market_price_range["high"] = float(high_match.group(1).replace(',', ''))

        # Extract strategic recommendations
        rec_match = re.search(
            r'Strategic Recommendations[:\s]*((?:\d+\.\s*\*\*[^*]+\*\*[^\n]*\n?)+)',
            content,
            re.IGNORECASE
        )
        if rec_match:
            ptw.strategic_recommendations = [
                re.sub(r'^\d+\.\s*\*\*([^*]+)\*\*\s*-?\s*', r'\1: ', line.strip())
                for line in rec_match.group(1).strip().split('\n')
                if line.strip()
            ]

        return ptw

    def _parse_strategy_summary(self, content: str) -> Dict[str, Any]:
        """Parse strategy summary from LLM response."""
        import re

        result = {
            "executive_summary": "",
            "win_probability": "Unknown",
            "critical_success_factors": [],
            "risks": [],
            "action_items": [],
        }

        # Extract executive summary
        exec_match = re.search(
            r'Executive Summary[:\s]*(.*?)(?=###|\*\*Win Probability|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if exec_match:
            result["executive_summary"] = exec_match.group(1).strip()

        # Extract win probability
        prob_match = re.search(
            r'(?:Overall\s+)?Win Probability[:\s]*\*?\*?(\d+)-(\d+)%?\s*\(([^)]+)\)',
            content,
            re.IGNORECASE
        )
        if prob_match:
            result["win_probability"] = f"{prob_match.group(1)}-{prob_match.group(2)}% ({prob_match.group(3)})"
        else:
            # Alternative format
            alt_match = re.search(
                r'Win Probability[:\s]*(?:\*\*)?([^*\n]+)',
                content,
                re.IGNORECASE
            )
            if alt_match:
                result["win_probability"] = alt_match.group(1).strip()

        # Extract critical success factors
        csf_match = re.search(
            r'Critical Success Factors[:\s]*((?:\d+\.\s*[^\n]+\n?)+)',
            content,
            re.IGNORECASE
        )
        if csf_match:
            result["critical_success_factors"] = [
                re.sub(r'^\d+\.\s*', '', line.strip())
                for line in csf_match.group(1).strip().split('\n')
                if line.strip()
            ]

        # Extract risks
        risk_match = re.search(
            r'(?:Competitive\s+)?Risks[:\s]*\|.*?\|.*?\|.*?\|((?:\n\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|)+)',
            content,
            re.IGNORECASE
        )
        if risk_match:
            for line in risk_match.group(1).strip().split('\n'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 4:
                    result["risks"].append({
                        "risk": parts[0],
                        "probability": parts[1],
                        "impact": parts[2],
                        "mitigation": parts[3] if len(parts) > 3 else "",
                    })

        # Extract action items
        action_match = re.search(
            r'(?:Immediate|0-30 Days)[:\s]*((?:\[[ x]\]\s*[^\n]+\n?)+)',
            content,
            re.IGNORECASE
        )
        if action_match:
            for line in action_match.group(1).strip().split('\n'):
                item_match = re.match(r'\[([x ])\]\s*(.+)', line.strip(), re.IGNORECASE)
                if item_match:
                    result["action_items"].append({
                        "item": item_match.group(2).strip(),
                        "completed": item_match.group(1).lower() == 'x',
                        "timeframe": "Immediate (0-30 days)",
                    })

        return result

    def _format_analysis_content(
        self,
        result: CaptureStrategyResult,
        analysis_type: str,
    ) -> str:
        """Format analysis result as content string."""
        if analysis_type == "win_themes":
            return self._format_win_themes_section(result)
        elif analysis_type == "discriminators":
            return self._format_discriminators_section(result)
        elif analysis_type == "ghost_team":
            return self._format_ghost_team_section(result)
        elif analysis_type == "price_to_win":
            return self._format_price_to_win_section(result)
        else:
            return self._format_comprehensive_section(result)

    def _format_win_themes_section(self, result: CaptureStrategyResult) -> str:
        """Format win themes as a section."""
        return format_win_themes_section(result.win_themes)

    def _format_discriminators_section(self, result: CaptureStrategyResult) -> str:
        """Format discriminators as a section."""
        return format_discriminators_section(result.discriminators)

    def _format_ghost_team_section(self, result: CaptureStrategyResult) -> str:
        """Format ghost team analysis as a section."""
        return format_ghost_team_section(result.ghost_team_analyses, result.universal_counter_themes)

    def _format_price_to_win_section(self, result: CaptureStrategyResult) -> str:
        """Format price-to-win guidance as a section."""
        return format_price_to_win_section(result.price_to_win)

    def _format_comprehensive_section(self, result: CaptureStrategyResult) -> str:
        """Format comprehensive capture strategy as a section."""
        return format_capture_comprehensive_section(result)
