"""
Market Analyst Agent Prompts

Prompt templates for the Market Analyst agent, responsible for
government market intelligence, trend analysis, and opportunity
identification.
"""

from typing import Dict, Any, List, Optional

from agents.utils.profile_formatter import (
    format_federal_history,
    format_teaming_relationships,
    format_geographic_coverage,
    format_socioeconomic_status,
)


MARKET_ANALYST_SYSTEM_PROMPT = """You are the Market Analyst, a government contracting (GovCon) market intelligence specialist.
Your role is to analyze federal market data and provide actionable insights for business development strategy.

## Your Perspective
You are data-driven and analytical, focusing on objective market assessments. You identify opportunities
based on alignment between company capabilities and market demand, while honestly assessing competitive
challenges and timing considerations.

## Your Responsibilities
1. Analyze agency budget trends and procurement patterns
2. Identify relevant opportunities based on NAICS codes and company capabilities
3. Assess competitive density and incumbent strength
4. Provide timing recommendations aligned with fiscal year cycles
5. Produce market sizing estimates with clearly stated assumptions

## Data Sources You Analyze
- SAM.gov opportunity postings and forecasts
- FPDS (Federal Procurement Data System) award history
- USASpending contract data
- Agency procurement forecasts and budgets
- CPARS performance data (when available)

## Analysis Standards
- **Quantitative**: Provide specific numbers and percentages when possible
- **Sourced**: Reference data sources for key claims
- **Assumption-Aware**: Clearly state assumptions in market sizing
- **Actionable**: Translate data into strategic recommendations
- **Balanced**: Acknowledge uncertainties and data limitations

## Output Quality
Your analyses should:
- Lead with key findings and recommendations
- Support conclusions with specific data points
- Identify patterns in procurement behavior
- Flag timing sensitivities (fiscal year end, recompetes)
- Assess realistic probability of success
"""


