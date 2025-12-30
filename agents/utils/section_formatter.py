"""
Section Formatter Utilities

Common formatting utilities for blue team agents to format analysis results
into structured markdown sections.
"""

from typing import Any, Dict, List, Optional


class SectionFormatter:
    """
    Utility class for formatting analysis results into markdown sections.

    Provides common patterns used across blue team agents for consistent
    section formatting.
    """

    def __init__(self) -> None:
        """Initialize the section formatter."""
        self._parts: List[str] = []

    def reset(self) -> "SectionFormatter":
        """Reset the formatter for a new section."""
        self._parts = []
        return self

    def add_header(self, title: str, level: int = 2) -> "SectionFormatter":
        """Add a header line."""
        prefix = "#" * level
        self._parts.append(f"{prefix} {title}")
        self._parts.append("")
        return self

    def add_subheader(self, title: str, level: int = 3) -> "SectionFormatter":
        """Add a subheader line."""
        return self.add_header(title, level)

    def add_field(self, label: str, value: Any, bold_label: bool = True) -> "SectionFormatter":
        """Add a labeled field."""
        if value is not None and value != "":
            if bold_label:
                self._parts.append(f"**{label}**: {value}")
            else:
                self._parts.append(f"{label}: {value}")
            self._parts.append("")
        return self

    def add_text(self, text: str) -> "SectionFormatter":
        """Add plain text."""
        if text:
            self._parts.append(text)
            self._parts.append("")
        return self

    def add_bullet(self, text: str) -> "SectionFormatter":
        """Add a bullet point."""
        if text:
            self._parts.append(f"- {text}")
        return self

    def add_numbered(self, index: int, text: str) -> "SectionFormatter":
        """Add a numbered item."""
        if text:
            self._parts.append(f"{index}. {text}")
        return self

    def add_bullets(self, items: List[str], header: Optional[str] = None) -> "SectionFormatter":
        """Add a list of bullet points with optional header."""
        if not items:
            return self
        if header:
            self._parts.append(f"**{header}**:")
        for item in items:
            self._parts.append(f"- {item}")
        self._parts.append("")
        return self

    def add_numbered_list(self, items: List[str], header: Optional[str] = None) -> "SectionFormatter":
        """Add a numbered list with optional header."""
        if not items:
            return self
        if header:
            self._parts.append(f"**{header}**:")
        for i, item in enumerate(items, 1):
            self._parts.append(f"{i}. {item}")
        self._parts.append("")
        return self

    def add_separator(self) -> "SectionFormatter":
        """Add a horizontal separator."""
        self._parts.append("---")
        self._parts.append("")
        return self

    def add_blank_line(self) -> "SectionFormatter":
        """Add a blank line."""
        self._parts.append("")
        return self

    def build(self) -> str:
        """Build and return the formatted section."""
        return "\n".join(self._parts)


def format_section_header(title: str, level: int = 2) -> str:
    """Format a section header."""
    prefix = "#" * level
    return f"{prefix} {title}\n"


def format_field(label: str, value: Any, bold_label: bool = True) -> str:
    """Format a labeled field."""
    if value is None or value == "":
        return ""
    if bold_label:
        return f"**{label}**: {value}\n"
    return f"{label}: {value}\n"


def format_bullet_list(items: List[str], header: Optional[str] = None) -> str:
    """Format a bullet list with optional header."""
    if not items:
        return ""
    parts = []
    if header:
        parts.append(f"**{header}**:")
    for item in items:
        parts.append(f"- {item}")
    parts.append("")
    return "\n".join(parts)


def format_numbered_list(items: List[str], header: Optional[str] = None) -> str:
    """Format a numbered list with optional header."""
    if not items:
        return ""
    parts = []
    if header:
        parts.append(f"**{header}**:")
    for i, item in enumerate(items, 1):
        parts.append(f"{i}. {item}")
    parts.append("")
    return "\n".join(parts)


# --- Capture Strategist Section Formatters ---

