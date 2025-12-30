"""
Company Profile Model

Defines the structure for capturing company information relevant to
GovCon strategy development, including NAICS codes, certifications,
past performance, and core capabilities.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional
import json
import uuid


class BusinessStatus(str, Enum):
    """Business operational status."""

    ACTIVE = "Active"
    STARTUP = "Startup"
    PRE_REVENUE = "Pre-Revenue"
    DORMANT = "Dormant"
    DISSOLVED = "Dissolved"


class OwnershipType(str, Enum):
    """Type of ownership stake."""

    MEMBER = "Member"  # LLC
    SHAREHOLDER = "Shareholder"  # Corporation
    PARTNER = "Partner"  # Partnership
    SOLE_PROPRIETOR = "Sole Proprietor"


class CertificationType(str, Enum):
    """Federal small business certification types."""

    SBA_8A = "8(a)"
    HUBZONE = "HUBZone"
    SDVOSB = "SDVOSB"  # Service-Disabled Veteran-Owned Small Business
    VOSB = "VOSB"  # Veteran-Owned Small Business
    WOSB = "WOSB"  # Women-Owned Small Business
    EDWOSB = "EDWOSB"  # Economically Disadvantaged WOSB
    SMALL_BUSINESS = "Small Business"
    LARGE_BUSINESS = "Large Business"

    # GSA Schedules
    GSA_MAS = "GSA MAS"  # Multiple Award Schedule
    GSA_STARS_III = "GSA STARS III"
    GSA_OASIS = "GSA OASIS"
    GSA_ALLIANT = "GSA Alliant"

    # Security Clearances
    FACILITY_CLEARANCE = "Facility Clearance"

    # Quality Certifications
    ISO_9001 = "ISO 9001"
    ISO_27001 = "ISO 27001"
    CMMI_DEV = "CMMI DEV"
    CMMC = "CMMC"
    FEDRAMP = "FedRAMP"


class PerformanceRating(str, Enum):
    """CPARS performance rating scale."""

    EXCEPTIONAL = "Exceptional"
    VERY_GOOD = "Very Good"
    SATISFACTORY = "Satisfactory"
    MARGINAL = "Marginal"
    UNSATISFACTORY = "Unsatisfactory"
    NOT_RATED = "Not Rated"


@dataclass
class NAICSCode:
    """NAICS code with primary/secondary designation."""

    code: str
    description: str
    is_primary: bool = False
    small_business_size_standard: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "description": self.description,
            "is_primary": self.is_primary,
            "small_business_size_standard": self.small_business_size_standard,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NAICSCode":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "NAICSCode":
        return cls.from_dict(json.loads(json_str))


@dataclass
class Address:
    """Physical address for business locations."""

    street1: str
    city: str
    state: str
    zip_code: str
    street2: Optional[str] = None
    country: str = "USA"

    def to_dict(self) -> dict:
        return {
            "street1": self.street1,
            "street2": self.street2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Address":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Address":
        return cls.from_dict(json.loads(json_str))

    @property
    def full_address(self) -> str:
        """Return formatted full address."""
        parts = [self.street1]
        if self.street2:
            parts.append(self.street2)
        parts.append(f"{self.city}, {self.state} {self.zip_code}")
        if self.country != "USA":
            parts.append(self.country)
        return ", ".join(parts)


@dataclass
class OwnershipStake:
    """Ownership stake in the company."""

    name: str
    ownership_type: OwnershipType
    percentage: float  # 0-100
    title: Optional[str] = None  # e.g., "Managing Member", "CEO"
    is_veteran: bool = False
    is_service_disabled_veteran: bool = False
    is_woman: bool = False
    is_disadvantaged: bool = False  # For 8(a) purposes

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ownership_type": self.ownership_type.value,
            "percentage": self.percentage,
            "title": self.title,
            "is_veteran": self.is_veteran,
            "is_service_disabled_veteran": self.is_service_disabled_veteran,
            "is_woman": self.is_woman,
            "is_disadvantaged": self.is_disadvantaged,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OwnershipStake":
        return cls(
            name=data["name"],
            ownership_type=OwnershipType(data["ownership_type"]),
            percentage=data["percentage"],
            title=data.get("title"),
            is_veteran=data.get("is_veteran", False),
            is_service_disabled_veteran=data.get("is_service_disabled_veteran", False),
            is_woman=data.get("is_woman", False),
            is_disadvantaged=data.get("is_disadvantaged", False),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "OwnershipStake":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ManagementMember:
    """Management team member (officers, managers, key personnel)."""

    name: str
    title: str  # e.g., "CEO", "CFO", "Managing Member"
    role_description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "role_description": self.role_description,
            "email": self.email,
            "phone": self.phone,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ManagementMember":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ManagementMember":
        return cls.from_dict(json.loads(json_str))


@dataclass
class EmployeeResidenceInfo:
    """Employee residence location for HUBZone calculations."""

    zip_code: str
    employee_count: int
    is_hubzone: bool = False

    def to_dict(self) -> dict:
        return {
            "zip_code": self.zip_code,
            "employee_count": self.employee_count,
            "is_hubzone": self.is_hubzone,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmployeeResidenceInfo":
        return cls(**data)


@dataclass
class HUBZoneInfo:
    """HUBZone-specific information for certification compliance."""

    principal_office_in_hubzone: bool = False
    principal_office_address: Optional[Address] = None
    employee_residences: List[EmployeeResidenceInfo] = field(default_factory=list)
    hubzone_designation: Optional[str] = None  # e.g., "Qualified Census Tract"

    @property
    def hubzone_employee_percentage(self) -> float:
        """Calculate percentage of employees residing in HUBZone areas."""
        if not self.employee_residences:
            return 0.0
        total = sum(e.employee_count for e in self.employee_residences)
        if total == 0:
            return 0.0
        hubzone_count = sum(e.employee_count for e in self.employee_residences if e.is_hubzone)
        return (hubzone_count / total) * 100

    def to_dict(self) -> dict:
        return {
            "principal_office_in_hubzone": self.principal_office_in_hubzone,
            "principal_office_address": self.principal_office_address.to_dict() if self.principal_office_address else None,
            "employee_residences": [e.to_dict() for e in self.employee_residences],
            "hubzone_designation": self.hubzone_designation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HUBZoneInfo":
        return cls(
            principal_office_in_hubzone=data.get("principal_office_in_hubzone", False),
            principal_office_address=Address.from_dict(data["principal_office_address"]) if data.get("principal_office_address") else None,
            employee_residences=[EmployeeResidenceInfo.from_dict(e) for e in data.get("employee_residences", [])],
            hubzone_designation=data.get("hubzone_designation"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "HUBZoneInfo":
        return cls.from_dict(json.loads(json_str))


@dataclass
class FederalContractingHistory:
    """Summary of prior federal contracting experience."""

    has_federal_contracts: bool = False
    total_contracts: int = 0
    total_value: float = 0.0
    first_contract_date: Optional[date] = None
    agencies_worked_with: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "has_federal_contracts": self.has_federal_contracts,
            "total_contracts": self.total_contracts,
            "total_value": self.total_value,
            "first_contract_date": self.first_contract_date.isoformat() if self.first_contract_date else None,
            "agencies_worked_with": self.agencies_worked_with,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FederalContractingHistory":
        return cls(
            has_federal_contracts=data.get("has_federal_contracts", False),
            total_contracts=data.get("total_contracts", 0),
            total_value=data.get("total_value", 0.0),
            first_contract_date=date.fromisoformat(data["first_contract_date"]) if data.get("first_contract_date") else None,
            agencies_worked_with=data.get("agencies_worked_with", []),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "FederalContractingHistory":
        return cls.from_dict(json.loads(json_str))


@dataclass
class Certification:
    """Company certification with validity dates."""

    cert_type: CertificationType
    issuing_authority: str
    issue_date: date
    expiration_date: Optional[date] = None
    certification_number: Optional[str] = None
    level: Optional[str] = None  # e.g., CMMC Level 2, CMMI Level 3

    @property
    def is_valid(self) -> bool:
        """Check if certification is currently valid."""
        if self.expiration_date is None:
            return True
        return date.today() <= self.expiration_date

    def to_dict(self) -> dict:
        return {
            "cert_type": self.cert_type.value,
            "issuing_authority": self.issuing_authority,
            "issue_date": self.issue_date.isoformat(),
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "certification_number": self.certification_number,
            "level": self.level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Certification":
        return cls(
            cert_type=CertificationType(data["cert_type"]),
            issuing_authority=data["issuing_authority"],
            issue_date=date.fromisoformat(data["issue_date"]),
            expiration_date=date.fromisoformat(data["expiration_date"]) if data.get("expiration_date") else None,
            certification_number=data.get("certification_number"),
            level=data.get("level"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Certification":
        return cls.from_dict(json.loads(json_str))


@dataclass
class PastPerformance:
    """Past performance record for a completed or ongoing contract."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    contract_number: str = ""
    contract_name: str = ""
    agency: str = ""
    contracting_office: Optional[str] = None

    # Contract details
    contract_value: float = 0.0
    period_of_performance_start: Optional[date] = None
    period_of_performance_end: Optional[date] = None
    contract_type: str = ""  # FFP, T&M, Cost-Plus, etc.

    # Performance metrics
    overall_rating: PerformanceRating = PerformanceRating.NOT_RATED
    quality_rating: Optional[PerformanceRating] = None
    schedule_rating: Optional[PerformanceRating] = None
    cost_control_rating: Optional[PerformanceRating] = None
    management_rating: Optional[PerformanceRating] = None

    # Relevance
    naics_codes: List[str] = field(default_factory=list)
    description: str = ""
    key_accomplishments: List[str] = field(default_factory=list)
    relevance_keywords: List[str] = field(default_factory=list)

    # Reference
    reference_name: Optional[str] = None
    reference_title: Optional[str] = None
    reference_phone: Optional[str] = None
    reference_email: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "contract_number": self.contract_number,
            "contract_name": self.contract_name,
            "agency": self.agency,
            "contracting_office": self.contracting_office,
            "contract_value": self.contract_value,
            "period_of_performance_start": self.period_of_performance_start.isoformat() if self.period_of_performance_start else None,
            "period_of_performance_end": self.period_of_performance_end.isoformat() if self.period_of_performance_end else None,
            "contract_type": self.contract_type,
            "overall_rating": self.overall_rating.value,
            "quality_rating": self.quality_rating.value if self.quality_rating else None,
            "schedule_rating": self.schedule_rating.value if self.schedule_rating else None,
            "cost_control_rating": self.cost_control_rating.value if self.cost_control_rating else None,
            "management_rating": self.management_rating.value if self.management_rating else None,
            "naics_codes": self.naics_codes,
            "description": self.description,
            "key_accomplishments": self.key_accomplishments,
            "relevance_keywords": self.relevance_keywords,
            "reference_name": self.reference_name,
            "reference_title": self.reference_title,
            "reference_phone": self.reference_phone,
            "reference_email": self.reference_email,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PastPerformance":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            contract_number=data.get("contract_number", ""),
            contract_name=data.get("contract_name", ""),
            agency=data.get("agency", ""),
            contracting_office=data.get("contracting_office"),
            contract_value=data.get("contract_value", 0.0),
            period_of_performance_start=date.fromisoformat(data["period_of_performance_start"]) if data.get("period_of_performance_start") else None,
            period_of_performance_end=date.fromisoformat(data["period_of_performance_end"]) if data.get("period_of_performance_end") else None,
            contract_type=data.get("contract_type", ""),
            overall_rating=PerformanceRating(data.get("overall_rating", "Not Rated")),
            quality_rating=PerformanceRating(data["quality_rating"]) if data.get("quality_rating") else None,
            schedule_rating=PerformanceRating(data["schedule_rating"]) if data.get("schedule_rating") else None,
            cost_control_rating=PerformanceRating(data["cost_control_rating"]) if data.get("cost_control_rating") else None,
            management_rating=PerformanceRating(data["management_rating"]) if data.get("management_rating") else None,
            naics_codes=data.get("naics_codes", []),
            description=data.get("description", ""),
            key_accomplishments=data.get("key_accomplishments", []),
            relevance_keywords=data.get("relevance_keywords", []),
            reference_name=data.get("reference_name"),
            reference_title=data.get("reference_title"),
            reference_phone=data.get("reference_phone"),
            reference_email=data.get("reference_email"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "PastPerformance":
        return cls.from_dict(json.loads(json_str))


@dataclass
class TeamMember:
    """Key personnel information."""

    name: str
    title: str
    role: str  # Role on potential contract
    years_experience: int = 0
    clearance_level: Optional[str] = None
    certifications: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    relevant_experience: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "role": self.role,
            "years_experience": self.years_experience,
            "clearance_level": self.clearance_level,
            "certifications": self.certifications,
            "education": self.education,
            "relevant_experience": self.relevant_experience,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TeamMember":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "TeamMember":
        return cls.from_dict(json.loads(json_str))


@dataclass
class CoreCapability:
    """Core competency or service offering."""

    name: str
    description: str
    differentiators: List[str] = field(default_factory=list)
    relevant_naics: List[str] = field(default_factory=list)
    proof_points: List[str] = field(default_factory=list)  # References to past performance
    maturity_level: str = "Established"  # Emerging, Established, Market Leader

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "differentiators": self.differentiators,
            "relevant_naics": self.relevant_naics,
            "proof_points": self.proof_points,
            "maturity_level": self.maturity_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoreCapability":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CoreCapability":
        return cls.from_dict(json.loads(json_str))


@dataclass
class CompanyProfile:
    """
    Complete company profile for GovCon strategy development.

    This is the primary input for the Strategy Architect and other
    blue team agents when generating strategy documents.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Basic Information
    name: str = ""
    duns_number: Optional[str] = None
    uei_number: Optional[str] = None  # Unique Entity Identifier (replaced DUNS)
    cage_code: Optional[str] = None

    # === Company Fundamentals ===
    formation_date: Optional[date] = None  # Legal business formation date (incorporation/LLC)
    business_status: BusinessStatus = BusinessStatus.ACTIVE
    fiscal_year_end: Optional[str] = None  # e.g., "December 31" or "September 30"

    # Size and Structure
    employee_count: int = 0  # Current FTE count
    employee_headcount: Optional[int] = None  # Total headcount including contractors
    annual_revenue: float = 0.0  # Last fiscal year revenue
    revenue_is_ytd: bool = False  # True if revenue is YTD for pre-revenue companies
    years_in_business: int = 0
    headquarters_location: str = ""  # Legacy field - use principal_address for full address

    # === Principal Place of Business ===
    principal_address: Optional[Address] = None

    # === Ownership & Control ===
    ownership_structure: List[OwnershipStake] = field(default_factory=list)
    management_team: List[ManagementMember] = field(default_factory=list)

    # Socioeconomic Status Flags (for certification eligibility)
    veteran_owned: bool = False  # For VOSB certification
    service_disabled_veteran_owned: bool = False  # For SDVOSB certification
    woman_owned: bool = False  # For WOSB/EDWOSB certification
    economically_disadvantaged_woman_owned: bool = False  # For EDWOSB
    disadvantaged_business: bool = False  # For 8(a) certification

    # === Certification & Compliance ===
    sam_registration_status: str = ""  # "Active", "Inactive", "Pending", "Not Registered"
    sam_registration_date: Optional[date] = None
    sam_expiration_date: Optional[date] = None

    # Federal Contracting History
    federal_contracting_history: Optional[FederalContractingHistory] = None

    # === Geographic Information (HUBZone) ===
    hubzone_info: Optional[HUBZoneInfo] = None

    # GovCon Specific
    naics_codes: List[NAICSCode] = field(default_factory=list)
    certifications: List[Certification] = field(default_factory=list)
    past_performance: List[PastPerformance] = field(default_factory=list)

    # Capabilities
    core_capabilities: List[CoreCapability] = field(default_factory=list)
    key_personnel: List[TeamMember] = field(default_factory=list)

    # Strategic Context
    target_agencies: List[str] = field(default_factory=list)
    geographic_coverage: List[str] = field(default_factory=list)
    security_clearances: List[str] = field(default_factory=list)  # Facility clearance levels

    # Teaming
    existing_prime_relationships: List[str] = field(default_factory=list)
    existing_sub_relationships: List[str] = field(default_factory=list)
    teaming_preferences: str = ""

    @property
    def primary_naics(self) -> Optional[NAICSCode]:
        """Get the primary NAICS code."""
        for naics in self.naics_codes:
            if naics.is_primary:
                return naics
        return self.naics_codes[0] if self.naics_codes else None

    @property
    def valid_certifications(self) -> List[Certification]:
        """Get all currently valid certifications."""
        return [cert for cert in self.certifications if cert.is_valid]

    @property
    def small_business_certifications(self) -> List[Certification]:
        """Get small business set-aside certifications."""
        sb_types = {
            CertificationType.SBA_8A,
            CertificationType.HUBZONE,
            CertificationType.SDVOSB,
            CertificationType.VOSB,
            CertificationType.WOSB,
            CertificationType.EDWOSB,
            CertificationType.SMALL_BUSINESS,
        }
        return [cert for cert in self.valid_certifications if cert.cert_type in sb_types]

    def has_certification(self, cert_type: CertificationType) -> bool:
        """Check if company has a valid certification of the given type."""
        return any(
            cert.cert_type == cert_type and cert.is_valid
            for cert in self.certifications
        )

    def get_relevant_past_performance(
        self,
        naics_codes: Optional[List[str]] = None,
        agency: Optional[str] = None,
        min_value: Optional[float] = None,
    ) -> List[PastPerformance]:
        """Filter past performance by relevance criteria."""
        relevant = self.past_performance

        if naics_codes:
            relevant = [
                pp for pp in relevant
                if any(code in pp.naics_codes for code in naics_codes)
            ]

        if agency:
            relevant = [
                pp for pp in relevant
                if agency.lower() in pp.agency.lower()
            ]

        if min_value:
            relevant = [
                pp for pp in relevant
                if pp.contract_value >= min_value
            ]

        return relevant

    @property
    def veteran_ownership_percentage(self) -> float:
        """Calculate percentage owned by veterans."""
        return sum(o.percentage for o in self.ownership_structure if o.is_veteran)

    @property
    def service_disabled_veteran_ownership_percentage(self) -> float:
        """Calculate percentage owned by service-disabled veterans."""
        return sum(o.percentage for o in self.ownership_structure if o.is_service_disabled_veteran)

    @property
    def woman_ownership_percentage(self) -> float:
        """Calculate percentage owned by women."""
        return sum(o.percentage for o in self.ownership_structure if o.is_woman)

    @property
    def disadvantaged_ownership_percentage(self) -> float:
        """Calculate percentage owned by disadvantaged individuals."""
        return sum(o.percentage for o in self.ownership_structure if o.is_disadvantaged)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "duns_number": self.duns_number,
            "uei_number": self.uei_number,
            "cage_code": self.cage_code,
            # Company Fundamentals
            "formation_date": self.formation_date.isoformat() if self.formation_date else None,
            "business_status": self.business_status.value,
            "fiscal_year_end": self.fiscal_year_end,
            # Size and Structure
            "employee_count": self.employee_count,
            "employee_headcount": self.employee_headcount,
            "annual_revenue": self.annual_revenue,
            "revenue_is_ytd": self.revenue_is_ytd,
            "years_in_business": self.years_in_business,
            "headquarters_location": self.headquarters_location,
            # Principal Address
            "principal_address": self.principal_address.to_dict() if self.principal_address else None,
            # Ownership & Control
            "ownership_structure": [o.to_dict() for o in self.ownership_structure],
            "management_team": [m.to_dict() for m in self.management_team],
            # Socioeconomic Status
            "veteran_owned": self.veteran_owned,
            "service_disabled_veteran_owned": self.service_disabled_veteran_owned,
            "woman_owned": self.woman_owned,
            "economically_disadvantaged_woman_owned": self.economically_disadvantaged_woman_owned,
            "disadvantaged_business": self.disadvantaged_business,
            # SAM Registration
            "sam_registration_status": self.sam_registration_status,
            "sam_registration_date": self.sam_registration_date.isoformat() if self.sam_registration_date else None,
            "sam_expiration_date": self.sam_expiration_date.isoformat() if self.sam_expiration_date else None,
            # Federal Contracting History
            "federal_contracting_history": self.federal_contracting_history.to_dict() if self.federal_contracting_history else None,
            # HUBZone
            "hubzone_info": self.hubzone_info.to_dict() if self.hubzone_info else None,
            # GovCon Specific
            "naics_codes": [n.to_dict() for n in self.naics_codes],
            "certifications": [c.to_dict() for c in self.certifications],
            "past_performance": [pp.to_dict() for pp in self.past_performance],
            "core_capabilities": [cc.to_dict() for cc in self.core_capabilities],
            "key_personnel": [kp.to_dict() for kp in self.key_personnel],
            "target_agencies": self.target_agencies,
            "geographic_coverage": self.geographic_coverage,
            "security_clearances": self.security_clearances,
            "existing_prime_relationships": self.existing_prime_relationships,
            "existing_sub_relationships": self.existing_sub_relationships,
            "teaming_preferences": self.teaming_preferences,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompanyProfile":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            duns_number=data.get("duns_number"),
            uei_number=data.get("uei_number"),
            cage_code=data.get("cage_code"),
            # Company Fundamentals
            formation_date=date.fromisoformat(data["formation_date"]) if data.get("formation_date") else None,
            business_status=BusinessStatus(data["business_status"]) if data.get("business_status") else BusinessStatus.ACTIVE,
            fiscal_year_end=data.get("fiscal_year_end"),
            # Size and Structure
            employee_count=data.get("employee_count", 0),
            employee_headcount=data.get("employee_headcount"),
            annual_revenue=data.get("annual_revenue", 0.0),
            revenue_is_ytd=data.get("revenue_is_ytd", False),
            years_in_business=data.get("years_in_business", 0),
            headquarters_location=data.get("headquarters_location", ""),
            # Principal Address
            principal_address=Address.from_dict(data["principal_address"]) if data.get("principal_address") else None,
            # Ownership & Control
            ownership_structure=[OwnershipStake.from_dict(o) for o in data.get("ownership_structure", [])],
            management_team=[ManagementMember.from_dict(m) for m in data.get("management_team", [])],
            # Socioeconomic Status
            veteran_owned=data.get("veteran_owned", False),
            service_disabled_veteran_owned=data.get("service_disabled_veteran_owned", False),
            woman_owned=data.get("woman_owned", False),
            economically_disadvantaged_woman_owned=data.get("economically_disadvantaged_woman_owned", False),
            disadvantaged_business=data.get("disadvantaged_business", False),
            # SAM Registration
            sam_registration_status=data.get("sam_registration_status", ""),
            sam_registration_date=date.fromisoformat(data["sam_registration_date"]) if data.get("sam_registration_date") else None,
            sam_expiration_date=date.fromisoformat(data["sam_expiration_date"]) if data.get("sam_expiration_date") else None,
            # Federal Contracting History
            federal_contracting_history=FederalContractingHistory.from_dict(data["federal_contracting_history"]) if data.get("federal_contracting_history") else None,
            # HUBZone
            hubzone_info=HUBZoneInfo.from_dict(data["hubzone_info"]) if data.get("hubzone_info") else None,
            # GovCon Specific
            naics_codes=[NAICSCode.from_dict(n) for n in data.get("naics_codes", [])],
            certifications=[Certification.from_dict(c) for c in data.get("certifications", [])],
            past_performance=[PastPerformance.from_dict(pp) for pp in data.get("past_performance", [])],
            core_capabilities=[CoreCapability.from_dict(cc) for cc in data.get("core_capabilities", [])],
            key_personnel=[TeamMember.from_dict(kp) for kp in data.get("key_personnel", [])],
            target_agencies=data.get("target_agencies", []),
            geographic_coverage=data.get("geographic_coverage", []),
            security_clearances=data.get("security_clearances", []),
            existing_prime_relationships=data.get("existing_prime_relationships", []),
            existing_sub_relationships=data.get("existing_sub_relationships", []),
            teaming_preferences=data.get("teaming_preferences", ""),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "CompanyProfile":
        return cls.from_dict(json.loads(json_str))
