"""
Blue Team Agent Prompts

Prompt templates for blue team agents.
"""

from .strategy_architect_prompts import (
    STRATEGY_ARCHITECT_SYSTEM_PROMPT,
    get_draft_prompt,
    get_revision_prompt,
    get_section_prompt,
)
from .market_analyst_prompts import (
    MARKET_ANALYST_SYSTEM_PROMPT,
    get_market_analysis_prompt,
    get_opportunity_ranking_prompt,
    get_incumbent_analysis_prompt,
    get_timing_analysis_prompt,
)
from .compliance_navigator_prompts import (
    COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT,
    get_eligibility_assessment_prompt,
    get_far_compliance_prompt,
    get_oci_analysis_prompt,
    get_compliance_checklist_prompt,
    get_limitations_on_subcontracting_prompt,
)

__all__ = [
    # Strategy Architect
    "STRATEGY_ARCHITECT_SYSTEM_PROMPT",
    "get_draft_prompt",
    "get_revision_prompt",
    "get_section_prompt",
    # Market Analyst
    "MARKET_ANALYST_SYSTEM_PROMPT",
    "get_market_analysis_prompt",
    "get_opportunity_ranking_prompt",
    "get_incumbent_analysis_prompt",
    "get_timing_analysis_prompt",
    # Compliance Navigator
    "COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT",
    "get_eligibility_assessment_prompt",
    "get_far_compliance_prompt",
    "get_oci_analysis_prompt",
    "get_compliance_checklist_prompt",
    "get_limitations_on_subcontracting_prompt",
]
