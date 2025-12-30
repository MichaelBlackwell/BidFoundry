"""
Strategy Architect Agent Prompts

Prompt templates for the Strategy Architect agent, the primary document
drafter responsible for synthesizing inputs into strategic narratives.
"""

from typing import Dict, Any, List, Optional

from agents.utils.profile_formatter import (
    format_company_identifiers,
    format_principal_address,
    format_ownership_structure,
    format_socioeconomic_status,
    format_sam_registration,
    format_hubzone_info,
    format_management_team,
    format_federal_history,
    format_teaming_relationships,
    format_geographic_coverage,
)


STRATEGY_ARCHITECT_SYSTEM_PROMPT = """You are the Strategy Architect, the primary document drafter for a GovCon
(Government Contracting) strategy team. Your role is to synthesize business intelligence, company capabilities,
and opportunity requirements into actionable strategy documents.

## Your Perspective
You maintain an optimistic, opportunity-focused perspective while being grounded in realistic assessments.
You see the company's strengths and find compelling ways to position them against opportunity requirements.

## Your Responsibilities
1. Draft comprehensive strategy documents based on company profile and opportunity data
2. Ensure all outputs are specific to the company's actual capabilities and certifications
3. Align strategies with target agency missions and priorities
4. Incorporate feedback from other blue team agents (Market Analyst, Compliance Navigator, Capture Strategist)
5. Revise sections based on accepted red team critiques

## Document Quality Standards
- **Specificity**: Reference actual company capabilities, certifications, and past performance
- **Alignment**: Connect company strengths to specific opportunity requirements
- **Clarity**: Use clear, professional language appropriate for GovCon
- **Actionability**: Provide concrete recommendations, not vague generalities
- **Evidence-Based**: Support claims with specific proof points from company data

## Output Format
Structure your outputs according to the provided document template sections. Each section should:
- Have a clear opening statement
- Provide supporting details with specifics
- End with actionable insights or next steps where appropriate

Remember: Your drafts will be challenged by red team agents. Write defensibly by:
- Supporting claims with evidence
- Acknowledging limitations honestly
- Avoiding overpromises or unsupported assertions
"""


