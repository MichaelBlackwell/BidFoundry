"""
Capture Strategist Agent Prompts

Prompt templates for the Capture Strategist agent, responsible for
win strategy development, discriminator identification, ghost team
analysis, and price-to-win guidance.
"""

from typing import Dict, Any, List, Optional

from agents.utils.profile_formatter import (
    format_management_team,
    format_ownership_structure,
    format_socioeconomic_status,
    format_teaming_relationships,
    format_geographic_coverage,
    extract_certification_types,
)


CAPTURE_STRATEGIST_SYSTEM_PROMPT = """You are the Capture Strategist, a win strategy expert for government contracting (GovCon).
Your role is to develop compelling win strategies that differentiate the company from competitors and maximize probability of winning.

## Your Perspective
You are strategically aggressive yet realistic, focusing on actionable competitive positioning. You identify what makes
the company uniquely qualified to win and how to counter competitor strengths. Your strategies are grounded in
evaluation criteria alignment and customer-focused value propositions.

## Your Responsibilities
1. Develop 3-5 compelling win themes based on company strengths vs. opportunity requirements
2. Identify discriminators that set the company apart from competition
3. Anticipate competitor positioning through ghost team analysis
4. Provide directional price-to-win guidance based on competitive landscape
5. Align capture strategy with evaluation criteria and customer hot buttons

## Strategic Framework
- **Win Themes**: High-level value propositions that resonate with evaluators
- **Discriminators**: Specific, provable differentiators that competitors cannot match
- **Ghost Team**: Realistic simulation of competitor strategies and positioning
- **Price-to-Win**: Directional guidance on competitive pricing positioning

## Analysis Standards
- **Customer-Focused**: Frame all strategies around customer benefits
- **Evidence-Based**: Link strategies to provable past performance and capabilities
- **Evaluation-Aligned**: Map strategies to stated evaluation criteria
- **Competitively Aware**: Account for likely competitor positioning
- **Actionable**: Provide specific implementation guidance

## Output Quality
Your strategies should:
- Be specific to the opportunity, not generic
- Include supporting evidence from company capabilities
- Address customer hot buttons and pain points
- Counter anticipated competitor strategies
- Align with evaluation criteria weighting

## Output Length
Keep responses concise - approximately 1 page (~500-600 words). Be direct and focus on the most critical points. Prioritize actionable insights over comprehensive coverage.
"""


