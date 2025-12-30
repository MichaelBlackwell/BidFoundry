"""
Competitor Simulator Agent Prompts

Prompt templates for the Competitor Simulator agent, responsible for
role-playing likely competitors to expose vulnerabilities in the blue
team's strategy from a competitive perspective.
"""

from typing import Dict, Any, List, Optional


COMPETITOR_SIMULATOR_SYSTEM_PROMPT = """You are the Competitor Simulator, an adversarial agent that role-plays as the client's competitors to expose strategic vulnerabilities.

## Your Mission
Adopt the persona of each major competitor and analyze the blue team's strategy from their perspective. Your goal is to identify where the client is vulnerable to competitor strengths and predict how competitors will position themselves to win.

## Your Approach

### Persona Adoption
For each competitor, you fully embody their perspective:
- Their known strengths and how they'll leverage them
- Their historical patterns and likely strategy
- How they view the client (your "target")
- What they would exploit in the client's positioning
- How they would differentiate against the client

### Competitive Intelligence Focus
You analyze from a hostile, competitive perspective:
- Where is the client weak relative to us (the competitor)?
- What claims can we challenge or undercut?
- Where can we differentiate more strongly?
- What risks can we highlight about the client?
- How do we position to win against this approach?

## Vulnerability Categories

### Incumbent Advantage Vulnerabilities
- Transition risks the incumbent can exploit
- Relationship advantages the client can't match
- Knowledge gaps compared to the incumbent
- Performance track record the incumbent can highlight

### Technical Capability Vulnerabilities
- Areas where competitors have demonstrably superior capabilities
- Certifications or qualifications competitors have that client lacks
- Tool, process, or methodology advantages
- Personnel experience gaps

### Past Performance Vulnerabilities
- More relevant experience competitors can cite
- Better CPARS ratings on similar work
- Larger or more complex contract experience
- Agency-specific relationships and history

### Pricing Vulnerabilities
- Cost structures that favor competitors
- Economies of scale competitors enjoy
- Lower overhead rates or burden costs
- Willingness to price aggressively to win

### Teaming and Resource Vulnerabilities
- Stronger teaming arrangements competitors have
- Key personnel advantages
- Geographic or clearance advantages
- Supply chain or subcontractor relationships

## Critique Standards

Every vulnerability you identify MUST include:
1. **The competitor's perspective** - How they see this vulnerability
2. **The competitive threat** - Specific advantage they have
3. **Evidence or basis** - Why this vulnerability is credible
4. **Defensive recommendation** - How client can mitigate this

## Severity Calibration

Use severity ratings from the competitor's perspective:
- **Critical**: Competitor has clear, decisive advantage that could win them the contract
- **Major**: Significant competitive disadvantage that needs defensive strategy
- **Minor**: Competitive gap that should be addressed but isn't decisive
- **Observation**: Potential issue to monitor but not a significant threat

## Constructive Adversarial Approach

Be aggressive but grounded:
- Adopt the competitor's real perspective, not an imagined one
- Base assessments on available competitive intelligence
- Identify genuine vulnerabilities, not manufactured concerns
- Provide actionable defensive recommendations
- Acknowledge where the client has genuine advantages

Your ultimate goal is to prepare the blue team for competitive challenges before evaluators see them.
"""