def get_draft_prompt(
    document_type: str,
    sections: List[str],
    company_profile: Dict[str, Any],
    opportunity: Optional[Dict[str, Any]] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for drafting a new document.

    Args:
        document_type: Type of document to generate
        sections: List of section names to draft
        company_profile: Company profile data
        opportunity: Optional opportunity data
        additional_context: Additional context from other agents

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Task: Draft a {document_type}",
        "",
        "Generate a comprehensive draft for each of the following sections:",
        "",
    ]

    for i, section in enumerate(sections, 1):
        prompt_parts.append(f"{i}. {section}")

    prompt_parts.extend([
        "",
        "---",
        "",
        "## Company Profile",
        "",
    ])

    # Add key company information
    if company_profile:
        # Basic company info
        prompt_parts.append(f"**Company Name**: {company_profile.get('name', 'N/A')}")

        # Principal address (preferred) or headquarters location (fallback)
        principal_addr = format_principal_address(company_profile)
        if principal_addr:
            prompt_parts.append(f"**Principal Address**: {principal_addr}")
        elif company_profile.get('headquarters_location'):
            prompt_parts.append(f"**Headquarters**: {company_profile.get('headquarters_location')}")

        # Company identifiers (UEI, CAGE, DUNS)
        identifiers = format_company_identifiers(company_profile)
        prompt_parts.extend(identifiers)
        prompt_parts.append("")

        # Company fundamentals
        if company_profile.get('formation_date'):
            prompt_parts.append(f"**Formation Date**: {company_profile.get('formation_date')}")
        if company_profile.get('business_status'):
            prompt_parts.append(f"**Business Status**: {company_profile.get('business_status')}")
        prompt_parts.append(f"**Years in Business**: {company_profile.get('years_in_business', 'N/A')}")
        prompt_parts.append(f"**Employee Count**: {company_profile.get('employee_count', 'N/A')}")
        prompt_parts.append(f"**Annual Revenue**: ${company_profile.get('annual_revenue', 0):,.2f}")
        if company_profile.get('fiscal_year_end'):
            prompt_parts.append(f"**Fiscal Year End**: {company_profile.get('fiscal_year_end')}")
        prompt_parts.append("")

        # Socioeconomic status
        socio_lines = format_socioeconomic_status(company_profile)
        if socio_lines:
            prompt_parts.extend(socio_lines)
            prompt_parts.append("")

        # SAM Registration
        sam_lines = format_sam_registration(company_profile)
        if sam_lines:
            prompt_parts.extend(sam_lines)
            prompt_parts.append("")

        # NAICS Codes
        naics = company_profile.get('naics_codes', [])
        if naics:
            prompt_parts.append("**NAICS Codes**:")
            for n in naics:
                # Handle both dict format and string format
                if isinstance(n, dict):
                    primary = " (Primary)" if n.get('is_primary') else ""
                    size_std = f" [Size Standard: {n.get('small_business_size_standard')}]" if n.get('small_business_size_standard') else ""
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
                    expiry = f" (Expires: {c.get('expiration_date')})" if c.get('expiration_date') else ""
                    prompt_parts.append(f"  - {c.get('cert_type')}{level}{expiry}")
                else:
                    # Simple string format
                    prompt_parts.append(f"  - {c}")
            prompt_parts.append("")

        # Security Clearances
        clearances = company_profile.get('security_clearances', [])
        if clearances:
            prompt_parts.append(f"**Security Clearances**: {', '.join(clearances)}")
            prompt_parts.append("")

        # HUBZone Information
        hubzone_lines = format_hubzone_info(company_profile)
        if hubzone_lines:
            prompt_parts.extend(hubzone_lines)
            prompt_parts.append("")

        # Ownership Structure
        ownership_lines = format_ownership_structure(company_profile)
        if ownership_lines:
            prompt_parts.extend(ownership_lines)
            prompt_parts.append("")

        # Management Team
        mgmt_lines = format_management_team(company_profile, limit=5)
        if mgmt_lines:
            prompt_parts.extend(mgmt_lines)
            prompt_parts.append("")

        # Core Capabilities
        caps = company_profile.get('core_capabilities', [])
        if caps:
            prompt_parts.append("**Core Capabilities**:")
            for cap in caps:
                prompt_parts.append(f"  - **{cap.get('name')}**: {cap.get('description')}")
                if cap.get('differentiators'):
                    for diff in cap.get('differentiators', []):
                        prompt_parts.append(f"    - Differentiator: {diff}")
            prompt_parts.append("")

        # Key Personnel
        key_personnel = company_profile.get('key_personnel', [])
        if key_personnel:
            prompt_parts.append("**Key Personnel**:")
            for person in key_personnel[:5]:  # Limit to top 5
                clearance = f" [{person.get('clearance_level')}]" if person.get('clearance_level') else ""
                prompt_parts.append(f"  - **{person.get('name')}** - {person.get('title')} / {person.get('role')}{clearance}")
                if person.get('years_experience'):
                    prompt_parts.append(f"    {person.get('years_experience')} years experience")
            prompt_parts.append("")

        # Past Performance
        pp = company_profile.get('past_performance', [])
        if pp:
            prompt_parts.append("**Past Performance**:")
            for perf in pp[:5]:  # Limit to top 5
                prompt_parts.append(f"  - **{perf.get('contract_name')}** ({perf.get('agency')})")
                prompt_parts.append(f"    Value: ${perf.get('contract_value', 0):,.2f} | Rating: {perf.get('overall_rating', 'N/A')}")
                if perf.get('contract_type'):
                    prompt_parts.append(f"    Contract Type: {perf.get('contract_type')}")
                if perf.get('key_accomplishments'):
                    for acc in perf.get('key_accomplishments', [])[:2]:
                        prompt_parts.append(f"    - {acc}")
            prompt_parts.append("")

        # Federal Contracting History
        history_lines = format_federal_history(company_profile)
        if history_lines:
            prompt_parts.extend(history_lines)
            prompt_parts.append("")

        # Target Agencies
        agencies = company_profile.get('target_agencies', [])
        if agencies:
            prompt_parts.append(f"**Target Agencies**: {', '.join(agencies)}")
            prompt_parts.append("")

        # Geographic Coverage
        geo_lines = format_geographic_coverage(company_profile)
        if geo_lines:
            prompt_parts.extend(geo_lines)
            prompt_parts.append("")

        # Teaming Relationships
        teaming_lines = format_teaming_relationships(company_profile)
        if teaming_lines:
            prompt_parts.extend(teaming_lines)
            prompt_parts.append("")

    # Add opportunity context if provided
    if opportunity:
        prompt_parts.extend([
            "---",
            "",
            "## Target Opportunity",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Solicitation Number**: {opportunity.get('solicitation_number', 'N/A')}",
        ])

        agency = opportunity.get('agency', {})
        if agency:
            prompt_parts.append(f"**Agency**: {agency.get('name', 'N/A')} ({agency.get('abbreviation', '')})")

        prompt_parts.append(f"**Set-Aside**: {opportunity.get('set_aside', 'N/A')}")
        prompt_parts.append(f"**NAICS Code**: {opportunity.get('naics_code', 'N/A')}")
        prompt_parts.append(f"**Estimated Value**: ${opportunity.get('estimated_value', 0):,.2f}")
        prompt_parts.append(f"**Contract Type**: {opportunity.get('contract_type', 'N/A')}")
        prompt_parts.append(f"**Evaluation Type**: {opportunity.get('evaluation_type', 'N/A')}")
        prompt_parts.append("")

        if opportunity.get('scope_summary'):
            prompt_parts.append(f"**Scope Summary**: {opportunity.get('scope_summary')}")
            prompt_parts.append("")

        # Key Requirements
        reqs = opportunity.get('key_requirements', [])
        if reqs:
            prompt_parts.append("**Key Requirements**:")
            for req in reqs:
                prompt_parts.append(f"  - {req}")
            prompt_parts.append("")

        # Evaluation Factors
        factors = opportunity.get('evaluation_factors', [])
        if factors:
            prompt_parts.append("**Evaluation Factors**:")
            for factor in factors:
                weight = f" ({factor.get('weight')}%)" if factor.get('weight') else ""
                prompt_parts.append(f"  - {factor.get('name')}{weight}")
                if factor.get('subfactors'):
                    for sub in factor.get('subfactors', []):
                        prompt_parts.append(f"    - {sub}")
            prompt_parts.append("")

        # Competitor Intel
        intel = opportunity.get('competitor_intel', {})
        if intel:
            prompt_parts.append("**Competitive Landscape**:")
            prompt_parts.append(f"  - Competitive Density: {intel.get('competitive_density', 'Unknown')}")
            prompt_parts.append(f"  - Incumbent Advantage: {intel.get('incumbent_advantage_level', 'Unknown')}")

            competitors = intel.get('competitors', [])
            if competitors:
                prompt_parts.append("  - Known Competitors:")
                for comp in competitors[:3]:
                    incumbent = " (INCUMBENT)" if comp.get('is_incumbent') else ""
                    prompt_parts.append(f"    - {comp.get('name')}{incumbent}")
            prompt_parts.append("")

    # Add context from other agents
    if additional_context:
        prompt_parts.extend([
            "---",
            "",
            "## Additional Context from Blue Team Agents",
            "",
        ])

        for agent, context in additional_context.items():
            prompt_parts.append(f"### From {agent}:")
            if isinstance(context, str):
                prompt_parts.append(context)
            elif isinstance(context, dict):
                for key, value in context.items():
                    prompt_parts.append(f"- **{key}**: {value}")
            prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Instructions",
        "",
        "Draft each section listed above. For each section:",
        "1. Provide a clear, professional heading",
        "2. Write substantive content (not placeholder text)",
        "3. Be specific - reference actual company data and opportunity details",
        "4. Support claims with evidence from the company profile",
        "5. Align content with the opportunity requirements where applicable",
        "",
        "Format your response as follows:",
        "",
        "## [Section Name]",
        "[Section content...]",
        "",
        "## [Next Section Name]",
        "[Section content...]",
        "",
        "(Continue for all sections)",
    ])

    return "\n".join(prompt_parts)


