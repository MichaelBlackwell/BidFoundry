"""
Evaluator Simulator Agent Prompts

Prompt templates for the Evaluator Simulator agent, responsible for
simulating the perspective of a government Source Selection Evaluation
Board (SSEB) to identify weaknesses, deficiencies, and compliance gaps.
"""

from typing import Dict, Any, List, Optional


EVALUATOR_SIMULATOR_SYSTEM_PROMPT = """You are the Evaluator Simulator, an adversarial agent that simulates the perspective of a government Source Selection Evaluation Board (SSEB) member.

## Your Mission
Evaluate the proposal strategy documents as if you were a government evaluator applying FAR source selection standards. Your goal is to identify weaknesses, deficiencies, and risks that would result in lower ratings or disqualification.

## Your Perspective

### You Are a Government Evaluator
- You are skeptical but fair
- You evaluate strictly against stated requirements
- You look for evidence, not claims
- You identify what's missing, not just what's wrong
- You use FAR-defined terminology precisely

### Your Evaluation Mindset
- "Show me, don't tell me" - claims without evidence are weaknesses
- "Does this actually meet the requirement?" - not just sound good
- "Would I stake my reputation on recommending this?" - professional skepticism
- "What questions would I ask in discussions?" - identify clarification needs

## FAR Evaluation Standards

### Weakness/Deficiency Terminology (FAR 15.305)

**Deficiency**: A material failure to meet a Government requirement or a combination of
significant weaknesses that increases the risk of unsuccessful performance to an
unacceptable level.
- Results in UNACCEPTABLE rating
- Cannot be in competitive range without correction

**Significant Weakness**: A flaw in the proposal that appreciably increases the risk
of unsuccessful contract performance.
- May result in MARGINAL or lower rating
- Must be addressed but may not be disqualifying

**Weakness**: A flaw in the proposal that increases the risk of unsuccessful
contract performance.
- Noted but may not significantly affect rating
- Accumulation of weaknesses can lower rating

**Risk**: The potential for unsuccessful contract performance, including:
- Technical risk (ability to achieve requirements)
- Cost risk (realistic cost estimates)
- Schedule risk (ability to meet timelines)

### Adjectival Rating Standards

**Outstanding**: Proposal significantly exceeds requirements in ways beneficial
to the Government. Multiple significant strengths, no significant weaknesses.

**Good**: Proposal exceeds some requirements with beneficial outcomes.
Strengths outweigh weaknesses.

**Acceptable**: Proposal meets requirements. Minor strengths and weaknesses
are balanced.

**Marginal**: Proposal fails to meet some requirements but deficiencies are
correctable. Significant weaknesses present.

**Unacceptable**: Material failure to meet requirements. Contains deficiencies
that cannot be corrected without major revision.

### Past Performance Confidence (FAR 15.305(a)(2))

**Substantial Confidence**: Based on performance record, expect successful performance.
**Satisfactory Confidence**: Based on record, will likely perform satisfactorily.
**Neutral Confidence**: No/limited record - neither positive nor negative prediction.
**Limited Confidence**: Performance record raises doubts.
**No Confidence**: Performance record shows significant problems.

## Critique Standards

Every finding you identify MUST include:
1. **FAR-compliant classification** - Deficiency, Significant Weakness, Weakness, or Risk
2. **Specific requirement reference** - What solicitation requirement is affected
3. **Evidence from proposal** - What you saw (or didn't see) in the document
4. **Impact statement** - How this affects the rating
5. **Evaluator note** - What you would write in the evaluation report

## Evaluation Types

### LPTA (Lowest Price Technically Acceptable)
- Binary pass/fail on technical factors
- Any deficiency = Unacceptable = eliminated
- No credit for exceeding requirements
- Price is only discriminator among acceptable proposals

### Best Value Tradeoff
- Technical factors rated on adjectival scale
- Trade-offs permitted between price and non-price factors
- Superior technical approaches may justify higher prices
- Strengths can differentiate among acceptable proposals

## Constructive Adversarial Approach

Be rigorous but fair:
- Apply evaluation standards consistently
- Acknowledge genuine strengths
- Identify issues that real evaluators would find
- Provide clear remediation guidance
- Use correct FAR terminology

Your ultimate goal is to prepare the proposal for the scrutiny of actual government evaluators.
"""


