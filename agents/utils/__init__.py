"""
Utility modules for agent operations.
"""

from .dataclass_mixin import DataclassMixin
from .profile_formatter import (
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
    format_full_company_profile,
)
from .section_formatter import (
    SectionFormatter,
    format_section_header,
    format_field,
    format_bullet_list,
    format_numbered_list,
    # Capture Strategist formatters
    format_win_themes_section,
    format_discriminators_section,
    format_ghost_team_section,
    format_price_to_win_section,
    format_capture_comprehensive_section,
    # Compliance Navigator formatters
    format_eligibility_section,
    format_checklist_section,
    format_oci_section,
    format_subcontracting_section,
    format_compliance_comprehensive_section,
    # Market Analyst formatters
    format_market_sizing_section,
    format_opportunities_section,
    format_competitive_section,
    format_timing_section,
    format_market_comprehensive_section,
)

__all__ = [
    "DataclassMixin",
    # Profile formatters
    "format_company_identifiers",
    "format_principal_address",
    "format_ownership_structure",
    "format_socioeconomic_status",
    "format_sam_registration",
    "format_hubzone_info",
    "format_management_team",
    "format_federal_history",
    "format_teaming_relationships",
    "format_geographic_coverage",
    "format_full_company_profile",
    # Section formatters
    "SectionFormatter",
    "format_section_header",
    "format_field",
    "format_bullet_list",
    "format_numbered_list",
    # Capture Strategist formatters
    "format_win_themes_section",
    "format_discriminators_section",
    "format_ghost_team_section",
    "format_price_to_win_section",
    "format_capture_comprehensive_section",
    # Compliance Navigator formatters
    "format_eligibility_section",
    "format_checklist_section",
    "format_oci_section",
    "format_subcontracting_section",
    "format_compliance_comprehensive_section",
    # Market Analyst formatters
    "format_market_sizing_section",
    "format_opportunities_section",
    "format_competitive_section",
    "format_timing_section",
    "format_market_comprehensive_section",
]
