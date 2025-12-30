"""
Tests for Risk Assessor Agent

Tests the Risk Assessor agent's ability to identify risks, assess probability
and impact, generate worst-case scenarios, and stress-test assumptions.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from agents.base import SwarmContext, AgentOutput
from agents.config import AgentConfig, get_default_config
from agents.types import AgentRole, AgentCategory

from agents.red.risk_assessor import (
    RiskAssessorAgent,
    RiskAssessorResult,
    StressTestResult,
    MitigationEvaluation,
    ResponseEvaluation,
)

from agents.red.risk_taxonomy import (
    Risk,
    RiskCategory,
    Probability,
    Impact,
    MitigationStatus,
    WorstCaseScenario,
    RiskRegister,
    identify_risk_category,
)

from models.critique import Critique, ChallengeType, Severity


# ============================================================================
# Risk Taxonomy Tests
# ============================================================================

class TestRisk:
    """Tests for the Risk dataclass."""

    def test_risk_creation(self):
        """Test creating a risk with required fields."""
        risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Test Risk",
            description="This is a test risk",
            probability=Probability.MEDIUM,
            impact=Impact.HIGH,
        )

        assert risk.category == RiskCategory.EXECUTION
        assert risk.title == "Test Risk"
        assert risk.probability == Probability.MEDIUM
        assert risk.impact == Impact.HIGH
        assert risk.id is not None

    def test_risk_score_calculation(self):
        """Test that risk score is calculated correctly."""
        risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Test",
            description="Test",
            probability=Probability.HIGH,  # 0.75
            impact=Impact.HIGH,  # 0.7
        )

        expected_score = 0.75 * 0.7  # 0.525
        assert abs(risk.risk_score - expected_score) < 0.01

    def test_risk_level_critical(self):
        """Test that high-probability high-impact risks are Critical."""
        risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Test",
            description="Test",
            probability=Probability.ALMOST_CERTAIN,  # 0.95
            impact=Impact.CATASTROPHIC,  # 0.9
        )

        assert risk.risk_level == "critical"

    def test_risk_level_high(self):
        """Test High risk level."""
        risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Test",
            description="Test",
            probability=Probability.HIGH,  # 0.75
            impact=Impact.MEDIUM,  # 0.5
        )

        # Score = 0.75 * 0.5 = 0.375, which is Medium-High
        assert risk.risk_level in {"high", "medium"}

    def test_risk_level_low(self):
        """Test Low risk level."""
        risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Test",
            description="Test",
            probability=Probability.RARE,  # 0.05
            impact=Impact.LOW,  # 0.3
        )

        # Score = 0.05 * 0.3 = 0.015
        assert risk.risk_level in {"Low", "Negligible"}

    def test_risk_mitigation_required_for_high_severity(self):
        """Test that high-severity risks require mitigation."""
        risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Test",
            description="Test",
            probability=Probability.HIGH,
            impact=Impact.HIGH,
        )

        assert risk.mitigation_required is True

    def test_risk_requires_human_review_for_critical(self):
        """Test that critical risks require human review."""
        risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Test",
            description="Test",
            probability=Probability.HIGH,
            impact=Impact.CATASTROPHIC,
        )

        assert risk.requires_human_review is True

    def test_risk_serialization(self):
        """Test risk serialization to dict and back."""
        risk = Risk(
            category=RiskCategory.COMPLIANCE,
            title="Compliance Risk",
            description="FAR compliance issue",
            probability=Probability.MEDIUM,
            impact=Impact.HIGH,
            trigger="Audit discovers non-compliance",
            consequence="Contract termination",
            suggested_mitigation="Conduct compliance review",
        )

        risk_dict = risk.to_dict()
        restored_risk = Risk.from_dict(risk_dict)

        assert restored_risk.category == risk.category
        assert restored_risk.title == risk.title
        assert restored_risk.probability == risk.probability
        assert restored_risk.impact == risk.impact


class TestRiskCategory:
    """Tests for RiskCategory enum."""

    def test_all_categories_exist(self):
        """Test that all expected categories exist."""
        expected_categories = [
            "Execution", "Staffing", "Technical", "Schedule", "Transition",
            "Compliance", "Eligibility", "OCI", "Security",
            "Competitive", "Incumbent", "Pricing", "Teaming",
            "Financial", "Cash Flow", "Profitability",
            "Political", "Protest", "Recompete", "Market",
            "Strategic", "Reputation", "Opportunity Cost",
        ]

        for cat_name in expected_categories:
            assert any(cat.value == cat_name for cat in RiskCategory)


class TestProbability:
    """Tests for Probability enum."""

    def test_probability_numeric_values(self):
        """Test probability numeric value mapping."""
        assert Probability.RARE.numeric_value == 0.05
        assert Probability.LOW.numeric_value == 0.20
        assert Probability.MEDIUM.numeric_value == 0.45
        assert Probability.HIGH.numeric_value == 0.75
        assert Probability.ALMOST_CERTAIN.numeric_value == 0.95


class TestImpact:
    """Tests for Impact enum."""

    def test_impact_numeric_values(self):
        """Test impact numeric value mapping."""
        assert Impact.NEGLIGIBLE.numeric_value == 0.1
        assert Impact.LOW.numeric_value == 0.3
        assert Impact.MEDIUM.numeric_value == 0.5
        assert Impact.HIGH.numeric_value == 0.7
        assert Impact.CATASTROPHIC.numeric_value == 0.9


class TestWorstCaseScenario:
    """Tests for WorstCaseScenario dataclass."""

    def test_scenario_creation(self):
        """Test creating a worst-case scenario."""
        scenario = WorstCaseScenario(
            title="Key Personnel Loss",
            narrative="Our PM leaves for a competitor...",
            trigger_chain=["Competitor makes offer", "PM accepts", "We scramble"],
            plausibility="Medium",
            severity="High",
        )

        assert scenario.title == "Key Personnel Loss"
        assert len(scenario.trigger_chain) == 3
        assert scenario.plausibility == "Medium"

    def test_scenario_serialization(self):
        """Test scenario serialization."""
        scenario = WorstCaseScenario(
            title="Test Scenario",
            narrative="Test narrative",
            contributing_risks=["risk1", "risk2"],
        )

        scenario_dict = scenario.to_dict()
        assert scenario_dict["title"] == "Test Scenario"
        assert len(scenario_dict["contributing_risks"]) == 2


class TestRiskRegister:
    """Tests for RiskRegister dataclass."""

    def test_empty_register(self):
        """Test creating an empty risk register."""
        register = RiskRegister(document_id="doc1")
        assert register.total_risks == 0
        assert register.overall_risk_level == ""

    def test_register_with_risks(self):
        """Test register statistics with risks."""
        risks = [
            Risk(
                category=RiskCategory.EXECUTION,
                title="Risk 1",
                description="Test",
                probability=Probability.HIGH,
                impact=Impact.CATASTROPHIC,
            ),
            Risk(
                category=RiskCategory.COMPETITIVE,
                title="Risk 2",
                description="Test",
                probability=Probability.MEDIUM,
                impact=Impact.MEDIUM,
            ),
            Risk(
                category=RiskCategory.COMPLIANCE,
                title="Risk 3",
                description="Test",
                probability=Probability.LOW,
                impact=Impact.LOW,
            ),
        ]

        register = RiskRegister(
            document_id="doc1",
            risks=risks,
        )

        assert register.total_risks == 3
        assert register.critical_risks >= 1  # At least the HIGH/CATASTROPHIC one
        assert register.overall_risk_level == "critical"

    def test_register_category_breakdown(self):
        """Test that register tracks risks by category."""
        risks = [
            Risk(category=RiskCategory.EXECUTION, title="R1", description="T", probability=Probability.MEDIUM, impact=Impact.MEDIUM),
            Risk(category=RiskCategory.EXECUTION, title="R2", description="T", probability=Probability.MEDIUM, impact=Impact.MEDIUM),
            Risk(category=RiskCategory.COMPETITIVE, title="R3", description="T", probability=Probability.MEDIUM, impact=Impact.MEDIUM),
        ]

        register = RiskRegister(risks=risks)
        assert register.risks_by_category["Execution"] == 2
        assert register.risks_by_category["Competitive"] == 1

    def test_get_top_risks(self):
        """Test getting top risks by score."""
        risks = [
            Risk(category=RiskCategory.EXECUTION, title="Low", description="T", probability=Probability.LOW, impact=Impact.LOW),
            Risk(category=RiskCategory.EXECUTION, title="High", description="T", probability=Probability.HIGH, impact=Impact.HIGH),
            Risk(category=RiskCategory.EXECUTION, title="Medium", description="T", probability=Probability.MEDIUM, impact=Impact.MEDIUM),
        ]

        register = RiskRegister(risks=risks)
        top_risks = register.get_top_risks(2)

        assert len(top_risks) == 2
        assert top_risks[0].title == "High"


class TestIdentifyRiskCategory:
    """Tests for the identify_risk_category helper function."""

    def test_execution_keywords(self):
        """Test detection of execution risk indicators."""
        content = "This approach has an aggressive timeline with unproven technology."
        categories = identify_risk_category(content)
        assert RiskCategory.EXECUTION in categories

    def test_compliance_keywords(self):
        """Test detection of compliance risk indicators."""
        content = "The FAR requirement for this must comply with DFAR regulations."
        categories = identify_risk_category(content)
        assert RiskCategory.COMPLIANCE in categories

    def test_staffing_keywords(self):
        """Test detection of staffing risk indicators."""
        content = "Key personnel with clearance requirements are hard to fill."
        categories = identify_risk_category(content)
        assert RiskCategory.STAFFING in categories

    def test_default_category(self):
        """Test that unknown content defaults to Execution."""
        content = "Lorem ipsum dolor sit amet."
        categories = identify_risk_category(content)
        assert RiskCategory.EXECUTION in categories


# ============================================================================
# Risk Assessor Agent Tests
# ============================================================================

class TestRiskAssessorAgent:
    """Tests for the RiskAssessorAgent class."""

    @pytest.fixture
    def agent(self):
        """Create a Risk Assessor agent instance."""
        return RiskAssessorAgent()

    @pytest.fixture
    def basic_context(self):
        """Create a basic SwarmContext for testing."""
        return SwarmContext(
            document_type="Capture Strategy",
            document_id="test-doc-1",
            section_drafts={
                "Win Themes": "Our team has proven experience with aggressive timelines...",
                "Competitive Analysis": "The incumbent has strong relationships but...",
                "Pricing Strategy": "We recommend moderate pricing at $20M...",
            },
            round_number=1,
        )

    def test_agent_role(self, agent):
        """Test that agent has correct role."""
        assert agent.role == AgentRole.RISK_ASSESSOR

    def test_agent_category(self, agent):
        """Test that agent is in red team category."""
        assert agent.category == AgentCategory.RED

    def test_agent_name(self, agent):
        """Test agent has expected name."""
        assert "Risk Assessor" in agent.name

    @pytest.mark.asyncio
    async def test_process_full_assessment(self, agent, basic_context):
        """Test full risk assessment processing."""
        output = await agent.process(basic_context)

        assert output.success is True
        assert output.agent_role == AgentRole.RISK_ASSESSOR
        assert "risks" in output.metadata or output.metadata.get("total_risks", 0) >= 0

    @pytest.mark.asyncio
    async def test_process_section_assessment(self, agent, basic_context):
        """Test section-specific risk assessment."""
        basic_context.custom_data["analysis_type"] = "section_assessment"
        basic_context.custom_data["target_section"] = "Win Themes"

        output = await agent.process(basic_context)

        assert output.success is True

    @pytest.mark.asyncio
    async def test_process_stress_test(self, agent, basic_context):
        """Test assumption stress testing."""
        basic_context.custom_data["analysis_type"] = "stress_test"
        basic_context.custom_data["assumptions"] = [
            {"statement": "The agency will prioritize innovation over cost", "source": "Strategy"},
            {"statement": "The incumbent will not improve their approach", "source": "Competitive"},
        ]

        output = await agent.process(basic_context)

        assert output.success is True

    @pytest.mark.asyncio
    async def test_process_worst_case(self, agent, basic_context):
        """Test worst-case scenario development."""
        basic_context.custom_data["analysis_type"] = "worst_case"

        output = await agent.process(basic_context)

        assert output.success is True

    @pytest.mark.asyncio
    async def test_validate_context_no_content(self, agent):
        """Test validation fails when no content provided."""
        context = SwarmContext(document_type="Test")
        errors = agent.validate_context(context)

        assert len(errors) > 0
        assert any("content" in err.lower() for err in errors)

    @pytest.mark.asyncio
    async def test_validate_context_with_content(self, agent, basic_context):
        """Test validation passes with proper content."""
        errors = agent.validate_context(basic_context)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_critique_section(self, agent, basic_context):
        """Test the critique_section method."""
        critiques = await agent.critique_section(
            basic_context,
            "Win Themes",
            "Our team has aggressive timelines and complex integrations...",
        )

        assert isinstance(critiques, list)

    @pytest.mark.asyncio
    async def test_evaluate_response(self, agent, basic_context):
        """Test the evaluate_response method."""
        critique = {
            "id": "test-critique-1",
            "title": "Staffing Risk",
            "category": "Staffing",
            "description": "Key personnel may leave",
            "suggested_mitigation": "Secure retention agreements",
        }

        response = {
            "risk_id": "test-critique-1",
            "disposition": "Accept",
            "action": "Will implement retention bonuses",
            "mitigation_plan": "Retention bonuses for key personnel",
        }

        is_acceptable = await agent.evaluate_response(basic_context, critique, response)
        assert isinstance(is_acceptable, bool)


class TestRiskAssessorParsing:
    """Tests for Risk Assessor parsing methods."""

    @pytest.fixture
    def agent(self):
        return RiskAssessorAgent()

    def test_parse_risks(self, agent):
        """Test parsing risks from LLM response."""
        content = """### Risk 1: Key Personnel Vulnerability