def get_evaluation_prompt(
    document_type: str,
    document_content: Dict[str, str],
    evaluation_type: str = "Best Value",
    evaluation_factors: Optional[List[Dict[str, Any]]] = None,
    company_profile: Optional[Dict[str, Any]] = None,
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for evaluating a proposal strategy document.

    Args:
        document_type: Type of document being evaluated
        document_content: Dictionary of section names to content
        evaluation_type: "LPTA" or "Best Value"
        evaluation_factors: List of evaluation factors and weights
        company_profile: Optional company profile for context
        opportunity: Optional opportunity details for context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Government Evaluator Simulation",
        "",
        f"Evaluate this {document_type} as if you are a government Source Selection",
        f"Evaluation Board (SSEB) member applying **{evaluation_type}** evaluation standards.",
        "",
        "---",
        "",
    ]

    # Add evaluation factors
    if evaluation_factors:
        prompt_parts.extend([
            "## Evaluation Factors (from Solicitation)",
            "",
        ])

        for i, factor in enumerate(evaluation_factors, 1):
            name = factor.get('name', f'Factor {i}')
            weight = factor.get('weight')
            importance = factor.get('importance')

            weight_str = f" ({weight}%)" if weight else ""
            importance_str = f" - {importance}" if importance else ""

            prompt_parts.append(f"### {name}{weight_str}{importance_str}")
            prompt_parts.append("")

            if factor.get('description'):
                prompt_parts.append(f"**Description**: {factor.get('description')}")
                prompt_parts.append("")

            sub_factors = factor.get('sub_factors', [])
            if sub_factors:
                prompt_parts.append("**Sub-factors**:")
                for sf in sub_factors:
                    sf_name = sf.get('name', 'Sub-factor') if isinstance(sf, dict) else sf
                    prompt_parts.append(f"  - {sf_name}")
                prompt_parts.append("")

            criteria = factor.get('evaluation_criteria', [])
            if criteria:
                prompt_parts.append("**Evaluation Criteria**:")
                for criterion in criteria:
                    prompt_parts.append(f"  - {criterion}")
                prompt_parts.append("")

        prompt_parts.extend(["---", ""])

    # Add document content
    prompt_parts.extend([
        "## Proposal Strategy Document to Evaluate",
        "",
    ])

    for section_name, content in document_content.items():
        prompt_parts.append(f"### {section_name}")
        prompt_parts.append("")
        prompt_parts.append(content)
        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    # Add company context if available
    if company_profile:
        prompt_parts.extend([
            "## Offeror Profile (for context)",
            "",
            f"**Company**: {company_profile.get('name', 'N/A')}",
        ])

        certs = company_profile.get('certifications', [])
        if certs:
            cert_types = [c.get('cert_type') for c in certs if c.get('cert_type')]
            prompt_parts.append(f"**Certifications**: {', '.join(cert_types)}")

        past_perf = company_profile.get('past_performance', [])
        if past_perf:
            prompt_parts.append(f"**Past Performance References**: {len(past_perf)} contracts")

        prompt_parts.extend(["", "---", ""])

    # Add opportunity context
    if opportunity:
        prompt_parts.extend([
            "## Solicitation Context",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
        ])

        agency = opportunity.get('agency', {})
        if isinstance(agency, dict):
            prompt_parts.append(f"**Agency**: {agency.get('name', 'N/A')}")
        else:
            prompt_parts.append(f"**Agency**: {agency}")

        if opportunity.get('is_recompete'):
            prompt_parts.append("**Type**: RECOMPETE")

        prompt_parts.extend(["", "---", ""])

    # Add evaluation type specific guidance
    if evaluation_type == "LPTA":
        prompt_parts.extend([
            "## LPTA Evaluation Instructions",
            "",
            "For LPTA evaluation:",
            "- Evaluate each factor for ACCEPTABILITY only (pass/fail)",
            "- ANY deficiency makes the proposal UNACCEPTABLE",
            "- No credit for exceeding requirements",
            "- Focus on whether minimum requirements are met",
            "",
        ])
    else:
        prompt_parts.extend([
            "## Best Value Evaluation Instructions",
            "",
            "For Best Value evaluation:",
            "- Rate each factor using the adjectival scale",
            "- Identify strengths that exceed requirements",
            "- Identify weaknesses, significant weaknesses, and deficiencies",
            "- Assess risk areas",
            "- Consider trade-off implications",
            "",
        ])

    # Required output format
    prompt_parts.extend([
        "---",
        "",
        "## Required Output",
        "",
        "### 1. Overall Evaluation Summary",
        "",
        "Provide your overall assessment including:",
        "- **Overall Rating**: [Outstanding | Good | Acceptable | Marginal | Unacceptable]",
        "- **In Competitive Range**: [Yes | No | Pending Clarifications]",
        "- **Key Concerns**: [Top 3 issues that affect the rating]",
        "- **Key Strengths**: [Top 3 strengths, if any]",
        "",
        "### 2. Factor-by-Factor Evaluation",
        "",
        "For each evaluation factor:",
        "",
        "**[Factor Name]**",
        "",
        "- **Rating**: [Outstanding | Good | Acceptable | Marginal | Unacceptable]",
        "- **Rationale**: [Why this rating was assigned]",
        "",
        "**Strengths Identified**:",
        "  - [Strength description] - [Benefit to Government]",
        "",
        "**Weaknesses/Deficiencies Identified**:",
        "  - **Type**: [Deficiency | Significant Weakness | Weakness | Risk]",
        "  - **Description**: [What is the issue]",
        "  - **Requirement Affected**: [Which solicitation requirement]",
        "  - **Evidence**: [What in the proposal led to this finding]",
        "  - **Impact**: [How this affects the rating]",
        "  - **Recommendation**: [How to address this]",
        "",
        "### 3. Evaluator Margin Notes",
        "",
        "Provide the informal notes an evaluator might write in margins:",
        "- Questions they would want to ask in discussions",
        "- Red flags they would highlight",
        "- Areas that seem too good to be true",
        "- Missing elements they expected to see",
        "",
        "### 4. Clarification Questions",
        "",
        "List questions you would submit during the clarification process:",
        "- [Question 1 - what information is missing or unclear]",
        "- [Question 2]",
        "- [etc.]",
        "",
        "### 5. Competitive Assessment",
        "",
        "From an evaluator perspective:",
        "- How would this proposal likely rank against competitors?",
        "- What differentiators are compelling?",
        "- What would it take to achieve a higher rating?",
    ])

    return "\n".join(prompt_parts)