def get_market_analysis_prompt(
    company_profile: Dict[str, Any],
    market_data: Optional[Dict[str, Any]] = None,
    target_agencies: Optional[List[str]] = None,
    focus_areas: Optional[List[str]] = None,
) -> str:
    """
    Generate a prompt for comprehensive market analysis.

    Args:
        company_profile: Company profile data
        market_data: Market data including budgets, awards, forecasts
        target_agencies: Specific agencies to focus on
        focus_areas: Specific areas or capabilities to analyze

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Comprehensive Market Analysis",
        "",
        "Analyze the federal contracting market for the following company and provide strategic recommendations.",
        "",
        "---",
        "",
        "## Company Profile",
        "",
    ]

    # Add company information
    if company_profile:
        prompt_parts.append(f"**Company**: {company_profile.get('name', 'N/A')}")
        prompt_parts.append(f"**Annual Revenue**: ${company_profile.get('annual_revenue', 0):,.2f}")
        prompt_parts.append(f"**Employee Count**: {company_profile.get('employee_count', 'N/A')}")
        if company_profile.get('years_in_business'):
            prompt_parts.append(f"**Years in Business**: {company_profile.get('years_in_business')}")
        prompt_parts.append("")

        # Socioeconomic status (relevant for set-aside market analysis)
        socio_lines = format_socioeconomic_status(company_profile)
        if socio_lines:
            prompt_parts.extend(socio_lines)
            prompt_parts.append("")

        # NAICS codes
        naics = company_profile.get('naics_codes', [])
        if naics:
            prompt_parts.append("**NAICS Codes**:")
            for n in naics:
                # Handle both dict format and string format
                if isinstance(n, dict):
                    primary = " (Primary)" if n.get('is_primary') else ""
                    size_std = f" [Size Std: {n.get('small_business_size_standard')}]" if n.get('small_business_size_standard') else ""
                    prompt_parts.append(f"  - {n.get('code')}: {n.get('description')}{primary}{size_std}")
                else:
                    # Simple string format (just the code)
                    prompt_parts.append(f"  - {n}")
            prompt_parts.append("")

        # Certifications
        certs = company_profile.get('certifications', [])
        if certs:
            prompt_parts.append("**Certifications**:")
            for c in certs:
                # Handle both dict format and string format
                if isinstance(c, dict):
                    level = f" - Level {c.get('level')}" if c.get('level') else ""
                    prompt_parts.append(f"  - {c.get('cert_type')}{level}")
                else:
                    # Simple string format
                    prompt_parts.append(f"  - {c}")
            prompt_parts.append("")

        # Core capabilities
        caps = company_profile.get('core_capabilities', [])
        if caps:
            prompt_parts.append("**Core Capabilities**:")
            for cap in caps:
                prompt_parts.append(f"  - {cap.get('name')}")
            prompt_parts.append("")

        # Target agencies
        agencies = target_agencies or company_profile.get('target_agencies', [])
        if agencies:
            prompt_parts.append(f"**Target Agencies**: {', '.join(agencies)}")
            prompt_parts.append("")

        # Geographic Coverage (important for market analysis)
        geo_lines = format_geographic_coverage(company_profile)
        if geo_lines:
            prompt_parts.extend(geo_lines)
            prompt_parts.append("")

        # Federal Contracting History (provides market context)
        history_lines = format_federal_history(company_profile)
        if history_lines:
            prompt_parts.extend(history_lines)
            prompt_parts.append("")

        # Teaming Relationships (important for market positioning)
        teaming_lines = format_teaming_relationships(company_profile)
        if teaming_lines:
            prompt_parts.extend(teaming_lines)
            prompt_parts.append("")

    # Add market data if provided
    if market_data:
        prompt_parts.extend([
            "---",
            "",
            "## Market Data",
            "",
        ])

        # Agency budgets
        budgets = market_data.get('agency_budgets', {})
        if budgets:
            prompt_parts.append("### Agency Budget Information")
            for agency, budget in budgets.items():
                prompt_parts.append(f"**{agency}** (FY{budget.get('fiscal_year', 'N/A')})")
                prompt_parts.append(f"  - Total Budget: ${budget.get('total_budget', 0):.1f}M")
                prompt_parts.append(f"  - Trend: {budget.get('budget_trend', 'Unknown')}")
                if budget.get('yoy_change_percent'):
                    prompt_parts.append(f"  - YoY Change: {budget.get('yoy_change_percent'):+.1f}%")
                if budget.get('priority_areas'):
                    prompt_parts.append(f"  - Priority Areas: {', '.join(budget.get('priority_areas', []))}")
            prompt_parts.append("")

        # Recent awards
        awards = market_data.get('recent_awards', [])
        if awards:
            prompt_parts.append("### Recent Contract Awards")
            for award in awards[:10]:  # Limit to top 10
                prompt_parts.append(f"- **{award.get('title', 'Untitled')}**")
                prompt_parts.append(f"  Agency: {award.get('agency', 'N/A')} | Value: ${award.get('award_amount', 0):,.0f}")
                prompt_parts.append(f"  Awardee: {award.get('awardee_name', 'N/A')} | NAICS: {award.get('naics_code', 'N/A')}")
                if award.get('set_aside'):
                    prompt_parts.append(f"  Set-Aside: {award.get('set_aside')}")
            prompt_parts.append("")

        # Forecast opportunities
        forecasts = market_data.get('forecast_opportunities', [])
        if forecasts:
            prompt_parts.append("### Forecasted Opportunities")
            for forecast in forecasts[:10]:  # Limit to top 10
                prompt_parts.append(f"- **{forecast.get('title', 'Untitled')}**")
                prompt_parts.append(f"  Agency: {forecast.get('agency', 'N/A')}")
                if forecast.get('estimated_value'):
                    prompt_parts.append(f"  Estimated Value: ${forecast.get('estimated_value'):,.0f}")
                if forecast.get('fiscal_quarter'):
                    prompt_parts.append(f"  Expected: {forecast.get('fiscal_quarter')}")
                if forecast.get('is_recompete') and forecast.get('incumbent'):
                    prompt_parts.append(f"  Recompete - Incumbent: {forecast.get('incumbent')}")
            prompt_parts.append("")

        # Incumbent performance
        incumbents = market_data.get('incumbent_performance', {})
        if incumbents:
            prompt_parts.append("### Incumbent Performance Data")
            for name, perf in incumbents.items():
                prompt_parts.append(f"- **{name}**")
                if perf.get('overall_rating'):
                    prompt_parts.append(f"  Overall Rating: {perf.get('overall_rating')}")
                prompt_parts.append(f"  Relationship: {perf.get('relationship_strength', 'Unknown')}")
                prompt_parts.append(f"  Recompete Risk: {perf.get('recompete_likelihood', 'Unknown')}")
                if perf.get('vulnerabilities'):
                    prompt_parts.append(f"  Vulnerabilities: {', '.join(perf.get('vulnerabilities', []))}")
            prompt_parts.append("")

    # Focus areas
    if focus_areas:
        prompt_parts.extend([
            "---",
            "",
            f"## Focus Areas: {', '.join(focus_areas)}",
            "",
            "Prioritize analysis of these specific areas or capabilities.",
            "",
        ])

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Analysis Sections",
        "",
        "Provide analysis for each of the following sections:",
        "",
        "### 1. Market Sizing",
        "- Total Addressable Market (TAM) for company's NAICS codes",
        "- Serviceable Addressable Market (SAM) based on certifications and capabilities",
        "- Target Market based on agency focus and competitive position",
        "- State all assumptions clearly",
        "",
        "### 2. Top Opportunities",
        "- Identify 3-5 priority opportunities",
        "- For each: rationale, estimated value, timing, competitive assessment",
        "- Rank by alignment with company capabilities and probability of success",
        "",
        "### 3. Competitive Landscape",
        "- Overall competitive density assessment",
        "- Key competitors and their strengths",
        "- Incumbent analysis and vulnerabilities",
        "- Market barriers and enablers",
        "",
        "### 4. Timing Considerations",
        "- Fiscal year timing (Q4 surge, year-end spending)",
        "- Upcoming recompete windows",
        "- Solicitation timing recommendations",
        "- Budget cycle considerations",
        "",
        "### 5. Market Trends",
        "- Budget trends affecting target agencies",
        "- Technology or methodology shifts",
        "- Policy changes impacting procurement",
        "- Emerging opportunity areas",
        "",
        "### 6. Recommendations",
        "- Strategic recommendations for market entry/expansion",
        "- Positioning recommendations",
        "- Timing recommendations",
        "- Risk factors to monitor",
        "",
        "Format each section with a clear heading (## Section Name) and provide specific, data-backed insights.",
    ])

    return "\n".join(prompt_parts)


def get_opportunity_ranking_prompt(
    company_profile: Dict[str, Any],
    opportunities: List[Dict[str, Any]],
    max_opportunities: int = 5,
) -> str:
    """
    Generate a prompt for ranking and prioritizing opportunities.

    Args:
        company_profile: Company profile data
        opportunities: List of opportunities to rank
        max_opportunities: Maximum number of opportunities to return

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Opportunity Ranking and Prioritization",
        "",
        f"Evaluate the following opportunities and rank the top {max_opportunities} based on fit with the company's capabilities.",
        "",
        "---",
        "",
        "## Company Summary",
        "",
    ]

    # Summarize company capabilities
    if company_profile:
        prompt_parts.append(f"**Company**: {company_profile.get('name', 'N/A')}")

        naics = company_profile.get('naics_codes', [])
        if naics:
            codes = [n.get('code') for n in naics]
            prompt_parts.append(f"**NAICS Codes**: {', '.join(codes)}")

        certs = company_profile.get('certifications', [])
        if certs:
            cert_types = [c.get('cert_type') for c in certs]
            prompt_parts.append(f"**Certifications**: {', '.join(cert_types)}")

        caps = company_profile.get('core_capabilities', [])
        if caps:
            cap_names = [c.get('name') for c in caps]
            prompt_parts.append(f"**Capabilities**: {', '.join(cap_names)}")

        agencies = company_profile.get('target_agencies', [])
        if agencies:
            prompt_parts.append(f"**Target Agencies**: {', '.join(agencies)}")

        prompt_parts.append("")

    # List opportunities
    prompt_parts.extend([
        "---",
        "",
        "## Opportunities to Evaluate",
        "",
    ])

    for i, opp in enumerate(opportunities, 1):
        prompt_parts.append(f"### Opportunity {i}: {opp.get('title', 'Untitled')}")
        prompt_parts.append(f"- **Agency**: {opp.get('agency', 'N/A')}")
        prompt_parts.append(f"- **NAICS**: {opp.get('naics_code', 'N/A')}")
        if opp.get('estimated_value'):
            prompt_parts.append(f"- **Estimated Value**: ${opp.get('estimated_value'):,.0f}")
        if opp.get('set_aside'):
            prompt_parts.append(f"- **Set-Aside**: {opp.get('set_aside')}")
        if opp.get('description'):
            prompt_parts.append(f"- **Description**: {opp.get('description')}")
        if opp.get('is_recompete'):
            incumbent = opp.get('incumbent', 'Unknown')
            prompt_parts.append(f"- **Recompete**: Yes (Incumbent: {incumbent})")
        if opp.get('fiscal_quarter'):
            prompt_parts.append(f"- **Expected Timing**: {opp.get('fiscal_quarter')}")
        prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Evaluation Criteria",
        "",
        "For each opportunity, assess:",
        "1. **Capability Fit** (1-10): How well do company capabilities align with requirements?",
        "2. **Certification Match** (1-10): Does the company have required certifications/set-aside eligibility?",
        "3. **Past Performance Relevance** (1-10): How relevant is existing past performance?",
        "4. **Competitive Position** (1-10): Likelihood of winning against competitors?",
        "5. **Strategic Value** (1-10): Importance for company's growth strategy?",
        "",
        f"## Required Output",
        "",
        f"Provide a ranked list of the top {max_opportunities} opportunities with:",
        "1. Overall score (average of criteria scores)",
        "2. Score breakdown by criterion",
        "3. Key rationale for ranking",
        "4. Risk factors or concerns",
        "5. Recommended next steps",
        "",
        "Format as:",
        "",
        "## Opportunity Rankings",
        "",
        "### Rank 1: [Opportunity Title]",
        "**Overall Score**: X.X/10",
        "**Breakdown**: Capability X, Certification X, Past Performance X, Competitive X, Strategic X",
        "**Rationale**: [Why this ranks highly]",
        "**Risks**: [Potential concerns]",
        "**Next Steps**: [Recommended actions]",
        "",
        "(Continue for remaining ranked opportunities)",
    ])

    return "\n".join(prompt_parts)


