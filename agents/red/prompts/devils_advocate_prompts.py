"""
Devil's Advocate Agent Prompts

Prompt templates for the Devil's Advocate agent, responsible for
systematic contrarian challenge to surface logical flaws, unsupported
assumptions, and alternative interpretations.
"""

from typing import Dict, Any, List, Optional


DEVILS_ADVOCATE_SYSTEM_PROMPT = """You are the Devil's Advocate, a systematic contrarian whose role is to strengthen strategy documents by identifying weaknesses before they become vulnerabilities.

## Your Mission
Challenge every major assumption, identify logical gaps, and propose alternative interpretations. Your goal is NOT to destroy the strategy but to make it bulletproof by exposing flaws that can be fixed before the proposal goes out.

## Your Perspective
You are skeptical but constructive. You assume nothing is proven until evidence is provided. You look for:
- Logical gaps and contradictions
- Unsupported claims and assumptions
- Missing evidence or weak proof points
- Alternative interpretations of data
- Completeness gaps in analysis
- Overly optimistic projections
- Risks that aren't acknowledged

## Challenge Types You Identify

### Logic Challenges
- Invalid reasoning or conclusions that don't follow from premises
- Circular arguments that assume what they're trying to prove
- False dichotomies that ignore valid alternatives
- Contradictions within or across document sections

### Evidence Challenges
- Claims made without supporting data
- Weak or outdated evidence
- Cherry-picked data that ignores contrary evidence
- Unverified assumptions presented as facts
- Proof points that don't actually support the claim

### Completeness Challenges
- Missing sections or required elements
- Gaps in analysis coverage
- Incomplete consideration of scenarios
- Missing stakeholder perspectives
- Unaddressed evaluation criteria

### Alternative Interpretation Challenges
- Data that could support different conclusions
- Competitor perspectives that weren't considered
- Evaluator viewpoints that might differ
- Risk scenarios that weren't explored

## Critique Standards

Every critique you provide MUST include:
1. **The specific claim being challenged** - Quote or reference the exact content
2. **Why it's problematic** - Clear explanation of the logical flaw or gap
3. **Impact if not addressed** - What happens if evaluators notice this issue
4. **A suggested remedy** - How to fix or strengthen the problematic content

## Severity Calibration

Use severity ratings appropriately:
- **Critical**: Fundamental flaws that could cause proposal rejection or evaluation weakness
- **Major**: Significant issues that materially weaken the strategy
- **Minor**: Smaller issues that could be improved but don't significantly impact outcomes
- **Observation**: Informational notes for consideration, no action required

Not everything is Critical. Most critiques should be Major or Minor. Reserve Critical for:
- Claims that are demonstrably false
- Contradictions with FAR requirements
- Claims that evaluators will likely challenge
- Missing elements that are required by the RFP

## Constructive Adversarial Approach

Be rigorous but fair:
- Challenge the argument, not the people who wrote it
- Acknowledge when evidence is strong, even as you probe for weaknesses
- Offer constructive paths forward, not just criticism
- Recognize that some uncertainty is inherent and acceptable
- Don't manufacture critiques where none exist

Your ultimate goal is to make the blue team's output stronger. A good Devil's Advocate critique leads to a better final document.
"""


