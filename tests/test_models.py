"""
Unit tests for Core Data Models (Chunk 1).

Tests JSON serialization/deserialization and validation logic for all models.
"""

import pytest
from datetime import date, datetime
from typing import List
import json

# Import all models
from models.company_profile import (
    CompanyProfile,
    NAICSCode,
    Certification,
    CertificationType,
    PastPerformance,
    PerformanceRating,
    TeamMember,
    CoreCapability,
)
from models.opportunity import (
    Opportunity,
    Agency,
    SetAsideType,
    ContractType,
    EvaluationType,
    Competitor,
    CompetitorIntel,
    OpportunityStatus,
    OpportunityPriority,
    EvaluationFactor,
)
from models.document_types import (
    DocumentType,
    DocumentSection,
    DocumentMetadata,
    DocumentStatus,
    SectionStatus,
    DOCUMENT_TEMPLATES,
    create_document_from_template,
)
from models.critique import (
    Critique,
    ChallengeType,
    Severity,
    CritiqueStatus,
    CritiqueSummary,
)
from models.response import (
    Response,
    Disposition,
    ActionType,
    ResponseSummary,
    DebateExchange,
)
from models.confidence import (
    ConfidenceScore,
    SectionConfidence,
    ConfidenceThresholds,
    ConfidenceLevel,
    RiskFlag,
)


# ============================================================================
# NAICS Code Tests
# ============================================================================

class TestNAICSCode:
    """Tests for NAICSCode model."""

    def test_create_naics_code(self):
        """Test basic NAICS code creation."""
        naics = NAICSCode(
            code="541512",
            description="Computer Systems Design Services",
            is_primary=True,
            small_business_size_standard="$30 million"
        )
        assert naics.code == "541512"
        assert naics.is_primary is True

    def test_naics_serialization(self):
        """Test NAICS code JSON serialization/deserialization."""
        naics = NAICSCode(
            code="541512",
            description="Computer Systems Design Services",
            is_primary=True
        )
        json_str = naics.to_json()
        restored = NAICSCode.from_json(json_str)

        assert restored.code == naics.code
        assert restored.description == naics.description
        assert restored.is_primary == naics.is_primary


# ============================================================================
# Certification Tests
# ============================================================================

class TestCertification:
    """Tests for Certification model."""

    def test_create_certification(self):
        """Test basic certification creation."""
        cert = Certification(
            cert_type=CertificationType.SBA_8A,
            issuing_authority="SBA",
            issue_date=date(2023, 1, 1),
            expiration_date=date(2032, 1, 1)
        )
        assert cert.cert_type == CertificationType.SBA_8A
        assert cert.is_valid is True

    def test_expired_certification(self):
        """Test expired certification detection."""
        cert = Certification(
            cert_type=CertificationType.SBA_8A,
            issuing_authority="SBA",
            issue_date=date(2020, 1, 1),
            expiration_date=date(2021, 1, 1)  # Expired
        )
        assert cert.is_valid is False

    def test_certification_serialization(self):
        """Test certification JSON serialization/deserialization."""
        cert = Certification(
            cert_type=CertificationType.SDVOSB,
            issuing_authority="VA",
            issue_date=date(2023, 6, 15),
            expiration_date=date(2026, 6, 15),
            level="Verified"
        )
        json_str = cert.to_json()
        restored = Certification.from_json(json_str)

        assert restored.cert_type == cert.cert_type
        assert restored.issue_date == cert.issue_date
        assert restored.level == cert.level


# ============================================================================
# Past Performance Tests
# ============================================================================

class TestPastPerformance:
    """Tests for PastPerformance model."""

    def test_create_past_performance(self):
        """Test basic past performance creation."""
        pp = PastPerformance(
            contract_number="GS-35F-0001X",
            contract_name="IT Support Services",
            agency="GSA",
            contract_value=5_000_000,
            overall_rating=PerformanceRating.VERY_GOOD
        )
        assert pp.contract_value == 5_000_000
        assert pp.overall_rating == PerformanceRating.VERY_GOOD

    def test_past_performance_serialization(self):
        """Test past performance JSON serialization/deserialization."""
        pp = PastPerformance(
            contract_number="W52P1J-20-C-0001",
            contract_name="Enterprise IT Services",
            agency="Army",
            contract_value=10_000_000,
            period_of_performance_start=date(2020, 1, 1),
            period_of_performance_end=date(2025, 12, 31),
            overall_rating=PerformanceRating.EXCEPTIONAL,
            naics_codes=["541512", "541519"],
            key_accomplishments=["Reduced downtime by 50%", "Zero security incidents"]
        )
        json_str = pp.to_json()
        restored = PastPerformance.from_json(json_str)

        assert restored.contract_number == pp.contract_number
        assert restored.naics_codes == pp.naics_codes
        assert len(restored.key_accomplishments) == 2


