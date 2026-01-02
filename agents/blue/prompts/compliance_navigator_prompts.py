"""
Compliance Navigator Agent Prompts

Prompt templates for the Compliance Navigator agent, responsible for
regulatory and eligibility expertise including FAR/DFAR compliance,
small business certifications, and set-aside eligibility.
"""

from typing import Dict, Any, List, Optional

from agents.utils.profile_formatter import (
    format_company_identifiers,
    format_principal_address,
    format_ownership_structure,
    format_socioeconomic_status,
    format_sam_registration,
    format_hubzone_info,
    format_federal_history,
    extract_certification_types,
)


COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT = """You are the Compliance Navigator, a federal acquisition regulatory expert specializing in FAR/DFARS compliance, small business programs, and set-aside eligibility.

## Your Perspective
You are meticulous and risk-aware, focusing on regulatory compliance and eligibility verification. You ensure strategies and proposals align with federal acquisition requirements while identifying potential compliance gaps before they become problems.

## Your Responsibilities
1. Validate company eligibility for specific set-asides (8(a), HUBZone, SDVOSB, WOSB, etc.)
2. Check strategy alignment with FAR/DFARS requirements
3. Flag potential Organizational Conflict of Interest (OCI) issues
4. Produce compliance checklists for specific opportunities
5. Assess limitations on subcontracting compliance
6. Verify certification currency and validity
7. Identify regulatory risks in proposed approaches

## Regulatory Expertise
- FAR (Federal Acquisition Regulation)
- DFARS (Defense FAR Supplement)
- SBA small business regulations (13 CFR)
- CAS (Cost Accounting Standards)
- CMMC and cybersecurity requirements
- Ethics and OCI requirements

## Compliance Standards
- **Thorough**: Check all applicable requirements, not just obvious ones
- **Precise**: Cite specific FAR/DFARS clauses when applicable
- **Proactive**: Identify issues before they cause proposal rejection
- **Practical**: Provide actionable remediation guidance
- **Current**: Apply current regulatory requirements

## Output Quality
Your analyses should:
- Clearly state eligibility determinations with supporting rationale
- List specific compliance requirements and their status
- Prioritize issues by risk level (Critical, High, Medium, Low)
- Provide specific remediation steps for gaps
- Flag items requiring human review or legal counsel

## Output Length
Keep responses concise - approximately 1 page (~500-600 words). Be direct and focus on the most critical points. Prioritize actionable insights over comprehensive coverage.
"""