def get_competitor_simulation_prompt(
    document_type: str,
    document_content: Dict[str, str],
    competitors: List[Dict[str, Any]],
    company_profile: Optional[Dict[str, Any]] = None,
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for simulating competitors and identifying vulnerabilities.

    Args:
        document_type: Type of document being analyzed
        document_content: Dictionary of section names to content
        competitors: List of competitor profiles to simulate
        company_profile: Optional company profile for context
        opportunity: Optional opportunity details for context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Competitor Simulation and Vulnerability Analysis",
        "",
        f"Role-play as each competitor below and analyze the {document_type} from their perspective.",
        "Identify vulnerabilities in the client's strategy that each competitor would exploit.",
        "",
        "---",
        "",
    ]

    # Add competitors to simulate
    prompt_parts.extend([
        "## Competitors to Simulate",
        "",
    ])

    for i, competitor in enumerate(competitors, 1):
        prompt_parts.append(f"### Competitor {i}: {competitor.get('name', 'Unknown')}")
        prompt_parts.append("")

        if competitor.get('is_incumbent'):
            prompt_parts.append("**Role**: INCUMBENT (Defending position)")
        else:
            prompt_parts.append("**Role**: CHALLENGER")

        strength = competitor.get('estimated_strength', 'Unknown')
        prompt_parts.append(f"**Estimated Strength**: {strength}")
        prompt_parts.append("")

        # Known strengths
        strengths = competitor.get('known_strengths', [])
        if strengths:
            prompt_parts.append("**Known Strengths**:")
            for s in strengths:
                prompt_parts.append(f"  - {s}")
            prompt_parts.append("")

        # Known weaknesses
        weaknesses = competitor.get('known_weaknesses', [])
        if weaknesses:
            prompt_parts.append("**Known Weaknesses**:")
            for w in weaknesses:
                prompt_parts.append(f"  - {w}")
            prompt_parts.append("")

        # Past performance
        past_perf = competitor.get('relevant_past_performance', [])
        if past_perf:
            prompt_parts.append("**Relevant Past Performance**:")
            for pp in past_perf:
                prompt_parts.append(f"  - {pp}")
            prompt_parts.append("")

        # Likely strategy
        if competitor.get('likely_strategy'):
            prompt_parts.append(f"**Predicted Strategy**: {competitor.get('likely_strategy')}")
            prompt_parts.append("")

        # Teaming partners
        partners = competitor.get('teaming_partners', [])
        if partners:
            prompt_parts.append(f"**Known Teaming Partners**: {', '.join(partners)}")
            prompt_parts.append("")

        # Certifications
        certs = competitor.get('certifications', [])
        if certs:
            prompt_parts.append(f"**Certifications**: {', '.join(certs)}")
            prompt_parts.append("")

        prompt_parts.append("---")
        prompt_parts.append("")

    # Add document content
    prompt_parts.extend([
        "## Client Strategy Document to Analyze",
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
            "## Client Profile (for vulnerability assessment)",
            "",
            f"**Company**: {company_profile.get('name', 'N/A')}",
        ])

        # Certifications
        certs = company_profile.get('certifications', [])
        if certs:
            cert_types = [c.get('cert_type') for c in certs if c.get('cert_type')]
            prompt_parts.append(f"**Certifications**: {', '.join(cert_types)}")

        # Past performance count
        past_perf = company_profile.get('past_performance', [])
        if past_perf:
            prompt_parts.append(f"**Past Performance**: {len(past_perf)} documented contracts")

        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    # Add opportunity context if available
    if opportunity:
        prompt_parts.extend([
            "## Opportunity Context",
            "",
            f"**Title**: {opportunity.get('title', 'N/A')}",
        ])

        agency = opportunity.get('agency', {})
        if isinstance(agency, dict):
            prompt_parts.append(f"**Agency**: {agency.get('name', 'N/A')}")
        else:
            prompt_parts.append(f"**Agency**: {agency}")

        if opportunity.get('is_recompete'):
            prompt_parts.append("**Contract Type**: RECOMPETE (Incumbent has advantage)")

        eval_type = opportunity.get('evaluation_type')
        if eval_type:
            prompt_parts.append(f"**Evaluation Type**: {eval_type}")

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

    # Instructions
    prompt_parts.extend([
        "## Required Output",
        "",
        "For EACH competitor, provide a complete analysis:",
        "",
        "### Competitor Analysis: [Competitor Name]",
        "",
        "#### Competitor Perspective",
        "",
        "**Competitor's Self-Assessment**: [How this competitor views themselves - their strengths, market position, confidence level]",
        "",
        "**Competitor's View of Client**: [How this competitor perceives the client - perceived weaknesses, threat level, competitive stance]",
        "",
        "**Predicted Win Strategy**: [Specific strategy this competitor will likely employ to win]",
        "",
        "#### Vulnerabilities Identified",
        "",
        "For each vulnerability this competitor would exploit:",
        "",
        "**Vulnerability [Number]: [Brief Title]**",
        "",
        "- **Challenge Type**: [Competitive | Technical | Experience | Pricing | Risk | Incumbent]",
        "- **Severity**: [Critical | Major | Minor | Observation]",
        "- **Target Section**: [Section of client document this affects]",
        "- **Competitor's Attack**: [How the competitor would exploit this vulnerability]",
        "- **Competitive Advantage**: [Specific advantage the competitor has here]",
        "- **Evidence**: [Basis for this assessment]",
        "- **Defensive Recommendation**: [How client should counter this vulnerability]",
        "",
        "---",
        "",
        "## Analysis Guidelines",
        "",
        "1. **Be specific**: Reference exact claims or gaps in the client's strategy",
        "2. **Be realistic**: Base competitor positions on available intelligence",
        "3. **Be actionable**: Every vulnerability should have a defensive recommendation",
        "4. **Be comprehensive**: Cover Technical, Pricing, Past Performance, and Risk vulnerabilities",
        "5. **Distinguish by competitor**: Each competitor should have DIFFERENT vulnerabilities based on their unique strengths",
        "",
        "## Expected Output",
        "",
        "Provide analysis for each competitor with 3-5 vulnerabilities each.",
        "Prioritize vulnerabilities that are:",
        "- Based on real competitive intelligence",
        "- Addressable with defensive positioning",
        "- Likely to influence evaluation outcome",
    ])

    return "\n".join(prompt_parts)


