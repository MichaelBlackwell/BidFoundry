"""
Profile Formatter Utility

Provides consistent formatting of company profile data for agent prompts.
These functions convert company profile dictionary data into formatted
strings suitable for inclusion in LLM prompts.
"""

from typing import Dict, Any, List, Optional


def format_company_identifiers(profile: Dict[str, Any]) -> List[str]:
    """
    Format company identifiers (UEI, CAGE, DUNS).

    Args:
        profile: Company profile dictionary

    Returns:
        List of formatted identifier strings
    """
    lines = []
    if profile.get('uei_number'):
        lines.append(f"**UEI Number**: {profile['uei_number']}")
    if profile.get('cage_code'):
        lines.append(f"**CAGE Code**: {profile['cage_code']}")
    if profile.get('duns_number'):
        lines.append(f"**DUNS Number**: {profile['duns_number']}")
    return lines


def format_principal_address(profile: Dict[str, Any]) -> Optional[str]:
    """
    Format principal address as a single formatted string.

    Args:
        profile: Company profile dictionary

    Returns:
        Formatted address string or None if no address data
    """
    addr = profile.get('principal_address')
    if not addr:
        return None

    parts = []
    if addr.get('street1'):
        parts.append(addr['street1'])
    if addr.get('street2'):
        parts.append(addr['street2'])

    city_state_zip = []
    if addr.get('city'):
        city_state_zip.append(addr['city'])
    if addr.get('state'):
        city_state_zip.append(addr['state'])
    if addr.get('zip_code'):
        city_state_zip.append(addr['zip_code'])

    if city_state_zip:
        parts.append(', '.join(city_state_zip[:1]) + ' ' + ' '.join(city_state_zip[1:]) if len(city_state_zip) > 1 else city_state_zip[0])

    if addr.get('country') and addr['country'] != 'USA':
        parts.append(addr['country'])

    return ', '.join(filter(None, parts)) if parts else None


def format_ownership_structure(profile: Dict[str, Any]) -> List[str]:
    """
    Format ownership structure with socioeconomic flags.

    Args:
        profile: Company profile dictionary

    Returns:
        List of formatted ownership strings
    """
    lines = []
    ownership = profile.get('ownership_structure', [])
    if not ownership:
        return lines

    lines.append("**Ownership Structure**:")

    total_veteran = 0.0
    total_sdv = 0.0
    total_woman = 0.0
    total_disadvantaged = 0.0

    for stake in ownership:
        pct = stake.get('percentage', 0)
        flags = []

        if stake.get('is_veteran'):
            flags.append("Veteran")
            total_veteran += pct
        if stake.get('is_service_disabled_veteran'):
            flags.append("Service-Disabled Veteran")
            total_sdv += pct
        if stake.get('is_woman'):
            flags.append("Woman")
            total_woman += pct
        if stake.get('is_disadvantaged'):
            flags.append("Disadvantaged")
            total_disadvantaged += pct

        flag_str = f" ({', '.join(flags)})" if flags else ""
        ownership_type = stake.get('ownership_type', '')
        title = f" - {stake.get('title')}" if stake.get('title') else ""
        lines.append(f"  - {stake.get('name', 'N/A')}: {pct}% {ownership_type}{title}{flag_str}")

    # Add summary percentages if any socioeconomic ownership exists
    if any([total_veteran, total_sdv, total_woman, total_disadvantaged]):
        lines.append("")
        lines.append("**Ownership by Category**:")
        if total_veteran > 0:
            lines.append(f"  - Veteran Ownership: {total_veteran}%")
        if total_sdv > 0:
            lines.append(f"  - Service-Disabled Veteran Ownership: {total_sdv}%")
        if total_woman > 0:
            lines.append(f"  - Woman Ownership: {total_woman}%")
        if total_disadvantaged > 0:
            lines.append(f"  - Disadvantaged Ownership: {total_disadvantaged}%")

    return lines


def format_socioeconomic_status(profile: Dict[str, Any]) -> List[str]:
    """
    Format socioeconomic status flags (SDVOSB, WOSB, 8(a), etc.).

    Args:
        profile: Company profile dictionary

    Returns:
        List of formatted socioeconomic status strings
    """
    flags = []

    if profile.get('veteran_owned'):
        flags.append("Veteran-Owned (VOSB)")
    if profile.get('service_disabled_veteran_owned'):
        flags.append("Service-Disabled Veteran-Owned (SDVOSB)")
    if profile.get('woman_owned'):
        flags.append("Woman-Owned (WOSB)")
    if profile.get('economically_disadvantaged_woman_owned'):
        flags.append("Economically Disadvantaged Woman-Owned (EDWOSB)")
    if profile.get('disadvantaged_business'):
        flags.append("8(a) Disadvantaged Business")

    if flags:
        return [f"**Socioeconomic Status**: {', '.join(flags)}"]
    return []


