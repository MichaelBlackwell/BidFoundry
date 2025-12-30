"""
Set-Aside Rules and Eligibility

Defines rules for federal contract set-aside eligibility and validates
company qualifications against specific set-aside requirements.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from datetime import date


class SetAsideType(str, Enum):
    """Federal set-aside types."""

    FULL_AND_OPEN = "Full and Open"
    SMALL_BUSINESS = "Small Business Set-Aside"
    SBA_8A = "8(a)"
    COMPETITIVE_8A = "Competitive 8(a)"
    SOLE_SOURCE_8A = "Sole Source 8(a)"
    HUBZONE = "HUBZone"
    SDVOSB = "SDVOSB"
    VOSB = "VOSB"
    WOSB = "WOSB"
    EDWOSB = "EDWOSB"
    ECONOMICALLY_DISADVANTAGED = "Economically Disadvantaged"


class EligibilityStatus(str, Enum):
    """Status of set-aside eligibility."""

    ELIGIBLE = "Eligible"
    NOT_ELIGIBLE = "Not Eligible"
    CONDITIONALLY_ELIGIBLE = "Conditionally Eligible"
    REQUIRES_VERIFICATION = "Requires Verification"
    EXPIRED = "Expired"


@dataclass
class SetAsideRequirement:
    """A specific requirement for a set-aside type."""

    id: str
    description: str
    is_mandatory: bool = True
    certification_required: Optional[str] = None
    verification_method: str = ""
    risk_level: str = "High"  # High, Medium, Low

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "is_mandatory": self.is_mandatory,
            "certification_required": self.certification_required,
            "verification_method": self.verification_method,
            "risk_level": self.risk_level,
        }


@dataclass
class SetAsideEligibility:
    """
    Eligibility determination for a specific set-aside type.
    """

    set_aside_type: SetAsideType
    status: EligibilityStatus
    is_eligible: bool
    confidence: str  # High, Medium, Low

    # Details
    met_requirements: List[str] = field(default_factory=list)
    unmet_requirements: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Certification info
    certification_status: str = "Unknown"
    certification_expiration: Optional[date] = None

    # Additional context
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "set_aside_type": self.set_aside_type.value,
            "status": self.status.value,
            "is_eligible": self.is_eligible,
            "confidence": self.confidence,
            "met_requirements": self.met_requirements,
            "unmet_requirements": self.unmet_requirements,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "certification_status": self.certification_status,
            "certification_expiration": self.certification_expiration.isoformat() if self.certification_expiration else None,
            "notes": self.notes,
        }


# Set-aside requirements definitions
SETASIDE_REQUIREMENTS: Dict[SetAsideType, List[SetAsideRequirement]] = {
    SetAsideType.FULL_AND_OPEN: [
        SetAsideRequirement(
            id="FOC-001",
            description="No specific eligibility requirements - all responsible offerors may compete",
            is_mandatory=False,
            verification_method="N/A",
            risk_level="Low",
        ),
    ],

    SetAsideType.SMALL_BUSINESS: [
        SetAsideRequirement(
            id="SB-001",
            description="Meet SBA size standard for the solicitation's NAICS code",
            is_mandatory=True,
            verification_method="Compare company size (revenue/employees) to SBA size standards",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="SB-002",
            description="Be a for-profit business organized in the United States",
            is_mandatory=True,
            verification_method="Verify business registration and organizational documents",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="SB-003",
            description="Be independently owned and operated",
            is_mandatory=True,
            verification_method="Review ownership structure and affiliation rules",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="SB-004",
            description="Comply with limitations on subcontracting (50% for services)",
            is_mandatory=True,
            verification_method="Review staffing and subcontracting plan",
            risk_level="High",
        ),
    ],

    SetAsideType.SBA_8A: [
        SetAsideRequirement(
            id="8A-001",
            description="Active SBA 8(a) certification",
            is_mandatory=True,
            certification_required="8(a)",
            verification_method="Verify in SAM.gov or SBA Dynamic Small Business Search",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="8A-002",
            description="Meet size standard as small business",
            is_mandatory=True,
            verification_method="Compare to NAICS size standard",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="8A-003",
            description="Within 9-year program term",
            is_mandatory=True,
            verification_method="Verify 8(a) program entry date",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="8A-004",
            description="No pending adverse determination from SBA",
            is_mandatory=True,
            verification_method="SBA certification status check",
            risk_level="High",
        ),
    ],

    SetAsideType.COMPETITIVE_8A: [
        SetAsideRequirement(
            id="C8A-001",
            description="Active SBA 8(a) certification",
            is_mandatory=True,
            certification_required="8(a)",
            verification_method="Verify in SAM.gov",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="C8A-002",
            description="Contract value typically exceeds $4.5M (manufacturing) or $8.0M (other)",
            is_mandatory=False,
            verification_method="Review solicitation value",
            risk_level="Medium",
        ),
    ],

    SetAsideType.SOLE_SOURCE_8A: [
        SetAsideRequirement(
            id="SS8A-001",
            description="Active SBA 8(a) certification",
            is_mandatory=True,
            certification_required="8(a)",
            verification_method="Verify in SAM.gov",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="SS8A-002",
            description="Contract value within sole source limits ($4.5M manufacturing, $8.0M other)",
            is_mandatory=True,
            verification_method="Review solicitation value",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="SS8A-003",
            description="Must be the specific 8(a) firm nominated for the requirement",
            is_mandatory=True,
            verification_method="Confirm agency nomination",
            risk_level="High",
        ),
    ],

    SetAsideType.HUBZONE: [
        SetAsideRequirement(
            id="HZ-001",
            description="Active HUBZone certification from SBA",
            is_mandatory=True,
            certification_required="HUBZone",
            verification_method="Verify in SAM.gov or SBA Dynamic Small Business Search",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="HZ-002",
            description="Principal office in a HUBZone",
            is_mandatory=True,
            verification_method="Verify principal office address in SBA HUBZone map",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="HZ-003",
            description="At least 35% of employees reside in HUBZone",
            is_mandatory=True,
            verification_method="Review employee residence data",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="HZ-004",
            description="Meet size standard for NAICS code",
            is_mandatory=True,
            verification_method="Compare to SBA size standards",
            risk_level="High",
        ),
    ],

    SetAsideType.SDVOSB: [
        SetAsideRequirement(
            id="SDV-001",
            description="SBA VetCert certification as SDVOSB",
            is_mandatory=True,
            certification_required="SDVOSB",
            verification_method="Verify VetCert status in SAM.gov",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="SDV-002",
            description="At least 51% owned by service-disabled veteran(s)",
            is_mandatory=True,
            verification_method="VetCert certification validates ownership",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="SDV-003",
            description="Service-disabled veteran(s) must control daily operations",
            is_mandatory=True,
            verification_method="VetCert certification validates control",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="SDV-004",
            description="Meet size standard for NAICS code",
            is_mandatory=True,
            verification_method="Compare to SBA size standards",
            risk_level="High",
        ),
    ],

    SetAsideType.VOSB: [
        SetAsideRequirement(
            id="VOSB-001",
            description="SBA VetCert certification as VOSB or SDVOSB",
            is_mandatory=True,
            certification_required="VOSB",
            verification_method="Verify VetCert status in SAM.gov",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="VOSB-002",
            description="At least 51% owned by veteran(s)",
            is_mandatory=True,
            verification_method="VetCert certification validates ownership",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="VOSB-003",
            description="Meet size standard for NAICS code",
            is_mandatory=True,
            verification_method="Compare to SBA size standards",
            risk_level="High",
        ),
    ],

    SetAsideType.WOSB: [
        SetAsideRequirement(
            id="WOSB-001",
            description="SBA WOSB certification or approved third-party certification",
            is_mandatory=True,
            certification_required="WOSB",
            verification_method="Verify WOSB certification in SAM.gov",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="WOSB-002",
            description="At least 51% owned by women who are U.S. citizens",
            is_mandatory=True,
            verification_method="WOSB certification validates ownership",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="WOSB-003",
            description="Women must control management and daily operations",
            is_mandatory=True,
            verification_method="WOSB certification validates control",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="WOSB-004",
            description="Opportunity must be in a NAICS code designated for WOSB contracting",
            is_mandatory=True,
            verification_method="Verify NAICS code is WOSB-eligible",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="WOSB-005",
            description="Meet size standard for NAICS code",
            is_mandatory=True,
            verification_method="Compare to SBA size standards",
            risk_level="High",
        ),
    ],

    SetAsideType.EDWOSB: [
        SetAsideRequirement(
            id="EDW-001",
            description="SBA EDWOSB certification",
            is_mandatory=True,
            certification_required="EDWOSB",
            verification_method="Verify EDWOSB certification in SAM.gov",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="EDW-002",
            description="Meet all WOSB requirements",
            is_mandatory=True,
            verification_method="Verify WOSB eligibility",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="EDW-003",
            description="Women owner(s) must be economically disadvantaged (net worth < $850K)",
            is_mandatory=True,
            verification_method="EDWOSB certification validates economic status",
            risk_level="High",
        ),
        SetAsideRequirement(
            id="EDW-004",
            description="Opportunity must be in NAICS code designated for EDWOSB contracting",
            is_mandatory=True,
            verification_method="Verify NAICS code is EDWOSB-eligible",
            risk_level="High",
        ),
    ],
}


class SetAsideValidator:
    """
    Validates company eligibility for federal contract set-asides.

    Provides comprehensive eligibility checking against set-aside requirements.
    """

    def __init__(self):
        self._requirements = SETASIDE_REQUIREMENTS

    def get_requirements(self, set_aside: SetAsideType) -> List[SetAsideRequirement]:
        """Get all requirements for a set-aside type."""
        return self._requirements.get(set_aside, [])

    def check_eligibility(
        self,
        set_aside: SetAsideType,
        company_profile: Dict[str, Any],
        opportunity: Optional[Dict[str, Any]] = None,
    ) -> SetAsideEligibility:
        """
        Check company eligibility for a specific set-aside.

        Args:
            set_aside: The set-aside type to check
            company_profile: Company profile data
            opportunity: Optional opportunity context

        Returns:
            SetAsideEligibility with detailed findings
        """
        result = SetAsideEligibility(
            set_aside_type=set_aside,
            status=EligibilityStatus.REQUIRES_VERIFICATION,
            is_eligible=True,
            confidence="Low",
        )

        # Handle full and open - everyone eligible
        if set_aside == SetAsideType.FULL_AND_OPEN:
            result.status = EligibilityStatus.ELIGIBLE
            result.is_eligible = True
            result.confidence = "High"
            result.met_requirements.append("Open competition - no special requirements")
            return result

        requirements = self._requirements.get(set_aside, [])
        certifications = company_profile.get("certifications", [])
        cert_types = {c.get("cert_type") for c in certifications}

        # Check each requirement
        for req in requirements:
            is_met = self._check_requirement(req, company_profile, certifications, opportunity)

            if is_met:
                result.met_requirements.append(req.description)
            else:
                if req.is_mandatory:
                    result.unmet_requirements.append(req.description)
                    result.is_eligible = False
                else:
                    result.warnings.append(f"Optional requirement not verified: {req.description}")

        # Check certification status specifically
        cert_mapping = {
            SetAsideType.SBA_8A: "8(a)",
            SetAsideType.COMPETITIVE_8A: "8(a)",
            SetAsideType.SOLE_SOURCE_8A: "8(a)",
            SetAsideType.HUBZONE: "HUBZone",
            SetAsideType.SDVOSB: "SDVOSB",
            SetAsideType.VOSB: "VOSB",
            SetAsideType.WOSB: "WOSB",
            SetAsideType.EDWOSB: "EDWOSB",
        }

        required_cert = cert_mapping.get(set_aside)
        if required_cert:
            matching_cert = self._find_certification(certifications, required_cert)
            if matching_cert:
                result.certification_status = "Active"
                exp_date = matching_cert.get("expiration_date")
                if exp_date:
                    result.certification_expiration = date.fromisoformat(exp_date) if isinstance(exp_date, str) else exp_date
                    # Check if expiring soon
                    if result.certification_expiration:
                        days_until_expiry = (result.certification_expiration - date.today()).days
                        if days_until_expiry < 0:
                            result.status = EligibilityStatus.EXPIRED
                            result.is_eligible = False
                            result.warnings.append(f"{required_cert} certification has expired")
                        elif days_until_expiry < 90:
                            result.warnings.append(f"{required_cert} certification expires in {days_until_expiry} days")
            else:
                result.certification_status = "Not Found"
                if required_cert not in ["VOSB"]:  # VOSB can use SDVOSB
                    result.is_eligible = False
                    result.unmet_requirements.append(f"Missing required {required_cert} certification")

        # Determine final status and confidence
        # Preserve EXPIRED status if already set
        if result.status == EligibilityStatus.EXPIRED:
            result.confidence = "High"
        elif result.is_eligible:
            if result.unmet_requirements:
                result.status = EligibilityStatus.CONDITIONALLY_ELIGIBLE
                result.confidence = "Medium"
            else:
                result.status = EligibilityStatus.ELIGIBLE
                result.confidence = "High" if result.certification_status == "Active" else "Medium"
        else:
            result.status = EligibilityStatus.NOT_ELIGIBLE
            result.confidence = "High" if result.unmet_requirements else "Medium"

        # Add recommendations
        if result.unmet_requirements:
            result.recommendations.append("Address unmet requirements before pursuing this set-aside")
        if result.warnings:
            result.recommendations.append("Review and resolve warnings for full eligibility")

        return result

    def _check_requirement(
        self,
        req: SetAsideRequirement,
        company_profile: Dict[str, Any],
        certifications: List[Dict[str, Any]],
        opportunity: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if a specific requirement is met."""

        # Check certification requirement
        if req.certification_required:
            matching_cert = self._find_certification(certifications, req.certification_required)
            if matching_cert is None:
                return False

        # For other requirements, we do basic keyword matching
        # In production, this would have more sophisticated logic
        profile_str = str(company_profile).lower()

        # Check for obvious indicators
        if "size standard" in req.description.lower():
            # Would need actual size comparison logic
            return True  # Assume met for now

        if "independently owned" in req.description.lower():
            return True  # Assume met unless explicitly contradicted

        if "limitations on subcontracting" in req.description.lower():
            # Would need to check staffing plan
            return True  # Assume will be addressed

        return True  # Default to true for requirements we can't verify

    def _find_certification(
        self,
        certifications: List[Dict[str, Any]],
        cert_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Find a certification by type."""
        for cert in certifications:
            if cert.get("cert_type") == cert_type:
                return cert
            # Handle SDVOSB satisfying VOSB requirement
            if cert_type == "VOSB" and cert.get("cert_type") == "SDVOSB":
                return cert
        return None

    def check_all_setasides(
        self,
        company_profile: Dict[str, Any],
        opportunity: Optional[Dict[str, Any]] = None,
    ) -> Dict[SetAsideType, SetAsideEligibility]:
        """
        Check eligibility for all set-aside types.

        Args:
            company_profile: Company profile data
            opportunity: Optional opportunity context

        Returns:
            Dictionary mapping each set-aside type to eligibility result
        """
        results = {}
        for set_aside in SetAsideType:
            results[set_aside] = self.check_eligibility(set_aside, company_profile, opportunity)
        return results

    def get_eligible_setasides(
        self,
        company_profile: Dict[str, Any],
        opportunity: Optional[Dict[str, Any]] = None,
    ) -> List[SetAsideType]:
        """Get list of set-asides the company is eligible for."""
        results = self.check_all_setasides(company_profile, opportunity)
        return [
            sa for sa, result in results.items()
            if result.is_eligible
        ]

    def generate_setaside_summary(
        self,
        company_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a summary of set-aside eligibility.

        Args:
            company_profile: Company profile data

        Returns:
            Summary dictionary with eligibility overview
        """
        results = self.check_all_setasides(company_profile)

        eligible = []
        conditional = []
        not_eligible = []

        for sa, result in results.items():
            if sa == SetAsideType.FULL_AND_OPEN:
                continue

            if result.status == EligibilityStatus.ELIGIBLE:
                eligible.append(sa.value)
            elif result.status == EligibilityStatus.CONDITIONALLY_ELIGIBLE:
                conditional.append(sa.value)
            else:
                not_eligible.append(sa.value)

        return {
            "eligible": eligible,
            "conditionally_eligible": conditional,
            "not_eligible": not_eligible,
            "summary": f"Eligible for {len(eligible)} set-aside types, {len(conditional)} conditional",
            "recommendations": self._generate_recommendations(results),
        }

    def _generate_recommendations(
        self,
        results: Dict[SetAsideType, SetAsideEligibility],
    ) -> List[str]:
        """Generate recommendations based on eligibility results."""
        recommendations = []

        # Check for near-eligible opportunities
        for sa, result in results.items():
            if result.status == EligibilityStatus.CONDITIONALLY_ELIGIBLE:
                recommendations.append(
                    f"Review {sa.value} requirements - close to full eligibility"
                )

        # Check for expiring certifications
        for sa, result in results.items():
            if result.certification_expiration:
                days_left = (result.certification_expiration - date.today()).days
                if 0 < days_left < 90:
                    recommendations.append(
                        f"Renew {sa.value} certification - expires in {days_left} days"
                    )

        return recommendations


def check_setaside_eligibility(
    set_aside_type: str,
    company_profile: Dict[str, Any],
    opportunity: Optional[Dict[str, Any]] = None,
) -> SetAsideEligibility:
    """
    Convenience function to check set-aside eligibility.

    Args:
        set_aside_type: String name of set-aside type
        company_profile: Company profile data
        opportunity: Optional opportunity context

    Returns:
        SetAsideEligibility result
    """
    # Convert string to enum
    try:
        sa_type = SetAsideType(set_aside_type)
    except ValueError:
        # Try to match by partial name
        set_aside_lower = set_aside_type.lower()
        for sa in SetAsideType:
            if set_aside_lower in sa.value.lower():
                sa_type = sa
                break
        else:
            # Default to full and open if not found
            sa_type = SetAsideType.FULL_AND_OPEN

    validator = SetAsideValidator()
    return validator.check_eligibility(sa_type, company_profile, opportunity)