# ============================================================================
# Company Profile Tests
# ============================================================================

class TestCompanyProfile:
    """Tests for CompanyProfile model."""

    @pytest.fixture
    def sample_profile(self) -> CompanyProfile:
        """Create a sample company profile for testing."""
        return CompanyProfile(
            name="Acme Federal Solutions",
            uei_number="ABC123456789",
            cage_code="1ABC2",
            employee_count=150,
            annual_revenue=25_000_000,
            years_in_business=10,
            headquarters_location="Reston, VA",
            naics_codes=[
                NAICSCode("541512", "Computer Systems Design", is_primary=True),
                NAICSCode("541519", "Other Computer Related Services"),
            ],
            certifications=[
                Certification(
                    cert_type=CertificationType.SDVOSB,
                    issuing_authority="VA",
                    issue_date=date(2023, 1, 1),
                    expiration_date=date(2026, 1, 1)
                ),
                Certification(
                    cert_type=CertificationType.ISO_27001,
                    issuing_authority="BSI",
                    issue_date=date(2022, 6, 1)
                ),
            ],
            target_agencies=["VA", "DoD", "DHS"],
        )

    def test_primary_naics(self, sample_profile):
        """Test primary NAICS code retrieval."""
        primary = sample_profile.primary_naics
        assert primary is not None
        assert primary.code == "541512"

    def test_valid_certifications(self, sample_profile):
        """Test filtering for valid certifications."""
        valid = sample_profile.valid_certifications
        assert len(valid) == 2  # Both should be valid

    def test_small_business_certifications(self, sample_profile):
        """Test filtering for small business certifications."""
        sb_certs = sample_profile.small_business_certifications
        assert len(sb_certs) == 1
        assert sb_certs[0].cert_type == CertificationType.SDVOSB

    def test_has_certification(self, sample_profile):
        """Test certification check."""
        assert sample_profile.has_certification(CertificationType.SDVOSB) is True
        assert sample_profile.has_certification(CertificationType.HUBZONE) is False

    def test_profile_serialization(self, sample_profile):
        """Test company profile JSON serialization/deserialization."""
        json_str = sample_profile.to_json()
        restored = CompanyProfile.from_json(json_str)

        assert restored.name == sample_profile.name
        assert restored.employee_count == sample_profile.employee_count
        assert len(restored.naics_codes) == 2
        assert len(restored.certifications) == 2


# ============================================================================
# Opportunity Tests
# ============================================================================

class TestOpportunity:
    """Tests for Opportunity model."""

    @pytest.fixture
    def sample_opportunity(self) -> Opportunity:
        """Create a sample opportunity for testing."""
        return Opportunity(
            title="Enterprise IT Support Services",
            solicitation_number="W52P1J-25-R-0001",
            agency=Agency(
                name="Department of Defense",
                abbreviation="DoD",
                sub_agency="Army"
            ),
            status=OpportunityStatus.FINAL_RFP,
            priority=OpportunityPriority.HIGH,
            response_deadline=datetime(2025, 3, 15, 14, 0),
            estimated_value=50_000_000,
            set_aside=SetAsideType.SDVOSB,
            contract_type=ContractType.IDIQ,
            evaluation_type=EvaluationType.BEST_VALUE,
            naics_code="541512",
            is_recompete=True,
        )

    def test_is_small_business_setaside(self, sample_opportunity):
        """Test small business set-aside detection."""
        assert sample_opportunity.is_small_business_setaside is True

        sample_opportunity.set_aside = SetAsideType.FULL_AND_OPEN
        assert sample_opportunity.is_small_business_setaside is False

    def test_is_active(self, sample_opportunity):
        """Test active status detection."""
        assert sample_opportunity.is_active is True

        sample_opportunity.status = OpportunityStatus.AWARDED
        assert sample_opportunity.is_active is False

    def test_opportunity_serialization(self, sample_opportunity):
        """Test opportunity JSON serialization/deserialization."""
        json_str = sample_opportunity.to_json()
        restored = Opportunity.from_json(json_str)

        assert restored.title == sample_opportunity.title
        assert restored.set_aside == SetAsideType.SDVOSB
        assert restored.agency.abbreviation == "DoD"


