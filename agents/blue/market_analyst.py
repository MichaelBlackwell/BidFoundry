"""
Market Analyst Agent

Government market intelligence and trend analysis agent.
Analyzes market data to identify opportunities, assess competitive
landscape, and provide timing recommendations.
"""

import re
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Any, Optional

from agents.base import BlueTeamAgent, SwarmContext, AgentOutput
from agents.config import AgentConfig
from agents.types import AgentRole, AgentCategory

from .prompts.market_analyst_prompts import (
    MARKET_ANALYST_SYSTEM_PROMPT,
    get_market_analysis_prompt,
    get_opportunity_ranking_prompt,
    get_incumbent_analysis_prompt,
    get_timing_analysis_prompt,
)
from agents.utils.section_formatter import (
    format_market_sizing_section,
    format_opportunities_section,
    format_competitive_section,
    format_timing_section,
    format_market_comprehensive_section,
)


@dataclass
class MarketAnalysisResult:
    """Result of a market analysis operation."""

    # Market sizing
    total_addressable_market: Optional[float] = None
    serviceable_addressable_market: Optional[float] = None
    target_market: Optional[float] = None
    market_sizing_assumptions: List[str] = field(default_factory=list)

    # Opportunities
    ranked_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    opportunity_count: int = 0

    # Competitive landscape
    competitive_density: str = "Unknown"
    incumbent_assessment: str = ""
    market_barriers: List[str] = field(default_factory=list)
    market_enablers: List[str] = field(default_factory=list)

    # Timing
    timing_recommendations: List[str] = field(default_factory=list)
    fiscal_considerations: List[str] = field(default_factory=list)

    # Trends and insights
    market_trends: List[str] = field(default_factory=list)
    agency_insights: Dict[str, str] = field(default_factory=dict)

    # Meta
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)


