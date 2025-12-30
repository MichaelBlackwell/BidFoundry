"""
Arbiter Agent Prompts

Prompt templates for the Arbiter orchestrator agent.
"""

from .arbiter_prompts import (
    ARBITER_SYSTEM_PROMPT,
    SYNTHESIS_PROMPT,
    CONFLICT_RESOLUTION_PROMPT,
    NEXT_ACTION_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
    DOCUMENT_TYPE_PROMPTS,
    get_document_type_guidance,
    format_critique_summary,
    format_response_summary,
    build_synthesis_prompt,
    build_conflict_resolution_prompt,
    build_next_action_prompt,
    build_executive_summary_prompt,
)

__all__ = [
    "ARBITER_SYSTEM_PROMPT",
    "SYNTHESIS_PROMPT",
    "CONFLICT_RESOLUTION_PROMPT",
    "NEXT_ACTION_PROMPT",
    "EXECUTIVE_SUMMARY_PROMPT",
    "DOCUMENT_TYPE_PROMPTS",
    "get_document_type_guidance",
    "format_critique_summary",
    "format_response_summary",
    "build_synthesis_prompt",
    "build_conflict_resolution_prompt",
    "build_next_action_prompt",
    "build_executive_summary_prompt",
]