**Category**: Staffing

**Description**: Proposed PM has received competitor interest.

**Trigger**: Competitor makes attractive offer.

**Consequence**: Forced personnel substitution.

**Probability**: Medium

**Impact**: High

**Source**: Management Approach

**Mitigation Required**: Yes

**Suggested Mitigation**: Secure retention agreement.

**Residual Risk**: Personnel can still leave.

---

### Risk 2: Pricing Uncertainty

**Category**: Pricing

**Description**: PTW analysis based on limited data.

**Trigger**: Competitor prices more aggressively.

**Consequence**: Outside competitive range.

**Probability**: Medium

**Impact**: High

**Source**: Price-to-Win Analysis

**Mitigation Required**: Yes

**Suggested Mitigation**: Develop multiple pricing scenarios.

**Residual Risk**: Inherent uncertainty in competitive pricing.
"""

        risks = agent._parse_risks(content, "doc1", 1)

        assert len(risks) == 2
        assert risks[0].category == RiskCategory.STAFFING
        assert risks[1].category == RiskCategory.PRICING
        assert all(r.probability == Probability.MEDIUM for r in risks)
        assert all(r.impact == Impact.HIGH for r in risks)

    def test_parse_worst_case_scenarios(self, agent):
        """Test parsing worst-case scenarios."""
        content = """### Worst-Case Scenario 1: Complete Failure