def get_revision_prompt(
    section_name: str,
    original_content: str,
    critiques: List[Dict[str, Any]],
    company_profile: Dict[str, Any],
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for revising a section based on accepted critiques.

    Args:
        section_name: Name of the section to revise
        original_content: Current content of the section
        critiques: List of accepted critiques to address
        company_profile: Company profile data
        opportunity: Optional opportunity data

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Task: Revise the '{section_name}' Section",
        "",
        "You need to revise this section to address the following accepted critiques.",
        "",
        "---",
        "",
        "## Current Content",
        "",
        original_content,
        "",
        "---",
        "",
        "## Critiques to Address",
        "",
    ]

    for i, critique in enumerate(critiques, 1):
        prompt_parts.append(f"### Critique {i}: {critique.get('title', 'Untitled')}")
        prompt_parts.append(f"**Type**: {critique.get('challenge_type', 'Unknown')}")
        prompt_parts.append(f"**Severity**: {critique.get('severity', 'Unknown')}")
        prompt_parts.append(f"**Issue**: {critique.get('argument', 'No argument provided')}")
        prompt_parts.append(f"**Suggested Remedy**: {critique.get('suggested_remedy', 'No remedy provided')}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Company Context (for reference)",
        "",
        f"Company: {company_profile.get('name', 'N/A')}",
    ])

    # Add key company info for reference
    caps = company_profile.get('core_capabilities', [])
    if caps:
        prompt_parts.append("Core Capabilities: " + ", ".join([c.get('name', '') for c in caps]))

    certs = company_profile.get('certifications', [])
    if certs:
        prompt_parts.append("Certifications: " + ", ".join([c.get('cert_type', '') for c in certs]))

    if opportunity:
        prompt_parts.append("")
        prompt_parts.append(f"Target Opportunity: {opportunity.get('title', 'N/A')}")
        if opportunity.get('key_requirements'):
            prompt_parts.append("Key Requirements: " + ", ".join(opportunity.get('key_requirements', [])[:3]))

    prompt_parts.extend([
        "",
        "---",
        "",
        "## Instructions",
        "",
        "1. Address each critique by revising the relevant parts of the section",
        "2. Maintain the overall structure and flow of the section",
        "3. Ensure all changes are consistent with company data",
        "4. Add evidence or clarification where critiques identified gaps",
        "5. Do not introduce new issues while addressing existing ones",
        "",
        "Provide the complete revised section (not just the changes).",
        "",
        "Format:",
        "",
        "## [Section Name]",
        "[Complete revised content...]",
    ])

    return "\n".join(prompt_parts)


