"""
Tests for the Compliance Navigator Agent

Tests cover:
- FAR compliance rule checking
- Small business program eligibility
- Set-aside eligibility validation
- OCI analysis
- Compliance checklist generation
- Agent processing
"""

import pytest
from datetime import date, timedelta
from typing import Dict, Any

from agents.blue.compliance_navigator import (
    ComplianceNavigatorAgent,
    ComplianceAnalysisResult,
)
from agents.blue.rules.far_rules import (
    FARRule,
    FARSubpart,
    FARComplianceChecker,
    ComplianceStatus,
    RiskLevel,
    get_common_far_rules,
)
from agents.blue.rules.small_business_rules import (
    SmallBusinessRule,
    SmallBusinessProgram,
    SmallBusinessValidator,
    EligibilityCheckResult,
    SizeStandard,
    SizeStandardType,
    get_size_standard,
    get_common_size_standards,
)
from agents.blue.rules.setaside_rules import (
    SetAsideType,
    SetAsideValidator,
    SetAsideEligibility,
    EligibilityStatus,
    check_setaside_eligibility,
)
from agents.base import SwarmContext, AgentOutput
from agents.config import AgentConfig, LLMConfig
from agents.types import AgentRole, AgentCategory


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_company_profile() -> Dict[str, Any]:
    """Sample company profile for testing."""
    return {
        "name": "TechSolutions Inc.",
        "annual_revenue": 15_000_000,  # $15M
        "employee_count": 75,
        "years_in_business": 8,
        "naics_codes": [
            {
                "code": "541512",
                "description": "Computer Systems Design Services",
                "is_primary": True,
                "small_business_size_standard": "$34.0M",
            },
            {
                "code": "541511",
                "description": "Custom Computer Programming Services",
                "is_primary": False,
            },
        ],
        "certifications": [
            {
                "cert_type": "8(a)",
                "issuing_authority": "SBA",
                "issue_date": (date.today() - timedelta(days=2*365)).isoformat(),
                "expiration_date": (date.today() + timedelta(days=5*365)).isoformat(),
            },
            {
                "cert_type": "SDVOSB",
                "issuing_authority": "SBA VetCert",
                "issue_date": (date.today() - timedelta(days=365)).isoformat(),
            },
            {
                "cert_type": "ISO 9001",
                "issuing_authority": "Certification Body",
                "issue_date": (date.today() - timedelta(days=180)).isoformat(),
            },
        ],
        "security_clearances": ["Facility Clearance - Secret"],
        "target_agencies": ["DoD", "DHS", "VA"],
        "existing_prime_relationships": ["Acme Federal"],
        "existing_sub_relationships": ["CloudTech Solutions"],
    }


@pytest.fixture
def sample_opportunity() -> Dict[str, Any]:
    """Sample opportunity for testing."""
    return {
        "title": "Enterprise IT Modernization Support Services",
        "solicitation_number": "W91234-25-R-0001",
        "agency": {
            "name": "Department of Defense",
            "abbreviation": "DoD",
            "sub_agency": "Defense Information Systems Agency",
        },
        "set_aside": "8(a)",
        "contract_type": "Firm Fixed Price",
        "naics_code": "541512",
        "estimated_value": 25_000_000,
        "evaluation_type": "Best Value Tradeoff",
        "mandatory_qualifications": [
            "Active 8(a) certification",
            "ISO 9001 certification",
            "Secret facility clearance",
        ],
        "clearance_requirements": "Secret",
    }


@pytest.fixture
def sample_context(sample_company_profile, sample_opportunity) -> SwarmContext:
    """Sample SwarmContext for testing."""
    return SwarmContext(
        company_profile=sample_company_profile,
        opportunity=sample_opportunity,
        document_type="proposal_strategy",
    )


@pytest.fixture
def compliance_agent() -> ComplianceNavigatorAgent:
    """Create a Compliance Navigator agent for testing."""
    config = AgentConfig(
        role=AgentRole.COMPLIANCE_NAVIGATOR,
        name="Test Compliance Navigator",
        llm_config=LLMConfig(model="test-model"),
    )
    return ComplianceNavigatorAgent(config)


# =============================================================================
# FAR Compliance Tests
# =============================================================================