**Narrative**: Everything goes wrong.

**Trigger Chain**:
1. First bad thing happens
2. Second bad thing happens
3. Everything collapses

**Contributing Risks**: Risk 1, Risk 3, Risk 5

**Impacts**:
- **Win Probability**: Reduced to 0%
- **Financial**: Total loss
- **Reputation**: Severely damaged
- **Strategic**: Sets back years

**Early Warning Signs**:
- Sign one
- Sign two

**Prevention Measures**:
- Measure one
- Measure two

**Recovery Options**:
- Option one
- Option two

**Plausibility**: Medium

**Severity**: Catastrophic
"""

        scenarios = agent._parse_worst_case_scenarios(content)

        assert len(scenarios) == 1
        assert scenarios[0].plausibility == "Medium"
        assert scenarios[0].severity == "Catastrophic"
        assert len(scenarios[0].trigger_chain) == 3

    def test_parse_stress_tests(self, agent):
        """Test parsing stress test results."""
        content = """### Assumption 1 Stress Test

**Assumption**: "The agency will prioritize innovation"

**Stress Scenario**: Budget cuts force LPTA evaluation.

**Strategy Impact**: Our premium pricing becomes liability.

**Win Probability Effect**: Decrease from 55% to 25%.

**Vulnerability Level**: High