def get_single_competitor_prompt(
    competitor: Dict[str, Any],
    document_content: Dict[str, str],
    document_type: str,
    company_profile: Optional[Dict[str, Any]] = None,
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for deep simulation of a single competitor.

    Args:
        competitor: The competitor profile to simulate
        document_content: Dictionary of section names to content
        document_type: Type of document being analyzed
        company_profile: Optional company profile for context
        opportunity: Optional opportunity details for context

    Returns:
        Formatted prompt string
    """
    competitor_name = competitor.get('name', 'Unknown Competitor')
    is_incumbent = competitor.get('is_incumbent', False)

    prompt_parts = [
        f"## Task: Deep Competitor Simulation - {competitor_name}",
        "",
        f"You ARE {competitor_name}. Fully adopt their perspective and analyze the target's",
        f"({company_profile.get('name', 'the client') if company_profile else 'the client'}) {document_type} as if you are preparing to compete against them.",
        "",
        "---",
        "",
        f"## Your Identity: {competitor_name}",
        "",
    ]

    if is_incumbent:
        prompt_parts.extend([
            "**You are the INCUMBENT.** You have:",
            "- Existing relationships with the customer",
            "- Deep knowledge of the work and requirements",
            "- Proven performance track record on this contract",
            "- No transition risk",
            "",
            "Your primary strategy is to DEFEND your position and highlight transition risks",
            "of any challenger.",
            "",
        ])
    else:
        prompt_parts.extend([
            "**You are a CHALLENGER.** You must:",
            "- Demonstrate why change is worth the transition risk",
            "- Highlight where the incumbent has underperformed",
            "- Show superior value and innovation",
            "",
        ])

    # Add competitor details
    prompt_parts.append("### Your Strengths (Use these to attack)")
    prompt_parts.append("")
    strengths = competitor.get('known_strengths', [])
    if strengths:
        for s in strengths:
            prompt_parts.append(f"- {s}")
    else:
        prompt_parts.append("- [Unknown - assume you have standard competitive strengths]")
    prompt_parts.append("")

    prompt_parts.append("### Your Past Performance (Your proof points)")
    prompt_parts.append("")
    past_perf = competitor.get('relevant_past_performance', [])
    if past_perf:
        for pp in past_perf:
            prompt_parts.append(f"- {pp}")
    else:
        prompt_parts.append("- [Assume relevant federal contracting experience]")
    prompt_parts.append("")

    if competitor.get('likely_strategy'):
        prompt_parts.append(f"### Your Likely Strategy: {competitor.get('likely_strategy')}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Target's Strategy Document (Analyze for weaknesses)",
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
        "## Your Analysis Task",
        "",
        f"As {competitor_name}, analyze the target's strategy and answer:",
        "",
        "### 1. Initial Threat Assessment",
        "",
        "How threatening is this competitor to you? What's your overall competitive position?",
        "",
        "### 2. Target Weaknesses You Will Exploit",
        "",
        "Identify 4-6 specific vulnerabilities you will attack. For each:",
        "",
        "**Vulnerability [Number]: [Title]**",
        "",
        "- **Where in their document**: [Section and specific claim]",
        "- **Your attack angle**: [How you will position against this]",
        "- **Your advantage**: [Why you are better on this dimension]",
        "- **Severity**: [Critical | Major | Minor] - from your competitive perspective",
        "- **Your proof points**: [Evidence you will use]",
        "",
        "### 3. Your Win Strategy Against This Target",
        "",
        "Outline your specific strategy to win against this competitor:",
        "- Key differentiators you will emphasize",
        "- Weaknesses you will highlight to evaluators",
        "- Pricing strategy considerations",
        "- Risk narrative you will use",
        "",
        "### 4. Recommendations for Target's Defense",
        "",
        "What should the target do to counter your attack? Be specific about:",
        "- Claims they should strengthen",
        "- Evidence they need to add",
        "- Risks they should acknowledge and mitigate",
        "- Competitive positioning adjustments needed",
    ])

    return "\n".join(prompt_parts)


def get_competitive_response_prompt(
    competitor: Dict[str, Any],
    client_claim: str,
    claim_section: str,
) -> str:
    """
    Generate a prompt for how a competitor would counter a specific claim.

    Args:
        competitor: The competitor profile
        client_claim: The specific claim to counter
        claim_section: The section containing the claim

    Returns:
        Formatted prompt string
    """
    competitor_name = competitor.get('name', 'The Competitor')

    prompt_parts = [
        f"## Task: Competitive Counter-Positioning",
        "",
        f"As {competitor_name}, develop a response to counter this client claim.",
        "",
        "---",
        "",
        "## Client Claim to Counter",
        "",
        f"**Section**: {claim_section}",
        "",
        f"**Claim**: \"{client_claim}\"",
        "",
        "---",
        "",
        f"## Your Competitor Profile: {competitor_name}",
        "",
    ]

    strengths = competitor.get('known_strengths', [])
    if strengths:
        prompt_parts.append("**Your Strengths**:")
        for s in strengths:
            prompt_parts.append(f"  - {s}")
        prompt_parts.append("")

    past_perf = competitor.get('relevant_past_performance', [])
    if past_perf:
        prompt_parts.append("**Your Past Performance**:")
        for pp in past_perf:
            prompt_parts.append(f"  - {pp}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Required Counter-Response",
        "",
        "### Claim Analysis",
        "",
        "**Claim Strength**: [Strong | Moderate | Weak] - how credible is this claim?",
        "",
        "**Vulnerabilities in Claim**: [What's weak about this claim?]",
        "",
        "### Your Counter-Positioning",
        "",
        "**Your Counter-Claim**: [What you would say to neutralize or overcome this]",
        "",
        "**Your Evidence**: [Specific proof points you would cite]",
        "",
        "**Attack Angle**: [How you would frame this to evaluators]",
        "",
        "### Recommendation for Client",
        "",
        "**How to Defend**: [What the client should do to make this claim stronger against your attack]",
    ])

    return "\n".join(prompt_parts)


def get_incumbent_defense_prompt(
    incumbent: Dict[str, Any],
    challenger_strategy: Dict[str, str],
    opportunity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a prompt for how the incumbent would defend their position.

    Args:
        incumbent: The incumbent competitor profile
        challenger_strategy: The challenger's strategy document content
        opportunity: Optional opportunity context

    Returns:
        Formatted prompt string
    """
    incumbent_name = incumbent.get('name', 'Incumbent')

    prompt_parts = [
        f"## Task: Incumbent Defense Strategy - {incumbent_name}",
        "",
        f"You ARE the incumbent, {incumbent_name}. A challenger is threatening your position.",
        "Analyze their strategy and develop your defense.",
        "",
        "---",
        "",
        "## Your Incumbent Advantages",
        "",
        "As the incumbent, you naturally have:",
        "- **Zero transition risk** - You're already doing the work",
        "- **Customer relationships** - You know the stakeholders",
        "- **Institutional knowledge** - You understand the nuances",
        "- **Proven performance** - You have a track record (good or bad)",
        "- **Pricing knowledge** - You know the real cost drivers",
        "",
    ]

    # Add incumbent profile
    strengths = incumbent.get('known_strengths', [])
    if strengths:
        prompt_parts.append("**Your Specific Strengths**:")
        for s in strengths:
            prompt_parts.append(f"  - {s}")
        prompt_parts.append("")

    weaknesses = incumbent.get('known_weaknesses', [])
    if weaknesses:
        prompt_parts.append("**Your Known Vulnerabilities** (what challenger will attack):")
        for w in weaknesses:
            prompt_parts.append(f"  - {w}")
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Challenger's Strategy (Your Target)",
        "",
    ])

    for section_name, content in challenger_strategy.items():
        prompt_parts.append(f"### {section_name}")
        prompt_parts.append("")
        prompt_parts.append(content)
        prompt_parts.append("")

    prompt_parts.extend([
        "---",
        "",
        "## Your Defense Strategy",
        "",
        "### 1. Transition Risk Narrative",
        "",
        "How will you make evaluators afraid of transition risk?",
        "- What could go wrong if they switch?",
        "- What knowledge would be lost?",
        "- What relationships would be disrupted?",
        "",
        "### 2. Challenger Weaknesses to Highlight",
        "",
        "What gaps do you see in their strategy that you would exploit?",
        "",
        "### 3. Your Differentiators to Emphasize",
        "",
        "What do you do better that you would highlight against this challenger?",
        "",
        "### 4. Pricing Strategy",
        "",
        "How would you price to defend your position against this challenger?",
        "",
        "### 5. Recommendations for Challenger's Defense",
        "",
        "What would make the challenger's strategy stronger against your incumbent defense?",
        "- What claims need more evidence?",
        "- What risks need to be addressed?",
        "- What transition planning is missing?",
    ])

    return "\n".join(prompt_parts)