def get_win_theme_development_prompt(
    company_profile: Dict[str, Any],
    opportunity: Dict[str, Any],
    competitor_intel: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for developing win themes.

    Args:
        company_profile: Company profile data
        opportunity: Opportunity details
        competitor_intel: Optional competitor intelligence

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Win Theme Development",
        "",
        "Develop 3-5 compelling win themes that position the company to win this opportunity.",
        "",
        "---",
        "",
        "## Company Profile",
        "",
    ]

    # Add company information
    if company_profile:
        prompt_parts.append(f"**Company**: {company_profile.get('name', 'N/A')}")
        prompt_parts.append("")

        # Socioeconomic status (potential discriminator for set-asides)
        socio_lines = format_socioeconomic_status(company_profile)
        if socio_lines:
            prompt_parts.extend(socio_lines)
            prompt_parts.append("")

        # Security Clearances (key differentiator)
        clearances = company_profile.get('security_clearances', [])
        if clearances:
            prompt_parts.append(f"**Security Clearances**: {', '.join(clearances)}")
            prompt_parts.append("")

        # Core capabilities
        caps = company_profile.get('core_capabilities', [])
        if caps:
            prompt_parts.append("**Core Capabilities**:")
            for cap in caps:
                prompt_parts.append(f"  - **{cap.get('name', 'N/A')}**")
                if cap.get('description'):
                    prompt_parts.append(f"    {cap.get('description')}")
                if cap.get('differentiators'):
                    for diff in cap.get('differentiators', []):
                        prompt_parts.append(f"    - Differentiator: {diff}")
            prompt_parts.append("")

        # Past performance
        past_perf = company_profile.get('past_performance', [])
        if past_perf:
            prompt_parts.append("**Relevant Past Performance**:")
            for pp in past_perf[:5]:  # Limit to top 5
                # Handle both dict format and string format
                if isinstance(pp, dict):
                    prompt_parts.append(f"  - **{pp.get('contract_name', 'N/A')}**")
                    value = pp.get('contract_value', pp.get('value', 0))
                    prompt_parts.append(f"    Agency: {pp.get('agency', 'N/A')} | Value: ${value:,.0f}")
                    if pp.get('overall_rating'):
                        prompt_parts.append(f"    Rating: {pp.get('overall_rating')}")
                    if pp.get('relevance'):
                        prompt_parts.append(f"    Relevance: {pp.get('relevance')}")
                    achievements = pp.get('key_accomplishments', pp.get('achievements', []))
                    if achievements:
                        for ach in achievements[:3]:
                            prompt_parts.append(f"    - {ach}")
                else:
                    # Simple string format
                    prompt_parts.append(f"  - {pp}")
            prompt_parts.append("")

        # Certifications
        certs = company_profile.get('certifications', [])
        if certs:
            cert_list = extract_certification_types(certs)
            prompt_parts.append(f"**Certifications**: {', '.join(cert_list)}")
            prompt_parts.append("")

        # Key personnel
        key_personnel = company_profile.get('key_personnel', [])
        if key_personnel:
            prompt_parts.append("**Key Personnel**:")
            for person in key_personnel[:5]:
                clearance = f" [{person.get('clearance_level')}]" if person.get('clearance_level') else ""
                prompt_parts.append(f"  - **{person.get('name', 'N/A')}** - {person.get('title', '')} / {person.get('role', 'N/A')}{clearance}")
                if person.get('years_experience'):
                    prompt_parts.append(f"    {person.get('years_experience')} years experience")
                qualifications = person.get('qualifications') or person.get('relevant_experience')
                if qualifications:
                    prompt_parts.append(f"    {qualifications}")
            prompt_parts.append("")

        # Management Team (leadership as differentiator)
        mgmt_lines = format_management_team(company_profile, limit=5)
        if mgmt_lines:
            prompt_parts.extend(mgmt_lines)
            prompt_parts.append("")

        # Ownership Structure (relevant for socioeconomic differentiators)
        ownership_lines = format_ownership_structure(company_profile)
        if ownership_lines:
            prompt_parts.extend(ownership_lines)
            prompt_parts.append("")

        # Geographic Coverage (geographic advantage)
        geo_lines = format_geographic_coverage(company_profile)
        if geo_lines:
            prompt_parts.extend(geo_lines)
            prompt_parts.append("")

        # Teaming Relationships (teaming discriminators)
        teaming_lines = format_teaming_relationships(company_profile)
        if teaming_lines:
            prompt_parts.extend(teaming_lines)
            prompt_parts.append("")

    # Add opportunity details
    prompt_parts.extend([
        "---",
        "",
        "## Opportunity Details",
        "",
    ])

    if opportunity:
        prompt_parts.append(f"**Title**: {opportunity.get('title', 'N/A')}")
        prompt_parts.append(f"**Agency**: {opportunity.get('agency', {}).get('name', opportunity.get('agency', 'N/A'))}")
        prompt_parts.append(f"**Estimated Value**: ${opportunity.get('estimated_value', 0):,.0f}")
        prompt_parts.append(f"**Set-Aside**: {opportunity.get('set_aside', 'N/A')}")
        prompt_parts.append("")

        # Scope
        if opportunity.get('scope_summary'):
            prompt_parts.append(f"**Scope**: {opportunity.get('scope_summary')}")
            prompt_parts.append("")

        # Key requirements
        key_reqs = opportunity.get('key_requirements', [])
        if key_reqs:
            prompt_parts.append("**Key Requirements**:")
            for req in key_reqs:
                prompt_parts.append(f"  - {req}")
            prompt_parts.append("")

        # Evaluation factors
        eval_factors = opportunity.get('evaluation_factors', [])
        if eval_factors:
            prompt_parts.append("**Evaluation Factors**:")
            for factor in eval_factors:
                if isinstance(factor, dict):
                    weight = f" (Weight: {factor.get('weight')}%)" if factor.get('weight') else ""
                    importance = f" [{factor.get('relative_importance')}]" if factor.get('relative_importance') else ""
                    prompt_parts.append(f"  - **{factor.get('name', 'N/A')}**{weight}{importance}")
                    if factor.get('subfactors'):
                        for sub in factor.get('subfactors', []):
                            prompt_parts.append(f"    - {sub}")
                else:
                    prompt_parts.append(f"  - {factor}")
            prompt_parts.append("")

        # Customer hot buttons
        hot_buttons = opportunity.get('customer_hot_buttons', [])
        if hot_buttons:
            prompt_parts.append("**Customer Hot Buttons**:")
            for hb in hot_buttons:
                prompt_parts.append(f"  - {hb}")
            prompt_parts.append("")

    # Add competitor intel if provided
    if competitor_intel:
        prompt_parts.extend([
            "---",
            "",
            "## Competitive Intelligence",
            "",
        ])

        competitors = competitor_intel.get('competitors', [])
        if competitors:
            for comp in competitors:
                is_incumbent = " (INCUMBENT)" if comp.get('is_incumbent') else ""
                prompt_parts.append(f"### {comp.get('name', 'Unknown')}{is_incumbent}")
                prompt_parts.append(f"**Estimated Strength**: {comp.get('estimated_strength', 'Unknown')}")

                if comp.get('known_strengths'):
                    prompt_parts.append("**Strengths**:")
                    for s in comp.get('known_strengths', []):
                        prompt_parts.append(f"  - {s}")

                if comp.get('known_weaknesses'):
                    prompt_parts.append("**Weaknesses**:")
                    for w in comp.get('known_weaknesses', []):
                        prompt_parts.append(f"  - {w}")

                if comp.get('likely_strategy'):
                    prompt_parts.append(f"**Likely Strategy**: {comp.get('likely_strategy')}")

                prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Output",
        "",
        "Develop 3-5 win themes following this structure for each:",
        "",
        "### Win Theme [Number]: [Theme Title]",
        "",
        "**Theme Statement**: A concise, customer-focused value proposition (1-2 sentences)",
        "",
        "**Supporting Evidence**:",
        "- Specific past performance that proves this capability",
        "- Relevant certifications or qualifications",
        "- Key personnel experience",
        "",
        "**Customer Benefit**: How this theme addresses customer hot buttons or pain points",
        "",
        "**Evaluation Criteria Alignment**: Which evaluation factors this theme addresses",
        "",
        "**Competitive Advantage**: Why competitors cannot match this theme",
        "",
        "---",
        "",
        "## Quality Criteria",
        "",
        "Each win theme must be:",
        "1. **Specific**: Tailored to this opportunity, not generic",
        "2. **Provable**: Supported by evidence from past performance",
        "3. **Customer-Focused**: Framed in terms of customer benefit",
        "4. **Differentiated**: Something competitors cannot easily claim",
        "5. **Evaluation-Aligned**: Mapped to stated evaluation criteria",
        "",
        "Prioritize win themes by impact on evaluation scoring.",
    ])

    return "\n".join(prompt_parts)