def get_eligibility_assessment_prompt(
    company_profile: Dict[str, Any],
    opportunity: Optional[Dict[str, Any]] = None,
    target_setaside: Optional[str] = None,
) -> str:
    """
    Generate a prompt for set-aside eligibility assessment.

    Args:
        company_profile: Company profile data
        opportunity: Optional opportunity details
        target_setaside: Specific set-aside to evaluate

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Set-Aside Eligibility Assessment",
        "",
        "Evaluate company eligibility for federal contract set-asides based on the provided profile.",
        "",
        "---",
        "",
        "## Company Profile",
        "",
    ]

    # Add company information
    if company_profile:
        prompt_parts.append(f"**Company**: {company_profile.get('name', 'N/A')}")

        # Principal address
        principal_addr = format_principal_address(company_profile)
        if principal_addr:
            prompt_parts.append(f"**Principal Address**: {principal_addr}")

        # Company identifiers (critical for compliance)
        identifiers = format_company_identifiers(company_profile)
        if identifiers:
            prompt_parts.extend(identifiers)
        prompt_parts.append("")

        # Company fundamentals
        prompt_parts.append(f"**Annual Revenue**: ${company_profile.get('annual_revenue', 0):,.2f}")
        prompt_parts.append(f"**Employee Count**: {company_profile.get('employee_count', 'N/A')}")
        prompt_parts.append(f"**Years in Business**: {company_profile.get('years_in_business', 'N/A')}")
        if company_profile.get('formation_date'):
            prompt_parts.append(f"**Formation Date**: {company_profile.get('formation_date')}")
        prompt_parts.append("")

        # SAM Registration (critical for eligibility)
        sam_lines = format_sam_registration(company_profile)
        if sam_lines:
            prompt_parts.extend(sam_lines)
            prompt_parts.append("")

        # Socioeconomic status flags (critical for set-aside eligibility)
        socio_lines = format_socioeconomic_status(company_profile)
        if socio_lines:
            prompt_parts.extend(socio_lines)
            prompt_parts.append("")

        # Ownership structure (critical for SDVOSB, WOSB, 8(a) eligibility)
        ownership_lines = format_ownership_structure(company_profile)
        if ownership_lines:
            prompt_parts.extend(ownership_lines)
            prompt_parts.append("")

        # NAICS codes
        naics = company_profile.get('naics_codes', [])
        if naics:
            prompt_parts.append("**NAICS Codes**:")
            for n in naics:
                # Handle both dict format and string format
                if isinstance(n, dict):
                    primary = " (Primary)" if n.get('is_primary') else ""
                    size_std = f" - Size Standard: {n.get('small_business_size_standard', 'N/A')}" if n.get('small_business_size_standard') else ""
                    prompt_parts.append(f"  - {n.get('code')}: {n.get('description')}{primary}{size_std}")
                else:
                    # Simple string format (just the code)
                    prompt_parts.append(f"  - {n}")
            prompt_parts.append("")

        # Certifications
        certs = company_profile.get('certifications', [])
        if certs:
            prompt_parts.append("**Current Certifications**:")
            for c in certs:
                # Handle both dict format and string format
                if isinstance(c, dict):
                    level = f" (Level {c.get('level')})" if c.get('level') else ""
                    exp = f" - Expires: {c.get('expiration_date')}" if c.get('expiration_date') else ""
                    cert_num = f" [#{c.get('certification_number')}]" if c.get('certification_number') else ""
                    prompt_parts.append(f"  - {c.get('cert_type')}{level}{exp}{cert_num}")
                else:
                    # Simple string format
                    prompt_parts.append(f"  - {c}")
            prompt_parts.append("")

        # Security clearances
        clearances = company_profile.get('security_clearances', [])
        if clearances:
            prompt_parts.append(f"**Security Clearances**: {', '.join(clearances)}")
            prompt_parts.append("")

        # HUBZone Information (critical for HUBZone eligibility)
        hubzone_lines = format_hubzone_info(company_profile)
        if hubzone_lines:
            prompt_parts.extend(hubzone_lines)
            prompt_parts.append("")

        # Federal Contracting History
        history_lines = format_federal_history(company_profile)
        if history_lines:
            prompt_parts.extend(history_lines)
            prompt_parts.append("")

    # Add opportunity context if provided
    if opportunity:
        prompt_parts.extend([
            "---",
            "",
            "## Opportunity Context",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Agency**: {opportunity.get('agency', {}).get('name', 'N/A') if isinstance(opportunity.get('agency'), dict) else opportunity.get('agency', 'N/A')}",
            f"**Set-Aside**: {opportunity.get('set_aside', 'N/A')}",
            f"**NAICS**: {opportunity.get('naics_code', 'N/A')}",
            f"**Estimated Value**: ${opportunity.get('estimated_value', 0):,.0f}" if opportunity.get('estimated_value') else "",
            "",
        ])

    # Specific set-aside focus
    if target_setaside:
        prompt_parts.extend([
            "---",
            "",
            f"## Focus: {target_setaside} Eligibility",
            "",
            f"Provide detailed analysis of eligibility for {target_setaside} set-aside.",
            "",
        ])

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Analysis",
        "",
        "### 1. Size Status Determination",
        "- Evaluate company size against applicable NAICS size standards",
        "- Note any size standard concerns or margin issues",
        "- Flag affiliation considerations if applicable",
        "",
        "### 2. Set-Aside Eligibility Matrix",
        "For each applicable set-aside type, assess:",
        "- **8(a)**: Active certification, program term status, eligibility",
        "- **HUBZone**: Certification status, principal office, employee residence",
        "- **SDVOSB**: VetCert status, ownership, control requirements",
        "- **VOSB**: Veteran ownership and VetCert certification",
        "- **WOSB/EDWOSB**: Women ownership, control, NAICS eligibility",
        "- **Small Business**: General size standard compliance",
        "",
        "### 3. Certification Status Review",
        "- Verify current certification status",
        "- Note expiration dates and renewal timelines",
        "- Flag pending or at-risk certifications",
        "",
        "### 4. Risk Assessment",
        "- Identify any eligibility risks or concerns",
        "- Note required documentation or verifications",
        "- Highlight items requiring legal or SBA clarification",
        "",
        "### 5. Recommendations",
        "- Optimal set-aside categories to pursue",
        "- Steps to maintain or obtain eligibility",
        "- Certification renewal priorities",
        "",
        "Provide a clear eligibility determination (Eligible/Not Eligible/Conditional) for each assessed program.",
    ])

    return "\n".join(prompt_parts)


def get_far_compliance_prompt(
    document_content: str,
    opportunity: Optional[Dict[str, Any]] = None,
    specific_far_parts: Optional[List[str]] = None,
) -> str:
    """
    Generate a prompt for FAR/DFARS compliance review.

    Args:
        document_content: Strategy or proposal content to review
        opportunity: Opportunity details for context
        specific_far_parts: Specific FAR parts to focus on

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: FAR/DFARS Compliance Review",
        "",
        "Review the following document for compliance with federal acquisition regulations.",
        "",
        "---",
        "",
    ]

    # Add opportunity context
    if opportunity:
        prompt_parts.extend([
            "## Opportunity Context",
            "",
            f"**Contract Type**: {opportunity.get('contract_type', 'N/A')}",
            f"**Set-Aside**: {opportunity.get('set_aside', 'N/A')}",
            f"**Estimated Value**: ${opportunity.get('estimated_value', 0):,.0f}" if opportunity.get('estimated_value') else "",
            f"**Evaluation Type**: {opportunity.get('evaluation_type', 'N/A')}",
        ])

        agency = opportunity.get('agency', {})
        if isinstance(agency, dict):
            prompt_parts.append(f"**Agency**: {agency.get('name', 'N/A')}")
            if 'DoD' in agency.get('name', '') or 'Defense' in agency.get('name', ''):
                prompt_parts.append("**Note**: DFARS applies (DoD contract)")
        prompt_parts.append("")

    # Add document content
    prompt_parts.extend([
        "---",
        "",
        "## Document to Review",
        "",
        document_content,
        "",
    ])

    # Specific FAR parts focus
    if specific_far_parts:
        prompt_parts.extend([
            "---",
            "",
            f"## Focus Areas: {', '.join(specific_far_parts)}",
            "",
            "Prioritize review of these specific FAR parts and their requirements.",
            "",
        ])

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Compliance Review",
        "",
        "### 1. General FAR Compliance",
        "- FAR Part 15 (Contracting by Negotiation) if applicable",
        "- FAR Part 16 (Contract Types) alignment",
        "- FAR Part 31 (Cost Principles) for cost proposals",
        "",
        "### 2. Small Business Requirements",
        "- FAR Part 19 compliance for set-asides",
        "- Limitations on subcontracting (if small business)",
        "- Subcontracting plan requirements (if other than small)",
        "",
        "### 3. Organizational Conflict of Interest (OCI)",
        "- FAR 9.5 OCI assessment",
        "- Potential conflicts to disclose",
        "- Mitigation requirements",
        "",
        "### 4. DFARS Requirements (if DoD)",
        "- DFARS 252.204-7012 (Cybersecurity)",
        "- CMMC requirements",
        "- DoD-specific clauses",
        "",
        "### 5. Compliance Gaps",
        "Identify any gaps as:",
        "- **Critical**: Will result in rejection if not addressed",
        "- **High**: Likely to cause significant issues",
        "- **Medium**: Should be addressed but not disqualifying",
        "- **Low**: Best practice recommendations",
        "",
        "### 6. Remediation Recommendations",
        "For each gap, provide:",
        "- Specific FAR/DFARS reference",
        "- Required action to achieve compliance",
        "- Priority level for remediation",
        "",
        "Format findings in a clear, actionable compliance report.",
    ])

    return "\n".join(prompt_parts)