def get_critique_generation_prompt(
    document_type: str,
    document_content: Dict[str, str],
    company_profile: Optional[Dict[str, Any]] = None,
    opportunity: Optional[Dict[str, Any]] = None,
    focus_areas: Optional[List[str]] = None,
) -> str:
    """
    Generate a prompt for creating critiques of a strategy document.

    Args:
        document_type: Type of document being critiqued
        document_content: Dictionary of section names to content
        company_profile: Optional company profile for context
        opportunity: Optional opportunity details for context
        focus_areas: Optional specific areas to focus critiques on

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Systematic Critique Generation",
        "",
        f"Analyze the following {document_type} document and generate critiques that identify weaknesses,",
        "logical flaws, unsupported claims, and areas for improvement.",
        "",
        "---",
        "",
        "## Document Under Review",
        "",
    ]

    # Add document sections
    for section_name, content in document_content.items():
        prompt_parts.append(f"### {section_name}")
        prompt_parts.append("")
        prompt_parts.append(content)
        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    # Add context if available
    if company_profile:
        prompt_parts.extend([
            "## Company Context (for validation)",
            "",
            f"**Company**: {company_profile.get('name', 'N/A')}",
        ])

        # Core capabilities for validation
        caps = company_profile.get('core_capabilities', [])
        if caps:
            cap_names = [c.get('name') for c in caps if c.get('name')]
            prompt_parts.append(f"**Stated Capabilities**: {', '.join(cap_names)}")

        # Past performance for validation
        past_perf = company_profile.get('past_performance', [])
        if past_perf:
            prompt_parts.append(f"**Past Performance Count**: {len(past_perf)} documented contracts")

        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    if opportunity:
        prompt_parts.extend([
            "## Opportunity Requirements (for completeness check)",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Agency**: {opportunity.get('agency', {}).get('name', opportunity.get('agency', 'N/A'))}",
            "",
        ])

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
                    weight = f" ({factor.get('weight')}%)" if factor.get('weight') else ""
                    prompt_parts.append(f"  - {factor.get('name', factor)}{weight}")
                else:
                    prompt_parts.append(f"  - {factor}")
            prompt_parts.append("")

        prompt_parts.append("---")
        prompt_parts.append("")

    # Focus areas if specified
    if focus_areas:
        prompt_parts.extend([
            "## Priority Focus Areas",
            "",
            "Pay particular attention to:",
            "",
        ])
        for area in focus_areas:
            prompt_parts.append(f"- {area}")
        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "## Required Critique Output",
        "",
        "For each issue identified, provide a structured critique:",
        "",
        "### Critique [Number]: [Brief Title]",
        "",
        "**Challenge Type**: [Logic | Evidence | Completeness | Risk | Compliance | Feasibility | Clarity]",
        "",
        "**Severity**: [Critical | Major | Minor | Observation]",
        "",
        "**Target Section**: [Name of the section containing the issue]",
        "",
        "**Challenged Content**: \"[Quote or reference the specific content being challenged]\"",
        "",
        "**Argument**: [Detailed explanation of why this is problematic]",
        "",
        "**Evidence**: [Specific evidence supporting your critique - why you believe this is a flaw]",
        "",
        "**Impact If Not Addressed**: [What could happen if evaluators notice this issue]",
        "",
        "**Suggested Remedy**: [Specific, actionable recommendation to fix the issue]",
        "",
        "---",
        "",
        "## Critique Guidelines",
        "",
        "1. **Be specific**: Reference exact content, don't make vague criticisms",
        "2. **Be calibrated**: Use appropriate severity levels",
        "3. **Be constructive**: Every critique must include a remedy",
        "4. **Be comprehensive**: Cover Logic, Evidence, Completeness, and Risk",
        "5. **Be fair**: Acknowledge strengths while identifying weaknesses",
        "",
        "## Expected Output",
        "",
        "Provide 5-10 critiques covering different aspects of the document.",
        "Prioritize Critical and Major issues, but include Minor observations where relevant.",
        "",
        "At minimum, address:",
        "- At least 2 Logic or Evidence challenges",
        "- At least 1 Completeness challenge",
        "- At least 1 Risk or Feasibility challenge",
    ])

    return "\n".join(prompt_parts)


def get_section_critique_prompt(
    section_name: str,
    section_content: str,
    document_type: str,
    company_profile: Optional[Dict[str, Any]] = None,
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for critiquing a specific section.

    Args:
        section_name: Name of the section to critique
        section_content: Content of the section
        document_type: Type of document
        company_profile: Optional company profile for validation
        opportunity: Optional opportunity for context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Task: Focused Section Critique - {section_name}",
        "",
        f"Perform a deep critique of the '{section_name}' section from a {document_type} document.",
        "",
        "---",
        "",
        "## Section Content",
        "",
        section_content,
        "",
        "---",
        "",
    ]

    # Add validation context
    if company_profile:
        prompt_parts.extend([
            "## Validation Context",
            "",
            "Use this company profile to validate claims:",
            "",
            f"**Company**: {company_profile.get('name', 'N/A')}",
            "",
        ])

        # Certifications
        certs = company_profile.get('certifications', [])
        if certs:
            cert_types = [c.get('cert_type') for c in certs if c.get('cert_type')]
            prompt_parts.append(f"**Certifications**: {', '.join(cert_types)}")

        # Past performance
        past_perf = company_profile.get('past_performance', [])
        if past_perf:
            prompt_parts.append("**Past Performance**:")
            for pp in past_perf[:5]:
                prompt_parts.append(f"  - {pp.get('contract_name', 'N/A')} ({pp.get('agency', 'N/A')})")

        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    # Section-specific guidance
    section_lower = section_name.lower()

    if "win theme" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Focus",
            "",
            "For Win Themes, challenge:",
            "- Are theme statements specific enough or generic?",
            "- Is supporting evidence actually relevant and verifiable?",
            "- Do customer benefits resonate with actual agency priorities?",
            "- Are competitive advantages truly unique or easily matched?",
            "- Is evaluation criteria alignment accurate?",
            "",
        ])
    elif "discriminator" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Focus",
            "",
            "For Discriminators, challenge:",
            "- Is each discriminator truly unique to this company?",
            "- Can competitors easily replicate or counter these?",
            "- Are proof points verifiable and compelling?",
            "- Do discriminators map to actual evaluation criteria?",
            "- Is the competitor gap claim supportable?",
            "",
        ])
    elif "competitive" in section_lower or "ghost" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Focus",
            "",
            "For Competitive Analysis, challenge:",
            "- Are competitor assessments based on evidence or assumptions?",
            "- Are competitor strengths being underestimated?",
            "- Are our vulnerabilities being acknowledged?",
            "- Are predicted strategies realistic?",
            "- Is the positioning matrix balanced and honest?",
            "",
        ])
    elif "price" in section_lower or "ptw" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Focus",
            "",
            "For Price-to-Win, challenge:",
            "- Are market estimates supported by data?",
            "- Are competitor predictions realistic?",
            "- Is the recommended positioning achievable?",
            "- Are pricing risks adequately addressed?",
            "- Is the tradeoff analysis credible?",
            "",
        ])
    elif "risk" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Focus",
            "",
            "For Risk Assessment, challenge:",
            "- Are probability/impact ratings calibrated correctly?",
            "- Are mitigation strategies realistic and specific?",
            "- Are there obvious risks not being addressed?",
            "- Is the analysis too optimistic about execution?",
            "- Are worst-case scenarios honestly considered?",
            "",
        ])
    else:
        prompt_parts.extend([
            "## General Section Focus",
            "",
            "Challenge this section for:",
            "- Logical coherence and valid reasoning",
            "- Evidence supporting all claims",
            "- Completeness of required elements",
            "- Realistic assessment vs. wishful thinking",
            "- Alignment with opportunity requirements",
            "",
        ])

    # Instructions
    prompt_parts.extend([
        "---",
        "",
        "## Required Output",
        "",
        "Provide 3-5 focused critiques for this section, following the standard format:",
        "",
        "### Critique [Number]: [Brief Title]",
        "",
        "**Challenge Type**: [Logic | Evidence | Completeness | Risk | Compliance | Feasibility | Clarity]",
        "",
        "**Severity**: [Critical | Major | Minor | Observation]",
        "",
        "**Challenged Content**: \"[Quote the specific content]\"",
        "",
        "**Argument**: [Why this is problematic]",
        "",
        "**Evidence**: [Evidence supporting your critique]",
        "",
        "**Impact If Not Addressed**: [Potential negative consequences]",
        "",
        "**Suggested Remedy**: [How to fix it]",
        "",
        "---",
        "",
        "Be rigorous but fair. Not everything is flawed - focus on genuine issues.",
    ])

    return "\n".join(prompt_parts)


def get_assumption_challenge_prompt(
    assumptions: List[Dict[str, str]],
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt specifically for challenging assumptions.

    Args:
        assumptions: List of assumptions to challenge, each with 'statement' and optionally 'source'
        context: Optional context about the opportunity or company

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Assumption Challenge",
        "",
        "Systematically challenge the following assumptions identified in strategy documents.",
        "For each assumption, determine if it is valid, questionable, or unsupported.",
        "",
        "---",
        "",
        "## Assumptions to Challenge",
        "",
    ]

    for i, assumption in enumerate(assumptions, 1):
        prompt_parts.append(f"### Assumption {i}")
        prompt_parts.append(f"**Statement**: \"{assumption.get('statement', 'No statement provided')}\"")
        if assumption.get('source'):
            prompt_parts.append(f"**Source Section**: {assumption.get('source')}")
        prompt_parts.append("")

    if context:
        prompt_parts.extend([
            "---",
            "",
            "## Context for Validation",
            "",
        ])

        if context.get('opportunity'):
            opp = context.get('opportunity', {})
            prompt_parts.append(f"**Opportunity**: {opp.get('title', 'N/A')}")
            prompt_parts.append(f"**Agency**: {opp.get('agency', 'N/A')}")
            prompt_parts.append("")

        if context.get('market_conditions'):
            prompt_parts.append(f"**Market Conditions**: {context.get('market_conditions')}")
            prompt_parts.append("")

        prompt_parts.append("---")
        prompt_parts.append("")

    prompt_parts.extend([
        "## Required Analysis",
        "",
        "For each assumption, provide:",
        "",
        "### Assumption [Number] Analysis",
        "",
        "**Statement**: [Quote the assumption]",
        "",
        "**Validity Assessment**: [Valid | Questionable | Unsupported | False]",
        "",
        "**Challenge**: [Why this assumption may not hold]",
        "",
        "**Alternative Scenario**: [What if this assumption is wrong?]",
        "",
        "**Evidence Needed**: [What evidence would validate or invalidate this assumption?]",
        "",
        "**Recommendation**: [Keep as-is | Strengthen with evidence | Revise | Remove]",
        "",
        "---",
        "",
        "## Validity Categories",
        "",
        "- **Valid**: Assumption is well-supported and reasonable",
        "- **Questionable**: Assumption may hold but needs more support",
        "- **Unsupported**: No evidence provided for this assumption",
        "- **False**: Assumption contradicts known facts or evidence",
        "",
        "Not all assumptions are bad. Focus on identifying those that are",
        "unsupported, overly optimistic, or could lead to strategic errors.",
    ])

    return "\n".join(prompt_parts)


def get_counterargument_generation_prompt(
    claims: List[Dict[str, str]],
    opponent_perspective: str = "Government Evaluator",
) -> str:
    """
    Generate a prompt for creating counterarguments to strategy claims.

    Args:
        claims: List of claims to counter, each with 'claim' and 'section'
        opponent_perspective: Whose perspective to adopt for counterarguments

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Counterargument Generation",
        "",
        f"Adopt the perspective of a {opponent_perspective} and generate counterarguments",
        "to the following claims from the strategy document.",
        "",
        "---",
        "",
        "## Claims to Counter",
        "",
    ]

    for i, claim_obj in enumerate(claims, 1):
        prompt_parts.append(f"### Claim {i}")
        prompt_parts.append(f"**Claim**: \"{claim_obj.get('claim', 'No claim provided')}\"")
        prompt_parts.append(f"**Section**: {claim_obj.get('section', 'Unknown')}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        f"## Adopt the {opponent_perspective} Perspective",
        "",
    ])

    if "evaluator" in opponent_perspective.lower():
        prompt_parts.extend([
            "As a Government Evaluator, you:",
            "- Have seen many proposals with similar claims",
            "- Are looking for specific, provable evidence",
            "- Are skeptical of superlatives and vague promises",
            "- Want to see how claims map to evaluation criteria",
            "- Need to justify your ratings with evidence from the proposal",
            "",
        ])
    elif "competitor" in opponent_perspective.lower():
        prompt_parts.extend([
            "As a Competitor, you:",
            "- Want to highlight weaknesses in this proposal",
            "- Can point to your own superior capabilities",
            "- Know the customer's real priorities",
            "- Are aware of this company's past performance gaps",
            "- Will exploit any overstatements or unsupported claims",
            "",
        ])
    else:
        prompt_parts.extend([
            f"As a {opponent_perspective}, critically evaluate each claim",
            "from your unique perspective and challenge its validity.",
            "",
        ])

    prompt_parts.extend([
        "---",
        "",
        "## Required Output",
        "",
        "For each claim, provide:",
        "",
        "### Claim [Number] Counterargument",
        "",
        "**Original Claim**: [Quote the claim]",
        "",
        "**Counterargument**: [The challenge from this perspective]",
        "",
        "**Weakness Exposed**: [What flaw does this counterargument reveal?]",
        "",
        "**How Blue Team Should Respond**: [How to strengthen against this counterargument]",
        "",
        "---",
        "",
        "Be rigorous in your counterarguments. If a claim is actually well-supported,",
        "acknowledge that while still identifying any potential challenges.",
    ])

    return "\n".join(prompt_parts)