class TestFARComplianceChecker:
    """Tests for FAR compliance checking."""

    def test_load_default_rules(self):
        """Test that default FAR rules are loaded."""
        checker = FARComplianceChecker()
        rules = get_common_far_rules()

        assert len(rules) > 0
        assert all(isinstance(r, FARRule) for r in rules)

    def test_rule_structure(self):
        """Test that FAR rules have required fields."""
        rules = get_common_far_rules()

        for rule in rules:
            assert rule.id is not None
            assert rule.subpart is not None
            assert rule.title is not None
            assert rule.description is not None
            assert rule.requirement is not None
            assert isinstance(rule.risk_level, RiskLevel)

    def test_get_rules_by_subpart(self):
        """Test filtering rules by FAR subpart."""
        checker = FARComplianceChecker()

        sb_rules = checker.get_rules_by_subpart(FARSubpart.FAR_19_5)
        assert len(sb_rules) > 0
        assert all(r.subpart == FARSubpart.FAR_19_5 for r in sb_rules)

    def test_get_applicable_rules_small_business(self):
        """Test getting applicable rules for small business set-aside."""
        checker = FARComplianceChecker()

        rules = checker.get_applicable_rules(
            set_aside="Small Business Set-Aside",
        )

        # Should include small business rules
        rule_ids = [r.id for r in rules]
        assert any("19" in rid for rid in rule_ids)

    def test_get_applicable_rules_dod(self):
        """Test getting applicable rules for DoD contracts."""
        checker = FARComplianceChecker()

        rules = checker.get_applicable_rules(
            is_dod=True,
            contract_value=10_000_000,
        )

        # Should include DFARS rules
        rule_ids = [r.id for r in rules]
        assert any("DFARS" in rid for rid in rule_ids)

    def test_check_compliance_with_content(self):
        """Test compliance checking against document content."""
        checker = FARComplianceChecker()

        content = """
        Our proposal demonstrates full compliance with small business requirements.
        We will perform at least 50% of the work with our own personnel,
        meeting all limitations on subcontracting requirements.
        """

        results = checker.check_compliance(content)

        assert len(results) > 0
        assert all(hasattr(r, 'status') for r in results)
        assert all(hasattr(r, 'rule_id') for r in results)

    def test_generate_compliance_checklist(self, sample_opportunity):
        """Test compliance checklist generation."""
        checker = FARComplianceChecker()

        checklist = checker.generate_compliance_checklist(sample_opportunity)

        assert len(checklist) > 0
        assert all('rule_id' in item for item in checklist)
        assert all('title' in item for item in checklist)


# =============================================================================
# Small Business Validator Tests
# =============================================================================

class TestSmallBusinessValidator:
    """Tests for small business program validation."""

    def test_size_standards_loaded(self):
        """Test that size standards are loaded."""
        standards = get_common_size_standards()

        assert len(standards) > 0
        assert all(isinstance(s, SizeStandard) for s in standards)

    def test_size_standard_lookup(self):
        """Test looking up size standard by NAICS."""
        standard = get_size_standard("541512")

        assert standard is not None
        assert standard.naics_code == "541512"
        assert standard.standard_type == SizeStandardType.REVENUE
        assert standard.threshold == 34.0  # $34M

    def test_size_standard_small_determination(self):
        """Test small business size determination."""
        standard = get_size_standard("541512")

        # Company with $15M revenue should be small
        assert standard.is_small(annual_revenue=15_000_000) is True

        # Company with $50M revenue should not be small
        assert standard.is_small(annual_revenue=50_000_000) is False

    def test_size_standard_employee_based(self):
        """Test employee-based size standard."""
        standard = get_size_standard("541715")  # R&D - employee-based

        assert standard is not None
        assert standard.standard_type == SizeStandardType.EMPLOYEES

        # 500 employees should be small (threshold is 1000)
        assert standard.is_small(employee_count=500) is True

        # 1500 employees should not be small
        assert standard.is_small(employee_count=1500) is False

    def test_validator_check_size_status(self):
        """Test size status check through validator."""
        validator = SmallBusinessValidator()

        result = validator.check_size_status(
            naics_code="541512",
            annual_revenue=15_000_000,
        )

        assert result["is_small"] is True
        assert result["status"] == "Qualifies as Small"
        assert result["margin_percent"] > 0

    def test_validator_check_program_eligibility_8a(self, sample_company_profile):
        """Test 8(a) program eligibility check."""
        validator = SmallBusinessValidator()

        result = validator.check_program_eligibility(
            SmallBusinessProgram.SBA_8A,
            sample_company_profile,
        )

        assert isinstance(result, EligibilityCheckResult)
        assert result.program == SmallBusinessProgram.SBA_8A
        # Should be eligible - has 8(a) cert
        assert result.is_eligible is True

    def test_validator_check_program_eligibility_hubzone(self, sample_company_profile):
        """Test HUBZone program eligibility check."""
        validator = SmallBusinessValidator()

        result = validator.check_program_eligibility(
            SmallBusinessProgram.HUBZONE,
            sample_company_profile,
        )

        # Should not be eligible - no HUBZone cert
        assert result.is_eligible is False
        assert "HUBZone" in str(result.missing_requirements)


# =============================================================================
# Set-Aside Validator Tests
# =============================================================================