class TestCompetitorIntel:
    """Tests for CompetitorIntel model."""

    def test_competitor_intel(self):
        """Test competitor intelligence aggregation."""
        intel = CompetitorIntel(
            competitors=[
                Competitor(
                    name="Incumbent Corp",
                    is_incumbent=True,
                    is_confirmed=True,
                    estimated_strength="Strong"
                ),
                Competitor(
                    name="Challenger Inc",
                    is_confirmed=True,
                    estimated_strength="Moderate"
                ),
            ],
            competitive_density="Medium",
            incumbent_advantage_level="Strong"
        )

        assert intel.incumbent.name == "Incumbent Corp"
        assert len(intel.confirmed_competitors) == 2


# ============================================================================
# Document Types Tests
# ============================================================================

class TestDocumentSection:
    """Tests for DocumentSection model."""

    def test_update_content(self):
        """Test section content update tracking."""
        section = DocumentSection(
            name="Executive Summary",
            content="Initial content"
        )

        section.update_content("Revised content", "Strategy Architect")

        assert section.content == "Revised content"
        assert section.version == 2
        assert len(section.previous_versions) == 1
        assert section.modified_by == "Strategy Architect"

    def test_section_serialization(self):
        """Test section JSON serialization/deserialization."""
        section = DocumentSection(
            name="Win Themes",
            content="Theme 1: Superior technical approach",
            status=SectionStatus.DRAFTED
        )
        json_str = section.to_json()
        restored = DocumentSection.from_json(json_str)

        assert restored.name == section.name
        assert restored.status == SectionStatus.DRAFTED


class TestDocumentMetadata:
    """Tests for DocumentMetadata model."""

    def test_create_from_template(self):
        """Test document creation from template."""
        doc = create_document_from_template(
            DocumentType.PROPOSAL_STRATEGY,
            "IT Support Services Proposal Strategy",
            company_profile_id="cp-123",
            opportunity_id="opp-456"
        )

        assert doc.document_type == DocumentType.PROPOSAL_STRATEGY
        assert len(doc.sections) == len(DOCUMENT_TEMPLATES[DocumentType.PROPOSAL_STRATEGY])
        assert doc.company_profile_id == "cp-123"

    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        doc = DocumentMetadata()
        doc.add_section("Section 1")
        doc.add_section("Section 2")

        assert doc.completion_percentage == 0.0

        doc.sections[0].status = SectionStatus.COMPLETE
        assert doc.completion_percentage == 50.0

    def test_document_serialization(self):
        """Test document metadata JSON serialization/deserialization."""
        doc = create_document_from_template(
            DocumentType.CAPABILITY_STATEMENT,
            "Acme Capability Statement"
        )
        doc.debate_rounds = 3

        json_str = doc.to_json()
        restored = DocumentMetadata.from_json(json_str)

        assert restored.title == doc.title
        assert len(restored.sections) == len(doc.sections)
        assert restored.debate_rounds == 3


# ============================================================================
# Critique Tests
# ============================================================================

class TestCritique:
    """Tests for Critique model."""

    @pytest.fixture
    def sample_critique(self) -> Critique:
        """Create a sample critique for testing."""
        return Critique(
            agent="Devil's Advocate",
            target_section="Win Themes",
            challenge_type=ChallengeType.EVIDENCE,
            severity=Severity.MAJOR,
            title="Unsupported win theme claim",
            argument="The claim that the company has 'industry-leading' response times is not supported by any evidence.",
            evidence="No metrics or benchmarks provided in the draft.",
            suggested_remedy="Add specific SLA metrics and compare to industry standards."
        )

    def test_critique_blocking(self, sample_critique):
        """Test blocking critique detection."""
        assert sample_critique.is_blocking is False

        sample_critique.severity = Severity.CRITICAL
        assert sample_critique.is_blocking is True

        sample_critique.accept()
        assert sample_critique.is_blocking is False

    def test_critique_resolution_flow(self, sample_critique):
        """Test critique resolution workflow."""
        assert sample_critique.status == CritiqueStatus.PENDING

        sample_critique.mark_addressed("response-123")
        assert sample_critique.status == CritiqueStatus.ADDRESSED
        assert sample_critique.response_id == "response-123"

    def test_critique_serialization(self, sample_critique):
        """Test critique JSON serialization/deserialization."""
        json_str = sample_critique.to_json()
        restored = Critique.from_json(json_str)

        assert restored.agent == sample_critique.agent
        assert restored.challenge_type == ChallengeType.EVIDENCE
        assert restored.severity == Severity.MAJOR