def get_logic_analysis_prompt(
    content: str,
    section_name: str = "Strategy Document",
) -> str:
    """
    Generate a prompt specifically for logical analysis.

    Args:
        content: Content to analyze for logical issues
        section_name: Name of the section being analyzed

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Task: Logical Analysis - {section_name}",
        "",
        "Perform a rigorous logical analysis of the following content.",
        "Identify any reasoning errors, logical fallacies, or unsound conclusions.",
        "",
        "---",
        "",
        "## Content to Analyze",
        "",
        content,
        "",
        "---",
        "",
        "## Logical Issues to Identify",
        "",
        "Look for these common logical problems:",
        "",
        "### Reasoning Errors",
        "- **Non sequitur**: Conclusions that don't follow from premises",
        "- **Circular reasoning**: Assuming what needs to be proven",
        "- **False causation**: Assuming correlation implies causation",
        "- **Hasty generalization**: Drawing broad conclusions from limited evidence",
        "",
        "### Fallacies",
        "- **False dichotomy**: Presenting only two options when more exist",
        "- **Appeal to authority**: Relying on authority without evidence",
        "- **Straw man**: Misrepresenting positions to make them easier to attack",
        "- **Red herring**: Introducing irrelevant information",
        "",
        "### Structural Issues",
        "- **Internal contradictions**: Conflicting statements within the document",
        "- **Unsupported leaps**: Jumping to conclusions without intermediate steps",
        "- **Missing premises**: Arguments that require unstated assumptions",
        "- **Scope creep**: Claims that extend beyond what evidence supports",
        "",
        "---",
        "",
        "## Required Output",
        "",
        "For each logical issue identified, provide:",
        "",
        "### Logical Issue [Number]: [Type of Issue]",
        "",
        "**Location**: [Where in the content this appears]",
        "",
        "**The Flawed Reasoning**: [Quote or describe the problematic logic]",
        "",
        "**Why It's Flawed**: [Explain the logical error]",
        "",
        "**Correct Reasoning Would Be**: [How to fix the logic]",
        "",
        "**Severity**: [Critical | Major | Minor]",
        "",
        "---",
        "",
        "Focus on substantive logical issues, not stylistic preferences.",
        "If the logic is sound, say so - not everything contains fallacies.",
    ]

    return "\n".join(prompt_parts)


def get_response_evaluation_prompt(
    critique: Dict[str, Any],
    response: Dict[str, Any],
) -> str:
    """
    Generate a prompt for evaluating a blue team's response to a critique.

    Args:
        critique: The original critique that was raised
        response: The blue team's response to the critique

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Response Evaluation",
        "",
        "Evaluate whether the Blue Team's response adequately addresses the critique.",
        "Determine if the critique should be considered resolved.",
        "",
        "---",
        "",
        "## Original Critique",
        "",
        f"**Title**: {critique.get('title', 'N/A')}",
        f"**Challenge Type**: {critique.get('challenge_type', 'N/A')}",
        f"**Severity**: {critique.get('severity', 'N/A')}",
        f"**Target Section**: {critique.get('target_section', 'N/A')}",
        "",
        f"**Challenged Content**: \"{critique.get('target_content', 'N/A')}\"",
        "",
        f"**Argument**: {critique.get('argument', 'N/A')}",
        "",
        f"**Suggested Remedy**: {critique.get('suggested_remedy', 'N/A')}",
        "",
        "---",
        "",
        "## Blue Team Response",
        "",
        f"**Disposition**: {response.get('disposition', 'N/A')}",
        "",
        f"**Action Taken**: {response.get('action', 'N/A')}",
        "",
    ]

    if response.get('evidence'):
        prompt_parts.append(f"**Supporting Evidence**: {response.get('evidence')}")
        prompt_parts.append("")

    if response.get('revised_content'):
        prompt_parts.append(f"**Revised Content**: \"{response.get('revised_content')}\"")
        prompt_parts.append("")

    if response.get('residual_risk'):
        prompt_parts.append(f"**Acknowledged Residual Risk**: {response.get('residual_risk')}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Evaluation Criteria",
        "",
        "A response is **Acceptable** if:",
        "- It substantively addresses the core issue raised",
        "- It provides adequate evidence for any rebuttal",
        "- It implements a meaningful fix if accepting the critique",
        "- It honestly acknowledges any residual risk",
        "",
        "A response is **Insufficient** if:",
        "- It dismisses the critique without addressing the substance",
        "- It claims to rebut without providing evidence",
        "- It implements a superficial fix that doesn't address root cause",
        "- It ignores significant aspects of the critique",
        "",
        "---",
        "",
        "## Required Output",
        "",
        "### Evaluation Result",
        "",
        "**Verdict**: [Acceptable | Insufficient | Partially Acceptable]",
        "",
        "**Reasoning**: [Why this verdict was reached]",
        "",
        "**Strengths of Response**: [What the blue team did well]",
        "",
        "**Weaknesses of Response**: [What could be improved]",
        "",
        "**Follow-Up Required**: [Yes/No - If yes, what specifically]",
        "",
        "**Resolution Status**: [Resolved | Needs Further Work | Escalate to Human]",
        "",
        "---",
        "",
        "Be fair but rigorous. The goal is ensuring the final document is strong,",
        "not winning the argument for its own sake.",
    ])

    return "\n".join(prompt_parts)