class TestSetAsideValidator:
    """Tests for set-aside eligibility validation."""

    def test_full_and_open_always_eligible(self, sample_company_profile):
        """Test that full and open is always eligible."""
        validator = SetAsideValidator()

        result = validator.check_eligibility(
            SetAsideType.FULL_AND_OPEN,
            sample_company_profile,
        )

        assert result.is_eligible is True
        assert result.status == EligibilityStatus.ELIGIBLE
        assert result.confidence == "High"

    def test_8a_eligibility_with_cert(self, sample_company_profile):
        """Test 8(a) eligibility with active certification."""
        validator = SetAsideValidator()

        result = validator.check_eligibility(
            SetAsideType.SBA_8A,
            sample_company_profile,
        )

        assert result.is_eligible is True
        assert result.certification_status == "Active"

    def test_sdvosb_eligibility_with_cert(self, sample_company_profile):
        """Test SDVOSB eligibility with active certification."""
        validator = SetAsideValidator()

        result = validator.check_eligibility(
            SetAsideType.SDVOSB,
            sample_company_profile,
        )

        assert result.is_eligible is True

    def test_hubzone_not_eligible_without_cert(self, sample_company_profile):
        """Test HUBZone not eligible without certification."""
        validator = SetAsideValidator()

        result = validator.check_eligibility(
            SetAsideType.HUBZONE,
            sample_company_profile,
        )

        assert result.is_eligible is False
        assert "Not Found" in result.certification_status

    def test_check_all_setasides(self, sample_company_profile):
        """Test checking all set-aside types."""
        validator = SetAsideValidator()

        results = validator.check_all_setasides(sample_company_profile)

        assert len(results) == len(SetAsideType)
        assert SetAsideType.FULL_AND_OPEN in results
        assert SetAsideType.SBA_8A in results

    def test_get_eligible_setasides(self, sample_company_profile):
        """Test getting list of eligible set-asides."""
        validator = SetAsideValidator()

        eligible = validator.get_eligible_setasides(sample_company_profile)

        assert SetAsideType.FULL_AND_OPEN in eligible
        assert SetAsideType.SBA_8A in eligible
        assert SetAsideType.SDVOSB in eligible
        assert SetAsideType.HUBZONE not in eligible

    def test_convenience_function(self, sample_company_profile):
        """Test the check_setaside_eligibility convenience function."""
        result = check_setaside_eligibility(
            "8(a)",
            sample_company_profile,
        )

        assert isinstance(result, SetAsideEligibility)
        assert result.is_eligible is True

    def test_expired_certification_warning(self):
        """Test warning for expired certification."""
        validator = SetAsideValidator()

        profile_with_expired = {
            "certifications": [
                {
                    "cert_type": "8(a)",
                    "expiration_date": (date.today() - timedelta(days=30)).isoformat(),
                },
            ],
        }

        result = validator.check_eligibility(
            SetAsideType.SBA_8A,
            profile_with_expired,
        )

        assert result.status == EligibilityStatus.EXPIRED
        assert result.is_eligible is False


# =============================================================================
# Compliance Navigator Agent Tests
# =============================================================================