def get_section_evaluation_prompt(
    section_name: str,
    section_content: str,
    evaluation_factor: Dict[str, Any],
    evaluation_type: str = "Best Value",
    requirements: Optional[List[str]] = None,
) -> str:
    """
    Generate a prompt for evaluating a specific section.

    Args:
        section_name: Name of the section to evaluate
        section_content: Content of the section
        evaluation_factor: The factor this section addresses
        evaluation_type: "LPTA" or "Best Value"
        requirements: Specific requirements for this section

    Returns:
        Formatted prompt string
    """
    factor_name = evaluation_factor.get('name', section_name)

    prompt_parts = [
        f"## Task: Section Evaluation - {factor_name}",
        "",
        f"Evaluate this section as a government evaluator applying {evaluation_type} standards.",
        "",
        "---",
        "",
        "## Evaluation Factor",
        "",
        f"**Factor**: {factor_name}",
    ]

    if evaluation_factor.get('description'):
        prompt_parts.append(f"**Description**: {evaluation_factor.get('description')}")

    if evaluation_factor.get('weight'):
        prompt_parts.append(f"**Weight**: {evaluation_factor.get('weight')}%")

    prompt_parts.extend(["", "---", ""])

    if requirements:
        prompt_parts.extend([
            "## Requirements to Evaluate Against",
            "",
        ])
        for req in requirements:
            prompt_parts.append(f"- {req}")
        prompt_parts.extend(["", "---", ""])

    prompt_parts.extend([
        "## Section Content",
        "",
        section_content,
        "",
        "---",
        "",
        "## Required Evaluation Output",
        "",
        f"### {factor_name} Evaluation",
        "",
        "**Rating**: [Outstanding | Good | Acceptable | Marginal | Unacceptable]",
        "",
        "**Rating Rationale**: [Why this rating was assigned - reference specific content]",
        "",
        "**Strengths**:",
        "For each strength:",
        "- **Description**: [What exceeds requirements]",
        "- **Location**: [Where in section]",
        "- **Benefit**: [How this benefits the Government]",
        "",
        "**Weaknesses/Deficiencies**:",
        "For each weakness:",
        "- **Type**: [Deficiency | Significant Weakness | Weakness | Risk]",
        "- **Description**: [The specific issue]",
        "- **Requirement Affected**: [Which requirement]",
        "- **Evidence/Location**: [Where found or what's missing]",
        "- **Impact**: [Effect on rating and performance risk]",
        "- **Recommendation**: [How to fix]",
        "",
        "**Evaluator Notes**:",
        "- [Informal observations, questions, concerns]",
    ])

    return "\n".join(prompt_parts)


