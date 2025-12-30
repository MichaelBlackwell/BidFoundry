"""
Tests for Market Analyst Agent

Unit tests for the Market Analyst agent, including tests for
market data models, prompt generation, and agent processing.
"""

import pytest
from datetime import date, timedelta
import json

# Market Data Models
from models.market_data import (
    MarketData,
    BudgetInfo,
    BudgetTrend,
    ContractAward,
    ForecastOpportunity,
    ForecastConfidence,
    IncumbentPerformance,
    PerformanceRatingLevel,
    MarketOpportunityStatus,
    MarketAnalysis,
)

# Agent
from agents.blue.market_analyst import MarketAnalystAgent, MarketAnalysisResult
from agents.base import SwarmContext
from agents.config import AgentConfig, get_default_config
from agents.types import AgentRole, AgentCategory

# Prompts
from agents.blue.prompts.market_analyst_prompts import (
    MARKET_ANALYST_SYSTEM_PROMPT,
    get_market_analysis_prompt,
    get_opportunity_ranking_prompt,
    get_incumbent_analysis_prompt,
    get_timing_analysis_prompt,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_budget_info():
    """Create a sample BudgetInfo for testing."""
    return BudgetInfo(
        agency="Department of Defense",
        sub_agency="Army",
        fiscal_year=2025,
        total_budget=850.0,
        discretionary_budget=720.0,
        contracting_budget=350.0,
        budget_trend=BudgetTrend.INCREASING,
        yoy_change_percent=5.2,
        priority_areas=["Cloud Migration", "Cybersecurity", "AI/ML"],
        budget_highlights=["Major IT modernization initiative", "Zero Trust implementation"],
        source="FY2025 President's Budget",
        last_updated=date.today(),
    )


@pytest.fixture
def sample_contract_award():
    """Create a sample ContractAward for testing."""
    return ContractAward(
        contract_number="W91CRB-25-D-0001",
        title="Enterprise IT Support Services",
        award_date=date.today() - timedelta(days=30),
        award_amount=45000000.0,
        ceiling_amount=150000000.0,
        contract_type="IDIQ",
        agency="Department of Defense",
        sub_agency="Army",
        contracting_office="Army Contracting Command",
        awardee_name="TechCorp Solutions",
        awardee_uei="ABC123DEF456",
        naics_code="541512",
        psc_code="D302",
        set_aside="Small Business Set-Aside",
        is_recompete=True,
        previous_contract="W91CRB-20-D-0005",
        period_of_performance="5 Years",
        place_of_performance="Fort Belvoir, VA",
    )


@pytest.fixture
def sample_forecast_opportunity():
    """Create a sample ForecastOpportunity for testing."""
    return ForecastOpportunity(
        title="Cloud Migration Support Services",
        description="Support DoD cloud migration to commercial cloud providers",
        agency="Department of Defense",
        sub_agency="DISA",
        estimated_solicitation_date=date.today() + timedelta(days=90),
        estimated_award_date=date.today() + timedelta(days=180),
        fiscal_quarter="FY25 Q2",
        estimated_value=75000000.0,
        naics_code="541512",
        set_aside="SDVOSB",
        contract_type="IDIQ",
        is_recompete=True,
        incumbent="Legacy IT Corp",
        status=MarketOpportunityStatus.PRE_SOLICITATION,
        confidence=ForecastConfidence.HIGH,
        source="DoD Procurement Forecast FY25",
    )


@pytest.fixture
def sample_incumbent_performance():
    """Create a sample IncumbentPerformance for testing."""
    return IncumbentPerformance(
        contractor_name="Legacy IT Corp",
        contractor_uei="XYZ789ABC123",
        contract_number="HC1047-20-D-0012",
        agency="Department of Defense",
        overall_rating=PerformanceRatingLevel.SATISFACTORY,
        quality_rating=PerformanceRatingLevel.VERY_GOOD,
        schedule_rating=PerformanceRatingLevel.SATISFACTORY,
        cost_control_rating=PerformanceRatingLevel.SATISFACTORY,
        contract_modifications=12,
        option_years_exercised=3,
        total_option_years=4,
        has_stop_work_orders=False,
        has_cure_notices=False,
        years_with_agency=8,
        other_contracts_with_agency=3,
        relationship_strength="Strong",
        recompete_likelihood="High",
        vulnerabilities=["Limited innovation", "Key personnel turnover"],
        strengths=["Agency relationships", "Institutional knowledge"],
    )


@pytest.fixture
def sample_market_data(sample_budget_info, sample_contract_award,
                       sample_forecast_opportunity, sample_incumbent_performance):
    """Create a sample MarketData for testing."""
    return MarketData(
        agency_budgets={"DoD": sample_budget_info},
        recent_awards=[sample_contract_award],
        forecast_opportunities=[sample_forecast_opportunity],
        incumbent_performance={"Legacy IT Corp": sample_incumbent_performance},
        total_addressable_market=45000.0,
        target_market_size=5000.0,
        market_growth_rate=8.5,
        data_as_of=date.today(),
        sources=["SAM.gov", "FPDS", "USASpending"],
    )


@pytest.fixture
def sample_company_profile():
    """Create a sample company profile dict for testing."""
    return {
        "name": "TechStartup GovCon",
        "annual_revenue": 15000000.0,
        "employee_count": 75,
        "years_in_business": 5,
        "naics_codes": [
            {"code": "541512", "description": "Computer Systems Design Services", "is_primary": True},
            {"code": "541519", "description": "Other Computer Related Services", "is_primary": False},
        ],
        "certifications": [
            {"cert_type": "SDVOSB", "level": None},
            {"cert_type": "ISO 9001", "level": "2015"},
            {"cert_type": "CMMC", "level": "2"},
        ],
        "core_capabilities": [
            {"name": "Cloud Migration", "description": "AWS and Azure cloud migration services"},
            {"name": "Cybersecurity", "description": "Zero Trust architecture implementation"},
            {"name": "IT Modernization", "description": "Legacy system modernization"},
        ],
        "target_agencies": ["DoD", "DHS", "VA"],
        "past_performance": [
            {
                "contract_name": "Army Cloud Support",
                "agency": "Army",
                "contract_value": 8500000.0,
                "overall_rating": "Very Good",
                "key_accomplishments": ["Migrated 50+ applications to AWS"],
            },
        ],
    }


@pytest.fixture
def market_analyst_agent():
    """Create a MarketAnalystAgent for testing."""
    return MarketAnalystAgent()


# =============================================================================
# Market Data Model Tests
# =============================================================================

class TestBudgetInfo:
    """Tests for BudgetInfo model."""

    def test_budget_info_creation(self, sample_budget_info):
        """Test BudgetInfo is created correctly."""
        assert sample_budget_info.agency == "Department of Defense"
        assert sample_budget_info.fiscal_year == 2025
        assert sample_budget_info.budget_trend == BudgetTrend.INCREASING
        assert sample_budget_info.yoy_change_percent == 5.2

    def test_budget_info_serialization(self, sample_budget_info):
        """Test BudgetInfo serializes and deserializes correctly."""
        data = sample_budget_info.to_dict()
        assert data["agency"] == "Department of Defense"
        assert data["budget_trend"] == "Increasing"

        restored = BudgetInfo.from_dict(data)
        assert restored.agency == sample_budget_info.agency
        assert restored.budget_trend == sample_budget_info.budget_trend

    def test_budget_info_json(self, sample_budget_info):
        """Test BudgetInfo JSON serialization."""
        json_str = sample_budget_info.to_json()
        restored = BudgetInfo.from_json(json_str)
        assert restored.agency == sample_budget_info.agency


class TestContractAward:
    """Tests for ContractAward model."""

    def test_contract_award_creation(self, sample_contract_award):
        """Test ContractAward is created correctly."""
        assert sample_contract_award.contract_number == "W91CRB-25-D-0001"
        assert sample_contract_award.award_amount == 45000000.0
        assert sample_contract_award.is_recompete is True

    def test_contract_award_serialization(self, sample_contract_award):
        """Test ContractAward serializes correctly."""
        data = sample_contract_award.to_dict()
        assert data["contract_number"] == "W91CRB-25-D-0001"
        assert data["award_amount"] == 45000000.0

        restored = ContractAward.from_dict(data)
        assert restored.contract_number == sample_contract_award.contract_number


class TestForecastOpportunity:
    """Tests for ForecastOpportunity model."""

    def test_forecast_opportunity_creation(self, sample_forecast_opportunity):
        """Test ForecastOpportunity is created correctly."""
        assert sample_forecast_opportunity.title == "Cloud Migration Support Services"
        assert sample_forecast_opportunity.confidence == ForecastConfidence.HIGH
        assert sample_forecast_opportunity.is_recompete is True

    def test_forecast_opportunity_serialization(self, sample_forecast_opportunity):
        """Test ForecastOpportunity serializes correctly."""
        data = sample_forecast_opportunity.to_dict()
        assert data["confidence"] == "High"
        assert data["status"] == "Pre-Solicitation"

        restored = ForecastOpportunity.from_dict(data)
        assert restored.title == sample_forecast_opportunity.title


class TestIncumbentPerformance:
    """Tests for IncumbentPerformance model."""

    def test_incumbent_performance_creation(self, sample_incumbent_performance):
        """Test IncumbentPerformance is created correctly."""
        assert sample_incumbent_performance.contractor_name == "Legacy IT Corp"
        assert sample_incumbent_performance.overall_rating == PerformanceRatingLevel.SATISFACTORY
        assert len(sample_incumbent_performance.vulnerabilities) == 2

    def test_incumbent_performance_serialization(self, sample_incumbent_performance):
        """Test IncumbentPerformance serializes correctly."""
        data = sample_incumbent_performance.to_dict()
        assert data["overall_rating"] == "Satisfactory"
        assert "Limited innovation" in data["vulnerabilities"]

        restored = IncumbentPerformance.from_dict(data)
        assert restored.contractor_name == sample_incumbent_performance.contractor_name


class TestMarketData:
    """Tests for MarketData model."""

    def test_market_data_creation(self, sample_market_data):
        """Test MarketData is created correctly."""
        assert len(sample_market_data.agency_budgets) == 1
        assert len(sample_market_data.recent_awards) == 1
        assert sample_market_data.total_addressable_market == 45000.0

    def test_market_data_get_budget(self, sample_market_data):
        """Test MarketData budget retrieval."""
        budget = sample_market_data.get_budget_for_agency("DoD")
        assert budget is not None
        assert budget.agency == "Department of Defense"

        assert sample_market_data.get_budget_for_agency("Unknown") is None

    def test_market_data_get_awards_by_naics(self, sample_market_data):
        """Test filtering awards by NAICS."""
        awards = sample_market_data.get_awards_by_naics("541512")
        assert len(awards) == 1
        assert awards[0].naics_code == "541512"

    def test_market_data_get_forecasts_by_agency(self, sample_market_data):
        """Test filtering forecasts by agency."""
        forecasts = sample_market_data.get_forecasts_by_agency("Defense")
        assert len(forecasts) == 1

    def test_market_data_serialization(self, sample_market_data):
        """Test MarketData full serialization."""
        data = sample_market_data.to_dict()
        assert "agency_budgets" in data
        assert "recent_awards" in data

        restored = MarketData.from_dict(data)
        assert len(restored.agency_budgets) == 1
        assert len(restored.recent_awards) == 1


class TestMarketAnalysis:
    """Tests for MarketAnalysis model."""

    def test_market_analysis_creation(self):
        """Test MarketAnalysis is created correctly."""
        analysis = MarketAnalysis(
            total_addressable_market=45000.0,
            serviceable_addressable_market=12000.0,
            target_market=3000.0,
            competitive_density="Medium",
            market_trends=["Cloud adoption", "Zero Trust"],
        )
        assert analysis.total_addressable_market == 45000.0
        assert analysis.competitive_density == "Medium"
        assert len(analysis.market_trends) == 2

    def test_market_analysis_serialization(self):
        """Test MarketAnalysis serializes correctly."""
        analysis = MarketAnalysis(
            total_addressable_market=45000.0,
            ranked_opportunities=[
                {"rank": 1, "title": "Opp 1", "score": 8.5},
            ],
        )
        data = analysis.to_dict()
        assert data["total_addressable_market"] == 45000.0
        assert len(data["ranked_opportunities"]) == 1


# =============================================================================
# Prompt Tests
# =============================================================================

class TestMarketAnalystPrompts:
    """Tests for Market Analyst prompt generation."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert MARKET_ANALYST_SYSTEM_PROMPT is not None
        assert "Market Analyst" in MARKET_ANALYST_SYSTEM_PROMPT

    def test_market_analysis_prompt(self, sample_company_profile):
        """Test comprehensive market analysis prompt generation."""
        prompt = get_market_analysis_prompt(
            company_profile=sample_company_profile,
        )
        assert "TechStartup GovCon" in prompt
        assert "541512" in prompt
        assert "Market Sizing" in prompt

    def test_market_analysis_prompt_with_data(self, sample_company_profile, sample_market_data):
        """Test market analysis prompt with market data."""
        prompt = get_market_analysis_prompt(
            company_profile=sample_company_profile,
            market_data=sample_market_data.to_dict(),
            target_agencies=["DoD"],
        )
        assert "Market Data" in prompt
        assert "DoD" in prompt

    def test_opportunity_ranking_prompt(self, sample_company_profile, sample_forecast_opportunity):
        """Test opportunity ranking prompt generation."""
        opportunities = [sample_forecast_opportunity.to_dict()]
        prompt = get_opportunity_ranking_prompt(
            company_profile=sample_company_profile,
            opportunities=opportunities,
            max_opportunities=3,
        )
        assert "Opportunity Ranking" in prompt
        assert "Cloud Migration Support Services" in prompt
        assert "Capability Fit" in prompt

    def test_incumbent_analysis_prompt(self, sample_incumbent_performance):
        """Test incumbent analysis prompt generation."""
        prompt = get_incumbent_analysis_prompt(
            incumbent_data=sample_incumbent_performance.to_dict(),
        )
        assert "Incumbent Analysis" in prompt
        assert "Legacy IT Corp" in prompt
        assert "Satisfactory" in prompt

    def test_timing_analysis_prompt(self, sample_forecast_opportunity, sample_budget_info):
        """Test timing analysis prompt generation."""
        prompt = get_timing_analysis_prompt(
            forecast_opportunities=[sample_forecast_opportunity.to_dict()],
            agency_budgets={"DoD": sample_budget_info.to_dict()},
        )
        assert "Timing" in prompt
        assert "Fiscal" in prompt


# =============================================================================
# Agent Tests
# =============================================================================

class TestMarketAnalystAgent:
    """Tests for MarketAnalystAgent."""

    def test_agent_creation(self, market_analyst_agent):
        """Test agent is created with correct properties."""
        assert market_analyst_agent.role == AgentRole.MARKET_ANALYST
        assert market_analyst_agent.category == AgentCategory.BLUE
        assert market_analyst_agent.is_enabled is True

    def test_agent_default_config(self, market_analyst_agent):
        """Test agent has correct default configuration."""
        assert market_analyst_agent.config.role == AgentRole.MARKET_ANALYST
        assert market_analyst_agent.config.llm_config.temperature == 0.5

    def test_agent_custom_config(self):
        """Test agent with custom configuration."""
        config = AgentConfig(
            role=AgentRole.MARKET_ANALYST,
            name="Custom Market Analyst",
        )
        agent = MarketAnalystAgent(config=config)
        assert agent.name == "Custom Market Analyst"

    @pytest.mark.asyncio
    async def test_agent_validate_context_requires_profile(self, market_analyst_agent):
        """Test that validation requires company profile."""
        context = SwarmContext(
            document_type="Competitive Analysis",
        )
        errors = market_analyst_agent.validate_context(context)
        assert len(errors) > 0
        assert any("Company profile" in e for e in errors)

    @pytest.mark.asyncio
    async def test_agent_validate_context_valid(self, market_analyst_agent, sample_company_profile):
        """Test valid context passes validation."""
        context = SwarmContext(
            document_type="Competitive Analysis",
            company_profile=sample_company_profile,
        )
        errors = market_analyst_agent.validate_context(context)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_agent_process_comprehensive(self, market_analyst_agent, sample_company_profile):
        """Test comprehensive market analysis processing."""
        context = SwarmContext(
            document_type="Market Analysis",
            company_profile=sample_company_profile,
            round_type="BlueBuild",
        )
        output = await market_analyst_agent.process(context)
        assert output.success is True
        assert output.content != ""
        # Verify output has some analysis content
        assert len(output.content) > 0

    @pytest.mark.asyncio
    async def test_agent_process_opportunity_ranking(
        self, market_analyst_agent, sample_company_profile, sample_forecast_opportunity
    ):
        """Test opportunity ranking analysis."""
        context = SwarmContext(
            document_type="Opportunity Analysis",
            company_profile=sample_company_profile,
            custom_data={
                "analysis_type": "opportunity_ranking",
                "opportunities": [sample_forecast_opportunity.to_dict()],
            },
        )
        output = await market_analyst_agent.process(context)
        assert output.success is True
        assert "metadata" in dir(output) or hasattr(output, 'metadata')

    @pytest.mark.asyncio
    async def test_agent_process_incumbent_analysis(
        self, market_analyst_agent, sample_company_profile, sample_incumbent_performance
    ):
        """Test incumbent analysis processing."""
        context = SwarmContext(
            document_type="Incumbent Analysis",
            company_profile=sample_company_profile,
            custom_data={
                "analysis_type": "incumbent_analysis",
                "incumbent_data": sample_incumbent_performance.to_dict(),
            },
        )
        output = await market_analyst_agent.process(context)
        assert output.success is True

    @pytest.mark.asyncio
    async def test_agent_process_timing_analysis(
        self, market_analyst_agent, sample_company_profile, sample_market_data
    ):
        """Test timing analysis processing."""
        context = SwarmContext(
            document_type="Timing Analysis",
            company_profile=sample_company_profile,
            custom_data={
                "analysis_type": "timing_analysis",
                "market_data": sample_market_data.to_dict(),
            },
        )
        output = await market_analyst_agent.process(context)
        assert output.success is True

    @pytest.mark.asyncio
    async def test_agent_process_with_missing_profile(self, market_analyst_agent):
        """Test processing fails gracefully with missing profile."""
        context = SwarmContext(
            document_type="Market Analysis",
        )
        output = await market_analyst_agent.process(context)
        assert output.success is False
        assert output.error_message is not None

    @pytest.mark.asyncio
    async def test_agent_draft_section_market_sizing(
        self, market_analyst_agent, sample_company_profile
    ):
        """Test drafting market sizing section."""
        context = SwarmContext(
            company_profile=sample_company_profile,
        )
        content = await market_analyst_agent.draft_section(context, "Market Sizing")
        assert content != ""

    @pytest.mark.asyncio
    async def test_agent_draft_section_opportunities(
        self, market_analyst_agent, sample_company_profile
    ):
        """Test drafting opportunities section."""
        context = SwarmContext(
            company_profile=sample_company_profile,
        )
        content = await market_analyst_agent.draft_section(context, "Priority Opportunities")
        assert content != ""

    @pytest.mark.asyncio
    async def test_agent_revise_section(
        self, market_analyst_agent, sample_company_profile
    ):
        """Test revising a section based on critiques."""
        context = SwarmContext(
            company_profile=sample_company_profile,
            section_drafts={
                "Market Sizing": "## Market Sizing\n\nThe TAM is $45B.",
            },
        )
        critiques = [
            {
                "argument": "Market sizing lacks supporting assumptions",
                "severity": "major",
                "suggested_remedy": "Add specific assumptions for TAM calculation",
            },
        ]
        content = await market_analyst_agent.revise_section(context, "Market Sizing", critiques)
        assert content != ""


class TestMarketAnalysisResult:
    """Tests for MarketAnalysisResult dataclass."""

    def test_result_defaults(self):
        """Test MarketAnalysisResult has correct defaults."""
        result = MarketAnalysisResult()
        assert result.success is True
        assert result.competitive_density == "Unknown"
        assert result.ranked_opportunities == []

    def test_result_with_values(self):
        """Test MarketAnalysisResult with values."""
        result = MarketAnalysisResult(
            total_addressable_market=45000.0,
            serviceable_addressable_market=12000.0,
            ranked_opportunities=[
                {"rank": 1, "title": "Test Opp", "score": 8.5},
            ],
            competitive_density="High",
            market_trends=["Cloud", "AI"],
        )
        assert result.total_addressable_market == 45000.0
        assert len(result.ranked_opportunities) == 1
        assert result.competitive_density == "High"


# =============================================================================
# Integration Tests
# =============================================================================

class TestMarketAnalystIntegration:
    """Integration tests for Market Analyst with other components."""

    def test_agent_registry_discovery(self):
        """Test agent can be discovered via registry pattern."""
        from agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register(AgentRole.MARKET_ANALYST, MarketAnalystAgent)

        agent = registry.create(AgentRole.MARKET_ANALYST)
        assert agent is not None
        assert agent.role == AgentRole.MARKET_ANALYST

    def test_market_data_to_context(self, sample_market_data, sample_company_profile):
        """Test MarketData integrates with SwarmContext."""
        context = SwarmContext(
            company_profile=sample_company_profile,
            custom_data={
                "market_data": sample_market_data.to_dict(),
            },
        )
        assert context.custom_data["market_data"] is not None
        assert "agency_budgets" in context.custom_data["market_data"]

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(
        self, market_analyst_agent, sample_company_profile, sample_market_data
    ):
        """Test full analysis workflow from data to output."""
        context = SwarmContext(
            document_type="Market Analysis",
            company_profile=sample_company_profile,
            round_type="BlueBuild",
            custom_data={
                "market_data": sample_market_data.to_dict(),
                "target_agencies": ["DoD"],
            },
        )

        output = await market_analyst_agent.process(context)

        assert output.success is True
        assert output.agent_role == AgentRole.MARKET_ANALYST
        assert output.processing_time_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
