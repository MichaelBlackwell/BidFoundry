"""
Risk Assessor Agent Prompts

Prompt templates for the Risk Assessor agent, responsible for identifying
failure modes, stress-testing assumptions, and developing worst-case scenarios.
"""

from typing import Dict, Any, List, Optional

from agents.utils.profile_formatter import extract_certification_types


RISK_ASSESSOR_SYSTEM_PROMPT = """You are the Risk Assessor, a meticulous analyst who identifies potential failure modes in GovCon strategy documents before they become real problems.

## Your Mission
Identify risks across all categories, assess their probability and impact, require mitigation strategies for high risks, and develop worst-case scenarios that stress-test the strategy.

## Your Perspective
You are cautiously pessimistic but not paranoid. You assume that if something can go wrong, it probably will unless actively managed. You look for:
- Execution risks that could prevent delivery
- Competitive risks that could undermine win probability
- Compliance risks that could disqualify the bid
- Financial risks that could impact profitability
- External risks that could change the opportunity landscape

## Risk Categories You Assess

### Execution Risks
- Technical feasibility concerns
- Schedule and timeline risks
- Staffing and resource availability
- Transition/phase-in challenges
- Performance requirements

### Competitive Risks
- Incumbent advantages
- Competitor strengths we're underestimating
- Pricing position vulnerabilities
- Teaming arrangement risks
- Differentiation gaps

### Compliance Risks
- FAR/DFAR compliance gaps
- Set-aside eligibility questions
- OCI (Organizational Conflict of Interest) concerns
- Security clearance requirements
- Certification maintenance

### Financial Risks
- Cost estimation accuracy
- Margin and profitability concerns
- Cash flow and working capital
- Investment requirements
- Price realism challenges

### External Risks
- Political and budgetary environment
- Protest potential
- Market condition changes
- Regulatory changes
- Customer priority shifts

## Risk Assessment Standards

For each risk, you MUST provide:
1. **Clear description** - What could go wrong
2. **Trigger** - What would cause this risk to materialize
3. **Consequence** - What happens if the risk occurs
4. **Probability** - How likely is this to happen
5. **Impact** - How bad would it be if it happened
6. **Mitigation** - What can be done to prevent or reduce it

## Probability Calibration

- **Rare** (< 10%): Exceptional circumstances only
- **Low** (10-30%): Unlikely but possible
- **Medium** (30-60%): Could go either way
- **High** (60-90%): More likely than not
- **Almost Certain** (> 90%): Expected to occur

## Impact Calibration

- **Negligible**: Minor inconvenience, no material effect
- **Low**: Manageable impact, easily recoverable
- **Medium**: Moderate impact, requires effort to address
- **High**: Significant impact on win probability or execution
- **Catastrophic**: Could cause proposal rejection or contract failure

## Mitigation Requirements

For any risk with High probability OR High/Catastrophic impact:
- Mitigation is REQUIRED, not optional
- Mitigation must be specific and actionable
- Mitigation owner should be identified if possible
- Residual risk after mitigation should be noted

## Worst-Case Scenario Development

When developing worst-case scenarios:
- Be realistic, not apocalyptic
- Show the chain of events that could lead to failure
- Identify early warning signs
- Propose prevention measures
- Suggest recovery options if the worst case occurs

Your goal is to help the capture team see and address risks before they materialize. Good risk management wins contracts.

## Output Format
You MUST output risks in the following structured format - this is critical for downstream parsing:

### Risk 1: [Title]

**Category**: [Category Name]

**Description**: [What could go wrong]

**Trigger**: [What would cause it]

**Consequence**: [Impact if it occurs]

**Probability**: [Rare | Low | Medium | High | Almost Certain]

**Impact**: [Negligible | Low | Medium | High | Catastrophic]

**Source**: [Document section]

**Mitigation Required**: [Yes/No]

**Suggested Mitigation**: [How to address it]

**Residual Risk**: [Remaining risk after mitigation]

---

Repeat this format for each risk identified. Use ### Risk N: [Title] headers for each risk.
"""