def format_sam_registration(profile: Dict[str, Any]) -> List[str]:
    """
    Format SAM registration information.

    Args:
        profile: Company profile dictionary

    Returns:
        List of formatted SAM registration strings
    """
    lines = []

    sam_status = profile.get('sam_registration_status')
    if sam_status:
        lines.append(f"**SAM Registration Status**: {sam_status}")
        if profile.get('sam_registration_date'):
            lines.append(f"**SAM Registration Date**: {profile['sam_registration_date']}")
        if profile.get('sam_expiration_date'):
            lines.append(f"**SAM Expiration Date**: {profile['sam_expiration_date']}")

    return lines


def format_hubzone_info(profile: Dict[str, Any]) -> List[str]:
    """
    Format HUBZone eligibility information.

    Args:
        profile: Company profile dictionary

    Returns:
        List of formatted HUBZone strings
    """
    lines = []
    hubzone = profile.get('hubzone_info')
    if not hubzone:
        return lines

    lines.append("**HUBZone Information**:")
    lines.append(f"  - Principal Office in HUBZone: {'Yes' if hubzone.get('principal_office_in_hubzone') else 'No'}")

    if hubzone.get('hubzone_designation'):
        lines.append(f"  - Designation Type: {hubzone['hubzone_designation']}")

    # Calculate HUBZone employee percentage
    emp_residences = hubzone.get('employee_residences', [])
    if emp_residences:
        total_emp = sum(e.get('employee_count', 0) for e in emp_residences)
        hubzone_emp = sum(e.get('employee_count', 0) for e in emp_residences if e.get('is_hubzone'))
        if total_emp > 0:
            hubzone_pct = (hubzone_emp / total_emp) * 100
            lines.append(f"  - HUBZone Employee Residency: {hubzone_pct:.1f}% ({hubzone_emp} of {total_emp} employees)")

    return lines


def format_management_team(profile: Dict[str, Any], limit: int = 5) -> List[str]:
    """
    Format management team list.

    Args:
        profile: Company profile dictionary
        limit: Maximum number of team members to include

    Returns:
        List of formatted management team strings
    """
    lines = []
    team = profile.get('management_team', [])
    if not team:
        return lines

    lines.append("**Management Team**:")
    for member in team[:limit]:
        name = member.get('name', 'N/A')
        title = member.get('title', 'N/A')
        lines.append(f"  - **{name}** - {title}")
        if member.get('role_description'):
            lines.append(f"    {member['role_description']}")

        # Include contact info if available
        contact_parts = []
        if member.get('email'):
            contact_parts.append(member['email'])
        if member.get('phone'):
            contact_parts.append(member['phone'])
        if contact_parts:
            lines.append(f"    Contact: {', '.join(contact_parts)}")

    if len(team) > limit:
        lines.append(f"  - ... and {len(team) - limit} more")

    return lines


def format_federal_history(profile: Dict[str, Any]) -> List[str]:
    """
    Format federal contracting history.

    Args:
        profile: Company profile dictionary

    Returns:
        List of formatted federal history strings
    """
    lines = []
    history = profile.get('federal_contracting_history')
    if not history:
        return lines

    if not history.get('has_federal_contracts'):
        lines.append("**Federal Contracting History**: No prior federal contracts")
        return lines

    lines.append("**Federal Contracting History**:")
    lines.append(f"  - Total Contracts: {history.get('total_contracts', 0)}")

    total_value = history.get('total_value', 0)
    if total_value >= 1_000_000:
        lines.append(f"  - Total Contract Value: ${total_value:,.0f}")
    elif total_value > 0:
        lines.append(f"  - Total Contract Value: ${total_value:,.2f}")

    if history.get('first_contract_date'):
        lines.append(f"  - First Contract Date: {history['first_contract_date']}")

    agencies = history.get('agencies_worked_with', [])
    if agencies:
        lines.append(f"  - Agencies Served: {', '.join(agencies)}")

    return lines


