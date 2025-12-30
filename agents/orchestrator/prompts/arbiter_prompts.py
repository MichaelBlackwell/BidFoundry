"""
Arbiter Agent Prompts

System prompts and templates for the Arbiter orchestrator agent.
"""

from typing import Dict, List, Any


# System prompt for the Arbiter
ARBITER_SYSTEM_PROMPT = """You are the Arbiter, the master orchestrator of an adversarial document generation system for Government Contracting (GovCon) strategy documents.

Your role is to:
1. ORCHESTRATE the full adversarial workflow between blue team (constructive) and red team (adversarial) agents
2. MANAGE debate rounds to ensure thorough vetting of all strategic recommendations
3. DETECT CONSENSUS when the debate has reached productive resolution
4. RESOLVE CONFLICTS by making final decisions on contested points
5. SYNTHESIZE final documents that incorporate the best insights from both teams
6. ENSURE QUALITY by tracking confidence scores and triggering human review when needed

## Your Decision-Making Philosophy

You maintain a balanced perspective, valuing:
- The blue team's optimistic, opportunity-focused strategy development
- The red team's rigorous, adversarial challenge of assumptions
- Evidence-based reasoning over unsupported claims
- Practical recommendations that account for real-world constraints
- Transparency about uncertainties and risks

## Workflow Management

For each document, you will:

1. **BlueBuild Phase**: Coordinate blue team agents to create initial drafts
   - Strategy Architect: Primary document drafter
   - Market Analyst: Market intelligence
   - Compliance Navigator: Regulatory expertise
   - Capture Strategist: Win strategy development

2. **RedAttack Phase**: Coordinate red team agents to critique
   - Devil's Advocate: Logical challenges
   - Competitor Simulator: Competitive vulnerabilities
   - Evaluator Simulator: Government evaluator perspective
   - Risk Assessor: Risk identification

3. **BlueDefense Phase**: Coordinate blue team response to critiques
   - Accept: Incorporate the critique's recommendation
   - Rebut: Provide evidence/reasoning to refute
   - Acknowledge: Accept the point but explain constraints

4. **Synthesis Phase**: Compile final document
   - Incorporate accepted changes
   - Resolve any remaining conflicts
   - Calculate confidence scores
   - Generate transparency report

## Consensus Detection

Consensus is reached when:
- Resolution rate >= 80% (configurable)
- No unresolved critical critiques
- Remaining issues are minor or observational

## Human Escalation

Trigger human review when:
- Overall confidence < 70%
- Unresolved critical compliance issues
- Fundamental strategy disagreements between teams
- Missing required information that cannot be inferred

## Output Quality Standards

Ensure all outputs are:
- Specific to the client's capabilities and certifications
- Grounded in verifiable facts and past performance
- Aligned with the target agency's mission
- Actionable with clear next steps
- Honest about limitations and risks
"""


# Prompt for synthesizing final documents
SYNTHESIS_PROMPT = """Synthesize the following section content into a polished final version.

## Original Content
{original_content}

## Critiques Received
{critiques}

## Responses Given
{responses}

## Instructions
1. Incorporate any changes that were accepted
2. Ensure rebuttals are reflected in the reasoning
3. Address acknowledged points appropriately
4. Maintain the section's strategic focus
5. Ensure consistency with other sections

Produce a polished final version of this section."""


# Prompt for conflict resolution
CONFLICT_RESOLUTION_PROMPT = """A conflict exists that requires your resolution.

## The Issue
{issue_description}

## Blue Team Position
{blue_position}

## Red Team Position
{red_position}

## Relevant Evidence
{evidence}

## Instructions
Resolve this conflict by:
1. Weighing the evidence from both perspectives
2. Considering the practical implications
3. Making a clear decision with rationale
4. Suggesting any compromise language if appropriate

Your resolution:"""


# Prompt for determining next action
NEXT_ACTION_PROMPT = """Based on the current debate state, determine the next action.

## Current State
- Round: {current_round}
- Phase: {current_phase}
- Total Critiques: {total_critiques}
- Resolved: {resolved_critiques}
- Resolution Rate: {resolution_rate}%

## Unresolved Issues
{unresolved_issues}

## Options
1. Continue to next round of adversarial debate
2. Proceed to synthesis (consensus reached)
3. Force resolution on blocking issues
4. Escalate to human review

Recommend the next action with reasoning:"""


# Prompt for generating executive summary
EXECUTIVE_SUMMARY_PROMPT = """Generate an executive summary for the completed document.

## Document Type
{document_type}

## Key Sections
{section_summaries}

## Debate Summary
- Total Rounds: {total_rounds}
- Critiques Addressed: {critiques_addressed}
- Consensus Reached: {consensus_reached}
- Overall Confidence: {confidence_score}

## Instructions
Create a concise executive summary that:
1. Highlights the key strategic recommendations
2. Notes significant risks that were identified
3. Indicates confidence level and any caveats
4. Provides clear next steps

Executive Summary:"""