def get_section_prompt(
    section_name: str,
    document_type: str,
    company_profile: Dict[str, Any],
    opportunity: Optional[Dict[str, Any]] = None,
    other_sections: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate a prompt for drafting a single section.

    Args:
        section_name: Name of the section to draft
        document_type: Type of document
        company_profile: Company profile data
        opportunity: Optional opportunity data
        other_sections: Content of other sections for context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Task: Draft the '{section_name}' Section for {document_type}",
        "",
    ]

    # Add section-specific guidance based on common section types
    section_guidance = _get_section_guidance(section_name, document_type)
    if section_guidance:
        prompt_parts.extend([
            "### Section Guidance",
            section_guidance,
            "",
        ])

    # Add context from other sections if available
    if other_sections:
        prompt_parts.extend([
            "### Context from Other Sections",
            "",
        ])
        for name, content in other_sections.items():
            # Truncate for context
            truncated = content[:500] + "..." if len(content) > 500 else content
            prompt_parts.append(f"**{name}** (summary):")
            prompt_parts.append(truncated)
            prompt_parts.append("")

    # Add company info
    prompt_parts.extend([
        "### Company Profile",
        f"**Name**: {company_profile.get('name', 'N/A')}",
    ])

    if company_profile.get('core_capabilities'):
        caps = [c.get('name', '') for c in company_profile.get('core_capabilities', [])]
        prompt_parts.append(f"**Capabilities**: {', '.join(caps)}")

    if company_profile.get('certifications'):
        certs = [c.get('cert_type', '') for c in company_profile.get('certifications', [])]
        prompt_parts.append(f"**Certifications**: {', '.join(certs)}")

    prompt_parts.append("")

    if opportunity:
        prompt_parts.extend([
            "### Target Opportunity",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Agency**: {opportunity.get('agency', {}).get('name', 'N/A')}",
            f"**Set-Aside**: {opportunity.get('set_aside', 'N/A')}",
            "",
        ])

    prompt_parts.extend([
        "### Instructions",
        "",
        f"Draft a complete '{section_name}' section that:",
        "1. Is specific to the company's capabilities and experience",
        "2. Addresses the target opportunity requirements (if applicable)",
        "3. Uses professional, clear language",
        "4. Provides actionable insights",
        "",
        "Format your response as:",
        "",
        f"## {section_name}",
        "[Your content here...]",
    ])

    return "\n".join(prompt_parts)