def get_risk_assessment_prompt(
    document_type: str,
    document_content: Dict[str, str],
    company_profile: Optional[Dict[str, Any]] = None,
    opportunity: Optional[Dict[str, Any]] = None,
    focus_categories: Optional[List[str]] = None,
) -> str:
    """
    Generate a prompt for comprehensive risk assessment.

    Args:
        document_type: Type of document being assessed
        document_content: Dictionary of section names to content
        company_profile: Optional company profile for context
        opportunity: Optional opportunity details for context
        focus_categories: Optional list of risk categories to prioritize

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Comprehensive Risk Assessment",
        "",
        f"Analyze the following {document_type} document and identify all material risks",
        "across execution, competitive, compliance, financial, and external categories.",
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
            "## Company Context (for risk assessment)",
            "",
            f"**Company**: {company_profile.get('name', 'N/A')}",
        ])

        # Size and experience
        if company_profile.get('employee_count'):
            prompt_parts.append(f"**Size**: {company_profile.get('employee_count')} employees")

        # Certifications (potential eligibility risks)
        certs = company_profile.get('certifications', [])
        if certs:
            cert_types = extract_certification_types(certs)
            prompt_parts.append(f"**Certifications**: {', '.join(cert_types)}")

        # Past performance (execution risk indicators)
        past_perf = company_profile.get('past_performance', [])
        if past_perf:
            prompt_parts.append(f"**Past Performance**: {len(past_perf)} documented contracts")

        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    if opportunity:
        prompt_parts.extend([
            "## Opportunity Details (risk factors)",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Agency**: {opportunity.get('agency', {}).get('name', opportunity.get('agency', 'N/A'))}",
            f"**Contract Value**: {opportunity.get('estimated_value', 'N/A')}",
            f"**Period of Performance**: {opportunity.get('period_of_performance', 'N/A')}",
            "",
        ])

        # Set-aside (eligibility risk)
        if opportunity.get('set_aside'):
            prompt_parts.append(f"**Set-Aside**: {opportunity.get('set_aside')}")

        # Contract type (financial risk indicator)
        if opportunity.get('contract_type'):
            prompt_parts.append(f"**Contract Type**: {opportunity.get('contract_type')}")

        # Incumbent (competitive risk)
        if opportunity.get('incumbent'):
            prompt_parts.append(f"**Incumbent**: {opportunity.get('incumbent')}")

        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    # Focus categories if specified
    if focus_categories:
        prompt_parts.extend([
            "## Priority Risk Categories",
            "",
            "Focus particularly on these categories:",
            "",
        ])
        for cat in focus_categories:
            prompt_parts.append(f"- {cat}")
        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    # Instructions
    prompt_parts.extend([
        "## Required Risk Assessment Output",
        "",
        "For each risk identified, provide a structured assessment:",
        "",
        "### Risk [Number]: [Brief Title]",
        "",
        "**Category**: [Execution | Staffing | Technical | Compliance | Competitive | Financial | Pricing | Teaming | Transition | External]",
        "",
        "**Description**: [Clear explanation of what could go wrong]",
        "",
        "**Trigger**: [What would cause this risk to materialize]",
        "",
        "**Consequence**: [What happens if this risk occurs - impact on win/execution]",
        "",
        "**Probability**: [Rare | Low | Medium | High | Almost Certain]",
        "",
        "**Impact**: [Negligible | Low | Medium | High | Catastrophic]",
        "",
        "**Source**: [Document section where this risk was identified]",
        "",
        "**Mitigation Required**: [Yes/No]",
        "",
        "**Suggested Mitigation**: [Specific, actionable mitigation strategy]",
        "",
        "**Residual Risk**: [Risk remaining after mitigation is applied]",
        "",
        "---",
        "",
        "## Assessment Requirements",
        "",
        "1. **Identify at least one risk in each major category** (Execution, Competitive, Compliance, Financial)",
        "2. **Prioritize high-probability and high-impact risks**",
        "3. **Require mitigation for any High probability OR High/Catastrophic impact risk**",
        "4. **Be specific** - generic risks like 'things might go wrong' are not helpful",
        "5. **Be calibrated** - not everything is High/Catastrophic; use the full range",
        "",
        "## Expected Output",
        "",
        "Provide 8-15 risks covering all major categories.",
        "Include 2-3 high-severity risks that require immediate attention.",
    ])

    return "\n".join(prompt_parts)


def get_section_risk_prompt(
    section_name: str,
    section_content: str,
    document_type: str,
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for section-specific risk assessment.

    Args:
        section_name: Name of the section to assess
        section_content: Content of the section
        document_type: Type of document
        opportunity: Optional opportunity for context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Task: Section Risk Assessment - {section_name}",
        "",
        f"Perform focused risk assessment on the '{section_name}' section from a {document_type}.",
        "Identify risks specific to this section's content and claims.",
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

    # Section-specific guidance
    section_lower = section_name.lower()

    if "win theme" in section_lower or "discriminator" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Risk Focus",
            "",
            "For Win Themes/Discriminators, assess risks related to:",
            "- Can we actually deliver on these claims?",
            "- Are proof points verifiable and current?",
            "- Could competitors easily match or exceed these?",
            "- Are there execution risks in the promised approaches?",
            "- Do any claims create compliance exposure?",
            "",
        ])
    elif "competitive" in section_lower or "ghost" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Risk Focus",
            "",
            "For Competitive Analysis, assess risks related to:",
            "- Are we underestimating competitor capabilities?",
            "- Is our competitive intelligence current and accurate?",
            "- Are predicted competitor strategies realistic?",
            "- What if competitors change their approach?",
            "- Are we overconfident in our advantages?",
            "",
        ])
    elif "price" in section_lower or "cost" in section_lower or "ptw" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Risk Focus",
            "",
            "For Pricing/Cost sections, assess risks related to:",
            "- Are cost estimates realistic and complete?",
            "- Is the price-to-win achievable profitably?",
            "- What if competitors price more aggressively?",
            "- Are there hidden costs not accounted for?",
            "- Does the pricing support required investment?",
            "",
        ])
    elif "technical" in section_lower or "approach" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Risk Focus",
            "",
            "For Technical Approach, assess risks related to:",
            "- Is the approach technically feasible?",
            "- Do we have the right skills and experience?",
            "- Are there integration or interface risks?",
            "- What could cause schedule slippage?",
            "- Are technology assumptions current?",
            "",
        ])
    elif "teaming" in section_lower or "partner" in section_lower:
        prompt_parts.extend([
            "## Section-Specific Risk Focus",
            "",
            "For Teaming sections, assess risks related to:",
            "- Are teaming partners committed and capable?",
            "- What if a key partner withdraws?",
            "- Are work share arrangements sustainable?",
            "- Are there OCI or eligibility concerns?",
            "- Can we manage partner performance?",
            "",
        ])
    else:
        prompt_parts.extend([
            "## General Risk Focus",
            "",
            "Assess this section for:",
            "- Execution risks in any commitments made",
            "- Competitive risks in positioning claims",
            "- Compliance risks in any regulatory references",
            "- Financial risks in any cost-related statements",
            "",
        ])

    if opportunity:
        prompt_parts.extend([
            "---",
            "",
            "## Opportunity Context",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Value**: {opportunity.get('estimated_value', 'N/A')}",
            f"**Set-Aside**: {opportunity.get('set_aside', 'None')}",
            "",
        ])

    prompt_parts.extend([
        "---",
        "",
        "## Required Output",
        "",
        "Provide 3-5 focused risks for this section, following the standard format:",
        "",
        "### Risk [Number]: [Brief Title]",
        "",
        "**Category**: [Category]",
        "",
        "**Description**: [What could go wrong]",
        "",
        "**Trigger**: [What would cause it]",
        "",
        "**Consequence**: [Impact if it occurs]",
        "",
        "**Probability**: [Rare | Low | Medium | High | Almost Certain]",
        "",
        "**Impact**: [Negligible | Low | Medium | High | Catastrophic]",
        "",
        "**Mitigation Required**: [Yes/No]",
        "",
        "**Suggested Mitigation**: [How to address it]",
        "",
        "---",
    ])

    return "\n".join(prompt_parts)


def get_worst_case_scenario_prompt(
    risks: List[Dict[str, Any]],
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for worst-case scenario development.

    Args:
        risks: List of identified risks to build scenarios from
        opportunity: Optional opportunity context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Worst-Case Scenario Development",
        "",
        "Based on the identified risks, develop realistic worst-case scenarios",
        "that show how multiple risks could combine to cause serious problems.",
        "",
        "---",
        "",
        "## Identified Risks",
        "",
    ]

    for i, risk in enumerate(risks, 1):
        prompt_parts.append(f"### Risk {i}: {risk.get('title', 'Untitled')}")
        prompt_parts.append(f"**Category**: {risk.get('category', 'Unknown')}")
        prompt_parts.append(f"**Probability**: {risk.get('probability', 'Unknown')}")
        prompt_parts.append(f"**Impact**: {risk.get('impact', 'Unknown')}")
        prompt_parts.append(f"**Description**: {risk.get('description', 'No description')}")
        prompt_parts.append("")

    if opportunity:
        prompt_parts.extend([
            "---",
            "",
            "## Opportunity Context",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Value**: {opportunity.get('estimated_value', 'N/A')}",
            "",
        ])

    prompt_parts.extend([
        "---",
        "",
        "## Scenario Development Requirements",
        "",
        "Develop 2-3 worst-case scenarios that:",
        "- Show how identified risks could combine or cascade",
        "- Are realistic and plausible, not paranoid fantasies",
        "- Include a chain of events leading to the worst case",
        "- Identify early warning signs that would signal trouble",
        "- Propose prevention measures and recovery options",
        "",
        "## Required Output Format",
        "",
        "### Worst-Case Scenario [Number]: [Title]",
        "",
        "**Narrative**: [Detailed description of what could go wrong - tell the story]",
        "",
        "**Trigger Chain**:",
        "1. [First event/risk that triggers the scenario]",
        "2. [Second event that escalates the situation]",
        "3. [Subsequent events leading to worst case]",
        "",
        "**Contributing Risks**: [List the risk numbers that combine in this scenario]",
        "",
        "**Impacts**:",
        "- **Win Probability**: [Effect on likelihood of winning]",
        "- **Financial**: [Potential financial consequences]",
        "- **Reputation**: [Effect on company standing]",
        "- **Strategic**: [Long-term consequences]",
        "",
        "**Early Warning Signs**:",
        "- [Sign 1]",
        "- [Sign 2]",
        "",
        "**Prevention Measures**:",
        "- [Measure 1]",
        "- [Measure 2]",
        "",
        "**Recovery Options** (if worst case occurs):",
        "- [Option 1]",
        "- [Option 2]",
        "",
        "**Plausibility**: [Low | Medium | High]",
        "",
        "**Severity**: [Medium | High | Catastrophic]",
        "",
        "---",
        "",
        "Focus on scenarios that are plausible enough to warrant attention",
        "but severe enough to justify proactive risk management.",
    ])

    return "\n".join(prompt_parts)


def get_stress_test_prompt(
    assumptions: List[Dict[str, str]],
    strategy_summary: str,
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for stress-testing strategy assumptions.

    Args:
        assumptions: List of assumptions to stress-test
        strategy_summary: Summary of the overall strategy
        opportunity: Optional opportunity context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Strategy Stress Test",
        "",
        "Stress-test the following strategy by systematically examining",
        "what happens if key assumptions prove incorrect.",
        "",
        "---",
        "",
        "## Strategy Summary",
        "",
        strategy_summary,
        "",
        "---",
        "",
        "## Assumptions to Stress-Test",
        "",
    ]

    for i, assumption in enumerate(assumptions, 1):
        prompt_parts.append(f"### Assumption {i}")
        prompt_parts.append(f"**Statement**: \"{assumption.get('statement', 'No statement')}\"")
        if assumption.get('source'):
            prompt_parts.append(f"**Source**: {assumption.get('source')}")
        prompt_parts.append("")

    if opportunity:
        prompt_parts.extend([
            "---",
            "",
            "## Opportunity Context",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
            f"**Agency**: {opportunity.get('agency', 'N/A')}",
            "",
        ])

    prompt_parts.extend([
        "---",
        "",
        "## Stress Test Requirements",
        "",
        "For each assumption, analyze:",
        "1. What if this assumption is completely wrong?",
        "2. How would the strategy need to change?",
        "3. What's the impact on win probability?",
        "4. What early indicators would show the assumption failing?",
        "",
        "## Required Output Format",
        "",
        "### Assumption [Number] Stress Test",
        "",
        "**Assumption**: [Quote the assumption]",
        "",
        "**Stress Scenario**: [What if this assumption is wrong?]",
        "",
        "**Strategy Impact**: [How would the strategy need to change?]",
        "",
        "**Win Probability Effect**: [Impact on likelihood of winning]",
        "",
        "**Vulnerability Level**: [Low | Medium | High | Critical]",
        "",
        "**Early Warning Indicators**:",
        "- [Indicator 1]",
        "- [Indicator 2]",
        "",
        "**Contingency Recommendation**: [What should be prepared as a backup?]",
        "",
        "---",
        "",
        "Focus on assumptions that, if wrong, would significantly",
        "impact the viability of the overall strategy.",
    ])

    return "\n".join(prompt_parts)


def get_mitigation_evaluation_prompt(
    risk: Dict[str, Any],
    proposed_mitigation: Dict[str, Any],
) -> str:
    """
    Generate a prompt for evaluating proposed risk mitigation.

    Args:
        risk: The risk being mitigated
        proposed_mitigation: The proposed mitigation approach

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Mitigation Evaluation",
        "",
        "Evaluate whether the proposed mitigation adequately addresses the identified risk.",
        "",
        "---",
        "",
        "## Risk Being Mitigated",
        "",
        f"**Title**: {risk.get('title', 'N/A')}",
        f"**Category**: {risk.get('category', 'N/A')}",
        f"**Description**: {risk.get('description', 'N/A')}",
        f"**Probability**: {risk.get('probability', 'N/A')}",
        f"**Impact**: {risk.get('impact', 'N/A')}",
        f"**Trigger**: {risk.get('trigger', 'N/A')}",
        f"**Consequence**: {risk.get('consequence', 'N/A')}",
        "",
        "---",
        "",
        "## Proposed Mitigation",
        "",
        f"**Strategy**: {proposed_mitigation.get('strategy', 'N/A')}",
        f"**Owner**: {proposed_mitigation.get('owner', 'N/A')}",
        f"**Timeline**: {proposed_mitigation.get('timeline', 'N/A')}",
        f"**Resources Required**: {proposed_mitigation.get('resources', 'N/A')}",
        "",
        "---",
        "",
        "## Evaluation Criteria",
        "",
        "Evaluate the mitigation against these criteria:",
        "",
        "1. **Effectiveness**: Does it actually reduce probability or impact?",
        "2. **Feasibility**: Can it realistically be implemented?",
        "3. **Timeliness**: Will it be in place when needed?",
        "4. **Completeness**: Does it address the root cause?",
        "5. **Side Effects**: Does it create new risks?",
        "",
        "---",
        "",
        "## Required Output",
        "",
        "### Mitigation Evaluation",
        "",
        "**Verdict**: [Adequate | Insufficient | Partially Adequate]",
        "",
        "**Effectiveness Assessment**: [Does it actually reduce the risk?]",
        "",
        "**Feasibility Assessment**: [Can it be implemented?]",
        "",
        "**Residual Risk After Mitigation**:",
        "- **New Probability**: [Rare | Low | Medium | High | Almost Certain]",
        "- **New Impact**: [Negligible | Low | Medium | High | Catastrophic]",
        "",
        "**Gaps Identified**: [What's missing from the mitigation?]",
        "",
        "**Improvement Recommendations**: [How to strengthen the mitigation]",
        "",
        "**New Risks Created**: [Any risks introduced by the mitigation itself]",
        "",
        "---",
    ]

    return "\n".join(prompt_parts)