def format_win_themes_section(win_themes: List[Any]) -> str:
    """Format win themes as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Win Themes")

    for i, theme in enumerate(win_themes, 1):
        fmt.add_subheader(f"Win Theme {i}: {theme.title}")
        fmt.add_field("Theme Statement", theme.theme_statement)

        if theme.supporting_evidence:
            fmt.add_bullets(theme.supporting_evidence, "Supporting Evidence")

        if theme.customer_benefit:
            fmt.add_field("Customer Benefit", theme.customer_benefit)

        if theme.evaluation_criteria_alignment:
            fmt.add_field("Evaluation Alignment", ", ".join(theme.evaluation_criteria_alignment))

        if theme.competitive_advantage:
            fmt.add_field("Competitive Advantage", theme.competitive_advantage)

        fmt.add_separator()

    return fmt.build()


def format_discriminators_section(discriminators: List[Any]) -> str:
    """Format discriminators as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Discriminators")

    for i, disc in enumerate(discriminators, 1):
        fmt.add_subheader(f"Discriminator {i}: {disc.title}")
        fmt.add_field("Type", disc.discriminator_type)
        fmt.add_field("Description", disc.description)

        if disc.proof_point:
            fmt.add_field("Proof Point", disc.proof_point)

        if disc.evaluation_factor_link:
            fmt.add_field("Evaluation Factor Link", ", ".join(disc.evaluation_factor_link))

        if disc.competitor_gap:
            fmt.add_field("Competitor Gap", disc.competitor_gap)

        if disc.messaging_guidance:
            fmt.add_field("Messaging", f'"{disc.messaging_guidance}"')

        fmt.add_separator()

    return fmt.build()


def format_ghost_team_section(ghost_team_analyses: List[Any], universal_counter_themes: Optional[List[str]] = None) -> str:
    """Format ghost team analysis as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Ghost Team Analysis")

    for analysis in ghost_team_analyses:
        incumbent_tag = " (INCUMBENT)" if analysis.is_incumbent else ""
        fmt.add_subheader(f"{analysis.competitor_name}{incumbent_tag}")

        if analysis.predicted_win_themes:
            fmt._parts.append("**Predicted Win Themes**:")
            for j, theme in enumerate(analysis.predicted_win_themes, 1):
                fmt.add_numbered(j, theme)
            fmt.add_blank_line()

        if analysis.predicted_pricing_strategy:
            fmt.add_field("Pricing Strategy", analysis.predicted_pricing_strategy)

        if analysis.counter_strategies:
            fmt.add_bullets(analysis.counter_strategies, "Our Counter-Strategy")

        fmt.add_separator()

    if universal_counter_themes:
        fmt.add_header("Universal Counter-Themes")
        for theme in universal_counter_themes:
            fmt.add_bullet(theme)
        fmt.add_blank_line()

    return fmt.build()


def format_price_to_win_section(price_to_win: Any) -> str:
    """Format price-to-win guidance as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Price-to-Win Guidance")

    if price_to_win:
        fmt.add_field("Recommended Positioning", price_to_win.recommended_positioning)

        if price_to_win.market_price_range:
            fmt._parts.append("**Market Price Range**:")
            for level, value in price_to_win.market_price_range.items():
                fmt.add_bullet(f"{level.capitalize()}: ${value:,.0f}M")
            fmt.add_blank_line()

        if price_to_win.strategic_recommendations:
            fmt.add_bullets(price_to_win.strategic_recommendations, "Strategic Recommendations")

        if price_to_win.risk_assessment:
            fmt.add_field("Risk Assessment", price_to_win.risk_assessment)

    return fmt.build()