# Prompt templates for specific document types
DOCUMENT_TYPE_PROMPTS: Dict[str, str] = {
    "Capability Statement": """Focus on:
- Core competencies that differentiate the company
- Relevant past performance examples
- Key certifications and clearances
- Alignment with target agency missions""",

    "Competitive Analysis": """Focus on:
- Market position relative to competitors
- Strengths and vulnerabilities
- Competitive differentiators
- Strategic recommendations for positioning""",

    "SWOT Analysis": """Focus on:
- Internal strengths the company can leverage
- Weaknesses requiring mitigation
- External opportunities to pursue
- Threats requiring contingency planning""",

    "Proposal Strategy": """Focus on:
- Win themes that resonate with evaluation criteria
- Discriminators that set the company apart
- Ghosting strategies for likely competitors
- Pricing considerations and price-to-win guidance""",

    "Go-to-Market Strategy": """Focus on:
- Target agency and contract prioritization
- Partnership and teaming opportunities
- Marketing and BD resource allocation
- Timeline and milestone recommendations""",

    "Teaming Strategy": """Focus on:
- Gap analysis for prime vs. sub opportunities
- Ideal partner profiles and criteria
- Teaming arrangement structures
- Risk sharing and work share considerations""",

    "BD Pipeline": """Focus on:
- Opportunity prioritization framework
- Resource allocation recommendations
- Timeline and decision point mapping
- Success probability assessments""",
}


def get_document_type_guidance(document_type: str) -> str:
    """Get the guidance prompt for a specific document type."""
    return DOCUMENT_TYPE_PROMPTS.get(document_type, "")


def format_critique_summary(critiques: List[Dict[str, Any]]) -> str:
    """Format a list of critiques for inclusion in prompts."""
    if not critiques:
        return "No critiques received."

    lines = []
    for i, critique in enumerate(critiques, 1):
        severity = critique.get("severity", "Unknown")
        agent = critique.get("agent", "Unknown Agent")
        title = critique.get("title", "No title")
        argument = critique.get("argument", "")

        lines.append(f"{i}. [{severity}] {title} (from {agent})")
        if argument:
            lines.append(f"   {argument[:200]}...")

    return "\n".join(lines)


def format_response_summary(responses: List[Dict[str, Any]]) -> str:
    """Format a list of responses for inclusion in prompts."""
    if not responses:
        return "No responses given."

    lines = []
    for response in responses:
        disposition = response.get("disposition", "Unknown")
        agent = response.get("agent", "Unknown Agent")
        summary = response.get("summary", "")

        lines.append(f"- [{disposition}] {summary[:150]}... (by {agent})")

    return "\n".join(lines)


def build_synthesis_prompt(
    section_name: str,
    original_content: str,
    critiques: List[Dict[str, Any]],
    responses: List[Dict[str, Any]],
) -> str:
    """Build a complete synthesis prompt for a section."""
    return SYNTHESIS_PROMPT.format(
        original_content=original_content,
        critiques=format_critique_summary(critiques),
        responses=format_response_summary(responses),
    )


def build_conflict_resolution_prompt(
    issue: str,
    blue_position: str,
    red_position: str,
    evidence: List[str],
) -> str:
    """Build a conflict resolution prompt."""
    return CONFLICT_RESOLUTION_PROMPT.format(
        issue_description=issue,
        blue_position=blue_position,
        red_position=red_position,
        evidence="\n".join(f"- {e}" for e in evidence),
    )


def build_next_action_prompt(
    current_round: int,
    current_phase: str,
    total_critiques: int,
    resolved_critiques: int,
    unresolved_issues: List[str],
) -> str:
    """Build a next action determination prompt."""
    resolution_rate = (
        resolved_critiques / total_critiques * 100
        if total_critiques > 0 else 100.0
    )

    return NEXT_ACTION_PROMPT.format(
        current_round=current_round,
        current_phase=current_phase,
        total_critiques=total_critiques,
        resolved_critiques=resolved_critiques,
        resolution_rate=f"{resolution_rate:.1f}",
        unresolved_issues="\n".join(f"- {issue}" for issue in unresolved_issues)
        if unresolved_issues else "None",
    )


def build_executive_summary_prompt(
    document_type: str,
    section_summaries: Dict[str, str],
    total_rounds: int,
    critiques_addressed: int,
    consensus_reached: bool,
    confidence_score: float,
) -> str:
    """Build an executive summary generation prompt."""
    section_text = "\n".join(
        f"### {name}\n{summary}"
        for name, summary in section_summaries.items()
    )

    return EXECUTIVE_SUMMARY_PROMPT.format(
        document_type=document_type,
        section_summaries=section_text,
        total_rounds=total_rounds,
        critiques_addressed=critiques_addressed,
        consensus_reached="Yes" if consensus_reached else "No",
        confidence_score=f"{confidence_score:.2f}",
    )
