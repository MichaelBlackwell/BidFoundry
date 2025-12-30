"""
FAR/DFAR Compliance Rules

Defines Federal Acquisition Regulation (FAR) and Defense FAR Supplement (DFARS)
compliance rules for government contracting. These rules help validate strategy
documents against regulatory requirements.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
import re


class FARSubpart(str, Enum):
    """Major FAR subparts relevant to GovCon strategy."""

    # Competition Requirements
    FAR_6 = "FAR Part 6"  # Competition Requirements
    FAR_6_1 = "FAR 6.1"  # Full and Open Competition
    FAR_6_2 = "FAR 6.2"  # Full and Open After Exclusion of Sources
    FAR_6_3 = "FAR 6.3"  # Other Than Full and Open Competition

    # Small Business Programs
    FAR_19 = "FAR Part 19"  # Small Business Programs
    FAR_19_5 = "FAR 19.5"  # Set-Asides for Small Business
    FAR_19_8 = "FAR 19.8"  # Contracting with the SBA (8(a))
    FAR_19_13 = "FAR 19.13"  # HUBZone Program
    FAR_19_14 = "FAR 19.14"  # SDVOSB Program

    # Contract Types
    FAR_16 = "FAR Part 16"  # Types of Contracts
    FAR_16_1 = "FAR 16.1"  # Fixed-Price Contracts
    FAR_16_2 = "FAR 16.2"  # Cost-Reimbursement Contracts
    FAR_16_3 = "FAR 16.3"  # Cost-Reimbursement Contracts

    # Source Selection
    FAR_15 = "FAR Part 15"  # Contracting by Negotiation
    FAR_15_3 = "FAR 15.3"  # Source Selection

    # Organizational Conflicts of Interest
    FAR_9_5 = "FAR 9.5"  # Organizational Conflicts of Interest

    # Cost Accounting
    FAR_30 = "FAR Part 30"  # Cost Accounting Standards
    FAR_31 = "FAR Part 31"  # Contract Cost Principles

    # Subcontracting
    FAR_44 = "FAR Part 44"  # Subcontracting Policies

    # DFARS Supplements
    DFARS_215 = "DFARS 215"  # Contracting by Negotiation
    DFARS_219 = "DFARS 219"  # Small Business Programs
    DFARS_252 = "DFARS 252"  # Solicitation Provisions and Contract Clauses


class ComplianceStatus(str, Enum):
    """Status of a compliance check."""

    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    NEEDS_REVIEW = "Needs Review"
    NOT_APPLICABLE = "Not Applicable"
    UNKNOWN = "Unknown"


class RiskLevel(str, Enum):
    """Risk level for compliance issues."""

    CRITICAL = "critical"  # Will result in rejection/disqualification
    HIGH = "high"  # Likely to result in significant issues
    MEDIUM = "medium"  # May cause issues, should address
    LOW = "low"  # Minor issue, best practice to address
    INFO = "informational"  # FYI, no action required


@dataclass
class FARRule:
    """
    A FAR/DFARS compliance rule.

    Represents a specific regulatory requirement that can be checked
    against a strategy or proposal.
    """

    id: str
    subpart: FARSubpart
    title: str
    description: str
    requirement: str  # The actual regulatory requirement text
    applicability: str  # When this rule applies
    risk_level: RiskLevel = RiskLevel.MEDIUM

    # Validation
    keywords: List[str] = field(default_factory=list)
    check_function: Optional[str] = None  # Name of validation function
    remediation_guidance: str = ""

    # Metadata
    effective_date: Optional[str] = None
    last_updated: Optional[str] = None
    related_rules: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subpart": self.subpart.value,
            "title": self.title,
            "description": self.description,
            "requirement": self.requirement,
            "applicability": self.applicability,
            "risk_level": self.risk_level.value,
            "keywords": self.keywords,
            "check_function": self.check_function,
            "remediation_guidance": self.remediation_guidance,
            "effective_date": self.effective_date,
            "last_updated": self.last_updated,
            "related_rules": self.related_rules,
            "exceptions": self.exceptions,
        }


@dataclass
class ComplianceCheckResult:
    """Result of a compliance check against a FAR rule."""

    rule_id: str
    rule_title: str
    status: ComplianceStatus
    risk_level: RiskLevel
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    requires_action: bool = False

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_title": self.rule_title,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "evidence": self.evidence,
            "requires_action": self.requires_action,
        }


class FARComplianceChecker:
    """
    Checks documents and strategies for FAR/DFARS compliance.

    Provides rule-based validation against federal acquisition regulations.
    """

    def __init__(self):
        self._rules: Dict[str, FARRule] = {}
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load the default set of FAR compliance rules."""
        for rule in get_common_far_rules():
            self._rules[rule.id] = rule

    def add_rule(self, rule: FARRule) -> None:
        """Add a custom rule to the checker."""
        self._rules[rule.id] = rule

    def get_rule(self, rule_id: str) -> Optional[FARRule]:
        """Get a rule by ID."""
        return self._rules.get(rule_id)

    def get_rules_by_subpart(self, subpart: FARSubpart) -> List[FARRule]:
        """Get all rules for a specific FAR subpart."""
        return [r for r in self._rules.values() if r.subpart == subpart]

    def get_applicable_rules(
        self,
        contract_type: Optional[str] = None,
        set_aside: Optional[str] = None,
        is_dod: bool = False,
        contract_value: Optional[float] = None,
    ) -> List[FARRule]:
        """
        Get rules applicable to a specific contract situation.

        Args:
            contract_type: Type of contract (FFP, T&M, etc.)
            set_aside: Set-aside type if applicable
            is_dod: Whether this is a DoD contract
            contract_value: Estimated contract value

        Returns:
            List of applicable FAR rules
        """
        applicable = []

        for rule in self._rules.values():
            # Check applicability keywords
            applicability = rule.applicability.lower()

            # Always include general rules
            if "all" in applicability or "general" in applicability:
                applicable.append(rule)
                continue

            # Check contract type applicability
            if contract_type and contract_type.lower() in applicability:
                applicable.append(rule)
                continue

            # Check set-aside applicability
            if set_aside:
                if set_aside.lower() in applicability:
                    applicable.append(rule)
                    continue
                if "small business" in applicability and set_aside != "Full and Open":
                    applicable.append(rule)
                    continue

            # Check DoD applicability
            if is_dod and ("dod" in applicability or "dfars" in rule.subpart.value.lower()):
                applicable.append(rule)
                continue

            # Check value thresholds
            if contract_value:
                if contract_value >= 750000 and "simplified acquisition" not in applicability:
                    if "negotiated" in applicability or "far 15" in applicability.lower():
                        applicable.append(rule)

        return applicable

    def check_compliance(
        self,
        content: str,
        company_profile: Optional[Dict[str, Any]] = None,
        opportunity: Optional[Dict[str, Any]] = None,
        rules: Optional[List[FARRule]] = None,
    ) -> List[ComplianceCheckResult]:
        """
        Check content against FAR compliance rules.

        Args:
            content: Document content to check
            company_profile: Company profile for context
            opportunity: Opportunity details for context
            rules: Specific rules to check (if None, uses applicable rules)

        Returns:
            List of compliance check results
        """
        results = []

        # Determine applicable rules if not specified
        if rules is None:
            rules = list(self._rules.values())

        for rule in rules:
            result = self._check_rule(content, rule, company_profile, opportunity)
            results.append(result)

        return results

    def _check_rule(
        self,
        content: str,
        rule: FARRule,
        company_profile: Optional[Dict[str, Any]] = None,
        opportunity: Optional[Dict[str, Any]] = None,
    ) -> ComplianceCheckResult:
        """Check content against a single rule."""

        result = ComplianceCheckResult(
            rule_id=rule.id,
            rule_title=rule.title,
            status=ComplianceStatus.UNKNOWN,
            risk_level=rule.risk_level,
        )

        content_lower = content.lower()

        # Check for keyword presence
        keyword_hits = []
        keyword_misses = []

        for keyword in rule.keywords:
            if keyword.lower() in content_lower:
                keyword_hits.append(keyword)
            else:
                keyword_misses.append(keyword)

        # Determine status based on keywords and context
        if not rule.keywords:
            result.status = ComplianceStatus.NEEDS_REVIEW
            result.findings.append(
                f"Rule requires manual review: {rule.description}"
            )
        elif keyword_hits and not keyword_misses:
            result.status = ComplianceStatus.COMPLIANT
            result.evidence = [f"Found reference to: {', '.join(keyword_hits)}"]
        elif keyword_misses:
            if rule.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                result.status = ComplianceStatus.NON_COMPLIANT
                result.requires_action = True
            else:
                result.status = ComplianceStatus.NEEDS_REVIEW
            result.findings.append(
                f"Missing discussion of: {', '.join(keyword_misses)}"
            )
            if rule.remediation_guidance:
                result.recommendations.append(rule.remediation_guidance)
        else:
            result.status = ComplianceStatus.NEEDS_REVIEW

        return result

    def generate_compliance_checklist(
        self,
        opportunity: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate a compliance checklist for an opportunity.

        Args:
            opportunity: Opportunity details

        Returns:
            List of checklist items
        """
        checklist = []

        # Determine context
        set_aside = opportunity.get("set_aside", "Full and Open")
        contract_type = opportunity.get("contract_type")
        is_dod = "DoD" in opportunity.get("agency", {}).get("name", "") if opportunity.get("agency") else False
        value = opportunity.get("estimated_value", 0)

        applicable_rules = self.get_applicable_rules(
            contract_type=contract_type,
            set_aside=set_aside,
            is_dod=is_dod,
            contract_value=value,
        )

        for rule in applicable_rules:
            checklist.append({
                "rule_id": rule.id,
                "title": rule.title,
                "requirement": rule.requirement,
                "risk_level": rule.risk_level.value,
                "checked": False,
                "notes": "",
                "guidance": rule.remediation_guidance,
            })

        return checklist


def get_common_far_rules() -> List[FARRule]:
    """
    Get the common FAR/DFARS rules for GovCon compliance.

    Returns:
        List of commonly applicable FAR rules
    """
    return [
        # Competition Requirements
        FARRule(
            id="FAR-6.1-001",
            subpart=FARSubpart.FAR_6_1,
            title="Full and Open Competition",
            description="Requirement to obtain full and open competition for government contracts",
            requirement="Contracting officers shall promote and provide for full and open competition in soliciting offers and awarding Government contracts.",
            applicability="All contracts above simplified acquisition threshold",
            risk_level=RiskLevel.CRITICAL,
            keywords=["competition", "competitive", "solicitation"],
            remediation_guidance="Ensure strategy addresses how full and open competition requirements are being met, or document applicable exceptions.",
        ),

        # Small Business
        FARRule(
            id="FAR-19.5-001",
            subpart=FARSubpart.FAR_19_5,
            title="Small Business Set-Aside Requirements",
            description="Requirements for small business set-aside eligibility",
            requirement="Contracting officers must set aside acquisitions exceeding the micro-purchase threshold for small business when there is reasonable expectation of receiving offers from two or more responsible small business concerns.",
            applicability="Small business set-asides",
            risk_level=RiskLevel.HIGH,
            keywords=["small business", "set-aside", "size standard"],
            remediation_guidance="Verify company meets SBA size standards and document small business status.",
        ),
        FARRule(
            id="FAR-19.5-002",
            subpart=FARSubpart.FAR_19_5,
            title="Limitations on Subcontracting",
            description="Performance requirements for small business set-asides",
            requirement="For services (except construction), at least 50 percent of the cost of contract performance incurred for personnel must be expended for employees of the concern.",
            applicability="Small business set-asides for services",
            risk_level=RiskLevel.CRITICAL,
            keywords=["limitations on subcontracting", "50 percent", "personnel costs"],
            remediation_guidance="Ensure staffing plan demonstrates compliance with 50% limitation on subcontracting for services.",
        ),

        # 8(a) Program
        FARRule(
            id="FAR-19.8-001",
            subpart=FARSubpart.FAR_19_8,
            title="8(a) Program Eligibility",
            description="Requirements for 8(a) Business Development program participation",
            requirement="To be eligible for the 8(a) program, a concern must be unconditionally owned and controlled by one or more socially and economically disadvantaged individuals.",
            applicability="8(a) set-asides and sole source",
            risk_level=RiskLevel.CRITICAL,
            keywords=["8(a)", "socially disadvantaged", "economically disadvantaged", "SBA"],
            remediation_guidance="Verify active 8(a) certification and eligibility for the specific contract.",
        ),

        # HUBZone
        FARRule(
            id="FAR-19.13-001",
            subpart=FARSubpart.FAR_19_13,
            title="HUBZone Program Requirements",
            description="Requirements for HUBZone program participation",
            requirement="A HUBZone small business concern must maintain compliance with HUBZone requirements including principal office location and employee residence requirements.",
            applicability="HUBZone set-asides",
            risk_level=RiskLevel.HIGH,
            keywords=["HUBZone", "principal office", "employee residence"],
            remediation_guidance="Verify current HUBZone certification and compliance with residence requirements.",
        ),

        # SDVOSB
        FARRule(
            id="FAR-19.14-001",
            subpart=FARSubpart.FAR_19_14,
            title="SDVOSB Eligibility",
            description="Requirements for Service-Disabled Veteran-Owned Small Business participation",
            requirement="A service-disabled veteran must unconditionally own at least 51% and control the management and daily operations.",
            applicability="SDVOSB set-asides",
            risk_level=RiskLevel.HIGH,
            keywords=["SDVOSB", "service-disabled veteran", "veteran-owned"],
            remediation_guidance="Verify SBA SDVOSB certification (VetCert) is current and valid.",
        ),

        # Source Selection (FAR 15)
        FARRule(
            id="FAR-15.3-001",
            subpart=FARSubpart.FAR_15_3,
            title="Evaluation Factors",
            description="Requirements for proposal evaluation against stated factors",
            requirement="Proposals shall be evaluated only on the factors and subfactors stated in the solicitation.",
            applicability="Negotiated procurements",
            risk_level=RiskLevel.HIGH,
            keywords=["evaluation factors", "technical evaluation", "past performance", "price"],
            remediation_guidance="Ensure proposal directly addresses all evaluation factors and subfactors stated in the solicitation.",
        ),
        FARRule(
            id="FAR-15.3-002",
            subpart=FARSubpart.FAR_15_3,
            title="Past Performance Evaluation",
            description="Requirements for past performance evaluation",
            requirement="Past performance information shall be evaluated for relevance and the quality of performance.",
            applicability="All negotiated procurements above SAT",
            risk_level=RiskLevel.MEDIUM,
            keywords=["past performance", "CPARS", "relevance", "recency"],
            remediation_guidance="Identify and document relevant past performance with currency, scope, and complexity alignment.",
        ),

        # Organizational Conflicts of Interest
        FARRule(
            id="FAR-9.5-001",
            subpart=FARSubpart.FAR_9_5,
            title="Organizational Conflicts of Interest",
            description="Requirements to identify and mitigate organizational conflicts of interest",
            requirement="Contractors must disclose actual or potential organizational conflicts of interest and government may require mitigation plans.",
            applicability="All contracts, especially advisory and assistance services",
            risk_level=RiskLevel.CRITICAL,
            keywords=["conflict of interest", "OCI", "mitigation", "disclosure", "unfair competitive advantage"],
            remediation_guidance="Analyze potential OCI issues and develop mitigation plan if necessary. Document any current contracts that could create conflicts.",
        ),

        # Cost Accounting
        FARRule(
            id="FAR-30-001",
            subpart=FARSubpart.FAR_30,
            title="Cost Accounting Standards (CAS)",
            description="Requirements for Cost Accounting Standards compliance",
            requirement="Contractors with CAS-covered contracts must follow specific cost accounting practices and disclose accounting methods.",
            applicability="CAS-covered contracts (generally >$50M in awards)",
            risk_level=RiskLevel.HIGH,
            keywords=["CAS", "cost accounting", "disclosure statement", "accounting system"],
            remediation_guidance="Ensure accounting system is compliant and disclosure statement is current if CAS-covered.",
        ),
        FARRule(
            id="FAR-31-001",
            subpart=FARSubpart.FAR_31,
            title="Allowable Costs",
            description="Requirements for cost allowability under government contracts",
            requirement="Costs must be allowable, allocable, and reasonable to be reimbursable under government contracts.",
            applicability="Cost-reimbursable contracts and T&M/LH contracts",
            risk_level=RiskLevel.MEDIUM,
            keywords=["allowable", "allocable", "reasonable", "indirect costs", "direct costs"],
            remediation_guidance="Review pricing approach to ensure all proposed costs meet FAR 31 allowability criteria.",
        ),

        # Subcontracting
        FARRule(
            id="FAR-44-001",
            subpart=FARSubpart.FAR_44,
            title="Subcontracting Plan",
            description="Requirements for small business subcontracting plans",
            requirement="For contracts exceeding $750,000, other than small business concerns must submit a subcontracting plan with goals for small business subcontracting.",
            applicability="Large business primes, contracts >$750K",
            risk_level=RiskLevel.MEDIUM,
            keywords=["subcontracting plan", "subcontracting goals", "small business subcontracting"],
            remediation_guidance="Develop subcontracting plan with realistic goals for SB, SDB, WOSB, HUBZone, VOSB, and SDVOSB participation.",
        ),

        # DFARS Cybersecurity
        FARRule(
            id="DFARS-252.204-7012",
            subpart=FARSubpart.DFARS_252,
            title="Safeguarding Covered Defense Information",
            description="DFARS clause requiring protection of CUI and cyber incident reporting",
            requirement="Contractors must implement NIST SP 800-171 security requirements and report cyber incidents within 72 hours.",
            applicability="DoD contracts involving CUI",
            risk_level=RiskLevel.CRITICAL,
            keywords=["DFARS 7012", "CUI", "NIST 800-171", "cyber incident", "safeguarding"],
            remediation_guidance="Verify NIST 800-171 compliance and document security controls. Ensure incident response procedures are in place.",
        ),

        # CMMC
        FARRule(
            id="DFARS-CMMC-001",
            subpart=FARSubpart.DFARS_252,
            title="CMMC Certification Requirements",
            description="Cybersecurity Maturity Model Certification requirements for DoD",
            requirement="Contractors must achieve and maintain CMMC certification at the level required by the solicitation.",
            applicability="DoD contracts requiring CMMC",
            risk_level=RiskLevel.CRITICAL,
            keywords=["CMMC", "cybersecurity maturity", "certification level"],
            remediation_guidance="Verify current CMMC certification level meets solicitation requirements. Plan for assessment if not yet certified.",
        ),
    ]