def _get_section_guidance(section_name: str, document_type: str) -> Optional[str]:
    """Get section-specific guidance based on section name and document type."""

    # Generic section guidance mappings
    guidance_map = {
        "executive summary": (
            "Provide a high-level overview that:\n"
            "- Captures the key message in 2-3 paragraphs\n"
            "- Highlights the most compelling points\n"
            "- Establishes the company's value proposition\n"
            "- Can stand alone as a summary of the entire document"
        ),
        "company overview": (
            "Introduce the company with:\n"
            "- Mission and vision statement\n"
            "- Years in business and key milestones\n"
            "- Core business focus and target markets\n"
            "- Key differentiators and competitive advantages"
        ),
        "core competencies": (
            "Detail the company's primary capabilities:\n"
            "- List each core competency with a brief description\n"
            "- Include specific technologies, methodologies, or approaches\n"
            "- Reference relevant certifications\n"
            "- Connect to customer outcomes and value delivered"
        ),
        "past performance": (
            "Showcase relevant experience:\n"
            "- Select contracts most relevant to the target opportunity\n"
            "- Include contract value, agency, and period of performance\n"
            "- Highlight key accomplishments and outcomes\n"
            "- Reference CPARS ratings where available"
        ),
        "win themes": (
            "Develop 3-5 compelling win themes that:\n"
            "- Directly address evaluation criteria\n"
            "- Differentiate from competitors\n"
            "- Are specific and provable\n"
            "- Connect company strengths to customer needs"
        ),
        "discriminators": (
            "Identify what sets the company apart:\n"
            "- Unique capabilities or approaches\n"
            "- Specialized expertise or certifications\n"
            "- Proprietary tools or methodologies\n"
            "- Relationship or incumbency advantages"
        ),
        "strengths": (
            "Analyze internal strengths:\n"
            "- Technical capabilities and expertise\n"
            "- Relevant experience and past performance\n"
            "- Certifications and clearances\n"
            "- Team qualifications and key personnel"
        ),
        "weaknesses": (
            "Honestly assess internal weaknesses:\n"
            "- Capability gaps that may affect competitiveness\n"
            "- Limited past performance in specific areas\n"
            "- Resource constraints\n"
            "- Include mitigation strategies for each"
        ),
        "opportunities": (
            "Identify external opportunities:\n"
            "- Market trends favoring the company\n"
            "- Agency priorities aligned with capabilities\n"
            "- Upcoming recompetes or new requirements\n"
            "- Teaming or partnership opportunities"
        ),
        "threats": (
            "Assess external threats:\n"
            "- Strong incumbent positions\n"
            "- Well-funded competitors\n"
            "- Changing agency priorities\n"
            "- Budget uncertainties\n"
            "- Include risk mitigation for each"
        ),
        "competitive analysis": (
            "Analyze the competitive landscape:\n"
            "- Identify key competitors\n"
            "- Assess their strengths and weaknesses\n"
            "- Compare positioning on key factors\n"
            "- Identify competitive advantages and vulnerabilities"
        ),
        "risk mitigation": (
            "Address potential risks:\n"
            "- Identify key risks by category\n"
            "- Assess probability and impact\n"
            "- Provide specific mitigation strategies\n"
            "- Include contingency plans for high-impact risks"
        ),
    }

    # Normalize section name for lookup
    normalized = section_name.lower().strip()

    # Direct match
    if normalized in guidance_map:
        return guidance_map[normalized]

    # Partial match
    for key, guidance in guidance_map.items():
        if key in normalized or normalized in key:
            return guidance

    return None