def format_teaming_relationships(profile: Dict[str, Any]) -> List[str]:
    """
    Format teaming relationships (primes, subs, preferences).

    Args:
        profile: Company profile dictionary

    Returns:
        List of formatted teaming relationship strings
    """
    lines = []

    primes = profile.get('existing_prime_relationships', [])
    subs = profile.get('existing_sub_relationships', [])
    preferences = profile.get('teaming_preferences', '')

    if not (primes or subs or preferences):
        return lines

    lines.append("**Teaming Relationships**:")

    if primes:
        lines.append(f"  - Prime Contractor Relationships: {', '.join(primes)}")
    if subs:
        lines.append(f"  - Subcontractor Relationships: {', '.join(subs)}")
    if preferences:
        lines.append(f"  - Teaming Preferences: {preferences}")

    return lines


def format_geographic_coverage(profile: Dict[str, Any]) -> List[str]:
    """
    Format geographic coverage areas.

    Args:
        profile: Company profile dictionary

    Returns:
        List of formatted geographic coverage strings
    """
    lines = []
    geo = profile.get('geographic_coverage', [])

    if geo:
        lines.append(f"**Geographic Coverage**: {', '.join(geo)}")

    return lines


def format_full_company_profile(
    profile: Dict[str, Any],
    include_identifiers: bool = True,
    include_address: bool = True,
    include_fundamentals: bool = True,
    include_ownership: bool = True,
    include_socioeconomic: bool = True,
    include_sam: bool = True,
    include_hubzone: bool = True,
    include_management: bool = True,
    include_federal_history: bool = True,
    include_teaming: bool = True,
    include_geographic: bool = True,
) -> str:
    """
    Format a complete company profile section for a prompt.

    This is the main function for generating a comprehensive company
    profile section. Use the include_* flags to customize which
    sections are included based on the agent's needs.

    Args:
        profile: Company profile dictionary
        include_*: Flags to control which sections to include

    Returns:
        Formatted string for inclusion in prompts
    """
    lines = []

    # Basic info - always included
    lines.append(f"**Company Name**: {profile.get('name', 'N/A')}")

    if include_address:
        addr = format_principal_address(profile)
        if addr:
            lines.append(f"**Principal Address**: {addr}")
        elif profile.get('headquarters_location'):
            lines.append(f"**Headquarters**: {profile['headquarters_location']}")

    if include_identifiers:
        id_lines = format_company_identifiers(profile)
        if id_lines:
            lines.extend(id_lines)

    lines.append("")

    # Company fundamentals
    if include_fundamentals:
        if profile.get('formation_date'):
            lines.append(f"**Formation Date**: {profile['formation_date']}")
        if profile.get('business_status'):
            lines.append(f"**Business Status**: {profile['business_status']}")
        if profile.get('fiscal_year_end'):
            lines.append(f"**Fiscal Year End**: {profile['fiscal_year_end']}")

        if profile.get('years_in_business'):
            lines.append(f"**Years in Business**: {profile['years_in_business']}")
        if profile.get('employee_count'):
            lines.append(f"**Employee Count**: {profile['employee_count']}")
        if profile.get('annual_revenue'):
            revenue = profile['annual_revenue']
            if revenue >= 1_000_000:
                lines.append(f"**Annual Revenue**: ${revenue:,.0f}")
            else:
                lines.append(f"**Annual Revenue**: ${revenue:,.2f}")
        lines.append("")

    # Socioeconomic status
    if include_socioeconomic:
        socio_lines = format_socioeconomic_status(profile)
        if socio_lines:
            lines.extend(socio_lines)
            lines.append("")

    # SAM Registration
    if include_sam:
        sam_lines = format_sam_registration(profile)
        if sam_lines:
            lines.extend(sam_lines)
            lines.append("")

    # Ownership structure
    if include_ownership:
        ownership_lines = format_ownership_structure(profile)
        if ownership_lines:
            lines.extend(ownership_lines)
            lines.append("")

    # Management team
    if include_management:
        mgmt_lines = format_management_team(profile)
        if mgmt_lines:
            lines.extend(mgmt_lines)
            lines.append("")

    # HUBZone information
    if include_hubzone:
        hubzone_lines = format_hubzone_info(profile)
        if hubzone_lines:
            lines.extend(hubzone_lines)
            lines.append("")

    # Federal contracting history
    if include_federal_history:
        history_lines = format_federal_history(profile)
        if history_lines:
            lines.extend(history_lines)
            lines.append("")

    # Geographic coverage
    if include_geographic:
        geo_lines = format_geographic_coverage(profile)
        if geo_lines:
            lines.extend(geo_lines)
            lines.append("")

    # Teaming relationships
    if include_teaming:
        teaming_lines = format_teaming_relationships(profile)
        if teaming_lines:
            lines.extend(teaming_lines)
            lines.append("")

    # Remove trailing empty lines
    while lines and lines[-1] == "":
        lines.pop()

    return '\n'.join(lines)