def get_risk_response_evaluation_prompt(
    risk: Dict[str, Any],
    response: Dict[str, Any],
) -> str:
    """
    Generate a prompt for evaluating blue team response to a risk.

    Args:
        risk: The risk that was raised
        response: The blue team's response

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Risk Response Evaluation",
        "",
        "Evaluate whether the Blue Team's response adequately addresses the risk.",
        "",
        "---",
        "",
        "## Risk Raised",
        "",
        f"**Title**: {risk.get('title', 'N/A')}",
        f"**Category**: {risk.get('category', 'N/A')}",
        f"**Probability**: {risk.get('probability', 'N/A')}",
        f"**Impact**: {risk.get('impact', 'N/A')}",
        f"**Description**: {risk.get('description', 'N/A')}",
        f"**Suggested Mitigation**: {risk.get('suggested_mitigation', 'N/A')}",
        "",
        "---",
        "",
        "## Blue Team Response",
        "",
        f"**Disposition**: {response.get('disposition', 'N/A')}",
        f"**Action**: {response.get('action', 'N/A')}",
    ]

    if response.get('evidence'):
        prompt_parts.append(f"**Evidence**: {response.get('evidence')}")

    if response.get('mitigation_plan'):
        prompt_parts.append(f"**Mitigation Plan**: {response.get('mitigation_plan')}")

    if response.get('residual_risk'):
        prompt_parts.append(f"**Acknowledged Residual Risk**: {response.get('residual_risk')}")

    prompt_parts.extend([
        "",
        "---",
        "",
        "## Evaluation Criteria",
        "",
        "A response is **Acceptable** if:",
        "- It acknowledges the risk appropriately",
        "- It provides a credible mitigation plan",
        "- It honestly assesses residual risk",
        "- It assigns clear ownership for mitigation",
        "",
        "A response is **Insufficient** if:",
        "- It dismisses the risk without justification",
        "- It proposes inadequate mitigation",
        "- It ignores significant aspects of the risk",
        "- It creates new risks through the proposed action",
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
        "**Risk Status After Response**:",
        "- **Residual Probability**: [Level if response implemented]",
        "- **Residual Impact**: [Level if response implemented]",
        "",
        "**Strengths**: [What the response does well]",
        "",
        "**Weaknesses**: [What could be improved]",
        "",
        "**Follow-Up Required**: [Yes/No - if yes, what specifically]",
        "",
        "**Resolution Status**: [Resolved | Needs Further Work | Escalate]",
        "",
        "---",
    ])

    return "\n".join(prompt_parts)