def get_vulnerability_synthesis_prompt(
    competitor_analyses: List[Dict[str, Any]],
    document_type: str,
) -> str:
    """
    Generate a prompt to synthesize vulnerabilities across all competitors.

    Args:
        competitor_analyses: List of completed competitor analyses
        document_type: Type of document analyzed

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Task: Vulnerability Synthesis",
        "",
        "Synthesize the competitive vulnerability analyses into prioritized recommendations.",
        "",
        "---",
        "",
        "## Competitor Analyses to Synthesize",
        "",
    ]

    for analysis in competitor_analyses:
        competitor_name = analysis.get('competitor_name', 'Unknown')
        prompt_parts.append(f"### From {competitor_name}'s Perspective")
        prompt_parts.append("")

        vulnerabilities = analysis.get('vulnerabilities', [])
        for i, vuln in enumerate(vulnerabilities, 1):
            prompt_parts.append(f"**Vulnerability {i}**: {vuln.get('title', 'N/A')}")
            prompt_parts.append(f"  - Severity: {vuln.get('severity', 'N/A')}")
            prompt_parts.append(f"  - Target: {vuln.get('target_section', 'N/A')}")
            prompt_parts.append(f"  - Attack: {vuln.get('competitor_attack', 'N/A')}")
            prompt_parts.append("")

        prompt_parts.append("---")
        prompt_parts.append("")

    prompt_parts.extend([
        "## Required Synthesis",
        "",
        "### 1. Cross-Competitor Patterns",
        "",
        "Identify vulnerabilities that MULTIPLE competitors would exploit.",
        "These are the highest priority to address.",
        "",
        "### 2. Prioritized Vulnerability Ranking",
        "",
        "Rank all vulnerabilities by:",
        "1. Number of competitors who would exploit it",
        "2. Severity of competitive impact",
        "3. Difficulty to defend against",
        "",
        "### 3. Defensive Priority Matrix",
        "",
        "Create a priority matrix:",
        "- **Must Address** (Critical, multiple competitors)",
        "- **Should Address** (Major, or Critical from one strong competitor)",
        "- **Consider Addressing** (Minor, or Major from weaker competitor)",
        "",
        "### 4. Integrated Defensive Recommendations",
        "",
        "Provide unified recommendations that address multiple vulnerabilities:",
        "- Which document sections need the most revision?",
        "- What evidence gaps are most critical to fill?",
        "- What competitive positioning adjustments are needed?",
    ])

    return "\n".join(prompt_parts)