def format_capture_comprehensive_section(result: Any) -> str:
    """Format comprehensive capture strategy as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Capture Strategy Summary")

    if result.executive_summary:
        fmt.add_subheader("Executive Summary")
        fmt.add_text(result.executive_summary)

    fmt.add_field("Win Probability", result.win_probability)

    if result.critical_success_factors:
        fmt.add_subheader("Critical Success Factors")
        for csf in result.critical_success_factors:
            fmt.add_bullet(csf)
        fmt.add_blank_line()

    if result.win_themes:
        fmt.add_subheader("Win Themes")
        for theme in result.win_themes:
            statement = theme.theme_statement[:100] + "..." if len(theme.theme_statement) > 100 else theme.theme_statement
            fmt.add_bullet(f"**{theme.title}**: {statement}")
        fmt.add_blank_line()

    if result.discriminators:
        fmt.add_subheader("Top Discriminators")
        for disc in result.discriminators[:5]:
            fmt.add_bullet(f"**{disc.title}** ({disc.discriminator_type})")
        fmt.add_blank_line()

    if result.price_to_win:
        fmt.add_subheader(f"Pricing Recommendation: {result.price_to_win.recommended_positioning}")

    if result.risks:
        fmt.add_subheader("Key Risks")
        for risk in result.risks[:5]:
            fmt.add_bullet(f"**{risk.get('risk', 'Unknown')}** ({risk.get('probability', 'Unknown')} probability)")
        fmt.add_blank_line()

    if result.action_items:
        fmt.add_subheader("Immediate Actions")
        for item in result.action_items[:5]:
            status = "[x]" if item.get('completed') else "[ ]"
            fmt._parts.append(f"{status} {item.get('item', 'Unknown')}")
        fmt.add_blank_line()

    return fmt.build()


# --- Compliance Navigator Section Formatters ---

def format_eligibility_section(result: Any) -> str:
    """Format eligibility analysis as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Set-Aside Eligibility Assessment")

    if result.eligible_setasides:
        fmt.add_bullets(result.eligible_setasides, "Eligible Set-Asides")

    if result.eligibility_results:
        fmt._parts.append("**Detailed Eligibility Results**:")
        for sa_type, details in result.eligibility_results.items():
            status = "Eligible" if details.get("is_eligible") else "Not Eligible"
            fmt.add_bullet(f"**{sa_type}**: {status}")
        fmt.add_blank_line()

    return fmt.build()


def format_checklist_section(compliance_checklist: List[Dict[str, Any]]) -> str:
    """Format compliance checklist as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Compliance Checklist")

    for item in compliance_checklist:
        status = "[x]" if item.get("checked") else "[ ]"
        risk = f"({item.get('risk_level', 'Medium')})" if item.get("risk_level") else ""
        fmt._parts.append(f"{status} **{item.get('title', 'Item')}** {risk}")
        if item.get("description"):
            fmt._parts.append(f"    {item.get('description')}")
        fmt.add_blank_line()

    return fmt.build()


def format_oci_section(oci_risk_level: str, oci_assessment: Optional[Dict[str, Any]] = None) -> str:
    """Format OCI analysis as a section."""
    fmt = SectionFormatter()
    fmt.add_header("OCI Analysis")

    fmt.add_field("Risk Level", oci_risk_level)

    if oci_assessment:
        if oci_assessment.get("recommendation"):
            fmt.add_field("Recommendation", oci_assessment.get("recommendation"))
        if oci_assessment.get("mitigation_required"):
            fmt.add_field("Mitigation Required", "Yes")

    return fmt.build()


def format_subcontracting_section(subcontracting_compliance: Dict[str, Any]) -> str:
    """Format subcontracting compliance as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Limitations on Subcontracting")

    if subcontracting_compliance:
        status = "Compliant" if subcontracting_compliance.get("is_compliant") else "Non-Compliant"
        fmt.add_field("Status", status)
        if subcontracting_compliance.get("prime_percentage"):
            fmt.add_field("Prime Percentage", f"{subcontracting_compliance.get('prime_percentage')}%")
        if subcontracting_compliance.get("margin"):
            fmt.add_field("Margin Above Threshold", f"{subcontracting_compliance.get('margin')}%")

    return fmt.build()