def get_discriminator_identification_prompt(
    company_profile: Dict[str, Any],
    opportunity: Dict[str, Any],
    competitor_intel: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for identifying discriminators.

    Args:
        company_profile: Company profile data
        opportunity: Opportunity details
        competitor_intel: Optional competitor intelligence

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Discriminator Identification",
        "",
        "Identify specific discriminators that differentiate the company from competitors for this opportunity.",
        "",
        "---",
        "",
        "## Discriminator Types",
        "",
        "Identify discriminators in each category:",
        "",
        "1. **Technical Discriminators**: Unique technical approaches, methodologies, or solutions",
        "2. **Management Discriminators**: Unique management approaches, processes, or tools",
        "3. **Past Performance Discriminators**: Unique experience that competitors lack",
        "4. **Personnel Discriminators**: Key personnel with unique qualifications",
        "5. **Corporate Discriminators**: Certifications, clearances, or capabilities unique to the company",
        "6. **Teaming Discriminators**: Unique teaming arrangements or partner capabilities",
        "",
        "---",
        "",
        "## Company Profile",
        "",
    ]

    # Add company information
    if company_profile:
        prompt_parts.append(f"**Company**: {company_profile.get('name', 'N/A')}")
        prompt_parts.append("")

        # Core capabilities with differentiators
        caps = company_profile.get('core_capabilities', [])
        if caps:
            prompt_parts.append("**Core Capabilities**:")
            for cap in caps:
                prompt_parts.append(f"  - **{cap.get('name', 'N/A')}**")
                if cap.get('differentiators'):
                    for diff in cap.get('differentiators', []):
                        prompt_parts.append(f"    - {diff}")
            prompt_parts.append("")

        # Proprietary assets
        proprietary = company_profile.get('proprietary_assets', [])
        if proprietary:
            prompt_parts.append("**Proprietary Assets**:")
            for asset in proprietary:
                prompt_parts.append(f"  - **{asset.get('name', 'N/A')}**: {asset.get('description', '')}")
            prompt_parts.append("")

        # Past performance highlights
        past_perf = company_profile.get('past_performance', [])
        if past_perf:
            prompt_parts.append("**Past Performance Highlights**:")
            for pp in past_perf[:5]:
                # Handle both dict format and string format
                if isinstance(pp, dict):
                    prompt_parts.append(f"  - {pp.get('contract_name', 'N/A')} ({pp.get('agency', 'N/A')})")
                    if pp.get('unique_aspects'):
                        for ua in pp.get('unique_aspects', []):
                            prompt_parts.append(f"    - {ua}")
                else:
                    # Simple string format
                    prompt_parts.append(f"  - {pp}")
            prompt_parts.append("")

        # Key personnel unique qualifications
        key_personnel = company_profile.get('key_personnel', [])
        if key_personnel:
            prompt_parts.append("**Key Personnel Unique Qualifications**:")
            for person in key_personnel[:5]:
                if person.get('unique_qualifications'):
                    prompt_parts.append(f"  - **{person.get('name', 'N/A')}**: {person.get('unique_qualifications')}")
            prompt_parts.append("")

        # Certifications
        certs = company_profile.get('certifications', [])
        if certs:
            prompt_parts.append("**Certifications**:")
            for c in certs:
                # Handle both dict format and string format
                if isinstance(c, dict):
                    level = f" (Level {c.get('level')})" if c.get('level') else ""
                    prompt_parts.append(f"  - {c.get('cert_type', 'N/A')}{level}")
                else:
                    prompt_parts.append(f"  - {c}")
            prompt_parts.append("")

    # Add opportunity context
    prompt_parts.extend([
        "---",
        "",
        "## Opportunity Requirements",
        "",
    ])

    if opportunity:
        prompt_parts.append(f"**Title**: {opportunity.get('title', 'N/A')}")
        prompt_parts.append("")

        key_reqs = opportunity.get('key_requirements', [])
        if key_reqs:
            prompt_parts.append("**Key Requirements**:")
            for req in key_reqs:
                prompt_parts.append(f"  - {req}")
            prompt_parts.append("")

        eval_factors = opportunity.get('evaluation_factors', [])
        if eval_factors:
            prompt_parts.append("**Evaluation Factors**:")
            for factor in eval_factors:
                if isinstance(factor, dict):
                    prompt_parts.append(f"  - {factor.get('name', factor)}")
                else:
                    prompt_parts.append(f"  - {factor}")
            prompt_parts.append("")

    # Add competitor context
    if competitor_intel:
        prompt_parts.extend([
            "---",
            "",
            "## Competitor Capabilities (for differentiation)",
            "",
        ])

        competitors = competitor_intel.get('competitors', [])
        for comp in competitors:
            prompt_parts.append(f"**{comp.get('name', 'Unknown')}**:")
            if comp.get('known_strengths'):
                prompt_parts.append(f"  Strengths: {', '.join(comp.get('known_strengths', []))}")
            if comp.get('certifications'):
                prompt_parts.append(f"  Certifications: {', '.join(comp.get('certifications', []))}")
        prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Output",
        "",
        "For each discriminator identified, provide:",
        "",
        "### Discriminator [Number]: [Title]",
        "",
        "**Type**: [Technical | Management | Past Performance | Personnel | Corporate | Teaming]",
        "",
        "**Description**: What specifically differentiates the company",
        "",
        "**Proof Point**: Specific evidence that validates this discriminator",
        "",
        "**Evaluation Factor Link**: Which evaluation factor(s) this supports",
        "",
        "**Competitor Gap**: Why competitors cannot claim this (be specific)",
        "",
        "**Messaging Guidance**: How to communicate this in the proposal",
        "",
        "---",
        "",
        "## Prioritization",
        "",
        "Rank discriminators by:",
        "1. Impact on evaluation scoring",
        "2. Difficulty for competitors to replicate",
        "3. Relevance to customer hot buttons",
        "",
        "Identify at least 5-7 discriminators across different categories.",
    ])

    return "\n".join(prompt_parts)


