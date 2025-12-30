"""
Small Business Program Rules

Defines rules and validation logic for SBA small business programs,
including size standards, affiliation rules, and program eligibility.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import date


class SmallBusinessProgram(str, Enum):
    """SBA small business programs and certifications."""

    SMALL_BUSINESS = "Small Business"
    SBA_8A = "8(a) Business Development"
    HUBZONE = "HUBZone"
    SDVOSB = "SDVOSB"  # Service-Disabled Veteran-Owned Small Business
    VOSB = "VOSB"  # Veteran-Owned Small Business
    WOSB = "WOSB"  # Women-Owned Small Business
    EDWOSB = "EDWOSB"  # Economically Disadvantaged WOSB


class SizeStandardType(str, Enum):
    """Types of SBA size standards."""

    REVENUE = "Annual Revenue"
    EMPLOYEES = "Number of Employees"


@dataclass
class SizeStandard:
    """SBA size standard for a NAICS code."""

    naics_code: str
    naics_description: str
    standard_type: SizeStandardType
    threshold: float  # In millions for revenue, count for employees
    exceptions: List[str] = field(default_factory=list)

    def is_small(
        self,
        annual_revenue: Optional[float] = None,
        employee_count: Optional[int] = None,
    ) -> bool:
        """
        Check if company qualifies as small business under this standard.

        Args:
            annual_revenue: Company's average annual revenue (in dollars)
            employee_count: Company's employee count

        Returns:
            True if company meets small business size standard
        """
        if self.standard_type == SizeStandardType.REVENUE:
            if annual_revenue is None:
                return False
            # Convert to millions for comparison
            revenue_millions = annual_revenue / 1_000_000
            return revenue_millions <= self.threshold
        else:  # EMPLOYEES
            if employee_count is None:
                return False
            return employee_count <= self.threshold

    def to_dict(self) -> dict:
        unit = "million" if self.standard_type == SizeStandardType.REVENUE else "employees"
        return {
            "naics_code": self.naics_code,
            "naics_description": self.naics_description,
            "standard_type": self.standard_type.value,
            "threshold": self.threshold,
            "threshold_display": f"${self.threshold}M" if self.standard_type == SizeStandardType.REVENUE else f"{int(self.threshold)} employees",
            "exceptions": self.exceptions,
        }


@dataclass
class SmallBusinessRule:
    """
    A small business program eligibility rule.

    Represents a specific requirement for small business program participation.
    """

    id: str
    program: SmallBusinessProgram
    title: str
    description: str
    requirement: str
    verification_method: str  # How to verify compliance
    risk_if_non_compliant: str
    keywords: List[str] = field(default_factory=list)
    related_cfr: Optional[str] = None  # CFR citation

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "program": self.program.value,
            "title": self.title,
            "description": self.description,
            "requirement": self.requirement,
            "verification_method": self.verification_method,
            "risk_if_non_compliant": self.risk_if_non_compliant,
            "keywords": self.keywords,
            "related_cfr": self.related_cfr,
        }


@dataclass
class EligibilityCheckResult:
    """Result of a small business eligibility check."""

    program: SmallBusinessProgram
    is_eligible: bool
    confidence: str  # High, Medium, Low
    findings: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    certification_status: str = "Unknown"  # Current, Expired, Pending, None

    def to_dict(self) -> dict:
        return {
            "program": self.program.value,
            "is_eligible": self.is_eligible,
            "confidence": self.confidence,
            "findings": self.findings,
            "missing_requirements": self.missing_requirements,
            "recommendations": self.recommendations,
            "certification_status": self.certification_status,
        }


class SmallBusinessValidator:
    """
    Validates company eligibility for SBA small business programs.

    Checks company profile against program requirements and provides
    detailed eligibility assessment.
    """

    def __init__(self):
        self._rules: Dict[SmallBusinessProgram, List[SmallBusinessRule]] = {}
        self._size_standards: Dict[str, SizeStandard] = {}
        self._load_default_rules()
        self._load_common_size_standards()

    def _load_default_rules(self) -> None:
        """Load default small business program rules."""
        rules = get_small_business_rules()
        for rule in rules:
            if rule.program not in self._rules:
                self._rules[rule.program] = []
            self._rules[rule.program].append(rule)

    def _load_common_size_standards(self) -> None:
        """Load common NAICS size standards."""
        for standard in get_common_size_standards():
            self._size_standards[standard.naics_code] = standard

    def get_size_standard(self, naics_code: str) -> Optional[SizeStandard]:
        """Get size standard for a NAICS code."""
        return self._size_standards.get(naics_code)

    def check_size_status(
        self,
        naics_code: str,
        annual_revenue: Optional[float] = None,
        employee_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Check if company qualifies as small business for a NAICS code.

        Args:
            naics_code: NAICS code to check
            annual_revenue: Average annual receipts (3-year average)
            employee_count: Number of employees

        Returns:
            Dictionary with size determination results
        """
        standard = self._size_standards.get(naics_code)

        if standard is None:
            return {
                "naics_code": naics_code,
                "is_small": None,
                "status": "Unknown - NAICS code not found in database",
                "recommendation": "Verify size standard with SBA NAICS lookup tool",
            }

        is_small = standard.is_small(annual_revenue, employee_count)

        if standard.standard_type == SizeStandardType.REVENUE:
            value = annual_revenue / 1_000_000 if annual_revenue else 0
            threshold = standard.threshold
            margin = ((threshold - value) / threshold * 100) if threshold > 0 else 0
            value_str = f"${value:.1f}M"
            threshold_str = f"${threshold:.1f}M"
        else:
            value = employee_count or 0
            threshold = standard.threshold
            margin = ((threshold - value) / threshold * 100) if threshold > 0 else 0
            value_str = f"{value} employees"
            threshold_str = f"{int(threshold)} employees"

        return {
            "naics_code": naics_code,
            "naics_description": standard.naics_description,
            "is_small": is_small,
            "standard_type": standard.standard_type.value,
            "company_value": value_str,
            "threshold": threshold_str,
            "margin_percent": round(margin, 1),
            "status": "Qualifies as Small" if is_small else "Exceeds Size Standard",
            "warning": "Close to threshold" if 0 < margin < 20 else None,
        }

    def check_program_eligibility(
        self,
        program: SmallBusinessProgram,
        company_profile: Dict[str, Any],
    ) -> EligibilityCheckResult:
        """
        Check company eligibility for a specific program.

        Args:
            program: The small business program to check
            company_profile: Company profile data

        Returns:
            EligibilityCheckResult with detailed findings
        """
        result = EligibilityCheckResult(
            program=program,
            is_eligible=True,  # Assume eligible until proven otherwise
            confidence="Low",
        )

        # Get certifications from profile
        certifications = company_profile.get("certifications", [])
        cert_types = {c.get("cert_type") for c in certifications}

        # Check for existing certification
        program_cert_mapping = {
            SmallBusinessProgram.SBA_8A: "8(a)",
            SmallBusinessProgram.HUBZONE: "HUBZone",
            SmallBusinessProgram.SDVOSB: "SDVOSB",
            SmallBusinessProgram.VOSB: "VOSB",
            SmallBusinessProgram.WOSB: "WOSB",
            SmallBusinessProgram.EDWOSB: "EDWOSB",
        }

        if program in program_cert_mapping:
            cert_name = program_cert_mapping[program]
            has_cert = cert_name in cert_types

            if has_cert:
                result.certification_status = "Current"
                result.findings.append(f"Company has {cert_name} certification")
                result.confidence = "High"
            else:
                result.certification_status = "None"
                result.findings.append(f"No {cert_name} certification found")
                result.missing_requirements.append(f"SBA {cert_name} certification required")
                result.is_eligible = False

        # Check program-specific requirements
        rules = self._rules.get(program, [])
        for rule in rules:
            self._evaluate_rule(rule, company_profile, result)

        # Update confidence based on findings
        if result.missing_requirements:
            result.is_eligible = False
            result.confidence = "High" if len(result.missing_requirements) <= 2 else "Medium"

        return result

    def _evaluate_rule(
        self,
        rule: SmallBusinessRule,
        company_profile: Dict[str, Any],
        result: EligibilityCheckResult,
    ) -> None:
        """Evaluate a single rule against company profile."""

        # This is a simplified check - in production, would have more sophisticated logic
        profile_str = str(company_profile).lower()

        # Check if any keywords are present
        keyword_found = any(kw.lower() in profile_str for kw in rule.keywords)

        if not keyword_found and rule.keywords:
            result.findings.append(f"Could not verify: {rule.title}")
            result.recommendations.append(f"Ensure documentation of: {rule.requirement}")

    def check_all_programs(
        self,
        company_profile: Dict[str, Any],
    ) -> Dict[SmallBusinessProgram, EligibilityCheckResult]:
        """
        Check eligibility for all small business programs.

        Args:
            company_profile: Company profile data

        Returns:
            Dictionary mapping each program to its eligibility result
        """
        results = {}

        for program in SmallBusinessProgram:
            results[program] = self.check_program_eligibility(program, company_profile)

        return results

    def get_eligible_programs(
        self,
        company_profile: Dict[str, Any],
    ) -> List[SmallBusinessProgram]:
        """Get list of programs the company is eligible for."""
        results = self.check_all_programs(company_profile)
        return [prog for prog, result in results.items() if result.is_eligible]