class TestCritiqueSummary:
    """Tests for CritiqueSummary model."""

    def test_summary_from_critiques(self):
        """Test summary generation from critiques."""
        critiques = [
            Critique(
                agent="Devil's Advocate",
                target_section="Section 1",
                challenge_type=ChallengeType.LOGIC,
                severity=Severity.CRITICAL,
                argument="Logical flaw",
                suggested_remedy="Fix it"
            ),
            Critique(
                agent="Risk Assessor",
                target_section="Section 2",
                challenge_type=ChallengeType.RISK,
                severity=Severity.MAJOR,
                argument="Risk concern",
                suggested_remedy="Mitigate it"
            ),
        ]
        critiques[1].accept()

        summary = CritiqueSummary.from_critiques(critiques, document_id="doc-123")

        assert summary.total == 2
        assert summary.critical == 1
        assert summary.major == 1
        assert summary.accepted == 1
        assert summary.has_blocking_issues is True


# ============================================================================
# Response Tests
# ============================================================================

class TestResponse:
    """Tests for Response model."""

    @pytest.fixture
    def sample_response(self) -> Response:
        """Create a sample response for testing."""
        return Response(
            critique_id="critique-123",
            agent="Strategy Architect",
            disposition=Disposition.ACCEPT,
            summary="Accepted the critique about unsupported claims",
            action="Added specific SLA metrics to the win themes section",
            action_type=ActionType.ADD_CONTENT,
            rationale="The critique is valid; we need concrete evidence.",
            original_content="We have industry-leading response times.",
            revised_content="We maintain 99.9% uptime with <2hr response times, exceeding the industry average of 99.5%."
        )

    def test_requires_revision(self, sample_response):
        """Test revision requirement detection."""
        assert sample_response.requires_revision is True

        sample_response.disposition = Disposition.REBUT
        assert sample_response.requires_revision is False

    def test_made_changes(self, sample_response):
        """Test change detection."""
        assert sample_response.made_changes is True

    def test_response_serialization(self, sample_response):
        """Test response JSON serialization/deserialization."""
        json_str = sample_response.to_json()
        restored = Response.from_json(json_str)

        assert restored.critique_id == sample_response.critique_id
        assert restored.disposition == Disposition.ACCEPT
        assert restored.revised_content == sample_response.revised_content


class TestResponseSummary:
    """Tests for ResponseSummary model."""

    def test_summary_rates(self):
        """Test acceptance and rebuttal rate calculations."""
        responses = [
            Response(critique_id="c1", agent="Agent1", disposition=Disposition.ACCEPT),
            Response(critique_id="c2", agent="Agent1", disposition=Disposition.REBUT),
            Response(critique_id="c3", agent="Agent1", disposition=Disposition.ACCEPT),
            Response(critique_id="c4", agent="Agent1", disposition=Disposition.ACKNOWLEDGE),
        ]

        summary = ResponseSummary.from_responses(responses)

        assert summary.total == 4
        assert summary.acceptance_rate == 50.0  # 2 out of 4
        assert summary.rebuttal_rate == 25.0  # 1 out of 4


# ============================================================================
# Confidence Tests
# ============================================================================

class TestConfidenceThresholds:
    """Tests for ConfidenceThresholds model."""

    def test_get_level(self):
        """Test confidence level determination."""
        thresholds = ConfidenceThresholds()

        assert thresholds.get_level(0.95) == ConfidenceLevel.VERY_HIGH
        assert thresholds.get_level(0.85) == ConfidenceLevel.HIGH
        assert thresholds.get_level(0.75) == ConfidenceLevel.MODERATE
        assert thresholds.get_level(0.55) == ConfidenceLevel.LOW
        assert thresholds.get_level(0.40) == ConfidenceLevel.VERY_LOW