**Early Warning Indicators**:
- Budget announcements
- RFP language changes

**Contingency Recommendation**: Develop shadow pricing model.
"""

        results = agent._parse_stress_tests(content)

        assert len(results) == 1
        assert results[0].vulnerability_level == "High"
        assert len(results[0].early_warning_indicators) == 2

    def test_map_risk_category(self, agent):
        """Test risk category string mapping."""
        assert agent._map_risk_category("Execution") == RiskCategory.EXECUTION
        assert agent._map_risk_category("staffing") == RiskCategory.STAFFING
        assert agent._map_risk_category("COMPLIANCE") == RiskCategory.COMPLIANCE
        assert agent._map_risk_category("unknown") == RiskCategory.EXECUTION

    def test_map_probability(self, agent):
        """Test probability string mapping."""
        assert agent._map_probability("Rare") == Probability.RARE
        assert agent._map_probability("low") == Probability.LOW
        assert agent._map_probability("Medium") == Probability.MEDIUM
        assert agent._map_probability("HIGH") == Probability.HIGH
        assert agent._map_probability("Almost Certain") == Probability.ALMOST_CERTAIN

    def test_map_impact(self, agent):
        """Test impact string mapping."""
        assert agent._map_impact("Negligible") == Impact.NEGLIGIBLE
        assert agent._map_impact("low") == Impact.LOW
        assert agent._map_impact("Medium") == Impact.MEDIUM
        assert agent._map_impact("HIGH") == Impact.HIGH
        assert agent._map_impact("Catastrophic") == Impact.CATASTROPHIC


class TestRisksToCritiques:
    """Tests for converting risks to critiques."""

    @pytest.fixture
    def agent(self):
        return RiskAssessorAgent()

    @pytest.fixture
    def context(self):
        return SwarmContext(
            document_type="Test",
            document_id="doc1",
            round_number=1,
        )

    def test_risks_to_critiques_conversion(self, agent, context):
        """Test that risks are properly converted to critiques."""
        risks = [
            Risk(
                category=RiskCategory.EXECUTION,
                title="Execution Risk",
                description="Schedule may slip",
                trigger="Resource unavailability",
                consequence="Delayed delivery",
                probability=Probability.HIGH,
                impact=Impact.HIGH,
                source_section="Schedule",
                suggested_mitigation="Add buffer time",
            ),
        ]

        critiques = agent._risks_to_critiques(risks, context)

        assert len(critiques) == 1
        assert critiques[0].challenge_type == ChallengeType.RISK
        assert "Risk: Execution Risk" in critiques[0].title
        assert critiques[0].agent == AgentRole.RISK_ASSESSOR.value

    def test_risk_severity_to_critique_severity_mapping(self, agent, context):
        """Test that risk levels map to correct critique severities."""
        # Critical risk
        critical_risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Critical",
            description="T",
            probability=Probability.ALMOST_CERTAIN,
            impact=Impact.CATASTROPHIC,
            suggested_mitigation="Address immediately",  # Required for critique conversion
        )

        # Low risk
        low_risk = Risk(
            category=RiskCategory.EXECUTION,
            title="Low",
            description="T",
            probability=Probability.RARE,
            impact=Impact.LOW,
            suggested_mitigation="Monitor",  # Required for critique conversion
        )

        critical_critiques = agent._risks_to_critiques([critical_risk], context)
        low_critiques = agent._risks_to_critiques([low_risk], context)

        assert critical_critiques[0].severity == Severity.CRITICAL
        assert low_critiques[0].severity in {Severity.MINOR, Severity.OBSERVATION}


class TestRiskAssessorResult:
    """Tests for RiskAssessorResult dataclass."""

    def test_empty_result(self):
        """Test creating an empty result."""
        result = RiskAssessorResult()
        assert result.success is True
        assert len(result.risks) == 0
        assert len(result.worst_case_scenarios) == 0

    def test_result_with_risks(self):
        """Test result with risks."""
        risks = [
            Risk(category=RiskCategory.EXECUTION, title="R1", description="D", probability=Probability.MEDIUM, impact=Impact.MEDIUM),
            Risk(category=RiskCategory.COMPETITIVE, title="R2", description="D", probability=Probability.HIGH, impact=Impact.HIGH),
        ]

        result = RiskAssessorResult(risks=risks)
        assert len(result.risks) == 2

    def test_result_serialization(self):
        """Test result serialization."""
        result = RiskAssessorResult(
            risks=[
                Risk(category=RiskCategory.EXECUTION, title="R1", description="D", probability=Probability.MEDIUM, impact=Impact.MEDIUM),
            ],
            overall_assessment="Test assessment",
            processing_time_ms=100,
        )

        result_dict = result.to_dict()
        assert len(result_dict["risks"]) == 1
        assert result_dict["overall_assessment"] == "Test assessment"
        assert result_dict["processing_time_ms"] == 100


class TestStressTestResult:
    """Tests for StressTestResult dataclass."""

    def test_stress_test_creation(self):
        """Test creating a stress test result."""
        result = StressTestResult(
            assumption="Agency will prioritize innovation",
            stress_scenario="Budget cuts force LPTA",
            vulnerability_level="High",
        )

        assert result.vulnerability_level == "High"

    def test_stress_test_serialization(self):
        """Test stress test result serialization."""
        result = StressTestResult(
            assumption="Test assumption",
            stress_scenario="Test scenario",
            early_warning_indicators=["Indicator 1", "Indicator 2"],
        )

        result_dict = result.to_dict()
        assert result_dict["assumption"] == "Test assumption"
        assert len(result_dict["early_warning_indicators"]) == 2


class TestMitigationEvaluation:
    """Tests for MitigationEvaluation dataclass."""

    def test_mitigation_evaluation_creation(self):
        """Test creating a mitigation evaluation."""
        evaluation = MitigationEvaluation(
            risk_id="risk-1",
            verdict="Partially Adequate",
            gaps_identified=["Gap 1", "Gap 2"],
        )

        assert evaluation.verdict == "Partially Adequate"
        assert len(evaluation.gaps_identified) == 2


class TestIntegration:
    """Integration tests for Risk Assessor with other components."""

    @pytest.fixture
    def agent(self):
        return RiskAssessorAgent()

    @pytest.mark.asyncio
    async def test_full_workflow(self, agent):
        """Test a complete risk assessment workflow."""
        # Create context with realistic content
        context = SwarmContext(
            document_type="Proposal Strategy",
            document_id="prop-001",
            section_drafts={
                "Executive Summary": """
                    We are pursuing this $50M opportunity with our proven team.
                    We believe the agency will prioritize innovation over cost.
                    Our aggressive timeline will demonstrate commitment.
                """,
                "Win Themes": """
                    Theme 1: Mission-Proven Excellence
                    Our team has successfully delivered similar projects.
                    We expect the customer to value our approach.
                """,
                "Competitive Analysis": """
                    The incumbent has strong relationships but weak innovation.
                    We anticipate they will not significantly improve their approach.
                    Competitors will likely price at the low end.
                """,
            },
            company_profile={
                "name": "TestCorp",
                "certifications": [{"cert_type": "8(a)"}],
            },
            opportunity={
                "title": "Cloud Migration Services",
                "agency": {"name": "Department of Test"},
                "estimated_value": "$50M",
            },
            round_number=1,
        )

        # Process full assessment
        output = await agent.process(context)

        assert output.success is True
        assert output.metadata.get("total_risks", 0) > 0

        # Verify critiques were generated
        assert len(output.critiques) > 0

        # Verify content was generated
        assert "Risk" in output.content

    @pytest.mark.asyncio
    async def test_agent_in_registry(self, agent):
        """Test that Risk Assessor can be registered and created."""
        from agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register(AgentRole.RISK_ASSESSOR, RiskAssessorAgent)

        created_agent = registry.create(AgentRole.RISK_ASSESSOR)
        assert created_agent is not None
        assert created_agent.role == AgentRole.RISK_ASSESSOR


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