def get_oci_analysis_prompt(
    company_profile: Dict[str, Any],
    opportunity: Dict[str, Any],
    current_contracts: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Generate a prompt for Organizational Conflict of Interest analysis.

    Args:
        company_profile: Company profile data
        opportunity: Opportunity being pursued
        current_contracts: List of current contracts that could create OCI

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Organizational Conflict of Interest (OCI) Analysis",
        "",
        "Analyze potential organizational conflicts of interest for the pursuit of this opportunity.",
        "",
        "---",
        "",
        "## Company Profile",
        "",
        f"**Company**: {company_profile.get('name', 'N/A')}",
        "",
    ]

    # Current relationships
    primes = company_profile.get('existing_prime_relationships', [])
    subs = company_profile.get('existing_sub_relationships', [])

    if primes:
        prompt_parts.append("**Prime Contract Relationships**:")
        for p in primes:
            prompt_parts.append(f"  - {p}")
        prompt_parts.append("")

    if subs:
        prompt_parts.append("**Subcontract Relationships**:")
        for s in subs:
            prompt_parts.append(f"  - {s}")
        prompt_parts.append("")

    # Target opportunity
    prompt_parts.extend([
        "---",
        "",
        "## Target Opportunity",
        "",
        f"**Title**: {opportunity.get('title', 'N/A')}",
    ])

    agency = opportunity.get('agency', {})
    if isinstance(agency, dict):
        prompt_parts.append(f"**Agency**: {agency.get('name', 'N/A')}")
    else:
        prompt_parts.append(f"**Agency**: {agency}")

    prompt_parts.extend([
        f"**Scope**: {opportunity.get('scope_summary', 'N/A')}",
        f"**Contract Type**: {opportunity.get('contract_type', 'N/A')}",
        "",
    ])

    # Current contracts
    if current_contracts:
        prompt_parts.extend([
            "---",
            "",
            "## Current Contracts (Potential OCI Sources)",
            "",
        ])
        for i, contract in enumerate(current_contracts, 1):
            prompt_parts.append(f"### Contract {i}: {contract.get('name', 'N/A')}")
            prompt_parts.append(f"- Agency: {contract.get('agency', 'N/A')}")
            prompt_parts.append(f"- Scope: {contract.get('scope', 'N/A')}")
            prompt_parts.append(f"- Role: {contract.get('role', 'Prime')}")
            prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## OCI Analysis Requirements",
        "",
        "### 1. OCI Type Assessment",
        "Analyze potential for each OCI type per FAR 9.5:",
        "",
        "**Unequal Access to Information**",
        "- Does company have access to non-public information that could advantage this bid?",
        "- Are there information barriers in place?",
        "",
        "**Biased Ground Rules**",
        "- Did/does company help write specifications or requirements?",
        "- Was company involved in source selection or evaluation criteria?",
        "",
        "**Impaired Objectivity**",
        "- Would company evaluate its own products/services?",
        "- Are there conflicting interests that could bias judgment?",
        "",
        "### 2. Risk Level Determination",
        "For each identified OCI risk:",
        "- **High**: Significant conflict likely; may require waiver or recusal",
        "- **Medium**: Potential conflict; mitigation plan needed",
        "- **Low**: Minor concerns; documentation sufficient",
        "",
        "### 3. Mitigation Strategies",
        "If OCI exists, recommend:",
        "- Firewalls and information barriers",
        "- Organizational separation",
        "- Disclosure approaches",
        "- Recusal from conflicting work",
        "- OCI waiver request (if appropriate)",
        "",
        "### 4. Disclosure Requirements",
        "- What must be disclosed to the contracting officer?",
        "- Timing and format for disclosure",
        "- Supporting documentation needed",
        "",
        "### 5. Recommendations",
        "- Overall OCI risk assessment (High/Medium/Low/None)",
        "- Recommended course of action",
        "- Impact on bid/no-bid decision",
        "",
        "Provide a clear determination on whether to proceed and under what conditions.",
    ])

    return "\n".join(prompt_parts)