def get_ghost_team_analysis_prompt(
    company_profile: Dict[str, Any],
    opportunity: Dict[str, Any],
    competitor_intel: Dict[str, Any],
) -> str:
    """
    Generate a prompt for ghost team (competitor simulation) analysis.

    Args:
        company_profile: Company profile data
        opportunity: Opportunity details
        competitor_intel: Competitor intelligence data

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Ghost Team Analysis",
        "",
        "Simulate competitor bid strategies to anticipate their positioning and develop counter-strategies.",
        "",
        "---",
        "",
        "## Opportunity Context",
        "",
    ]

    if opportunity:
        prompt_parts.append(f"**Title**: {opportunity.get('title', 'N/A')}")
        prompt_parts.append(f"**Estimated Value**: ${opportunity.get('estimated_value', 0):,.0f}")
        prompt_parts.append(f"**Set-Aside**: {opportunity.get('set_aside', 'N/A')}")
        prompt_parts.append(f"**Evaluation Type**: {opportunity.get('evaluation_type', 'N/A')}")
        prompt_parts.append("")

        eval_factors = opportunity.get('evaluation_factors', [])
        if eval_factors:
            prompt_parts.append("**Evaluation Factors**:")
            for factor in eval_factors:
                if isinstance(factor, dict):
                    weight = f" ({factor.get('weight')}%)" if factor.get('weight') else ""
                    prompt_parts.append(f"  - {factor.get('name', factor)}{weight}")
                else:
                    prompt_parts.append(f"  - {factor}")
            prompt_parts.append("")

    # Competitor details
    prompt_parts.extend([
        "---",
        "",
        "## Competitors to Simulate",
        "",
    ])

    competitors = competitor_intel.get('competitors', [])
    for i, comp in enumerate(competitors[:3], 1):  # Focus on top 3
        is_incumbent = " (INCUMBENT)" if comp.get('is_incumbent') else ""
        prompt_parts.append(f"### Competitor {i}: {comp.get('name', 'Unknown')}{is_incumbent}")
        prompt_parts.append("")
        prompt_parts.append(f"**Estimated Strength**: {comp.get('estimated_strength', 'Unknown')}")
        prompt_parts.append("")

        if comp.get('known_strengths'):
            prompt_parts.append("**Known Strengths**:")
            for s in comp.get('known_strengths', []):
                prompt_parts.append(f"  - {s}")
            prompt_parts.append("")

        if comp.get('known_weaknesses'):
            prompt_parts.append("**Known Weaknesses**:")
            for w in comp.get('known_weaknesses', []):
                prompt_parts.append(f"  - {w}")
            prompt_parts.append("")

        if comp.get('relevant_past_performance'):
            prompt_parts.append("**Relevant Past Performance**:")
            for pp in comp.get('relevant_past_performance', []):
                prompt_parts.append(f"  - {pp}")
            prompt_parts.append("")

        if comp.get('certifications'):
            prompt_parts.append(f"**Certifications**: {', '.join(comp.get('certifications', []))}")
            prompt_parts.append("")

        if comp.get('teaming_partners'):
            prompt_parts.append(f"**Known Teaming Partners**: {', '.join(comp.get('teaming_partners', []))}")
            prompt_parts.append("")

        if comp.get('likely_strategy'):
            prompt_parts.append(f"**Intel on Likely Strategy**: {comp.get('likely_strategy')}")
            prompt_parts.append("")

    # Our company summary for comparison
    prompt_parts.extend([
        "---",
        "",
        "## Our Company Summary",
        "",
    ])

    if company_profile:
        prompt_parts.append(f"**Company**: {company_profile.get('name', 'N/A')}")

        caps = company_profile.get('core_capabilities', [])
        if caps:
            cap_names = [c.get('name') for c in caps if c.get('name')]
            prompt_parts.append(f"**Key Capabilities**: {', '.join(cap_names)}")

        certs = company_profile.get('certifications', [])
        if certs:
            cert_types = extract_certification_types(certs)
            prompt_parts.append(f"**Certifications**: {', '.join(cert_types)}")

        prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Analysis",
        "",
        "For each competitor, simulate their likely bid strategy:",
        "",
        "### [Competitor Name] - Ghost Team Analysis",
        "",
        "#### Predicted Win Themes",
        "What 3-5 win themes will this competitor likely emphasize?",
        "",
        "#### Predicted Technical Approach",
        "How will they likely propose to meet the requirements?",
        "",
        "#### Predicted Pricing Strategy",
        "Will they be aggressive, moderate, or premium? Why?",
        "",
        "#### Predicted Teaming Strategy",
        "Who might they team with and why?",
        "",
        "#### Key Strengths to Counter",
        "What are their strongest arguments that we must address?",
        "",
        "#### Vulnerabilities to Exploit",
        "What weaknesses can we highlight (without disparaging)?",
        "",
        "#### Our Counter-Strategy",
        "Specific strategies to position against this competitor",
        "",
        "---",
        "",
        "## Summary Outputs",
        "",
        "After individual competitor analysis, provide:",
        "",
        "1. **Competitive Positioning Matrix**: How we compare on each evaluation factor",
        "2. **Universal Counter-Themes**: Themes that work against all competitors",
        "3. **Competitive Risk Assessment**: Overall probability assessment",
        "4. **Recommended Emphasis**: What to emphasize most in our proposal",
    ])

    return "\n".join(prompt_parts)


def get_price_to_win_prompt(
    company_profile: Dict[str, Any],
    opportunity: Dict[str, Any],
    competitor_intel: Dict[str, Any],
    cost_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for price-to-win analysis.

    Args:
        company_profile: Company profile data
        opportunity: Opportunity details
        competitor_intel: Competitor intelligence
        cost_data: Optional cost and pricing data

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Price-to-Win Analysis",
        "",
        "Provide directional price-to-win guidance based on competitive landscape and evaluation methodology.",
        "",
        "**DISCLAIMER**: This is strategic guidance only. Actual pricing must be developed with cost accounting,",
        "contracts, and pricing professionals in compliance with FAR requirements.",
        "",
        "---",
        "",
        "## Opportunity Parameters",
        "",
    ]

    if opportunity:
        prompt_parts.append(f"**Title**: {opportunity.get('title', 'N/A')}")
        prompt_parts.append(f"**Estimated Value**: ${opportunity.get('estimated_value', 0):,.0f}")
        prompt_parts.append(f"**Contract Type**: {opportunity.get('contract_type', 'N/A')}")
        prompt_parts.append(f"**Evaluation Type**: {opportunity.get('evaluation_type', 'N/A')}")
        prompt_parts.append(f"**Set-Aside**: {opportunity.get('set_aside', 'N/A')}")
        prompt_parts.append("")

        # Evaluation methodology is critical for PTW
        eval_type = opportunity.get('evaluation_type', '')
        if 'LPTA' in str(eval_type):
            prompt_parts.append("**CRITICAL**: LPTA evaluation - price is paramount")
        elif 'Best Value' in str(eval_type):
            prompt_parts.append("**NOTE**: Best Value tradeoff - technical excellence can offset higher price")
        prompt_parts.append("")

        eval_factors = opportunity.get('evaluation_factors', [])
        if eval_factors:
            prompt_parts.append("**Evaluation Factor Weights**:")
            for factor in eval_factors:
                if isinstance(factor, dict):
                    weight = f": {factor.get('weight')}%" if factor.get('weight') else ""
                    importance = f" ({factor.get('relative_importance')})" if factor.get('relative_importance') else ""
                    prompt_parts.append(f"  - {factor.get('name', factor)}{weight}{importance}")
                else:
                    prompt_parts.append(f"  - {factor}")
            prompt_parts.append("")

    # Competitor pricing intel
    prompt_parts.extend([
        "---",
        "",
        "## Competitive Pricing Intelligence",
        "",
    ])

    competitors = competitor_intel.get('competitors', [])
    for comp in competitors:
        prompt_parts.append(f"### {comp.get('name', 'Unknown')}")

        if comp.get('estimated_rates'):
            prompt_parts.append(f"**Estimated Rates**: {comp.get('estimated_rates')}")
        if comp.get('historical_pricing'):
            prompt_parts.append(f"**Historical Pricing Pattern**: {comp.get('historical_pricing')}")
        if comp.get('pricing_strategy'):
            prompt_parts.append(f"**Expected Pricing Strategy**: {comp.get('pricing_strategy')}")
        if comp.get('is_incumbent'):
            prompt_parts.append("**Incumbent Advantage**: May have lower transition costs")

        prompt_parts.append("")

    # Cost data if available
    if cost_data:
        prompt_parts.extend([
            "---",
            "",
            "## Our Cost Position",
            "",
        ])

        if cost_data.get('wrap_rates'):
            prompt_parts.append(f"**Wrap Rate Range**: {cost_data.get('wrap_rates')}")
        if cost_data.get('labor_rates'):
            prompt_parts.append("**Labor Rate Ranges**:")
            for category, rate in cost_data.get('labor_rates', {}).items():
                prompt_parts.append(f"  - {category}: {rate}")
        if cost_data.get('profit_margin_target'):
            prompt_parts.append(f"**Target Profit Margin**: {cost_data.get('profit_margin_target')}")
        if cost_data.get('minimum_acceptable_margin'):
            prompt_parts.append(f"**Minimum Acceptable Margin**: {cost_data.get('minimum_acceptable_margin')}")

        prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Analysis",
        "",
        "### 1. Market Price Range Assessment",
        "- Estimated low, mid, and high price points for competitive range",
        "- Factors driving price variance",
        "",
        "### 2. Evaluation Impact Analysis",
        "- How price is weighted in evaluation",
        "- Technical/price tradeoff tolerance",
        "- Threshold for price reasonableness",
        "",
        "### 3. Competitor Price Predictions",
        "- Predicted price positioning for each major competitor",
        "- Rationale for each prediction",
        "",
        "### 4. Price Positioning Recommendation",
        "- Recommended price positioning (aggressive/moderate/premium)",
        "- Rationale based on competitive analysis",
        "- Technical strength requirements to support positioning",
        "",
        "### 5. Price Sensitivity Analysis",
        "- Impact of being 5%, 10%, 15% above competitors",
        "- Impact of being 5%, 10%, 15% below competitors",
        "- Break-even points for technical advantage",
        "",
        "### 6. Risk Assessment",
        "- Risk of pricing too aggressively (sustainability, credibility)",
        "- Risk of pricing too high (elimination)",
        "- Protest risk considerations",
        "",
        "### 7. Strategic Recommendations",
        "- Specific pricing strategy recommendations",
        "- Investment trade-offs (if relevant)",
        "- Areas to optimize for cost competitiveness",
        "",
        "---",
        "",
        "**REMINDER**: All price-to-win guidance is directional only. Actual pricing must be developed",
        "through proper cost estimating processes with appropriate cost accounting support.",
    ])

    return "\n".join(prompt_parts)


def get_capture_strategy_summary_prompt(
    company_profile: Dict[str, Any],
    opportunity: Dict[str, Any],
    competitor_intel: Optional[Dict[str, Any]] = None,
    win_themes: Optional[List[str]] = None,
    discriminators: Optional[List[str]] = None,
) -> str:
    """
    Generate a prompt for creating a comprehensive capture strategy summary.

    Args:
        company_profile: Company profile data
        opportunity: Opportunity details
        competitor_intel: Optional competitor intelligence
        win_themes: Optional list of previously developed win themes
        discriminators: Optional list of identified discriminators

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Capture Strategy Summary",
        "",
        "Synthesize all capture intelligence into a comprehensive capture strategy document.",
        "",
        "---",
        "",
        "## Opportunity Overview",
        "",
    ]

    if opportunity:
        prompt_parts.append(f"**Title**: {opportunity.get('title', 'N/A')}")
        prompt_parts.append(f"**Agency**: {opportunity.get('agency', {}).get('name', opportunity.get('agency', 'N/A'))}")
        prompt_parts.append(f"**Estimated Value**: ${opportunity.get('estimated_value', 0):,.0f}")
        prompt_parts.append(f"**Set-Aside**: {opportunity.get('set_aside', 'N/A')}")
        prompt_parts.append(f"**Evaluation Type**: {opportunity.get('evaluation_type', 'N/A')}")
        prompt_parts.append(f"**Priority**: {opportunity.get('priority', 'N/A')}")
        prompt_parts.append("")

    # Include prior analysis if available
    if win_themes:
        prompt_parts.extend([
            "---",
            "",
            "## Developed Win Themes",
            "",
        ])
        for i, theme in enumerate(win_themes, 1):
            prompt_parts.append(f"{i}. {theme}")
        prompt_parts.append("")

    if discriminators:
        prompt_parts.extend([
            "---",
            "",
            "## Identified Discriminators",
            "",
        ])
        for i, disc in enumerate(discriminators, 1):
            prompt_parts.append(f"{i}. {disc}")
        prompt_parts.append("")

    if competitor_intel:
        prompt_parts.extend([
            "---",
            "",
            "## Competitive Summary",
            "",
        ])
        prompt_parts.append(f"**Competitive Density**: {competitor_intel.get('competitive_density', 'Unknown')}")
        prompt_parts.append(f"**Incumbent Advantage**: {competitor_intel.get('incumbent_advantage_level', 'Unknown')}")
        prompt_parts.append("")

        competitors = competitor_intel.get('competitors', [])
        for comp in competitors:
            is_incumbent = " (INCUMBENT)" if comp.get('is_incumbent') else ""
            prompt_parts.append(f"- **{comp.get('name', 'Unknown')}**{is_incumbent}: {comp.get('estimated_strength', 'Unknown')} strength")
        prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Capture Strategy Sections",
        "",
        "### 1. Executive Summary",
        "- 2-3 paragraph overview of capture strategy",
        "- Key win probability assessment",
        "- Critical success factors",
        "",
        "### 2. Win Themes Summary",
        "- Consolidated list of 3-5 win themes",
        "- How they align with evaluation criteria",
        "- Supporting evidence summary",
        "",
        "### 3. Competitive Assessment",
        "- Major competitors and their positioning",
        "- Our competitive advantages",
        "- Our vulnerabilities to address",
        "",
        "### 4. Discriminators",
        "- Top 5-7 discriminators",
        "- How each creates competitive separation",
        "- Proof points for each",
        "",
        "### 5. Pricing Strategy",
        "- Recommended pricing positioning",
        "- Price sensitivity considerations",
        "- Investment trade-offs",
        "",
        "### 6. Teaming Strategy",
        "- Recommended teaming structure",
        "- Key subcontractor roles",
        "- Teaming gaps to fill",
        "",
        "### 7. Risks and Mitigations",
        "- Top 5 capture risks",
        "- Mitigation strategies for each",
        "",
        "### 8. Action Items",
        "- Immediate actions (0-30 days)",
        "- Near-term actions (30-90 days)",
        "- Pre-proposal priorities",
        "",
        "---",
        "",
        "Format the output as a professional capture strategy document suitable for",
        "presentation to company leadership.",
    ])

    return "\n".join(prompt_parts)


