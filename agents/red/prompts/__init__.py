"""
Red Team Agent Prompts

Prompt templates for adversarial agents.
"""

from .devils_advocate_prompts import (
    DEVILS_ADVOCATE_SYSTEM_PROMPT,
    get_critique_generation_prompt,
    get_section_critique_prompt,
    get_assumption_challenge_prompt,
    get_counterargument_generation_prompt,
    get_logic_analysis_prompt,
    get_response_evaluation_prompt,
)

__all__ = [
    "DEVILS_ADVOCATE_SYSTEM_PROMPT",
    "get_critique_generation_prompt",
    "get_section_critique_prompt",
    "get_assumption_challenge_prompt",
    "get_counterargument_generation_prompt",
    "get_logic_analysis_prompt",
    "get_response_evaluation_prompt",
]
