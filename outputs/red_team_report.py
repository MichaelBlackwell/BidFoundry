"""
Red Team Report Structure

Defines the transparency report that documents all adversarial
challenges and their resolutions during document generation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any
import json


class ExchangeOutcome(str, Enum):
    """Outcome of a critique-response exchange."""

    ACCEPTED = "Accepted"
    PARTIALLY_ACCEPTED = "Partially Accepted"
    REBUTTED = "Rebutted"
    ACKNOWLEDGED = "Acknowledged"
    DEFERRED = "Deferred"
    UNRESOLVED = "Unresolved"


@dataclass
class CritiqueRecord:
    """
    Record of a single critique from the red team.
    """

    id: str = ""
    agent: str = ""
    section: str = ""

    # Classification
    challenge_type: str = ""  # Logic, Evidence, Completeness, Risk, Compliance, etc.
    severity: str = ""  # Critical, Major, Minor, Observation

    # Content
    title: str = ""
    argument: str = ""
    evidence: str = ""
    suggested_remedy: str = ""

    # Round info
    round_number: int = 0

    # Timestamp
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "section": self.section,
            "challenge_type": self.challenge_type,
            "severity": self.severity,
            "title": self.title,
            "argument": self.argument,
            "evidence": self.evidence,
            "suggested_remedy": self.suggested_remedy,
            "round_number": self.round_number,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CritiqueRecord":
        record = cls(
            id=data.get("id", ""),
            agent=data.get("agent", ""),
            section=data.get("section", ""),
            challenge_type=data.get("challenge_type", ""),
            severity=data.get("severity", ""),
            title=data.get("title", ""),
            argument=data.get("argument", ""),
            evidence=data.get("evidence", ""),
            suggested_remedy=data.get("suggested_remedy", ""),
            round_number=data.get("round_number", 0),
        )
        if data.get("created_at"):
            record.created_at = datetime.fromisoformat(data["created_at"])
        return record


@dataclass
class ResponseRecord:
    """
    Record of a response to a critique.
    """

    id: str = ""
    critique_id: str = ""
    agent: str = ""

    # Disposition
    disposition: str = ""  # Accept, Partial Accept, Rebut, Acknowledge, Defer
    outcome: ExchangeOutcome = ExchangeOutcome.UNRESOLVED

    # Content
    summary: str = ""
    action: str = ""
    rationale: str = ""
    evidence: str = ""
    residual_risk: str = ""

    # Round info
    round_number: int = 0

    # Timestamp
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "critique_id": self.critique_id,
            "agent": self.agent,
            "disposition": self.disposition,
            "outcome": self.outcome.value,
            "summary": self.summary,
            "action": self.action,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "residual_risk": self.residual_risk,
            "round_number": self.round_number,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResponseRecord":
        record = cls(
            id=data.get("id", ""),
            critique_id=data.get("critique_id", ""),
            agent=data.get("agent", ""),
            disposition=data.get("disposition", ""),
            outcome=ExchangeOutcome(data.get("outcome", "Unresolved")),
            summary=data.get("summary", ""),
            action=data.get("action", ""),
            rationale=data.get("rationale", ""),
            evidence=data.get("evidence", ""),
            residual_risk=data.get("residual_risk", ""),
            round_number=data.get("round_number", 0),
        )
        if data.get("created_at"):
            record.created_at = datetime.fromisoformat(data["created_at"])
        return record


@dataclass
class ExchangeRecord:
    """
    Record of a complete critique-response exchange.
    """

    critique: CritiqueRecord = field(default_factory=CritiqueRecord)
    response: Optional[ResponseRecord] = None

    @property
    def is_resolved(self) -> bool:
        return self.response is not None

    @property
    def outcome(self) -> ExchangeOutcome:
        if self.response:
            return self.response.outcome
        return ExchangeOutcome.UNRESOLVED

    def to_dict(self) -> dict:
        return {
            "critique": self.critique.to_dict(),
            "response": self.response.to_dict() if self.response else None,
            "is_resolved": self.is_resolved,
            "outcome": self.outcome.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExchangeRecord":
        exchange = cls()
        exchange.critique = CritiqueRecord.from_dict(data.get("critique", {}))
        if data.get("response"):
            exchange.response = ResponseRecord.from_dict(data["response"])
        return exchange


@dataclass
class RoundSummary:
    """
    Summary of activity in a single debate round.
    """

    round_number: int = 0
    round_type: str = ""  # BlueBuild, RedAttack, BlueDefense, Synthesis

    # Counts
    critiques_issued: int = 0
    responses_given: int = 0

    # By severity
    critiques_by_severity: Dict[str, int] = field(default_factory=dict)

    # By type
    critiques_by_type: Dict[str, int] = field(default_factory=dict)

    # By disposition
    responses_by_disposition: Dict[str, int] = field(default_factory=dict)

    # Participating agents
    red_team_agents: List[str] = field(default_factory=list)
    blue_team_agents: List[str] = field(default_factory=list)

    # Timing
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "round_type": self.round_type,
            "critiques_issued": self.critiques_issued,
            "responses_given": self.responses_given,
            "critiques_by_severity": self.critiques_by_severity,
            "critiques_by_type": self.critiques_by_type,
            "responses_by_disposition": self.responses_by_disposition,
            "red_team_agents": self.red_team_agents,
            "blue_team_agents": self.blue_team_agents,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class RedTeamReport:
    """
    Comprehensive transparency report documenting all adversarial
    challenges and their resolutions.
    """

    # Identification
    document_id: str = ""
    document_type: str = ""

    # Generation info
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Summary metrics
    total_rounds: int = 0
    adversarial_cycles: int = 0
    total_critiques: int = 0
    resolved_critiques: int = 0
    consensus_reached: bool = False

    # Calculated metrics
    @property
    def unresolved_critiques(self) -> int:
        return self.total_critiques - self.resolved_critiques

    @property
    def resolution_rate(self) -> float:
        if self.total_critiques == 0:
            return 100.0
        return (self.resolved_critiques / self.total_critiques) * 100

    # Breakdowns
    critiques_by_severity: Dict[str, int] = field(default_factory=dict)
    critiques_by_section: Dict[str, int] = field(default_factory=dict)
    critiques_by_type: Dict[str, int] = field(default_factory=dict)
    responses_by_disposition: Dict[str, int] = field(default_factory=dict)

    # Participation
    red_team_agents: List[str] = field(default_factory=list)
    blue_team_agents: List[str] = field(default_factory=list)

    # Detailed records
    exchanges: List[ExchangeRecord] = field(default_factory=list)
    round_summaries: List[RoundSummary] = field(default_factory=list)

    # Unresolved issues (for quick reference)
    unresolved_issues: List[CritiqueRecord] = field(default_factory=list)

    # Critical findings
    critical_findings: List[CritiqueRecord] = field(default_factory=list)

    def add_exchange(self, exchange: ExchangeRecord) -> None:
        """Add an exchange to the report."""
        self.exchanges.append(exchange)
        self.total_critiques += 1

        if exchange.is_resolved:
            self.resolved_critiques += 1
        else:
            self.unresolved_issues.append(exchange.critique)

        # Update severity counts
        severity = exchange.critique.severity
        self.critiques_by_severity[severity] = (
            self.critiques_by_severity.get(severity, 0) + 1
        )

        # Update section counts
        section = exchange.critique.section
        self.critiques_by_section[section] = (
            self.critiques_by_section.get(section, 0) + 1
        )

        # Update type counts
        ctype = exchange.critique.challenge_type
        self.critiques_by_type[ctype] = (
            self.critiques_by_type.get(ctype, 0) + 1
        )

        # Update disposition counts
        if exchange.response:
            disposition = exchange.response.disposition
            self.responses_by_disposition[disposition] = (
                self.responses_by_disposition.get(disposition, 0) + 1
            )

        # Track critical findings
        if severity == "critical":
            self.critical_findings.append(exchange.critique)

        # Track participating agents
        if exchange.critique.agent and exchange.critique.agent not in self.red_team_agents:
            self.red_team_agents.append(exchange.critique.agent)
        if exchange.response and exchange.response.agent:
            if exchange.response.agent not in self.blue_team_agents:
                self.blue_team_agents.append(exchange.response.agent)

    def add_round_summary(self, summary: RoundSummary) -> None:
        """Add a round summary to the report."""
        self.round_summaries.append(summary)
        self.total_rounds = len(self.round_summaries)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "generated_at": self.generated_at.isoformat(),

            "summary": {
                "total_rounds": self.total_rounds,
                "adversarial_cycles": self.adversarial_cycles,
                "total_critiques": self.total_critiques,
                "resolved_critiques": self.resolved_critiques,
                "unresolved_critiques": self.unresolved_critiques,
                "resolution_rate": self.resolution_rate,
                "consensus_reached": self.consensus_reached,
            },

            "participation": {
                "red_team_agents": self.red_team_agents,
                "blue_team_agents": self.blue_team_agents,
            },

            "breakdowns": {
                "critiques_by_severity": self.critiques_by_severity,
                "critiques_by_section": self.critiques_by_section,
                "critiques_by_type": self.critiques_by_type,
                "responses_by_disposition": self.responses_by_disposition,
            },

            "exchanges": [e.to_dict() for e in self.exchanges],
            "round_summaries": [r.to_dict() for r in self.round_summaries],
            "unresolved_issues": [c.to_dict() for c in self.unresolved_issues],
            "critical_findings": [c.to_dict() for c in self.critical_findings],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RedTeamReport":
        report = cls()
        report.document_id = data.get("document_id", "")
        report.document_type = data.get("document_type", "")

        if data.get("generated_at"):
            report.generated_at = datetime.fromisoformat(data["generated_at"])

        summary = data.get("summary", {})
        report.total_rounds = summary.get("total_rounds", 0)
        report.adversarial_cycles = summary.get("adversarial_cycles", 0)
        report.total_critiques = summary.get("total_critiques", 0)
        report.resolved_critiques = summary.get("resolved_critiques", 0)
        report.consensus_reached = summary.get("consensus_reached", False)

        participation = data.get("participation", {})
        report.red_team_agents = participation.get("red_team_agents", [])
        report.blue_team_agents = participation.get("blue_team_agents", [])

        breakdowns = data.get("breakdowns", {})
        report.critiques_by_severity = breakdowns.get("critiques_by_severity", {})
        report.critiques_by_section = breakdowns.get("critiques_by_section", {})
        report.critiques_by_type = breakdowns.get("critiques_by_type", {})
        report.responses_by_disposition = breakdowns.get("responses_by_disposition", {})

        report.exchanges = [ExchangeRecord.from_dict(e) for e in data.get("exchanges", [])]
        report.round_summaries = [RoundSummary(**r) for r in data.get("round_summaries", [])]
        report.unresolved_issues = [CritiqueRecord.from_dict(c) for c in data.get("unresolved_issues", [])]
        report.critical_findings = [CritiqueRecord.from_dict(c) for c in data.get("critical_findings", [])]

        return report

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "RedTeamReport":
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))

    def to_markdown(self) -> str:
        """Export report as Markdown."""
        lines = []

        # Header
        lines.append("# Red Team Report")
        lines.append("")
        lines.append(f"**Document:** {self.document_type}")
        lines.append(f"**Document ID:** {self.document_id}")
        lines.append(f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- **Total Debate Rounds:** {self.total_rounds}")
        lines.append(f"- **Adversarial Cycles:** {self.adversarial_cycles}")
        lines.append(f"- **Total Critiques:** {self.total_critiques}")
        lines.append(f"- **Resolved:** {self.resolved_critiques} ({self.resolution_rate:.1f}%)")
        lines.append(f"- **Unresolved:** {self.unresolved_critiques}")
        lines.append(f"- **Consensus Reached:** {'Yes' if self.consensus_reached else 'No'}")
        lines.append("")

        # Critical Findings
        if self.critical_findings:
            lines.append("## Critical Findings")
            lines.append("")
            for finding in self.critical_findings:
                lines.append(f"### {finding.title}")
                lines.append(f"- **Section:** {finding.section}")
                lines.append(f"- **Agent:** {finding.agent}")
                lines.append(f"- **Type:** {finding.challenge_type}")
                lines.append("")
                lines.append(finding.argument)
                lines.append("")
        else:
            lines.append("## Critical Findings")
            lines.append("")
            lines.append("*No critical findings.*")
            lines.append("")

        # Unresolved Issues
        if self.unresolved_issues:
            lines.append("## Unresolved Issues")
            lines.append("")
            for issue in self.unresolved_issues:
                lines.append(f"- **[{issue.severity}]** {issue.title} ({issue.section})")
            lines.append("")
        else:
            lines.append("## Unresolved Issues")
            lines.append("")
            lines.append("*All issues resolved.*")
            lines.append("")

        # Breakdown by Severity
        lines.append("## Critiques by Severity")
        lines.append("")
        for severity, count in sorted(self.critiques_by_severity.items()):
            lines.append(f"- **{severity}:** {count}")
        lines.append("")

        # Breakdown by Section
        lines.append("## Critiques by Section")
        lines.append("")
        for section, count in sorted(self.critiques_by_section.items()):
            lines.append(f"- **{section}:** {count}")
        lines.append("")

        # Response Disposition
        lines.append("## Response Dispositions")
        lines.append("")
        for disposition, count in sorted(self.responses_by_disposition.items()):
            lines.append(f"- **{disposition}:** {count}")
        lines.append("")

        # Participating Agents
        lines.append("## Participating Agents")
        lines.append("")
        lines.append("### Red Team")
        for agent in self.red_team_agents:
            lines.append(f"- {agent}")
        lines.append("")
        lines.append("### Blue Team")
        for agent in self.blue_team_agents:
            lines.append(f"- {agent}")
        lines.append("")

        # Detailed Exchanges
        lines.append("## Detailed Exchanges")
        lines.append("")
        for i, exchange in enumerate(self.exchanges, 1):
            critique = exchange.critique
            response = exchange.response

            lines.append(f"### Exchange {i}: {critique.title}")
            lines.append("")
            lines.append(f"**Critique** ({critique.severity}, {critique.challenge_type})")
            lines.append(f"- Agent: {critique.agent}")
            lines.append(f"- Section: {critique.section}")
            lines.append(f"- Argument: {critique.argument[:200]}...")
            lines.append("")

            if response:
                lines.append(f"**Response** ({response.disposition})")
                lines.append(f"- Agent: {response.agent}")
                lines.append(f"- Summary: {response.summary}")
                if response.residual_risk:
                    lines.append(f"- Residual Risk: {response.residual_risk}")
            else:
                lines.append("**Response:** *None - Unresolved*")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def get_summary_text(self) -> str:
        """Get a brief text summary of the report."""
        return (
            f"Red Team Report: {self.total_critiques} critiques across {self.total_rounds} rounds. "
            f"Resolution rate: {self.resolution_rate:.1f}%. "
            f"Consensus: {'Reached' if self.consensus_reached else 'Not Reached'}. "
            f"Critical findings: {len(self.critical_findings)}."
        )
