"""
Tests for Strategy Architect Agent

Tests the Strategy Architect's ability to:
- Generate all 7 document types
- Correctly incorporate critiques in revision mode
- Produce outputs conforming to document schemas
"""

import pytest
from datetime import date
from typing import Dict, Any

from agents.blue.strategy_architect import StrategyArchitectAgent, DraftResult
from agents.base import SwarmContext, AgentOutput
from agents.config import AgentConfig, get_default_config
from agents.types import AgentRole, AgentCategory

from agents.blue.templates.base import (
    DocumentTemplate,
    SectionSpec,
    get_template_for_document_type,
)
from agents.blue.templates import (
    CapabilityStatementTemplate,
    CompetitiveAnalysisTemplate,
    SWOTAnalysisTemplate,
    BDPipelineTemplate,
    ProposalStrategyTemplate,
    GoToMarketTemplate,
    TeamingStrategyTemplate,
)

from agents.blue.prompts.strategy_architect_prompts import (
    STRATEGY_ARCHITECT_SYSTEM_PROMPT,
    get_draft_prompt,
    get_revision_prompt,
    get_section_prompt,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_company_profile() -> Dict[str, Any]:
    """Create a sample company profile for testing."""
    return {
        "id": "test-company-001",
        "name": "TechSolutions Federal Inc.",
        "years_in_business": 15,
        "employee_count": 250,
        "annual_revenue": 45000000.00,
        "headquarters_location": "Reston, VA",
        "naics_codes": [
            {
                "code": "541512",
                "description": "Computer Systems Design Services",
                "is_primary": True,
                "small_business_size_standard": "$30 million",
            },
            {
                "code": "541519",
                "description": "Other Computer Related Services",
                "is_primary": False,
            },
        ],
        "certifications": [
            {
                "cert_type": "8(a)",
                "issuing_authority": "SBA",
                "issue_date": "2020-01-15",
                "expiration_date": "2029-01-14",
            },
            {
                "cert_type": "ISO 9001",
                "issuing_authority": "ISO",
                "issue_date": "2021-06-01",
            },
            {
                "cert_type": "CMMI DEV",
                "issuing_authority": "CMMI Institute",
                "issue_date": "2022-03-01",
                "level": "Level 3",
            },
        ],
        "core_capabilities": [
            {
                "name": "Cloud Migration & Modernization",
                "description": "End-to-end cloud migration services for legacy systems",
                "differentiators": [
                    "Proprietary migration assessment framework",
                    "Zero-downtime migration methodology",
                ],
                "maturity_level": "Market Leader",
            },
            {
                "name": "Cybersecurity Services",
                "description": "Comprehensive cybersecurity solutions including SOC operations",
                "differentiators": [
                    "24/7 SOC with cleared analysts",
                    "FedRAMP expertise",
                ],
                "maturity_level": "Established",
            },
        ],
        "past_performance": [
            {
                "contract_number": "GS-35F-0001X",
                "contract_name": "DHS Cloud Modernization",
                "agency": "Department of Homeland Security",
                "contract_value": 12500000.00,
                "overall_rating": "Exceptional",
                "key_accomplishments": [
                    "Migrated 150+ applications to AWS GovCloud",
                    "Reduced infrastructure costs by 40%",
                ],
            },
            {
                "contract_number": "HHSN-2020-0001",
                "contract_name": "HHS Security Operations Center",
                "agency": "Department of Health and Human Services",
                "contract_value": 8000000.00,
                "overall_rating": "Very Good",
                "key_accomplishments": [
                    "Established 24/7 SOC operations",
                    "Achieved zero security incidents in 18 months",
                ],
            },
        ],
        "target_agencies": [
            "Department of Homeland Security",
            "Department of Health and Human Services",
            "Department of Veterans Affairs",
        ],
        "security_clearances": ["Secret", "Top Secret"],
    }


@pytest.fixture
def sample_opportunity() -> Dict[str, Any]:
    """Create a sample opportunity for testing."""
    return {
        "id": "opp-001",
        "title": "Enterprise Cloud Migration Services",
        "solicitation_number": "HSHQDC-24-R-00001",
        "agency": {
            "name": "Department of Homeland Security",
            "abbreviation": "DHS",
            "sub_agency": "Cybersecurity and Infrastructure Security Agency",
        },
        "status": "Final RFP",
        "set_aside": "8(a)",
        "naics_code": "541512",
        "estimated_value": 50000000.00,
        "contract_type": "Firm Fixed Price",
        "evaluation_type": "Best Value Tradeoff",
        "scope_summary": (
            "The contractor shall provide cloud migration and modernization services "
            "for legacy systems across CISA divisions."
        ),
        "key_requirements": [
            "AWS GovCloud experience",
            "FedRAMP authorization support",
            "24/7 operational support capability",
            "Cleared personnel (Secret minimum)",
        ],
        "evaluation_factors": [
            {"name": "Technical Approach", "weight": 40},
            {"name": "Past Performance", "weight": 30},
            {"name": "Price", "weight": 30},
        ],
        "competitor_intel": {
            "competitive_density": "Medium",
            "incumbent_advantage_level": "Moderate",
            "competitors": [
                {
                    "name": "CloudFirst Federal",
                    "is_incumbent": True,
                    "estimated_strength": "Strong",
                    "known_strengths": ["Incumbent relationship", "Large cleared workforce"],
                },
                {
                    "name": "SecureCloud Solutions",
                    "is_incumbent": False,
                    "estimated_strength": "Moderate",
                    "known_strengths": ["AWS Partner status", "Competitive pricing"],
                },
            ],
        },
    }


@pytest.fixture
def strategy_architect() -> StrategyArchitectAgent:
    """Create a Strategy Architect agent for testing."""
    return StrategyArchitectAgent()


@pytest.fixture
def sample_context(
    sample_company_profile: Dict[str, Any],
    sample_opportunity: Dict[str, Any],
) -> SwarmContext:
    """Create a sample SwarmContext for testing."""
    return SwarmContext(
        document_type="Capability Statement",
        company_profile=sample_company_profile,
        opportunity=sample_opportunity,
        round_type="BlueBuild",
    )


# ============================================================================
# Template Tests
# ============================================================================

class TestDocumentTemplates:
    """Test document template definitions."""

    def test_all_templates_registered(self):
        """Verify all 7 document type templates are registered."""
        document_types = [
            "Capability Statement",
            "Competitive Analysis",
            "SWOT Analysis",
            "BD Pipeline",
            "Proposal Strategy",
            "Go-to-Market Strategy",
            "Teaming Strategy",
        ]

        for doc_type in document_types:
            template = get_template_for_document_type(doc_type)
            assert template is not None, f"Template not found for: {doc_type}"
            assert template.document_type == doc_type

    def test_capability_statement_sections(self):
        """Test Capability Statement template sections."""
        template = CapabilityStatementTemplate()

        expected_sections = [
            "Company Overview",
            "Core Competencies",
            "Past Performance",
            "Differentiators",
            "Certifications & Clearances",
            "Contact Information",
        ]

        assert template.section_names == expected_sections
        assert not template.requires_opportunity

    def test_proposal_strategy_requires_opportunity(self):
        """Test that Proposal Strategy requires opportunity context."""
        template = ProposalStrategyTemplate()
        assert template.requires_opportunity

    def test_section_guidance_provided(self):
        """Test that all sections have guidance."""
        template = CapabilityStatementTemplate()

        for section in template.sections:
            assert section.guidance, f"No guidance for section: {section.name}"
            assert len(section.guidance) > 50

    def test_section_validation(self):
        """Test section content validation."""
        template = CapabilityStatementTemplate()

        # Too short
        short_content = "Hello world"
        errors = template.validate_section_content("Company Overview", short_content)
        assert len(errors) > 0
        assert "too short" in errors[0].lower()

        # Valid length
        valid_content = " ".join(["word"] * 100)
        errors = template.validate_section_content("Company Overview", valid_content)
        assert len(errors) == 0

    def test_drafting_order_respects_dependencies(self):
        """Test that drafting order respects section dependencies."""
        template = CapabilityStatementTemplate()
        order = template.get_drafting_order()

        # Company Overview should come before Core Competencies
        overview_idx = order.index("Company Overview")
        competencies_idx = order.index("Core Competencies")
        assert overview_idx < competencies_idx


# ============================================================================
# Prompt Tests
# ============================================================================

class TestPrompts:
    """Test prompt generation functions."""

    def test_system_prompt_defined(self):
        """Test that system prompt is defined and substantive."""
        assert STRATEGY_ARCHITECT_SYSTEM_PROMPT
        assert len(STRATEGY_ARCHITECT_SYSTEM_PROMPT) > 500
        assert "Strategy Architect" in STRATEGY_ARCHITECT_SYSTEM_PROMPT

    def test_draft_prompt_includes_company_info(
        self, sample_company_profile: Dict[str, Any]
    ):
        """Test that draft prompt includes company information."""
        prompt = get_draft_prompt(
            document_type="Capability Statement",
            sections=["Company Overview", "Core Competencies"],
            company_profile=sample_company_profile,
        )

        assert "TechSolutions Federal Inc." in prompt
        assert "Cloud Migration" in prompt
        assert "541512" in prompt
        assert "8(a)" in prompt

    def test_draft_prompt_includes_opportunity(
        self,
        sample_company_profile: Dict[str, Any],
        sample_opportunity: Dict[str, Any],
    ):
        """Test that draft prompt includes opportunity information."""
        prompt = get_draft_prompt(
            document_type="Proposal Strategy",
            sections=["Executive Summary", "Win Themes"],
            company_profile=sample_company_profile,
            opportunity=sample_opportunity,
        )

        assert "Enterprise Cloud Migration Services" in prompt
        assert "DHS" in prompt
        assert "Best Value" in prompt
        assert "CloudFirst Federal" in prompt  # Competitor

    def test_revision_prompt_includes_critiques(
        self, sample_company_profile: Dict[str, Any]
    ):
        """Test that revision prompt includes critique details."""
        critiques = [
            {
                "title": "Missing proof points",
                "challenge_type": "evidence",
                "severity": "major",
                "argument": "The claim lacks supporting evidence",
                "suggested_remedy": "Add specific metrics from past performance",
            }
        ]

        prompt = get_revision_prompt(
            section_name="Core Competencies",
            original_content="We have excellent capabilities.",
            critiques=critiques,
            company_profile=sample_company_profile,
        )

        assert "Missing proof points" in prompt
        assert "evidence" in prompt.lower()
        assert "major" in prompt.lower()
        assert "Add specific metrics" in prompt

    def test_section_prompt_includes_other_sections(
        self, sample_company_profile: Dict[str, Any]
    ):
        """Test that section prompt includes context from other sections."""
        other_sections = {
            "Company Overview": "TechSolutions is a leading IT services provider..."
        }

        prompt = get_section_prompt(
            section_name="Core Competencies",
            document_type="Capability Statement",
            company_profile=sample_company_profile,
            other_sections=other_sections,
        )

        assert "TechSolutions is a leading" in prompt
        assert "Company Overview" in prompt


# ============================================================================
# Strategy Architect Agent Tests
# ============================================================================

class TestStrategyArchitectAgent:
    """Test Strategy Architect agent functionality."""

    def test_agent_properties(self, strategy_architect: StrategyArchitectAgent):
        """Test agent role and category properties."""
        assert strategy_architect.role == AgentRole.STRATEGY_ARCHITECT
        assert strategy_architect.category == AgentCategory.BLUE

    def test_agent_default_config(self, strategy_architect: StrategyArchitectAgent):
        """Test agent uses correct default configuration."""
        config = strategy_architect.config

        assert config.role == AgentRole.STRATEGY_ARCHITECT
        assert config.priority == 100  # Highest priority blue team agent
        assert config.llm_config.temperature == 0.7
        assert config.llm_config.max_tokens == 8192

    def test_context_validation_requires_company(
        self, strategy_architect: StrategyArchitectAgent
    ):
        """Test that context validation requires company profile."""
        context = SwarmContext(
            document_type="Capability Statement",
            company_profile=None,  # Missing
        )

        errors = strategy_architect.validate_context(context)
        assert len(errors) > 0
        assert any("company profile" in e.lower() for e in errors)

    def test_context_validation_requires_document_type(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_company_profile: Dict[str, Any],
    ):
        """Test that context validation requires document type."""
        context = SwarmContext(
            document_type=None,  # Missing
            company_profile=sample_company_profile,
        )

        errors = strategy_architect.validate_context(context)
        assert len(errors) > 0
        assert any("document type" in e.lower() for e in errors)

    def test_context_validation_opportunity_required(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_company_profile: Dict[str, Any],
    ):
        """Test that certain document types require opportunity."""
        context = SwarmContext(
            document_type="Proposal Strategy",
            company_profile=sample_company_profile,
            opportunity=None,  # Missing but required
        )

        errors = strategy_architect.validate_context(context)
        assert len(errors) > 0
        assert any("opportunity" in e.lower() for e in errors)

    @pytest.mark.asyncio
    async def test_process_generates_output(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_context: SwarmContext,
    ):
        """Test that process generates an AgentOutput."""
        output = await strategy_architect.process(sample_context)

        assert isinstance(output, AgentOutput)
        assert output.success
        assert output.agent_role == AgentRole.STRATEGY_ARCHITECT
        assert output.sections  # Should have section content
        assert output.processing_time_ms >= 0  # May be 0 in mock mode

    @pytest.mark.asyncio
    async def test_process_handles_all_document_types(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_company_profile: Dict[str, Any],
        sample_opportunity: Dict[str, Any],
    ):
        """Test that agent can process all 7 document types."""
        document_types = [
            ("Capability Statement", False),
            ("Competitive Analysis", True),
            ("SWOT Analysis", False),
            ("BD Pipeline", False),
            ("Proposal Strategy", True),
            ("Go-to-Market Strategy", False),
            ("Teaming Strategy", False),
        ]

        for doc_type, requires_opp in document_types:
            context = SwarmContext(
                document_type=doc_type,
                company_profile=sample_company_profile,
                opportunity=sample_opportunity if requires_opp else None,
                round_type="BlueBuild",
            )

            output = await strategy_architect.process(context)
            assert output.success, f"Failed for document type: {doc_type}"
            assert output.sections, f"No sections for document type: {doc_type}"

    @pytest.mark.asyncio
    async def test_revision_mode(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_company_profile: Dict[str, Any],
    ):
        """Test revision mode with pending critiques."""
        context = SwarmContext(
            document_type="Capability Statement",
            company_profile=sample_company_profile,
            round_type="BlueDefense",
            section_drafts={
                "Core Competencies": "We have excellent cloud capabilities.",
            },
            pending_critiques=[
                {
                    "id": "crit-001",
                    "target_section": "Core Competencies",
                    "challenge_type": "evidence",
                    "severity": "major",
                    "title": "Missing specifics",
                    "argument": "The claim lacks specific details",
                    "suggested_remedy": "Add AWS certifications and metrics",
                }
            ],
        )

        output = await strategy_architect.process(context)
        assert output.success
        assert "Core Competencies" in output.sections

    @pytest.mark.asyncio
    async def test_draft_specific_section(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_context: SwarmContext,
    ):
        """Test drafting a specific section."""
        sample_context.target_sections = ["Company Overview"]

        output = await strategy_architect.process(sample_context)
        assert output.success
        assert "Company Overview" in output.sections

    def test_parse_sections_from_response(
        self, strategy_architect: StrategyArchitectAgent
    ):
        """Test parsing sections from LLM response."""
        response = """## Company Overview

TechSolutions Federal is a leading IT services provider.

## Core Competencies

- Cloud Migration
- Cybersecurity
- DevSecOps
"""
        sections = strategy_architect._parse_sections_from_response(
            response,
            ["Company Overview", "Core Competencies"],
        )

        assert "Company Overview" in sections
        assert "Core Competencies" in sections
        assert "TechSolutions Federal" in sections["Company Overview"]
        assert "Cloud Migration" in sections["Core Competencies"]

    def test_group_critiques_by_section(
        self, strategy_architect: StrategyArchitectAgent
    ):
        """Test grouping critiques by target section."""
        critiques = [
            {"id": "1", "target_section": "Section A"},
            {"id": "2", "target_section": "Section B"},
            {"id": "3", "target_section": "Section A"},
        ]

        grouped = strategy_architect._group_critiques_by_section(critiques)

        assert "Section A" in grouped
        assert "Section B" in grouped
        assert len(grouped["Section A"]) == 2
        assert len(grouped["Section B"]) == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestStrategyArchitectIntegration:
    """Integration tests for Strategy Architect with other components."""

    @pytest.mark.asyncio
    async def test_output_conforms_to_schema(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_context: SwarmContext,
    ):
        """Test that output conforms to expected schema."""
        output = await strategy_architect.process(sample_context)

        # Check output structure
        output_dict = output.to_dict()

        assert "id" in output_dict
        assert "agent_role" in output_dict
        assert "content" in output_dict
        assert "sections" in output_dict
        assert "success" in output_dict
        assert "created_at" in output_dict

    @pytest.mark.asyncio
    async def test_blue_team_inputs_incorporated(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_company_profile: Dict[str, Any],
    ):
        """Test that blue team agent inputs are incorporated."""
        context = SwarmContext(
            document_type="Capability Statement",
            company_profile=sample_company_profile,
            round_type="BlueBuild",
            custom_data={
                "blue_team_inputs": {
                    "Market Analyst": {
                        "market_trend": "Cloud spending increasing 20% YoY",
                        "top_opportunities": ["DHS Cloud", "VA Modernization"],
                    },
                    "Compliance Navigator": {
                        "eligibility_confirmed": True,
                        "set_aside_status": "8(a) eligible through 2029",
                    },
                }
            },
        )

        output = await strategy_architect.process(context)
        assert output.success

    @pytest.mark.asyncio
    async def test_metadata_tracking(
        self,
        strategy_architect: StrategyArchitectAgent,
        sample_context: SwarmContext,
    ):
        """Test that processing metadata is tracked."""
        output = await strategy_architect.process(sample_context)

        assert output.metadata.get("round_type") == "BlueBuild"
        assert output.metadata.get("document_type") == "Capability Statement"
        assert output.metadata.get("section_count") > 0
        assert output.processing_time_ms >= 0  # May be 0 in mock mode
        assert "input_tokens" in output.token_usage
        assert "output_tokens" in output.token_usage


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