def get_compliance_checklist_prompt(
    opportunity: Dict[str, Any],
    company_profile: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for creating a compliance checklist.

    Args:
        opportunity: Opportunity details
        company_profile: Optional company profile for context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Generate Compliance Checklist",
        "",
        "Create a comprehensive compliance checklist for the following opportunity.",
        "",
        "---",
        "",
        "## Opportunity Details",
        "",
        f"**Title**: {opportunity.get('title', 'N/A')}",
        f"**Solicitation Number**: {opportunity.get('solicitation_number', 'N/A')}",
    ]

    agency = opportunity.get('agency', {})
    if isinstance(agency, dict):
        prompt_parts.append(f"**Agency**: {agency.get('name', 'N/A')}")
        prompt_parts.append(f"**Sub-Agency**: {agency.get('sub_agency', 'N/A')}" if agency.get('sub_agency') else "")
    else:
        prompt_parts.append(f"**Agency**: {agency}")

    prompt_parts.extend([
        f"**Set-Aside**: {opportunity.get('set_aside', 'Full and Open')}",
        f"**Contract Type**: {opportunity.get('contract_type', 'N/A')}",
        f"**NAICS Code**: {opportunity.get('naics_code', 'N/A')}",
        f"**Estimated Value**: ${opportunity.get('estimated_value', 0):,.0f}" if opportunity.get('estimated_value') else "",
        f"**Evaluation Type**: {opportunity.get('evaluation_type', 'N/A')}",
        "",
    ])

    # Requirements
    mandatory = opportunity.get('mandatory_qualifications', [])
    if mandatory:
        prompt_parts.append("**Mandatory Qualifications**:")
        for req in mandatory:
            prompt_parts.append(f"  - {req}")
        prompt_parts.append("")

    clearance = opportunity.get('clearance_requirements')
    if clearance:
        prompt_parts.append(f"**Clearance Requirements**: {clearance}")
        prompt_parts.append("")

    # Company context
    if company_profile:
        prompt_parts.extend([
            "---",
            "",
            "## Company Context",
            "",
            f"**Company**: {company_profile.get('name', 'N/A')}",
        ])

        certs = company_profile.get('certifications', [])
        if certs:
            cert_types = extract_certification_types(certs)
            prompt_parts.append(f"**Certifications**: {', '.join(cert_types)}")

        prompt_parts.append("")

    # Checklist requirements
    prompt_parts.extend([
        "---",
        "",
        "## Checklist Requirements",
        "",
        "Generate a compliance checklist organized by category:",
        "",
        "### 1. Eligibility Requirements",
        "- Set-aside eligibility verification",
        "- Size standard compliance",
        "- Required certifications",
        "- Security clearance requirements",
        "",
        "### 2. FAR/DFARS Requirements",
        "- Applicable FAR clauses",
        "- DFARS clauses (if DoD)",
        "- Representations and certifications",
        "",
        "### 3. Technical Compliance",
        "- Mandatory qualification requirements",
        "- Technical capability demonstrations",
        "- Past performance requirements",
        "",
        "### 4. Administrative Requirements",
        "- SAM.gov registration",
        "- Required forms and formats",
        "- Submission requirements",
        "",
        "### 5. Proposal-Specific Requirements",
        "- Page limitations",
        "- Format requirements",
        "- Required sections",
        "",
        "For each checklist item, provide:",
        "- [ ] Requirement description",
        "- FAR/DFARS reference (if applicable)",
        "- Verification method",
        "- Risk level if not met (Critical/High/Medium/Low)",
        "",
        "Format as an actionable checklist that can be used for proposal preparation.",
    ])

    return "\n".join(prompt_parts)