def format_compliance_comprehensive_section(result: Any) -> str:
    """Format comprehensive compliance analysis as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Compliance Analysis Summary")

    fmt.add_field("Overall Status", result.overall_compliance_status)

    if result.eligible_setasides:
        fmt.add_field("Eligible Set-Asides", ", ".join(result.eligible_setasides))

    fmt.add_field("OCI Risk Level", result.oci_risk_level)

    if result.critical_issues:
        fmt.add_bullets(result.critical_issues, "Critical Issues")

    if result.recommendations:
        fmt.add_bullets(result.recommendations, "Recommendations")

    return fmt.build()


# --- Market Analyst Section Formatters ---

def format_market_sizing_section(result: Any) -> str:
    """Format market sizing as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Market Sizing")

    if result.total_addressable_market:
        fmt.add_field("Total Addressable Market (TAM)", f"${result.total_addressable_market:,.0f}M")
    if result.serviceable_addressable_market:
        fmt.add_field("Serviceable Addressable Market (SAM)", f"${result.serviceable_addressable_market:,.0f}M")
    if result.target_market:
        fmt.add_field("Target Market", f"${result.target_market:,.0f}M")

    if result.market_sizing_assumptions:
        fmt.add_bullets(result.market_sizing_assumptions, "Assumptions")

    return fmt.build()


def format_opportunities_section(ranked_opportunities: List[Dict[str, Any]]) -> str:
    """Format opportunities as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Priority Opportunities")

    for opp in ranked_opportunities:
        fmt.add_subheader(f"{opp.get('rank')}. {opp.get('title')}")
        fmt.add_field("Score", f"{opp.get('score')}/10")
        if opp.get('rationale'):
            fmt.add_field("Rationale", opp.get('rationale'))

    return fmt.build()


def format_competitive_section(result: Any) -> str:
    """Format competitive landscape as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Competitive Landscape")

    fmt.add_field("Competitive Density", result.competitive_density)

    if result.market_barriers:
        fmt.add_bullets(result.market_barriers, "Market Barriers")

    if result.market_enablers:
        fmt.add_bullets(result.market_enablers, "Market Enablers")

    return fmt.build()


def format_timing_section(timing_recommendations: List[str], fiscal_considerations: Optional[List[str]] = None) -> str:
    """Format timing recommendations as a section."""
    fmt = SectionFormatter()
    fmt.add_header("Timing Recommendations")

    if timing_recommendations:
        for rec in timing_recommendations:
            fmt.add_bullet(rec)
        fmt.add_blank_line()

    if fiscal_considerations:
        fmt.add_bullets(fiscal_considerations, "Fiscal Year Considerations")

    return fmt.build()


def format_market_comprehensive_section(result: Any) -> str:
    """Format comprehensive market analysis as a section."""
    parts = []

    if result.total_addressable_market:
        parts.append("## Market Sizing")
        parts.append(f"- TAM: ${result.total_addressable_market:,.0f}M")
        if result.serviceable_addressable_market:
            parts.append(f"- SAM: ${result.serviceable_addressable_market:,.0f}M")
        if result.target_market:
            parts.append(f"- Target Market: ${result.target_market:,.0f}M")
        parts.append("")

    if result.ranked_opportunities:
        parts.append("## Top Opportunities")
        for opp in result.ranked_opportunities:
            parts.append(f"- **{opp.get('title')}** (Score: {opp.get('score')}/10)")
            if opp.get('rationale'):
                parts.append(f"  {opp.get('rationale')}")
        parts.append("")

    if result.competitive_density != "Unknown":
        parts.append("## Competitive Landscape")
        parts.append(f"- Competitive Density: {result.competitive_density}")
        parts.append("")

    if result.market_trends:
        parts.append("## Market Trends")
        for trend in result.market_trends:
            parts.append(f"- {trend}")
        parts.append("")

    if result.timing_recommendations:
        parts.append("## Timing Recommendations")
        for rec in result.timing_recommendations:
            parts.append(f"- {rec}")
        parts.append("")

    return "\n".join(parts) if parts else "Market analysis completed."