def get_compliance_check_prompt(
    document_content: Dict[str, str],
    solicitation_requirements: List[Dict[str, Any]],
) -> str:
    """
    Generate a prompt for compliance checking.

    Args:
        document_content: Dictionary of section names to content
        solicitation_requirements: List of mandatory requirements

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Compliance Verification",
        "",
        "Perform a compliance check against solicitation requirements.",
        "Identify any instances where the proposal fails to meet mandatory requirements.",
        "",
        "---",
        "",
        "## Mandatory Requirements",
        "",
    ]

    for i, req in enumerate(solicitation_requirements, 1):
        req_text = req.get('requirement', req) if isinstance(req, dict) else req
        section_ref = req.get('section', 'N/A') if isinstance(req, dict) else 'N/A'
        mandatory = req.get('mandatory', True) if isinstance(req, dict) else True

        prompt_parts.append(f"### Requirement {i}")
        prompt_parts.append(f"**Requirement**: {req_text}")
        prompt_parts.append(f"**Section Reference**: {section_ref}")
        prompt_parts.append(f"**Mandatory**: {'Yes' if mandatory else 'No'}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Proposal Content",
        "",
    ])

    for section_name, content in document_content.items():
        prompt_parts.append(f"### {section_name}")
        prompt_parts.append("")
        prompt_parts.append(content)
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Required Output",
        "",
        "### Compliance Matrix",
        "",
        "For each requirement:",
        "",
        "| Req # | Requirement | Compliant | Evidence/Gap | Risk |",
        "|-------|-------------|-----------|--------------|------|",
        "| 1 | [Requirement text] | [Yes/No/Partial] | [Where addressed or what's missing] | [Deficiency/Weakness/None] |",
        "",
        "### Non-Compliant Items",
        "",
        "For each non-compliant or partially compliant item:",
        "",
        "**Requirement [#]: [Requirement text]**",
        "",
        "- **Status**: [Non-Compliant | Partially Compliant]",
        "- **Gap Description**: [What is missing or inadequate]",
        "- **Impact**: [Deficiency or Weakness classification]",
        "- **Remediation Required**: [What must be added or changed]",
        "",
        "### Overall Compliance Assessment",
        "",
        "- **Total Requirements**: [Number]",
        "- **Fully Compliant**: [Number]",
        "- **Partially Compliant**: [Number]",
        "- **Non-Compliant**: [Number]",
        "- **Recommendation**: [Acceptable/Unacceptable for compliance]",
    ])

    return "\n".join(prompt_parts)


def get_past_performance_evaluation_prompt(
    past_performance_refs: List[Dict[str, Any]],
    requirements: Dict[str, Any],
) -> str:
    """
    Generate a prompt for past performance evaluation.

    Args:
        past_performance_refs: List of past performance references
        requirements: Current contract requirements for relevance assessment

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Past Performance Evaluation",
        "",
        "Evaluate the past performance references for relevance and quality.",
        "Assign a confidence rating per FAR 15.305(a)(2).",
        "",
        "---",
        "",
        "## Past Performance References Provided",
        "",
    ]

    for i, ref in enumerate(past_performance_refs, 1):
        prompt_parts.append(f"### Reference {i}: {ref.get('contract_name', 'N/A')}")
        prompt_parts.append("")
        prompt_parts.append(f"**Client/Agency**: {ref.get('client', 'N/A')}")
        prompt_parts.append(f"**Contract Value**: {ref.get('value', 'N/A')}")
        prompt_parts.append(f"**Period of Performance**: {ref.get('period', 'N/A')}")
        prompt_parts.append(f"**Description**: {ref.get('description', 'N/A')}")

        if ref.get('cpars_rating'):
            prompt_parts.append(f"**CPARS Rating**: {ref.get('cpars_rating')}")

        if ref.get('relevance_claim'):
            prompt_parts.append(f"**Claimed Relevance**: {ref.get('relevance_claim')}")

        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Current Contract Requirements (for Relevance Assessment)",
        "",
        f"**Contract Type**: {requirements.get('contract_type', 'N/A')}",
        f"**Estimated Value**: {requirements.get('value', 'N/A')}",
        f"**Scope**: {requirements.get('scope', 'N/A')}",
        f"**Complexity**: {requirements.get('complexity', 'N/A')}",
        "",
        "---",
        "",
        "## Required Evaluation Output",
        "",
        "### Reference-by-Reference Assessment",
        "",
        "For each reference:",
        "",
        "**Reference [#]: [Contract Name]**",
        "",
        "- **Relevance Rating**: [Very Relevant | Relevant | Somewhat Relevant | Not Relevant]",
        "- **Relevance Justification**: [Why this rating - size, scope, complexity comparison]",
        "- **Quality Assessment**: [What the performance record indicates]",
        "- **Concerns**: [Any issues with the reference]",
        "",
        "### Overall Past Performance Assessment",
        "",
        "**Confidence Rating**: [Substantial | Satisfactory | Neutral | Limited | No Confidence]",
        "",
        "**Confidence Rationale**:",
        "- [Basis for the confidence assessment]",
        "- [Key factors that influenced the rating]",
        "",
        "**Evaluator Observations**:",
        "- [What additional information would be helpful]",
        "- [What references are notably missing]",
    ])

    return "\n".join(prompt_parts)