def get_size_standard(naics_code: str) -> Optional[SizeStandard]:
    """
    Get the SBA size standard for a NAICS code.

    This is a convenience function that creates a validator and looks up the standard.

    Args:
        naics_code: The NAICS code to look up

    Returns:
        SizeStandard if found, None otherwise
    """
    validator = SmallBusinessValidator()
    return validator.get_size_standard(naics_code)


def get_common_size_standards() -> List[SizeStandard]:
    """
    Get common NAICS size standards for IT and professional services.

    Note: These are representative examples. Actual size standards should be
    verified at https://www.sba.gov/size-standards

    Returns:
        List of common size standards
    """
    return [
        # IT Services
        SizeStandard(
            naics_code="541512",
            naics_description="Computer Systems Design Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=34.0,  # $34 million
        ),
        SizeStandard(
            naics_code="541511",
            naics_description="Custom Computer Programming Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=34.0,
        ),
        SizeStandard(
            naics_code="541513",
            naics_description="Computer Facilities Management Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=34.0,
        ),
        SizeStandard(
            naics_code="541519",
            naics_description="Other Computer Related Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=34.0,
        ),

        # Cybersecurity
        SizeStandard(
            naics_code="541690",
            naics_description="Other Scientific and Technical Consulting Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=19.5,
        ),

        # Engineering
        SizeStandard(
            naics_code="541330",
            naics_description="Engineering Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=25.5,
        ),
        SizeStandard(
            naics_code="541310",
            naics_description="Architectural Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=12.5,
        ),

        # Management Consulting
        SizeStandard(
            naics_code="541611",
            naics_description="Administrative Management and General Management Consulting",
            standard_type=SizeStandardType.REVENUE,
            threshold=19.5,
        ),
        SizeStandard(
            naics_code="541612",
            naics_description="Human Resources Consulting Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=19.5,
        ),
        SizeStandard(
            naics_code="541618",
            naics_description="Other Management Consulting Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=19.5,
        ),

        # Research and Development
        SizeStandard(
            naics_code="541715",
            naics_description="Research and Development in Physical, Engineering, and Life Sciences",
            standard_type=SizeStandardType.EMPLOYEES,
            threshold=1000,
        ),
        SizeStandard(
            naics_code="541720",
            naics_description="Research and Development in Social Sciences and Humanities",
            standard_type=SizeStandardType.REVENUE,
            threshold=25.5,
        ),

        # Training
        SizeStandard(
            naics_code="611430",
            naics_description="Professional and Management Development Training",
            standard_type=SizeStandardType.REVENUE,
            threshold=15.0,
        ),

        # Support Services
        SizeStandard(
            naics_code="561110",
            naics_description="Office Administrative Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=12.5,
        ),
        SizeStandard(
            naics_code="561210",
            naics_description="Facilities Support Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=47.0,
        ),

        # Professional Services
        SizeStandard(
            naics_code="541990",
            naics_description="All Other Professional, Scientific, and Technical Services",
            standard_type=SizeStandardType.REVENUE,
            threshold=19.5,
        ),
    ]


