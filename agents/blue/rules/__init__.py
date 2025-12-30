"""
Compliance Rules Module

Contains rule definitions and validation logic for federal contracting
compliance, including FAR/DFAR rules, small business regulations, and
set-aside eligibility requirements.
"""

from .far_rules import (
    FARRule,
    FARSubpart,
    FARComplianceChecker,
    ComplianceCheckResult,
    ComplianceStatus,
    RiskLevel,
    get_common_far_rules,
)
from .small_business_rules import (
    SmallBusinessRule,
    SmallBusinessProgram,
    SmallBusinessValidator,
    EligibilityCheckResult,
    SizeStandard,
    SizeStandardType,
    get_size_standard,
    get_common_size_standards,
)
from .setaside_rules import (
    SetAsideEligibility,
    SetAsideType,
    SetAsideValidator,
    EligibilityStatus,
    check_setaside_eligibility,
)

__all__ = [
    # FAR
    "FARRule",
    "FARSubpart",
    "FARComplianceChecker",
    "ComplianceCheckResult",
    "ComplianceStatus",
    "RiskLevel",
    "get_common_far_rules",
    # Small Business
    "SmallBusinessRule",
    "SmallBusinessProgram",
    "SmallBusinessValidator",
    "EligibilityCheckResult",
    "SizeStandard",
    "SizeStandardType",
    "get_size_standard",
    "get_common_size_standards",
    # Set-Aside
    "SetAsideEligibility",
    "SetAsideType",
    "SetAsideValidator",
    "EligibilityStatus",
    "check_setaside_eligibility",
]