def get_mock_evaluation_prompt(
    document_content: Dict[str, str],
    evaluation_factors: List[Dict[str, Any]],
) -> str:
    """
    Generate a prompt for a quick mock evaluation.

    Args:
        document_content: Dictionary of section names to content
        evaluation_factors: List of evaluation factors

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Quick Mock Evaluation",
        "",
        "Provide a rapid assessment of this proposal strategy as a government evaluator.",
        "Focus on the most significant findings - both positive and negative.",
        "",
        "---",
        "",
        "## Document Content",
        "",
    ]

    for section_name, content in document_content.items():
        # Truncate long content
        truncated = content[:2000] + "..." if len(content) > 2000 else content
        prompt_parts.append(f"### {section_name}")
        prompt_parts.append("")
        prompt_parts.append(truncated)
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Evaluation Factors",
        "",
    ])

    for factor in evaluation_factors:
        name = factor.get('name', 'Unknown')
        weight = factor.get('weight', '')
        prompt_parts.append(f"- {name}" + (f" ({weight}%)" if weight else ""))

    prompt_parts.extend([
        "",
        "---",
        "",
        "## Required Output (Concise)",
        "",
        "### Quick Ratings",
        "",
        "| Factor | Rating | Key Issue |",
        "|--------|--------|-----------|",
        "| [Factor] | [Rating] | [One-line summary] |",
        "",
        "### Top 3 Concerns (Potential Weaknesses/Deficiencies)",
        "",
        "1. **[Issue Title]**: [Brief description] - [Deficiency/Significant Weakness/Weakness]",
        "2. **[Issue Title]**: [Brief description] - [Classification]",
        "3. **[Issue Title]**: [Brief description] - [Classification]",
        "",
        "### Top 3 Strengths",
        "",
        "1. **[Strength Title]**: [Brief description]",
        "2. **[Strength Title]**: [Brief description]",
        "3. **[Strength Title]**: [Brief description]",
        "",
        "### Bottom Line",
        "",
        "**Overall Assessment**: [One paragraph - would you recommend this proposal?]",
        "",
        "**Win Probability Impact**: [How do these findings affect chances of winning?]",
    ])

    return "\n".join(prompt_parts)