def get_incumbent_analysis_prompt(
    incumbent_data: Dict[str, Any],
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for analyzing incumbent performance and vulnerabilities.

    Args:
        incumbent_data: Incumbent performance data
        opportunity: Optional opportunity context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Incumbent Analysis",
        "",
        "Analyze the incumbent contractor and identify potential vulnerabilities for competitive positioning.",
        "",
        "---",
        "",
        "## Incumbent Data",
        "",
    ]

    # Add incumbent details
    if incumbent_data:
        prompt_parts.append(f"**Contractor**: {incumbent_data.get('contractor_name', 'N/A')}")
        prompt_parts.append(f"**Agency**: {incumbent_data.get('agency', 'N/A')}")

        if incumbent_data.get('overall_rating'):
            prompt_parts.append(f"**Overall CPARS Rating**: {incumbent_data.get('overall_rating')}")

        if incumbent_data.get('quality_rating'):
            prompt_parts.append(f"**Quality Rating**: {incumbent_data.get('quality_rating')}")

        if incumbent_data.get('schedule_rating'):
            prompt_parts.append(f"**Schedule Rating**: {incumbent_data.get('schedule_rating')}")

        prompt_parts.append("")
        prompt_parts.append("**Contract Performance**:")
        prompt_parts.append(f"  - Option Years Exercised: {incumbent_data.get('option_years_exercised', 0)} of {incumbent_data.get('total_option_years', 0)}")
        prompt_parts.append(f"  - Contract Modifications: {incumbent_data.get('contract_modifications', 0)}")

        if incumbent_data.get('has_stop_work_orders'):
            prompt_parts.append("  - Stop Work Orders: Yes")
        if incumbent_data.get('has_cure_notices'):
            prompt_parts.append("  - Cure Notices: Yes")
        if incumbent_data.get('has_show_cause_notices'):
            prompt_parts.append("  - Show Cause Notices: Yes")

        prompt_parts.append("")
        prompt_parts.append("**Relationship**:")
        prompt_parts.append(f"  - Years with Agency: {incumbent_data.get('years_with_agency', 0)}")
        prompt_parts.append(f"  - Other Contracts: {incumbent_data.get('other_contracts_with_agency', 0)}")
        prompt_parts.append(f"  - Relationship Strength: {incumbent_data.get('relationship_strength', 'Unknown')}")

        if incumbent_data.get('strengths'):
            prompt_parts.append("")
            prompt_parts.append("**Known Strengths**:")
            for s in incumbent_data.get('strengths', []):
                prompt_parts.append(f"  - {s}")

        if incumbent_data.get('vulnerabilities'):
            prompt_parts.append("")
            prompt_parts.append("**Known Vulnerabilities**:")
            for v in incumbent_data.get('vulnerabilities', []):
                prompt_parts.append(f"  - {v}")

        prompt_parts.append("")

    # Add opportunity context if provided
    if opportunity:
        prompt_parts.extend([
            "---",
            "",
            "## Opportunity Context",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Value**: ${opportunity.get('estimated_value', 0):,.0f}",
            f"**Contract End**: {opportunity.get('current_contract_end', 'N/A')}",
            "",
        ])

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Analysis",
        "",
        "### 1. Incumbent Strength Assessment",
        "- Overall strength of incumbent position (Strong/Moderate/Weak)",
        "- Key factors supporting their position",
        "- Relationship dynamics with the agency",
        "",
        "### 2. Performance Vulnerabilities",
        "- Specific performance issues that can be exploited",
        "- Areas where incumbent may be underperforming",
        "- Customer satisfaction indicators",
        "",
        "### 3. Competitive Strategy",
        "- Recommended approach to compete against this incumbent",
        "- Key differentiators to emphasize",
        "- Win themes that address incumbent weaknesses",
        "",
        "### 4. Risk Assessment",
        "- Probability of displacing incumbent (High/Medium/Low)",
        "- Factors that could favor the incumbent",
        "- Mitigation strategies for competitive risks",
        "",
        "Provide specific, actionable insights that can inform capture strategy.",
    ])

    return "\n".join(prompt_parts)