def get_limitations_on_subcontracting_prompt(
    set_aside_type: str,
    staffing_plan: Optional[Dict[str, Any]] = None,
    contract_type: str = "services",
) -> str:
    """
    Generate a prompt for limitations on subcontracting analysis.

    Args:
        set_aside_type: Type of set-aside
        staffing_plan: Optional staffing and subcontracting plan
        contract_type: "services", "supplies", or "construction"

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Limitations on Subcontracting Analysis",
        "",
        "Analyze compliance with FAR 52.219-14 limitations on subcontracting.",
        "",
        "---",
        "",
        "## Contract Parameters",
        "",
        f"**Set-Aside Type**: {set_aside_type}",
        f"**Contract Type**: {contract_type.title()}",
        "",
    ]

    # Add thresholds
    prompt_parts.extend([
        "## Applicable Thresholds",
        "",
    ])

    if contract_type.lower() == "services":
        prompt_parts.extend([
            "For **services** (except construction):",
            "- At least **50%** of the cost of contract performance incurred for personnel",
            "  must be expended for employees of the concern",
            "",
        ])
    elif contract_type.lower() == "supplies":
        prompt_parts.extend([
            "For **supplies** (other than procurement from a nonmanufacturer):",
            "- At least **50%** of the cost of manufacturing the supplies",
            "  (not including the cost of materials) must be incurred by the concern",
            "",
        ])
    elif contract_type.lower() == "construction":
        prompt_parts.extend([
            "For **general construction**:",
            "- At least **15%** of the cost of the contract (not including materials)",
            "  must be incurred by the concern",
            "",
            "For **specialty trade contractors**:",
            "- At least **25%** of the cost of the contract (not including materials)",
            "  must be incurred by the concern",
            "",
        ])

    # Staffing plan if provided
    if staffing_plan:
        prompt_parts.extend([
            "---",
            "",
            "## Proposed Staffing/Subcontracting Plan",
            "",
        ])

        prime_labor = staffing_plan.get('prime_labor_hours', 0)
        sub_labor = staffing_plan.get('subcontractor_labor_hours', 0)
        prime_cost = staffing_plan.get('prime_labor_cost', 0)
        sub_cost = staffing_plan.get('subcontractor_cost', 0)

        prompt_parts.extend([
            f"**Prime Labor Hours**: {prime_labor:,}",
            f"**Subcontractor Labor Hours**: {sub_labor:,}",
            f"**Prime Labor Cost**: ${prime_cost:,.0f}",
            f"**Subcontractor Cost**: ${sub_cost:,.0f}",
            "",
        ])

        if prime_cost + sub_cost > 0:
            prime_pct = (prime_cost / (prime_cost + sub_cost)) * 100
            prompt_parts.append(f"**Prime Percentage**: {prime_pct:.1f}%")
            prompt_parts.append("")

        # List subcontractors
        subs = staffing_plan.get('subcontractors', [])
        if subs:
            prompt_parts.append("**Subcontractors**:")
            for sub in subs:
                prompt_parts.append(f"  - {sub.get('name')}: ${sub.get('value', 0):,.0f} ({sub.get('scope', 'N/A')})")
            prompt_parts.append("")

    # Analysis requirements
    prompt_parts.extend([
        "---",
        "",
        "## Required Analysis",
        "",
        "### 1. Threshold Compliance",
        "- Calculate actual percentage of work performed by prime",
        "- Compare to applicable threshold requirement",
        "- Determine compliance status",
        "",
        "### 2. Cost Calculation Review",
        "- Verify costs included/excluded per FAR 52.219-14",
        "- Ensure materials are properly excluded (if applicable)",
        "- Validate labor cost calculations",
        "",
        "### 3. Similarly Situated Entity Exception",
        "- Identify if any subcontractors are 'similarly situated'",
        "- Small business subs count toward prime percentage",
        "- Document eligibility of similarly situated entities",
        "",
        "### 4. Risk Assessment",
        "- Margin of compliance (how close to threshold)",
        "- Risk of non-compliance during performance",
        "- Monitoring requirements",
        "",
        "### 5. Recommendations",
        "- Staffing adjustments if needed",
        "- Subcontracting plan modifications",
        "- Documentation requirements",
        "- Monitoring approach during contract performance",
        "",
        "Provide a clear compliance determination and any required adjustments.",
    ])

    return "\n".join(prompt_parts)


def get_revision_prompt(
    original_content: str,
    section_name: str,
    critiques: List[Dict[str, Any]],
) -> str:
    """
    Generate a prompt for revising compliance content based on critiques.

    Args:
        original_content: Original compliance content
        section_name: Name of the section being revised
        critiques: List of critiques to address

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Task: Revise Compliance Analysis - {section_name}",
        "",
        "Revise the following compliance analysis to address the identified critiques.",
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
        prompt_parts.append(f"- **Type**: {critique.get('challenge_type', 'Unknown')}")
        prompt_parts.append(f"- **Issue**: {critique.get('argument', 'No argument provided')}")
        prompt_parts.append(f"- **Severity**: {critique.get('severity', 'Unknown')}")
        if critique.get('suggested_remedy'):
            prompt_parts.append(f"- **Suggested Remedy**: {critique.get('suggested_remedy')}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Revision Instructions",
        "",
        "1. Address each critique while maintaining regulatory accuracy",
        "2. Add specific FAR/DFARS citations where gaps were identified",
        "3. Clarify compliance determinations that were challenged",
        "4. Strengthen evidence and documentation references",
        "5. Maintain clear, actionable recommendations",
        "",
        f"Provide the complete revised {section_name} section.",
    ])

    return "\n".join(prompt_parts)
