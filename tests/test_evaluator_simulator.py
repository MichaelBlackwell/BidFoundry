"""
Tests for Evaluator Simulator Agent

Tests the government SSEB evaluation simulation functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
import asyncio

from agents.red.evaluator_simulator import (
    EvaluatorSimulatorAgent,
    EvaluatorSimulatorResult,
    EvaluatorFinding,
    EvaluatorStrength,
    FactorEvaluation,
)
from agents.red.evaluation_criteria import (
    EvaluationFactor,
    RatingLevel,
    WeaknessType,
    ConfidenceLevel,
    AcceptabilityStatus,
    COMMON_TECHNICAL_FACTORS,
)
from agents.base import SwarmContext
from agents.config import AgentConfig
from agents.types import AgentRole, AgentCategory
from models.critique import ChallengeType, Severity


class TestEvaluatorFinding:
    """Tests for EvaluatorFinding dataclass."""

    def test_finding_creation(self):
        """Test creating an evaluator finding."""
        finding = EvaluatorFinding(
            finding_type=WeaknessType.DEFICIENCY,
            factor="Technical Approach",
            title="Missing Security Requirements",
            description="Proposal fails to address FedRAMP High requirements",
            requirement_affected="Section L.4.1 - Security Requirements",
            evidence_location="Technical Approach Section, Page 12",
            impact="Cannot be included in competitive range without correction",
            recommendation="Add FedRAMP High compliance documentation",
        )

        assert finding.finding_type == WeaknessType.DEFICIENCY
        assert finding.factor == "Technical Approach"
        assert "FedRAMP" in finding.description

    def test_finding_to_dict(self):
        """Test serialization of finding to dictionary."""
        finding = EvaluatorFinding(
            finding_type=WeaknessType.SIGNIFICANT_WEAKNESS,
            factor="Management Approach",
            title="Weak Risk Management",
            description="Risk management plan lacks specificity",
        )

        result = finding.to_dict()

        assert result["finding_type"] == "Significant Weakness"
        assert result["factor"] == "Management Approach"
        assert result["title"] == "Weak Risk Management"

    def test_finding_to_critique(self):
        """Test conversion of finding to standard Critique format."""
        finding = EvaluatorFinding(
            finding_type=WeaknessType.DEFICIENCY,
            factor="Technical Approach",
            title="Missing Requirement",
            description="Fails to meet mandatory requirement",
            requirement_affected="PWS 4.1",
            impact="Results in Unacceptable rating",
            recommendation="Address requirement explicitly",
        )

        critique = finding.to_critique(
            agent="Evaluator Simulator",
            round_number=1,
            document_id="doc-123",
        )

        assert critique.agent == "Evaluator Simulator"
        assert critique.severity == Severity.CRITICAL  # Deficiency = Critical
        assert critique.challenge_type == ChallengeType.COMPLIANCE
        assert "[SSEB]" in critique.title
        assert critique.target_section == "Technical Approach"


class TestEvaluatorStrength:
    """Tests for EvaluatorStrength dataclass."""

    def test_strength_creation(self):
        """Test creating an evaluator strength."""
        strength = EvaluatorStrength(
            factor="Technical Approach",
            title="Innovative Automation",
            description="Proposal includes proven automation framework",
            benefit_to_government="Reduces migration time by 40%",
            exceeds_requirements=True,
            location="Technical Approach, Section 2.3",
        )

        assert strength.factor == "Technical Approach"
        assert strength.exceeds_requirements is True
        assert "automation" in strength.description.lower()

    def test_strength_to_dict(self):
        """Test serialization of strength to dictionary."""
        strength = EvaluatorStrength(
            factor="Management",
            title="Strong QA Process",
            description="ISO 9001 certified quality system",
        )

        result = strength.to_dict()

        assert result["factor"] == "Management"
        assert result["title"] == "Strong QA Process"


class TestFactorEvaluation:
    """Tests for FactorEvaluation dataclass."""

    def test_factor_evaluation_creation(self):
        """Test creating a factor evaluation."""
        factor_eval = FactorEvaluation(
            factor_name="Technical Approach",
            rating=RatingLevel.GOOD,
            rating_rationale="Exceeds requirements in automation",
        )

        assert factor_eval.factor_name == "Technical Approach"
        assert factor_eval.rating == RatingLevel.GOOD
        assert factor_eval.is_acceptable is True
        assert factor_eval.has_deficiency is False

    def test_factor_with_deficiency(self):
        """Test factor evaluation with deficiency."""
        finding = EvaluatorFinding(
            finding_type=WeaknessType.DEFICIENCY,
            factor="Technical Approach",
            title="Critical Gap",
            description="Missing mandatory requirement",
        )

        factor_eval = FactorEvaluation(
            factor_name="Technical Approach",
            rating=RatingLevel.UNACCEPTABLE,
            findings=[finding],
        )

        assert factor_eval.has_deficiency is True
        assert factor_eval.is_acceptable is False

    def test_factor_acceptable_with_weaknesses(self):
        """Test factor can be acceptable with minor weaknesses."""
        finding = EvaluatorFinding(
            finding_type=WeaknessType.WEAKNESS,
            factor="Technical Approach",
            title="Minor Gap",
            description="Could be improved",
        )

        factor_eval = FactorEvaluation(
            factor_name="Technical Approach",
            rating=RatingLevel.ACCEPTABLE,
            findings=[finding],
        )

        assert factor_eval.has_deficiency is False
        assert factor_eval.is_acceptable is True


class TestEvaluatorSimulatorResult:
    """Tests for EvaluatorSimulatorResult dataclass."""

    def test_result_creation(self):
        """Test creating an evaluation result."""
        result = EvaluatorSimulatorResult(
            evaluation_type="Best Value",
            overall_rating=RatingLevel.ACCEPTABLE,
            in_competitive_range=True,
        )

        assert result.evaluation_type == "Best Value"
        assert result.overall_rating == RatingLevel.ACCEPTABLE
        assert result.in_competitive_range is True

    def test_deficiency_counts(self):
        """Test deficiency counting."""
        findings = [
            EvaluatorFinding(
                finding_type=WeaknessType.DEFICIENCY,
                factor="Tech",
                title="Def 1",
                description="Test",
            ),
            EvaluatorFinding(
                finding_type=WeaknessType.SIGNIFICANT_WEAKNESS,
                factor="Tech",
                title="SW 1",
                description="Test",
            ),
            EvaluatorFinding(
                finding_type=WeaknessType.WEAKNESS,
                factor="Tech",
                title="W 1",
                description="Test",
            ),
        ]

        result = EvaluatorSimulatorResult(all_findings=findings)

        assert result.deficiency_count == 1
        assert result.significant_weakness_count == 2  # Def + SW
        assert result.weakness_count == 3  # Total

    def test_result_to_dict(self):
        """Test serialization to dictionary."""
        result = EvaluatorSimulatorResult(
            evaluation_type="LPTA",
            overall_rating=RatingLevel.ACCEPTABLE,
            in_competitive_range=True,
            past_performance_confidence=ConfidenceLevel.SATISFACTORY_CONFIDENCE,
        )

        data = result.to_dict()

        assert data["evaluation_type"] == "LPTA"
        assert data["overall_rating"] == "Acceptable"
        assert data["past_performance_confidence"] == "Satisfactory Confidence"


class TestEvaluatorSimulatorAgent:
    """Tests for EvaluatorSimulatorAgent."""

    @pytest.fixture
    def agent(self):
        """Create an Evaluator Simulator agent for testing."""
        return EvaluatorSimulatorAgent()

    @pytest.fixture
    def sample_context(self):
        """Create a sample SwarmContext for testing."""
        return SwarmContext(
            document_type="Proposal Strategy",
            document_id="test-doc-123",
            section_drafts={
                "Technical Approach": """
                    Our team will implement a proven 5-phase methodology for cloud migration.
                    We leverage industry best practices and have deep experience with similar
                    federal systems. Our approach ensures minimal disruption while achieving
                    cost savings of approximately 30%.
                """,
                "Management Approach": """
                    We employ a dedicated Program Manager with 15 years of federal experience.
                    Our quality management system is ISO 9001 certified. We implement
                    comprehensive risk management with weekly risk reviews.
                """,
            },
            company_profile={
                "name": "TechCorp Federal",
                "certifications": [
                    {"cert_type": "ISO 9001"},
                    {"cert_type": "CMMI Level 3"},
                ],
            },
            opportunity={
                "title": "Cloud Migration Services",
                "agency": {"name": "Department of Homeland Security"},
                "evaluation_factors": [
                    {"name": "Technical Approach", "weight": 40},
                    {"name": "Management Approach", "weight": 30},
                    {"name": "Past Performance", "weight": 30},
                ],
            },
        )

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.role == AgentRole.EVALUATOR_SIMULATOR
        assert agent.category == AgentCategory.RED

    def test_agent_has_correct_role(self, agent):
        """Test agent has correct role assigned."""
        assert agent.role == AgentRole.EVALUATOR_SIMULATOR
        assert agent.role.is_red_team is True

    def test_validate_context_with_content(self, agent, sample_context):
        """Test context validation with valid content."""
        errors = agent.validate_context(sample_context)
        assert len(errors) == 0

    def test_validate_context_without_content(self, agent):
        """Test context validation without content."""
        empty_context = SwarmContext()
        errors = agent.validate_context(empty_context)
        assert len(errors) > 0
        assert any("content" in e.lower() for e in errors)

    @pytest.mark.asyncio
    async def test_process_full_evaluation(self, agent, sample_context):
        """Test full proposal evaluation."""
        output = await agent.process(sample_context)

        assert output.success is True
        assert output.agent_role == AgentRole.EVALUATOR_SIMULATOR
        # Output should have content and metadata about the evaluation
        assert output.content
        assert "overall_rating" in output.metadata

    @pytest.mark.asyncio
    async def test_process_best_value_evaluation(self, agent, sample_context):
        """Test Best Value evaluation mode."""
        sample_context.custom_data["evaluation_type"] = "Best Value"

        output = await agent.process(sample_context)

        assert output.success is True
        assert "Best Value" in output.content or output.metadata.get("evaluation_type") == "Best Value"

    @pytest.mark.asyncio
    async def test_process_lpta_evaluation(self, agent, sample_context):
        """Test LPTA evaluation mode."""
        sample_context.custom_data["evaluation_type"] = "LPTA"
        sample_context.custom_data["analysis_type"] = "full_evaluation"

        output = await agent.process(sample_context)

        assert output.success is True

    @pytest.mark.asyncio
    async def test_process_section_evaluation(self, agent, sample_context):
        """Test section-specific evaluation."""
        sample_context.custom_data["analysis_type"] = "section_evaluation"
        sample_context.custom_data["target_section"] = "Technical Approach"

        output = await agent.process(sample_context)

        assert output.success is True

    @pytest.mark.asyncio
    async def test_process_compliance_check(self, agent, sample_context):
        """Test compliance check mode."""
        sample_context.custom_data["analysis_type"] = "compliance_check"
        sample_context.custom_data["solicitation_requirements"] = [
            {"requirement": "FedRAMP High Authorization", "mandatory": True},
            {"requirement": "Key Personnel Qualifications", "mandatory": True},
        ]

        output = await agent.process(sample_context)

        assert output.success is True

    @pytest.mark.asyncio
    async def test_process_mock_evaluation(self, agent, sample_context):
        """Test quick mock evaluation."""
        sample_context.custom_data["analysis_type"] = "mock_evaluation"

        output = await agent.process(sample_context)

        assert output.success is True

    @pytest.mark.asyncio
    async def test_critique_section(self, agent, sample_context):
        """Test critique_section method."""
        critiques = await agent.critique_section(
            context=sample_context,
            section_name="Technical Approach",
            section_content=sample_context.section_drafts["Technical Approach"],
        )

        assert isinstance(critiques, list)
        # Each critique should be a dictionary
        for critique in critiques:
            assert isinstance(critique, dict)
            assert "severity" in critique or "challenge_type" in critique

    @pytest.mark.asyncio
    async def test_evaluate_response_accept(self, agent, sample_context):
        """Test response evaluation for accepted critique."""
        critique = {
            "id": "crit-123",
            "severity": "major",
            "title": "Missing Detail",
        }
        response = {
            "disposition": "Accept",
            "action": "Will add detailed timeline to section 2.3",
            "evidence": "Updated draft attached",
        }

        is_acceptable = await agent.evaluate_response(sample_context, critique, response)

        assert is_acceptable is True

    @pytest.mark.asyncio
    async def test_evaluate_response_deficiency_rebut_rejected(self, agent, sample_context):
        """Test that deficiency cannot be rebutted."""
        critique = {
            "id": "crit-456",
            "severity": "critical",
            "title": "[SSEB] Deficiency: Missing Requirement",
        }
        response = {
            "disposition": "Rebut",
            "evidence": "We believe we addressed this",
        }

        is_acceptable = await agent.evaluate_response(sample_context, critique, response)

        assert is_acceptable is False  # Cannot rebut a deficiency

    def test_map_rating_outstanding(self, agent):
        """Test rating mapping for outstanding."""
        rating = agent._map_rating("Outstanding")
        assert rating == RatingLevel.OUTSTANDING

    def test_map_rating_acceptable(self, agent):
        """Test rating mapping for acceptable."""
        rating = agent._map_rating("Acceptable - meets requirements")
        assert rating == RatingLevel.ACCEPTABLE

    def test_map_rating_unacceptable(self, agent):
        """Test rating mapping for unacceptable."""
        rating = agent._map_rating("UNACCEPTABLE")
        assert rating == RatingLevel.UNACCEPTABLE

    def test_map_weakness_type_deficiency(self, agent):
        """Test weakness type mapping for deficiency."""
        wtype = agent._map_weakness_type("Deficiency")
        assert wtype == WeaknessType.DEFICIENCY

    def test_map_weakness_type_significant(self, agent):
        """Test weakness type mapping for significant weakness."""
        wtype = agent._map_weakness_type("Significant Weakness")
        assert wtype == WeaknessType.SIGNIFICANT_WEAKNESS

    def test_map_weakness_type_risk(self, agent):
        """Test weakness type mapping for risk."""
        wtype = agent._map_weakness_type("Risk")
        assert wtype == WeaknessType.RISK


class TestEvaluationCriteria:
    """Tests for evaluation criteria modules."""

    def test_common_technical_factors_exist(self):
        """Test that common technical factors are defined."""
        assert len(COMMON_TECHNICAL_FACTORS) > 0

    def test_technical_factor_structure(self):
        """Test structure of technical evaluation factors."""
        for factor in COMMON_TECHNICAL_FACTORS:
            assert isinstance(factor, EvaluationFactor)
            assert factor.name
            assert len(factor.evaluation_criteria) > 0

    def test_rating_level_acceptability(self):
        """Test rating level acceptability checks."""
        assert RatingLevel.OUTSTANDING.is_acceptable is True
        assert RatingLevel.GOOD.is_acceptable is True
        assert RatingLevel.ACCEPTABLE.is_acceptable is True
        assert RatingLevel.MARGINAL.is_acceptable is False
        assert RatingLevel.UNACCEPTABLE.is_acceptable is False

    def test_rating_level_numeric_scores(self):
        """Test rating level numeric scores for comparison."""
        assert RatingLevel.OUTSTANDING.numeric_score > RatingLevel.GOOD.numeric_score
        assert RatingLevel.GOOD.numeric_score > RatingLevel.ACCEPTABLE.numeric_score
        assert RatingLevel.ACCEPTABLE.numeric_score > RatingLevel.MARGINAL.numeric_score
        assert RatingLevel.MARGINAL.numeric_score > RatingLevel.UNACCEPTABLE.numeric_score

    def test_weakness_type_severity_order(self):
        """Test weakness type severity ordering."""
        assert WeaknessType.DEFICIENCY.severity_order > WeaknessType.SIGNIFICANT_WEAKNESS.severity_order
        assert WeaknessType.SIGNIFICANT_WEAKNESS.severity_order > WeaknessType.WEAKNESS.severity_order
        assert WeaknessType.WEAKNESS.severity_order > WeaknessType.RISK.severity_order

    def test_confidence_level_favorability(self):
        """Test past performance confidence favorability."""
        assert ConfidenceLevel.SUBSTANTIAL_CONFIDENCE.is_favorable is True
        assert ConfidenceLevel.SATISFACTORY_CONFIDENCE.is_favorable is True
        assert ConfidenceLevel.NEUTRAL_CONFIDENCE.is_favorable is True
        assert ConfidenceLevel.LIMITED_CONFIDENCE.is_favorable is False
        assert ConfidenceLevel.NO_CONFIDENCE.is_favorable is False


class TestIntegration:
    """Integration tests for Evaluator Simulator."""

    @pytest.fixture
    def agent(self):
        return EvaluatorSimulatorAgent()

    @pytest.fixture
    def comprehensive_context(self):
        """Create comprehensive test context."""
        return SwarmContext(
            document_type="Proposal Strategy",
            document_id="integration-test-doc",
            section_drafts={
                "Executive Summary": """
                    TechCorp Federal proposes a comprehensive cloud migration solution
                    that leverages our proven methodology and experienced team.
                """,
                "Technical Approach": """
                    Our 5-phase migration methodology includes:
                    1. Assessment and Planning
                    2. Environment Preparation
                    3. Migration Execution
                    4. Testing and Validation
                    5. Transition to Operations

                    We will utilize AWS GovCloud infrastructure with FedRAMP Moderate
                    authorization. Our team has successfully completed 50+ federal
                    cloud migrations.
                """,
                "Management Approach": """
                    Our Program Manager, Jane Smith, has 15 years of federal IT
                    experience including 8 years managing cloud programs.

                    Quality Management:
                    - ISO 9001:2015 certified QMS
                    - Weekly quality reviews
                    - Monthly metrics reporting

                    Risk Management:
                    - Weekly risk identification meetings
                    - Risk register maintained in SharePoint
                    - Escalation procedures defined
                """,
                "Past Performance": """
                    Reference 1: DHS Cloud Migration Program
                    - Contract Value: $15M
                    - CPARS: Exceptional
                    - Completed on schedule with 99.9% uptime

                    Reference 2: VA EHR Support
                    - Contract Value: $8M
                    - CPARS: Very Good
                    - Successfully migrated 500+ applications
                """,
            },
            company_profile={
                "name": "TechCorp Federal",
                "certifications": [
                    {"cert_type": "ISO 9001"},
                    {"cert_type": "CMMI Level 3"},
                    {"cert_type": "FedRAMP Moderate"},
                ],
                "past_performance": [
                    {"contract_name": "DHS Cloud Migration", "cpars_rating": "Exceptional"},
                    {"contract_name": "VA EHR Support", "cpars_rating": "Very Good"},
                ],
            },
            opportunity={
                "title": "Enterprise Cloud Migration Services",
                "agency": {"name": "Department of Homeland Security"},
                "is_recompete": False,
                "evaluation_factors": [
                    {"name": "Technical Approach", "weight": 40},
                    {"name": "Management Approach", "weight": 30},
                    {"name": "Past Performance", "weight": 30},
                ],
            },
            round_number=1,
        )

    @pytest.mark.asyncio
    async def test_full_evaluation_workflow(self, agent, comprehensive_context):
        """Test complete evaluation workflow."""
        # Run full evaluation
        output = await agent.process(comprehensive_context)

        assert output.success is True
        assert output.agent_role == AgentRole.EVALUATOR_SIMULATOR

        # Check metadata
        metadata = output.metadata
        assert "overall_rating" in metadata
        assert "evaluation_type" in metadata
        assert "deficiency_count" in metadata

        # Check content includes key sections
        content = output.content
        assert "Overall" in content or "Evaluation" in content

    @pytest.mark.asyncio
    async def test_evaluation_identifies_issues(self, agent, comprehensive_context):
        """Test that evaluation identifies issues in proposals."""
        output = await agent.process(comprehensive_context)

        # Should have some critiques or findings
        assert output.critiques or len(output.content) > 100

    @pytest.mark.asyncio
    async def test_evaluation_provides_ratings(self, agent, comprehensive_context):
        """Test that evaluation provides ratings."""
        output = await agent.process(comprehensive_context)

        metadata = output.metadata
        assert "overall_rating" in metadata
        # Rating should be a valid value
        valid_ratings = ["Outstanding", "Good", "Acceptable", "Marginal", "Unacceptable"]
        assert metadata["overall_rating"] in valid_ratings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