def get_timing_analysis_prompt(
    forecast_opportunities: List[Dict[str, Any]],
    agency_budgets: Optional[Dict[str, Dict[str, Any]]] = None,
    current_fiscal_year: Optional[int] = None,
) -> str:
    """
    Generate a prompt for timing and fiscal year analysis.

    Args:
        forecast_opportunities: List of forecasted opportunities
        agency_budgets: Agency budget data
        current_fiscal_year: Current fiscal year for context

    Returns:
        Formatted prompt string
    """
    from datetime import date

    if current_fiscal_year is None:
        today = date.today()
        current_fiscal_year = today.year if today.month >= 10 else today.year

    prompt_parts = [
        "## Task: Timing and Fiscal Year Analysis",
        "",
        f"Analyze procurement timing for FY{current_fiscal_year} and FY{current_fiscal_year + 1} and provide strategic timing recommendations.",
        "",
        "---",
        "",
        "## Forecasted Opportunities",
        "",
    ]

    # Group by fiscal quarter
    by_quarter: Dict[str, List] = {}
    for opp in forecast_opportunities:
        quarter = opp.get('fiscal_quarter', 'Unknown')
        if quarter not in by_quarter:
            by_quarter[quarter] = []
        by_quarter[quarter].append(opp)

    for quarter, opps in sorted(by_quarter.items()):
        prompt_parts.append(f"### {quarter}")
        for opp in opps:
            prompt_parts.append(f"- **{opp.get('title', 'Untitled')}** ({opp.get('agency', 'N/A')})")
            if opp.get('estimated_value'):
                prompt_parts.append(f"  Value: ${opp.get('estimated_value'):,.0f}")
            if opp.get('is_recompete'):
                prompt_parts.append(f"  Recompete - Incumbent: {opp.get('incumbent', 'Unknown')}")
        prompt_parts.append("")

    # Add budget context
    if agency_budgets:
        prompt_parts.extend([
            "---",
            "",
            "## Agency Budget Context",
            "",
        ])
        for agency, budget in agency_budgets.items():
            trend = budget.get('budget_trend', 'Unknown')
            prompt_parts.append(f"- **{agency}**: {trend} trend")
            if budget.get('priority_areas'):
                prompt_parts.append(f"  Priority areas: {', '.join(budget.get('priority_areas', []))}")
        prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Analysis",
        "",
        "### 1. Fiscal Year Calendar",
        "- Q4 year-end spending surge opportunities",
        "- Budget expiration considerations",
        "- Continuing Resolution (CR) impacts",
        "",
        "### 2. Recompete Windows",
        "- Upcoming contract expirations",
        "- Option year decision points",
        "- Incumbent performance review timing",
        "",
        "### 3. Solicitation Timing",
        "- Expected solicitation release patterns",
        "- Historical procurement cycle timing",
        "- Lead time requirements for positioning",
        "",
        "### 4. Strategic Timing Recommendations",
        "- When to engage with agencies",
        "- Proposal preparation timelines",
        "- Teaming arrangement timing",
        "- Market research submission windows",
        "",
        "### 5. Risk Factors",
        "- Budget uncertainty impacts",
        "- Continuing Resolution scenarios",
        "- Potential delays to monitor",
        "",
        "Provide a timeline-focused analysis with specific dates and quarters where possible.",
    ])

    return "\n".join(prompt_parts)