def get_small_business_rules() -> List[SmallBusinessRule]:
    """
    Get rules for small business program eligibility.

    Returns:
        List of small business program rules
    """
    return [
        # General Small Business
        SmallBusinessRule(
            id="SB-001",
            program=SmallBusinessProgram.SMALL_BUSINESS,
            title="Size Standard Compliance",
            description="Company must meet SBA size standard for the relevant NAICS code",
            requirement="Average annual receipts (3-year) or employee count must not exceed the applicable size standard.",
            verification_method="Review company financials or employee count against SBA size standards table",
            risk_if_non_compliant="Ineligible for small business set-asides; potential fraud liability if misrepresented",
            keywords=["size standard", "annual revenue", "employee count", "receipts"],
            related_cfr="13 CFR 121",
        ),
        SmallBusinessRule(
            id="SB-002",
            program=SmallBusinessProgram.SMALL_BUSINESS,
            title="Independence Requirement",
            description="Company must be independently owned and operated",
            requirement="Company must not be dominant in its field of operation and must not be controlled by another entity.",
            verification_method="Review ownership structure and affiliation relationships",
            risk_if_non_compliant="May be deemed affiliated with larger entity, disqualifying from small business status",
            keywords=["independent", "owned", "operated", "affiliation"],
            related_cfr="13 CFR 121.103",
        ),

        # 8(a) Program
        SmallBusinessRule(
            id="8A-001",
            program=SmallBusinessProgram.SBA_8A,
            title="Socially Disadvantaged Status",
            description="Owner must be socially disadvantaged",
            requirement="At least 51% owned by individual(s) who are socially disadvantaged (presumed for certain racial/ethnic groups or demonstrated).",
            verification_method="SBA certification verification",
            risk_if_non_compliant="Ineligible for 8(a) program; potential fraud if misrepresented",
            keywords=["socially disadvantaged", "minority", "8(a)", "certification"],
            related_cfr="13 CFR 124.103",
        ),
        SmallBusinessRule(
            id="8A-002",
            program=SmallBusinessProgram.SBA_8A,
            title="Economically Disadvantaged Status",
            description="Owner must be economically disadvantaged",
            requirement="Personal net worth must not exceed $850,000 (excluding primary residence and business value).",
            verification_method="SBA financial review during certification",
            risk_if_non_compliant="Ineligible for 8(a) program",
            keywords=["economically disadvantaged", "net worth", "personal assets"],
            related_cfr="13 CFR 124.104",
        ),
        SmallBusinessRule(
            id="8A-003",
            program=SmallBusinessProgram.SBA_8A,
            title="Program Term Limit",
            description="9-year program participation limit",
            requirement="Company can only participate in the 8(a) program for 9 years total.",
            verification_method="Check program entry date and calculate remaining eligibility",
            risk_if_non_compliant="Cannot accept new 8(a) contracts after term expires",
            keywords=["program term", "9 years", "graduation", "expiration"],
            related_cfr="13 CFR 124.2",
        ),
        SmallBusinessRule(
            id="8A-004",
            program=SmallBusinessProgram.SBA_8A,
            title="Good Character",
            description="Owners must have good character",
            requirement="Principal owners must not have criminal history or lack of business integrity that would make them ineligible.",
            verification_method="SBA background check during certification",
            risk_if_non_compliant="Denial or termination of 8(a) status",
            keywords=["character", "integrity", "background"],
            related_cfr="13 CFR 124.108",
        ),

        # HUBZone
        SmallBusinessRule(
            id="HZ-001",
            program=SmallBusinessProgram.HUBZONE,
            title="Principal Office Location",
            description="Principal office must be in a HUBZone",
            requirement="The company's principal office must be located in a Historically Underutilized Business Zone.",
            verification_method="Verify address against SBA HUBZone map",
            risk_if_non_compliant="Loss of HUBZone certification",
            keywords=["principal office", "HUBZone", "location", "address"],
            related_cfr="13 CFR 126.200",
        ),
        SmallBusinessRule(
            id="HZ-002",
            program=SmallBusinessProgram.HUBZONE,
            title="Employee Residence Requirement",
            description="At least 35% of employees must reside in HUBZone",
            requirement="At least 35% of employees must reside in a HUBZone area.",
            verification_method="Review employee residence addresses against HUBZone map",
            risk_if_non_compliant="Loss of HUBZone certification",
            keywords=["employee residence", "35%", "HUBZone", "reside"],
            related_cfr="13 CFR 126.200",
        ),
        SmallBusinessRule(
            id="HZ-003",
            program=SmallBusinessProgram.HUBZONE,
            title="Attempt to Maintain",
            description="Must attempt to maintain compliance during contract performance",
            requirement="During contract performance, must 'attempt to maintain' 35% HUBZone residency requirement.",
            verification_method="Document good faith efforts to maintain compliance",
            risk_if_non_compliant="Potential contract issues if not attempting compliance",
            keywords=["attempt to maintain", "compliance", "residency"],
            related_cfr="13 CFR 126.200",
        ),

        # SDVOSB
        SmallBusinessRule(
            id="SDV-001",
            program=SmallBusinessProgram.SDVOSB,
            title="Service-Connected Disability",
            description="Owner must have service-connected disability",
            requirement="Owner must have disability rated by VA as service-connected.",
            verification_method="VA disability letter or VetCert verification",
            risk_if_non_compliant="Ineligible for SDVOSB set-asides",
            keywords=["service-connected", "disability", "VA rating", "veteran"],
            related_cfr="13 CFR 128",
        ),
        SmallBusinessRule(
            id="SDV-002",
            program=SmallBusinessProgram.SDVOSB,
            title="Ownership Requirement",
            description="51% owned by service-disabled veteran(s)",
            requirement="At least 51% unconditionally and directly owned by one or more service-disabled veterans.",
            verification_method="Review ownership documents and VetCert certification",
            risk_if_non_compliant="Ineligible for SDVOSB set-asides",
            keywords=["51%", "ownership", "unconditionally", "directly owned"],
            related_cfr="13 CFR 128.200",
        ),
        SmallBusinessRule(
            id="SDV-003",
            program=SmallBusinessProgram.SDVOSB,
            title="Control Requirement",
            description="Service-disabled veteran must control the business",
            requirement="Service-disabled veteran owner(s) must control the management and daily business operations.",
            verification_method="Review bylaws, operating agreements, and actual operations",
            risk_if_non_compliant="Ineligible for SDVOSB set-asides",
            keywords=["control", "management", "daily operations"],
            related_cfr="13 CFR 128.202",
        ),
        SmallBusinessRule(
            id="SDV-004",
            program=SmallBusinessProgram.SDVOSB,
            title="SBA VetCert Certification",
            description="Must be certified through SBA VetCert",
            requirement="As of January 2023, SDVOSB status requires certification through SBA's VetCert program.",
            verification_method="Verify active VetCert certification in SAM.gov",
            risk_if_non_compliant="Cannot compete for SDVOSB set-asides without VetCert",
            keywords=["VetCert", "SBA certification", "SDVOSB certification"],
            related_cfr="13 CFR 128",
        ),

        # VOSB
        SmallBusinessRule(
            id="VOSB-001",
            program=SmallBusinessProgram.VOSB,
            title="Veteran Status",
            description="Owner must be a veteran",
            requirement="At least 51% owned by one or more veterans (including service-disabled veterans).",
            verification_method="DD-214 and VetCert verification",
            risk_if_non_compliant="Ineligible for VOSB set-asides",
            keywords=["veteran", "DD-214", "military service"],
            related_cfr="13 CFR 128",
        ),

        # WOSB
        SmallBusinessRule(
            id="WOSB-001",
            program=SmallBusinessProgram.WOSB,
            title="Women Ownership",
            description="51% owned by women",
            requirement="At least 51% unconditionally and directly owned by one or more women who are U.S. citizens.",
            verification_method="SBA WOSB certification or approved third-party certifier",
            risk_if_non_compliant="Ineligible for WOSB set-asides",
            keywords=["women-owned", "51%", "unconditionally", "woman"],
            related_cfr="13 CFR 127",
        ),
        SmallBusinessRule(
            id="WOSB-002",
            program=SmallBusinessProgram.WOSB,
            title="Women Control",
            description="Women must control management and operations",
            requirement="Women owners must control management and daily business operations and make long-term decisions.",
            verification_method="Review operating agreements and governance documents",
            risk_if_non_compliant="Ineligible for WOSB set-asides",
            keywords=["control", "management", "operations", "decision-making"],
            related_cfr="13 CFR 127.202",
        ),

        # EDWOSB
        SmallBusinessRule(
            id="EDWOSB-001",
            program=SmallBusinessProgram.EDWOSB,
            title="Economically Disadvantaged Women",
            description="Women owners must be economically disadvantaged",
            requirement="Personal net worth must not exceed $850,000, and average adjusted gross income must not exceed $400,000.",
            verification_method="SBA EDWOSB certification",
            risk_if_non_compliant="May only compete for WOSB, not EDWOSB set-asides",
            keywords=["economically disadvantaged", "net worth", "income", "EDWOSB"],
            related_cfr="13 CFR 127.203",
        ),
    ]