class MarketAnalystAgent(BlueTeamAgent):
    """
    The Market Analyst provides government market intelligence and trend analysis.

    Responsibilities:
    - Analyze agency budget patterns and trends
    - Identify relevant opportunities based on NAICS and agency alignment
    - Assess competitive density and incumbent strength
    - Provide timing recommendations aligned with fiscal year cycles
    - Produce market sizing estimates with stated assumptions

    The Market Analyst works with data from:
    - SAM.gov (opportunities and forecasts)
    - FPDS (Federal Procurement Data System)
    - USASpending (contract award data)
    - Agency procurement forecasts
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Market Analyst agent.

        Args:
            config: Optional agent configuration. If not provided, uses defaults.
        """
        if config is None:
            from agents.config import get_default_config
            config = get_default_config(AgentRole.MARKET_ANALYST)

        super().__init__(config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.MARKET_ANALYST

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.BLUE

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and generate market analysis.

        The processing mode depends on the context:
        - BlueBuild round: Generate comprehensive market analysis
        - Specific analysis type: Run targeted analysis

        Args:
            context: SwarmContext containing company profile and market data

        Returns:
            AgentOutput with market analysis content
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

            if analysis_type == "opportunity_ranking":
                result = await self._rank_opportunities(context)
            elif analysis_type == "incumbent_analysis":
                result = await self._analyze_incumbent(context)
            elif analysis_type == "timing_analysis":
                result = await self._analyze_timing(context)
            else:
                # Default: comprehensive market analysis
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
                    "opportunity_count": result.opportunity_count,
                    "tam": result.total_addressable_market,
                    "sam": result.serviceable_addressable_market,
                    "competitive_density": result.competitive_density,
                    "ranked_opportunities": result.ranked_opportunities,
                    "timing_recommendations": result.timing_recommendations,
                    "market_trends": result.market_trends,
                },
            )

        except Exception as e:
            self.log_error(f"Error in Market Analyst processing: {e}")
            return self._create_output(
                success=False,
                error_message=f"Processing error: {str(e)}",
            )

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate the context for Market Analyst processing.

        Args:
            context: The SwarmContext to validate

        Returns:
            List of validation error messages
        """
        errors = super().validate_context(context)

        # Require company profile for market alignment
        if not context.company_profile:
            errors.append("Company profile is required for market analysis")

        return errors

    async def _comprehensive_analysis(self, context: SwarmContext) -> MarketAnalysisResult:
        """
        Perform comprehensive market analysis.

        Args:
            context: SwarmContext with company profile and market data

        Returns:
            MarketAnalysisResult with full analysis
        """
        result = MarketAnalysisResult()

        # Extract market data from custom_data
        market_data = context.custom_data.get("market_data", {})
        target_agencies = context.custom_data.get("target_agencies")
        focus_areas = context.custom_data.get("focus_areas")

        # Build prompt
        prompt = get_market_analysis_prompt(
            company_profile=context.company_profile,
            market_data=market_data,
            target_agencies=target_agencies,
            focus_areas=focus_areas,
        )

        # Call LLM
        llm_response = await self._call_llm(
            system_prompt=MARKET_ANALYST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        # Parse response into structured result
        content = llm_response.get("content", "")
        result = self._parse_analysis_response(content, result)
        result.token_usage = llm_response.get("usage", {})

        return result

    async def _rank_opportunities(self, context: SwarmContext) -> MarketAnalysisResult:
        """
        Rank and prioritize opportunities.

        Args:
            context: SwarmContext with opportunities to rank

        Returns:
            MarketAnalysisResult with ranked opportunities
        """
        result = MarketAnalysisResult()

        opportunities = context.custom_data.get("opportunities", [])
        max_opportunities = context.custom_data.get("max_opportunities", 5)

        if not opportunities:
            result.warnings.append("No opportunities provided for ranking")
            return result

        prompt = get_opportunity_ranking_prompt(
            company_profile=context.company_profile,
            opportunities=opportunities,
            max_opportunities=max_opportunities,
        )

        llm_response = await self._call_llm(
            system_prompt=MARKET_ANALYST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.ranked_opportunities = self._parse_ranked_opportunities(content)
        result.opportunity_count = len(result.ranked_opportunities)
        result.token_usage = llm_response.get("usage", {})

        return result

    async def _analyze_incumbent(self, context: SwarmContext) -> MarketAnalysisResult:
        """
        Analyze incumbent contractor performance and vulnerabilities.

        Args:
            context: SwarmContext with incumbent data

        Returns:
            MarketAnalysisResult with incumbent assessment
        """
        result = MarketAnalysisResult()

        incumbent_data = context.custom_data.get("incumbent_data", {})
        opportunity = context.opportunity

        if not incumbent_data:
            result.warnings.append("No incumbent data provided for analysis")
            return result

        prompt = get_incumbent_analysis_prompt(
            incumbent_data=incumbent_data,
            opportunity=opportunity,
        )

        llm_response = await self._call_llm(
            system_prompt=MARKET_ANALYST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.incumbent_assessment = content
        result.token_usage = llm_response.get("usage", {})

        return result

    async def _analyze_timing(self, context: SwarmContext) -> MarketAnalysisResult:
        """
        Analyze procurement timing and fiscal year considerations.

        Args:
            context: SwarmContext with forecast data

        Returns:
            MarketAnalysisResult with timing recommendations
        """
        result = MarketAnalysisResult()

        market_data = context.custom_data.get("market_data", {})
        forecast_opportunities = market_data.get("forecast_opportunities", [])
        agency_budgets = market_data.get("agency_budgets", {})

        prompt = get_timing_analysis_prompt(
            forecast_opportunities=forecast_opportunities,
            agency_budgets=agency_budgets,
        )

        llm_response = await self._call_llm(
            system_prompt=MARKET_ANALYST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not llm_response.get("success"):
            result.success = False
            result.errors.append(llm_response.get("error", "LLM call failed"))
            return result

        content = llm_response.get("content", "")
        result.timing_recommendations = self._parse_timing_recommendations(content)
        result.fiscal_considerations = self._parse_fiscal_considerations(content)
        result.token_usage = llm_response.get("usage", {})

        return result

    async def draft_section(
        self,
        context: SwarmContext,
        section_name: str,
    ) -> str:
        """
        Draft market analysis content for a specific section.

        Args:
            context: The swarm context
            section_name: Name of the section to draft

        Returns:
            The drafted content for the section
        """
        # Route to appropriate analysis based on section name
        section_lower = section_name.lower()

        if "market" in section_lower and "sizing" in section_lower:
            result = await self._comprehensive_analysis(context)
            return self._format_market_sizing_section(result)

        elif "opportunity" in section_lower or "opportunities" in section_lower:
            context.custom_data["analysis_type"] = "opportunity_ranking"
            result = await self._rank_opportunities(context)
            return self._format_opportunities_section(result)

        elif "competitive" in section_lower or "landscape" in section_lower:
            result = await self._comprehensive_analysis(context)
            return self._format_competitive_section(result)

        elif "timing" in section_lower or "fiscal" in section_lower:
            result = await self._analyze_timing(context)
            return self._format_timing_section(result)

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
        Revise market analysis section based on critiques.

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

        # Build revision prompt
        prompt_parts = [
            f"## Task: Revise Market Analysis - {section_name}",
            "",
            "Revise the following market analysis section to address the critiques.",
            "",
            "## Original Content",
            "",
            original,
            "",
            "## Critiques to Address",
            "",
        ]

        for i, critique in enumerate(critiques, 1):
            prompt_parts.append(f"### Critique {i}")
            prompt_parts.append(f"- **Issue**: {critique.get('argument', 'No argument')}")
            prompt_parts.append(f"- **Severity**: {critique.get('severity', 'Unknown')}")
            prompt_parts.append(f"- **Suggested Remedy**: {critique.get('suggested_remedy', 'None')}")
            prompt_parts.append("")

        prompt_parts.extend([
            "## Instructions",
            "",
            "1. Address each critique while maintaining analytical rigor",
            "2. Add data or evidence where gaps were identified",
            "3. Clarify assumptions where challenged",
            "4. Maintain objective, data-driven tone",
            "",
            f"Provide the complete revised {section_name} section.",
        ])

        prompt = "\n".join(prompt_parts)

        llm_response = await self._call_llm(
            system_prompt=MARKET_ANALYST_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            return llm_response.get("content", original)
        return original

    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock market analysis content for testing."""

        if "opportunity" in prompt.lower() and "ranking" in prompt.lower():
            return """## Opportunity Rankings

### Rank 1: Enterprise IT Modernization Support
**Overall Score**: 8.5/10
**Breakdown**: Capability 9, Certification 8, Past Performance 8, Competitive 8, Strategic 9
**Rationale**: Strong alignment with company's cloud migration and IT modernization capabilities.
Direct experience with similar scope at comparable agencies positions the company well.
**Risks**: Incumbent has been on contract for 5 years with strong relationship. May require
aggressive pricing strategy.
**Next Steps**: Engage with agency IT leadership, submit capability statement, identify teaming partners.

### Rank 2: Cybersecurity Assessment Services
**Overall Score**: 7.8/10
**Breakdown**: Capability 8, Certification 9, Past Performance 7, Competitive 7, Strategic 8
**Rationale**: CMMC certification provides significant advantage. Growing cybersecurity
budget allocation at this agency.
**Risks**: Competitive field with multiple qualified vendors. Need to differentiate on methodology.
**Next Steps**: Develop detailed technical approach, identify cleared personnel availability.

### Rank 3: Data Analytics Platform Development
**Overall Score**: 7.2/10
**Breakdown**: Capability 8, Certification 7, Past Performance 6, Competitive 8, Strategic 8
**Rationale**: Emerging capability area with strong market growth. Agency modernization
priorities align with company's platform experience.
**Risks**: Limited directly relevant past performance. May need teaming arrangement.
**Next Steps**: Identify subcontractor with agency-specific experience, develop proof of concept."""

        elif "incumbent" in prompt.lower():
            return """## Incumbent Strength Assessment

**Overall Position**: Moderate

The incumbent has maintained a satisfactory performance record over 4 years but shows
several vulnerabilities that could be exploited in a competitive recompete.

### Performance Vulnerabilities

1. **Schedule Performance Issues**: CPARS shows "Satisfactory" schedule ratings, indicating
   potential delivery challenges. This creates opportunity to emphasize delivery excellence.

2. **Limited Innovation**: Contract modifications suggest reactive rather than proactive
   approach to emerging requirements. Position company as forward-thinking partner.

3. **Key Personnel Turnover**: Industry sources indicate high turnover on the contract,
   potentially affecting institutional knowledge and customer relationships.

### Competitive Strategy Recommendations

1. **Emphasize Fresh Perspective**: Position as bringing new ideas and modern approaches
2. **Highlight Stability**: Showcase low turnover rates and key personnel commitment
3. **Demonstrate Proactive Value**: Propose innovation initiatives beyond basic requirements

### Risk Assessment

**Probability of Displacing Incumbent**: Medium (40-60%)

The incumbent has relationship advantages but performance gaps create openings. Success
depends on demonstrating clear value improvement proposition."""

        else:
            # Comprehensive market analysis
            return """## Market Sizing

### Total Addressable Market (TAM)
The federal IT services market for NAICS 541512 (Computer Systems Design Services) represents
approximately **$45.2 billion** in annual contract obligations based on FY2024 USASpending data.

### Serviceable Addressable Market (SAM)
Filtering for small business set-asides and target agencies reduces the addressable market to
approximately **$8.7 billion**, representing opportunities where the company has competitive eligibility.

### Target Market
Based on company capabilities, certifications, and geographic presence, the realistic target
market is estimated at **$1.2 billion** in annual opportunity value.

**Key Assumptions**:
- Small business revenue threshold maintained
- Active certifications (8(a), HUBZone) remain valid
- Geographic focus on DC Metro and remote-eligible contracts
- Excludes classified work requiring facility clearance

## Top Opportunities

### 1. DoD Enterprise Cloud Migration - IDIQ
- **Estimated Value**: $250M ceiling
- **Expected RFP**: FY25 Q2
- **Alignment Score**: 9/10
- **Rationale**: Direct alignment with cloud migration capabilities; SDVOSB set-aside preferred

### 2. DHS IT Modernization Support
- **Estimated Value**: $75M (5-year)
- **Expected RFP**: FY25 Q3
- **Alignment Score**: 8/10
- **Rationale**: Past performance at DHS component; incumbent showing performance gaps

### 3. VA Digital Transformation Services
- **Estimated Value**: $120M ceiling
- **Expected RFP**: FY25 Q4
- **Alignment Score**: 7/10
- **Rationale**: Growing budget allocation; emphasis on veteran-owned businesses

## Competitive Landscape

**Competitive Density**: Medium-High

The IT services market remains competitive with well-established players. However, small
business set-asides and specialized certifications create protected market segments.

**Key Competitors**:
- Competitor A: Strong incumbent position at DoD; comparable size and capabilities
- Competitor B: Aggressive pricing strategy; limited technical depth
- Competitor C: Strong past performance but capacity constraints

**Market Barriers**:
- Past performance requirements for large contracts
- Incumbent relationships at key agencies
- Cleared personnel availability

**Market Enablers**:
- Small business preference in acquisition strategies
- Agency modernization mandates driving new procurements
- Cloud-first policies creating technology refresh cycles

## Timing Considerations

### Fiscal Year Dynamics
- **Q4 Surge** (Jul-Sep): 35% of annual obligations awarded; prepare for accelerated timelines
- **Q1 Catch-up** (Oct-Dec): Continuing Resolution uncertainty may delay new starts
- **Q2-Q3** (Jan-Jun): Strategic timing for major recompetes and new requirements

### Key Upcoming Windows
1. DoD Enterprise Cloud - Position by December for Q2 RFP
2. DHS Modernization - Begin agency engagement Q1
3. VA Digital - Monitor for draft RFP in Q3

### Recompete Opportunities
- Current incumbent contracts expiring in 6-18 months represent prime opportunities
- Focus relationship building on contracts showing performance issues

## Market Trends

1. **Cloud Adoption Acceleration**: Agencies increasing cloud investments 15% annually
2. **Cybersecurity Priority**: CMMC requirements expanding across DoD supply chain
3. **AI/ML Integration**: Growing demand for AI-enabled solutions in federal IT
4. **Zero Trust Architecture**: Mandated implementation driving consulting demand

## Recommendations

1. **Prioritize DoD Enterprise Cloud opportunity** - Best alignment and timing
2. **Develop HHS/VA pipeline** - Growing budgets and veteran preference
3. **Invest in AI/ML capabilities** - Emerging differentiator for IT services
4. **Strengthen cleared workforce** - Enable classified opportunity pursuit
5. **Monitor DHS recompetes** - Incumbent vulnerabilities create openings"""

    def _parse_analysis_response(
        self,
        content: str,
        result: MarketAnalysisResult,
    ) -> MarketAnalysisResult:
        """Parse LLM response into structured MarketAnalysisResult."""

        # Extract market sizing
        tam_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(?:billion|B)', content, re.IGNORECASE)
        if tam_match:
            result.total_addressable_market = float(tam_match.group(1)) * 1000  # Convert to millions

        sam_match = re.search(
            r'serviceable.*?\$(\d+(?:\.\d+)?)\s*(?:billion|B|million|M)',
            content,
            re.IGNORECASE
        )
        if sam_match:
            value = float(sam_match.group(1))
            if 'billion' in content[sam_match.start():sam_match.end()].lower():
                value *= 1000
            result.serviceable_addressable_market = value

        # Extract competitive density
        if 'high' in content.lower() and 'competitive' in content.lower():
            result.competitive_density = "High"
        elif 'medium' in content.lower() and 'competitive' in content.lower():
            result.competitive_density = "Medium"
        elif 'low' in content.lower() and 'competitive' in content.lower():
            result.competitive_density = "Low"

        # Extract trends
        trend_section = re.search(
            r'##\s*Market Trends(.*?)(?=##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if trend_section:
            trends = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', trend_section.group(1))
            result.market_trends = trends

        # Extract timing recommendations
        timing_section = re.search(
            r'##\s*Timing(.*?)(?=##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if timing_section:
            recommendations = re.findall(r'[-•]\s*(.+?)(?=\n|$)', timing_section.group(1))
            result.timing_recommendations = [r.strip() for r in recommendations if r.strip()]

        return result

    def _parse_ranked_opportunities(self, content: str) -> List[Dict[str, Any]]:
        """Parse ranked opportunities from LLM response."""
        opportunities = []

        # Find rank sections
        rank_matches = re.finditer(
            r'###\s*Rank\s*(\d+)[:\s]*([^\n]+).*?'
            r'\*\*Overall Score\*\*[:\s]*(\d+(?:\.\d+)?)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        for match in rank_matches:
            rank = int(match.group(1))
            title = match.group(2).strip()
            score = float(match.group(3))

            # Extract rationale
            rationale_match = re.search(
                rf'Rank\s*{rank}.*?\*\*Rationale\*\*[:\s]*([^\n*]+)',
                content,
                re.DOTALL | re.IGNORECASE
            )
            rationale = rationale_match.group(1).strip() if rationale_match else ""

            opportunities.append({
                "rank": rank,
                "title": title,
                "score": score,
                "rationale": rationale,
            })

        return sorted(opportunities, key=lambda x: x["rank"])

    def _parse_timing_recommendations(self, content: str) -> List[str]:
        """Extract timing recommendations from content."""
        recommendations = []

        # Look for bullet points or numbered items in timing sections
        timing_section = re.search(
            r'timing|fiscal|schedule|window',
            content,
            re.IGNORECASE
        )

        if timing_section:
            bullets = re.findall(r'[-•]\s*([^-•\n]{20,})', content)
            recommendations = [b.strip() for b in bullets if 'timing' in b.lower() or 'Q' in b]

        return recommendations[:10]  # Limit to top 10

    def _parse_fiscal_considerations(self, content: str) -> List[str]:
        """Extract fiscal year considerations from content."""
        considerations = []

        fiscal_patterns = [
            r'Q[1-4]\s+(?:surge|spending|activity)',
            r'fiscal\s+year\s+(?:end|start)',
            r'continuing\s+resolution',
            r'budget\s+(?:cycle|expiration)',
        ]

        for pattern in fiscal_patterns:
            matches = re.findall(rf'.*{pattern}.*', content, re.IGNORECASE)
            considerations.extend([m.strip() for m in matches])

        return list(set(considerations))[:5]  # Dedupe and limit

    def _format_analysis_content(
        self,
        result: MarketAnalysisResult,
        analysis_type: str,
    ) -> str:
        """Format analysis result as content string."""

        if analysis_type == "opportunity_ranking":
            return self._format_opportunities_section(result)
        elif analysis_type == "incumbent_analysis":
            return result.incumbent_assessment
        elif analysis_type == "timing_analysis":
            return self._format_timing_section(result)
        else:
            # Comprehensive analysis - return full content
            return format_market_comprehensive_section(result)

    def _format_market_sizing_section(self, result: MarketAnalysisResult) -> str:
        """Format market sizing as a section."""
        return format_market_sizing_section(result)

    def _format_opportunities_section(self, result: MarketAnalysisResult) -> str:
        """Format opportunities as a section."""
        return format_opportunities_section(result.ranked_opportunities)

    def _format_competitive_section(self, result: MarketAnalysisResult) -> str:
        """Format competitive landscape as a section."""
        return format_competitive_section(result)

    def _format_timing_section(self, result: MarketAnalysisResult) -> str:
        """Format timing recommendations as a section."""
        return format_timing_section(result.timing_recommendations, result.fiscal_considerations)