class TestComplianceNavigatorAgent:
    """Tests for the Compliance Navigator agent."""

    def test_agent_initialization(self, compliance_agent):
        """Test agent initializes correctly."""
        assert compliance_agent.role == AgentRole.COMPLIANCE_NAVIGATOR
        assert compliance_agent.category == AgentCategory.BLUE
        assert compliance_agent._far_checker is not None
        assert compliance_agent._sb_validator is not None
        assert compliance_agent._setaside_validator is not None

    def test_agent_default_config(self):
        """Test agent with default configuration."""
        agent = ComplianceNavigatorAgent()

        assert agent.role == AgentRole.COMPLIANCE_NAVIGATOR
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_process_eligibility(self, compliance_agent, sample_context):
        """Test processing eligibility assessment."""
        sample_context.custom_data["analysis_type"] = "eligibility"

        output = await compliance_agent.process(sample_context)

        assert isinstance(output, AgentOutput)
        assert output.success is True
        assert output.agent_role == AgentRole.COMPLIANCE_NAVIGATOR
        assert "eligible" in output.content.lower() or "eligibility" in output.content.lower()

    @pytest.mark.asyncio
    async def test_process_comprehensive(self, compliance_agent, sample_context):
        """Test processing comprehensive analysis."""
        sample_context.custom_data["analysis_type"] = "comprehensive"

        output = await compliance_agent.process(sample_context)

        assert output.success is True
        assert "compliance" in output.content.lower()

    @pytest.mark.asyncio
    async def test_process_oci(self, compliance_agent, sample_context):
        """Test processing OCI analysis."""
        sample_context.custom_data["analysis_type"] = "oci"

        output = await compliance_agent.process(sample_context)

        assert output.success is True
        # Should have OCI risk level in metadata
        assert "oci_risk_level" in output.metadata

    @pytest.mark.asyncio
    async def test_process_checklist(self, compliance_agent, sample_context):
        """Test processing checklist generation."""
        sample_context.custom_data["analysis_type"] = "checklist"

        output = await compliance_agent.process(sample_context)

        assert output.success is True
        assert "checklist" in output.content.lower()

    @pytest.mark.asyncio
    async def test_process_without_company_profile(self, compliance_agent):
        """Test processing fails without company profile."""
        context = SwarmContext()

        output = await compliance_agent.process(context)

        assert output.success is False
        assert "company profile" in output.error_message.lower()

    @pytest.mark.asyncio
    async def test_draft_section_eligibility(self, compliance_agent, sample_context):
        """Test drafting eligibility section."""
        content = await compliance_agent.draft_section(
            sample_context,
            "eligibility_assessment",
        )

        assert len(content) > 0
        assert "eligibility" in content.lower()

    @pytest.mark.asyncio
    async def test_draft_section_checklist(self, compliance_agent, sample_context):
        """Test drafting compliance checklist section."""
        content = await compliance_agent.draft_section(
            sample_context,
            "compliance_checklist",
        )

        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_revise_section(self, compliance_agent, sample_context):
        """Test revising a section based on critiques."""
        sample_context.section_drafts["eligibility"] = "Initial eligibility assessment."

        critiques = [
            {
                "argument": "Missing size standard verification",
                "severity": "High",
                "suggested_remedy": "Add explicit size standard analysis",
            },
        ]

        revised = await compliance_agent.revise_section(
            sample_context,
            "eligibility",
            critiques,
        )

        assert len(revised) > 0

    def test_validate_context_with_profile(self, compliance_agent, sample_context):
        """Test context validation with company profile."""
        errors = compliance_agent.validate_context(sample_context)

        assert len(errors) == 0

    def test_validate_context_without_profile(self, compliance_agent):
        """Test context validation without company profile."""
        context = SwarmContext()

        errors = compliance_agent.validate_context(context)

        assert len(errors) > 0
        assert any("company profile" in e.lower() for e in errors)


# =============================================================================
# Compliance Analysis Result Tests
# =============================================================================

class TestComplianceAnalysisResult:
    """Tests for ComplianceAnalysisResult dataclass."""

    def test_default_initialization(self):
        """Test default initialization."""
        result = ComplianceAnalysisResult()

        assert result.success is True
        assert result.overall_compliance_status == "Unknown"
        assert len(result.eligible_setasides) == 0
        assert len(result.critical_issues) == 0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ComplianceAnalysisResult(
            eligible_setasides=["8(a)", "SDVOSB"],
            overall_compliance_status="Compliant",
            oci_risk_level="Low",
        )

        result_dict = result.to_dict()

        assert result_dict["eligible_setasides"] == ["8(a)", "SDVOSB"]
        assert result_dict["overall_compliance_status"] == "Compliant"
        assert result_dict["oci_risk_level"] == "Low"

    def test_with_compliance_gaps(self):
        """Test result with compliance gaps."""
        result = ComplianceAnalysisResult(
            compliance_gaps=[
                {"title": "Missing certification", "risk_level": "critical"},
            ],
            critical_issues=["Missing certification"],
        )

        assert len(result.compliance_gaps) == 1
        assert len(result.critical_issues) == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestComplianceIntegration:
    """Integration tests for compliance functionality."""

    @pytest.mark.asyncio
    async def test_full_compliance_workflow(
        self,
        compliance_agent,
        sample_company_profile,
        sample_opportunity,
    ):
        """Test full compliance workflow from context to output."""
        context = SwarmContext(
            company_profile=sample_company_profile,
            opportunity=sample_opportunity,
            custom_data={"analysis_type": "comprehensive"},
        )

        output = await compliance_agent.process(context)

        assert output.success is True
        assert "eligible_setasides" in output.metadata
        assert "overall_status" in output.metadata

    def test_eligibility_and_far_alignment(self, sample_company_profile, sample_opportunity):
        """Test that eligibility and FAR requirements align."""
        # Check eligibility
        sa_validator = SetAsideValidator()
        eligibility = sa_validator.check_eligibility(
            SetAsideType.SBA_8A,
            sample_company_profile,
            sample_opportunity,
        )

        # Get applicable FAR rules
        far_checker = FARComplianceChecker()
        rules = far_checker.get_applicable_rules(
            set_aside="8(a)",
        )

        # If eligible for 8(a), should have 8(a) FAR rules applicable
        assert eligibility.is_eligible is True
        rule_ids = [r.id for r in rules]
        assert any("8" in rid or "19" in rid for rid in rule_ids)


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