class TestSectionConfidence:
    """Tests for SectionConfidence model."""

    def test_apply_adjustment(self):
        """Test score adjustment application."""
        section = SectionConfidence(
            section_name="Win Themes",
            base_score=0.80,
            adjusted_score=0.80
        )

        section.apply_adjustment("Unresolved major critique", -0.08)

        assert section.adjusted_score == pytest.approx(0.72)
        assert len(section.adjustments) == 1


class TestConfidenceScore:
    """Tests for ConfidenceScore model."""

    def test_calculate_overall_score(self):
        """Test overall score calculation."""
        confidence = ConfidenceScore(document_id="doc-123")

        confidence.add_section_score(SectionConfidence(
            section_name="Section 1",
            adjusted_score=0.90
        ))
        confidence.add_section_score(SectionConfidence(
            section_name="Section 2",
            adjusted_score=0.70
        ))

        confidence.calculate_overall_score()

        # Overall score is now the minimum of section scores (not average)
        assert confidence.overall_score == 0.70
        assert confidence.overall_level == ConfidenceLevel.MODERATE

    def test_human_review_required(self):
        """Test human review requirement detection."""
        confidence = ConfidenceScore(document_id="doc-123")
        confidence.add_section_score(SectionConfidence(
            section_name="Section 1",
            adjusted_score=0.60  # Below threshold
        ))
        confidence.unresolved_critical = 1

        confidence.calculate_overall_score()

        assert confidence.requires_human_review is True
        assert len(confidence.review_reasons) > 0

    def test_confidence_serialization(self):
        """Test confidence score JSON serialization/deserialization."""
        confidence = ConfidenceScore(
            document_id="doc-123",
            overall_score=0.85,
            debate_rounds=3
        )
        confidence.add_section_score(SectionConfidence(
            section_name="Executive Summary",
            adjusted_score=0.85
        ))

        json_str = confidence.to_json()
        restored = ConfidenceScore.from_json(json_str)

        assert restored.document_id == confidence.document_id
        assert restored.overall_score == confidence.overall_score
        assert len(restored.section_scores) == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_full_document_workflow(self):
        """Test complete document creation and critique workflow."""
        # Create company profile
        profile = CompanyProfile(
            name="Test Company",
            naics_codes=[NAICSCode("541512", "IT Services", is_primary=True)],
            certifications=[
                Certification(
                    cert_type=CertificationType.SDVOSB,
                    issuing_authority="VA",
                    issue_date=date(2023, 1, 1)
                )
            ]
        )

        # Create opportunity
        opportunity = Opportunity(
            title="IT Support Services",
            set_aside=SetAsideType.SDVOSB,
            naics_code="541512"
        )

        # Create document from template
        doc = create_document_from_template(
            DocumentType.PROPOSAL_STRATEGY,
            "Proposal Strategy for IT Support",
            company_profile_id=profile.id,
            opportunity_id=opportunity.id
        )

        # Simulate drafting a section
        exec_summary = doc.get_section("Executive Summary")
        exec_summary.update_content(
            "We propose a comprehensive IT support solution...",
            "Strategy Architect"
        )

        # Create a critique
        critique = Critique(
            agent="Devil's Advocate",
            target_document_id=doc.id,
            target_section="Executive Summary",
            challenge_type=ChallengeType.COMPLETENESS,
            severity=Severity.MAJOR,
            argument="Missing specific technical approach details",
            suggested_remedy="Add details about proposed technologies and methodologies"
        )

        # Create a response
        response = Response(
            critique_id=critique.id,
            agent="Strategy Architect",
            disposition=Disposition.ACCEPT,
            action="Added technical approach details",
            action_type=ActionType.ADD_CONTENT
        )

        # Link response to critique
        critique.mark_addressed(response.id)
        critique.accept()

        # Calculate confidence
        confidence = ConfidenceScore(document_id=doc.id)
        confidence.add_section_score(SectionConfidence(
            section_id=exec_summary.id,
            section_name=exec_summary.name,
            adjusted_score=0.85
        ))
        confidence.total_critiques = 1
        confidence.resolved_critiques = 1
        confidence.calculate_overall_score()

        # Verify the workflow
        assert critique.is_resolved is True
        assert response.requires_revision is True
        assert confidence.resolution_rate == 100.0
        assert confidence.requires_human_review is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