def get_revision_prompt(
    original_content: str,
    section_name: str,
    critiques: List[Dict[str, Any]],
) -> str:
    """
    Generate a prompt for revising capture strategy content based on critiques.

    Args:
        original_content: The original content to revise
        section_name: Name of the section being revised
        critiques: List of critiques to address

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Task: Revise Capture Strategy - {section_name}",
        "",
        "Revise the following capture strategy content to address the critiques provided.",
        "",
        "---",
        "",
        "## Original Content",
        "",
        original_content,
        "",
        "---",
        "",
        "## Critiques to Address",
        "",
    ]

    for i, critique in enumerate(critiques, 1):
        prompt_parts.append(f"### Critique {i}")
        prompt_parts.append(f"**Type**: {critique.get('challenge_type', 'Unknown')}")
        prompt_parts.append(f"**Severity**: {critique.get('severity', 'Unknown')}")
        prompt_parts.append(f"**Issue**: {critique.get('argument', 'No argument provided')}")
        if critique.get('evidence'):
            prompt_parts.append(f"**Evidence**: {critique.get('evidence')}")
        prompt_parts.append(f"**Suggested Remedy**: {critique.get('suggested_remedy', 'None provided')}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Revision Instructions",
        "",
        "1. Address each critique substantively",
        "2. Strengthen evidence and proof points where challenged",
        "3. Clarify any ambiguous or unsupported claims",
        "4. Maintain strategic focus and customer orientation",
        "5. Ensure competitive positioning remains differentiated",
        "",
        f"Provide the complete revised {section_name} section.",
    ])

    return "\n".join(prompt_parts)
