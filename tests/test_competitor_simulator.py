"""
Tests for Competitor Simulator Agent

Tests the Competitor Simulator agent's ability to:
- Simulate 2-3 competitor personas per engagement
- Identify specific and actionable vulnerabilities
- Ground predictions in available competitor data
- Produce critiques conforming to the Critique schema
"""

import pytest
from datetime import date
from typing import Dict, Any, List

from agents.red.competitor_simulator import (
    CompetitorSimulatorAgent,
    CompetitorSimulatorResult,
    CompetitorAnalysis,
    CompetitorPerspective,
    CompetitiveVulnerability,
    CompetitorChallengeType,
)
from agents.base import SwarmContext, AgentOutput
from agents.config import AgentConfig, get_default_config
from agents.types import AgentRole, AgentCategory

from models.critique import (
    Critique,
    ChallengeType,
    Severity,
    CritiqueStatus,
    CritiqueSummary,
)

from agents.red.prompts.competitor_simulator_prompts import (
    COMPETITOR_SIMULATOR_SYSTEM_PROMPT,
    get_competitor_simulation_prompt,
    get_single_competitor_prompt,
    get_competitive_response_prompt,
    get_incumbent_defense_prompt,
    get_vulnerability_synthesis_prompt,
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
        "naics_codes": [
            {
                "code": "541512",
                "description": "Computer Systems Design Services",
                "is_primary": True,
            },
        ],
        "certifications": [
            {
                "cert_type": "8(a)",
                "issuing_authority": "SBA",
                "issue_date": "2020-01-15",
            },
            {
                "cert_type": "ISO 9001",
                "issuing_authority": "ISO",
                "issue_date": "2021-06-01",
            },
        ],
        "core_capabilities": [
            {
                "name": "Cloud Migration & Modernization",
                "description": "End-to-end cloud migration services",
                "differentiators": [
                    "Proprietary migration framework",
                ],
            },
        ],
        "past_performance": [
            {
                "contract_number": "GS-35F-0001X",
                "contract_name": "DHS Cloud Modernization",
                "agency": "Department of Homeland Security",
                "contract_value": 12500000.00,
                "overall_rating": "Exceptional",
            },
        ],
    }


@pytest.fixture
def sample_competitors() -> List[Dict[str, Any]]:
    """Create sample competitors for testing."""
    return [
        {
            "name": "TechCorp Federal",
            "is_incumbent": True,
            "is_confirmed": True,
            "estimated_strength": "Strong",
            "known_strengths": [
                "5-year incumbent on current contract",
                "Deep agency relationships",
                "Zero transition risk",
            ],
            "known_weaknesses": [
                "Slow to adopt new technologies",
                "Higher pricing due to legacy overhead",
            ],
            "relevant_past_performance": [
                "DHS EAGLE II - $50M - Exceptional",
                "CBP Infrastructure - $25M - Very Good",
            ],
            "certifications": ["ISO 27001", "CMMI Level 3"],
            "likely_strategy": "Defend position emphasizing transition risk",
            "teaming_partners": ["SubContractor Inc."],
        },
        {
            "name": "CloudFirst Solutions",
            "is_incumbent": False,
            "is_confirmed": True,
            "estimated_strength": "Moderate",
            "known_strengths": [
                "AWS Premier Partner",
                "Proprietary cloud migration accelerator",
                "Aggressive pricing strategy",
            ],
            "known_weaknesses": [
                "Limited federal experience",
                "No existing agency relationships",
            ],
            "relevant_past_performance": [
                "DoD Cloud Migration - $15M - Satisfactory",
            ],
            "certifications": ["AWS GovCloud Certified", "FedRAMP"],
            "likely_strategy": "Lead with innovation and competitive pricing",
            "teaming_partners": [],
        },
        {
            "name": "GovCloud Partners",
            "is_incumbent": False,
            "is_confirmed": False,
            "estimated_strength": "Unknown",
            "known_strengths": [
                "Strong security focus",
                "Multiple agency authorizations",
            ],
            "known_weaknesses": [],
            "relevant_past_performance": [],
            "certifications": ["FedRAMP High"],
            "likely_strategy": "Unknown",
            "teaming_partners": [],
        },
    ]


@pytest.fixture
def sample_opportunity(sample_competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a sample opportunity with competitor intel."""
    return {
        "id": "opp-001",
        "title": "Enterprise Cloud Migration Services",
        "agency": {
            "name": "Department of Homeland Security",
            "abbreviation": "DHS",
        },
        "status": "Final RFP",
        "set_aside": "8(a)",
        "naics_code": "541512",
        "estimated_value": 50000000.00,
        "contract_type": "Firm Fixed Price",
        "evaluation_type": "Best Value Tradeoff",
        "is_recompete": True,
        "key_requirements": [
            "AWS GovCloud experience",
            "FedRAMP authorization support",
            "24/7 operational support capability",
        ],
        "evaluation_factors": [
            {"name": "Technical Approach", "weight": 40},
            {"name": "Past Performance", "weight": 30},
            {"name": "Price", "weight": 30},
        ],
        "competitor_intel": {
            "competitors": sample_competitors,
            "competitive_density": "Medium",
            "incumbent_advantage_level": "Strong",
            "market_assessment": "Competitive recompete with strong incumbent",
        },
    }


@pytest.fixture
def sample_document_content() -> Dict[str, str]:
    """Create sample document content for competitive analysis."""
    return {
        "Win Themes": """## Win Theme 1: Cloud Excellence

**Theme Statement**: Our team delivers industry-leading cloud migration
capabilities with proven results across federal agencies.

**Supporting Evidence**:
- Successfully migrated 20+ federal systems to cloud
- Average 40% cost reduction achieved

**Competitive Advantage**: Our proprietary CloudBridge platform
reduces migration time by 50%.
""",
        "Competitive Analysis": """## Competitive Positioning

### TechCorp Federal (Incumbent)
- Strengths: Established relationships, proven track record
- Weaknesses: Legacy technology approach, higher costs
- Our Advantage: Modern technology stack, faster delivery

### CloudFirst Solutions
- Strengths: Strong cloud expertise, aggressive pricing
- Weaknesses: Limited federal experience
- Our Advantage: More relevant past performance

We are well-positioned to win this opportunity.
""",
        "Transition Approach": """## Transition Plan

We will execute a seamless transition within 90 days using our
proven methodology. Key activities include:
- Knowledge transfer sessions
- System access provisioning
- Stakeholder engagement

Transition risk is minimal due to our experienced team.
""",
    }


@pytest.fixture
def competitor_simulator() -> CompetitorSimulatorAgent:
    """Create a Competitor Simulator agent for testing."""
    return CompetitorSimulatorAgent()


@pytest.fixture
def sample_context(
    sample_company_profile: Dict[str, Any],
    sample_opportunity: Dict[str, Any],
    sample_document_content: Dict[str, str],
) -> SwarmContext:
    """Create a sample SwarmContext for testing."""
    return SwarmContext(
        document_type="Proposal Strategy",
        document_id="doc-001",
        company_profile=sample_company_profile,
        opportunity=sample_opportunity,
        section_drafts=sample_document_content,
        round_type="RedAttack",
        round_number=1,
    )


# ============================================================================
# Prompt Tests
# ============================================================================

class TestCompetitorSimulatorPrompts:
    """Test prompt generation functions."""

    def test_system_prompt_defined(self):
        """Test that system prompt is defined and substantive."""
        assert COMPETITOR_SIMULATOR_SYSTEM_PROMPT
        assert len(COMPETITOR_SIMULATOR_SYSTEM_PROMPT) > 500
        assert "Competitor Simulator" in COMPETITOR_SIMULATOR_SYSTEM_PROMPT
        assert "competitor" in COMPETITOR_SIMULATOR_SYSTEM_PROMPT.lower()
        assert "vulnerabilit" in COMPETITOR_SIMULATOR_SYSTEM_PROMPT.lower()

    def test_system_prompt_covers_vulnerability_types(self):
        """Test that system prompt covers key vulnerability categories."""
        prompt = COMPETITOR_SIMULATOR_SYSTEM_PROMPT.lower()

        assert "incumbent" in prompt
        assert "technical" in prompt
        assert "past performance" in prompt or "experience" in prompt
        assert "pricing" in prompt

    def test_system_prompt_addresses_severity(self):
        """Test that system prompt addresses severity calibration."""
        prompt = COMPETITOR_SIMULATOR_SYSTEM_PROMPT

        assert "Critical" in prompt
        assert "Major" in prompt
        assert "Minor" in prompt

    def test_competitor_simulation_prompt_includes_competitors(
        self, sample_document_content: Dict[str, str], sample_competitors: List[Dict[str, Any]]
    ):
        """Test that simulation prompt includes competitor details."""
        prompt = get_competitor_simulation_prompt(
            document_type="Proposal Strategy",
            document_content=sample_document_content,
            competitors=sample_competitors,
        )

        assert "TechCorp Federal" in prompt
        assert "CloudFirst Solutions" in prompt
        assert "INCUMBENT" in prompt
        assert "AWS Premier Partner" in prompt

    def test_competitor_simulation_prompt_includes_document(
        self, sample_document_content: Dict[str, str], sample_competitors: List[Dict[str, Any]]
    ):
        """Test that simulation prompt includes document content."""
        prompt = get_competitor_simulation_prompt(
            document_type="Proposal Strategy",
            document_content=sample_document_content,
            competitors=sample_competitors,
        )

        assert "Win Theme" in prompt
        assert "CloudBridge platform" in prompt
        assert "Transition Plan" in prompt

    def test_single_competitor_prompt_adopts_persona(
        self, sample_document_content: Dict[str, str], sample_competitors: List[Dict[str, Any]]
    ):
        """Test that single competitor prompt adopts persona correctly."""
        incumbent = sample_competitors[0]  # TechCorp Federal

        prompt = get_single_competitor_prompt(
            competitor=incumbent,
            document_content=sample_document_content,
            document_type="Proposal Strategy",
        )

        assert "You ARE" in prompt
        assert "TechCorp Federal" in prompt
        assert "INCUMBENT" in prompt
        assert "transition risk" in prompt.lower()

    def test_single_competitor_prompt_challenger(
        self, sample_document_content: Dict[str, str], sample_competitors: List[Dict[str, Any]]
    ):
        """Test that single competitor prompt handles challengers."""
        challenger = sample_competitors[1]  # CloudFirst Solutions

        prompt = get_single_competitor_prompt(
            competitor=challenger,
            document_content=sample_document_content,
            document_type="Proposal Strategy",
        )

        assert "You ARE" in prompt
        assert "CloudFirst Solutions" in prompt
        assert "CHALLENGER" in prompt

    def test_competitive_response_prompt_includes_claim(
        self, sample_competitors: List[Dict[str, Any]]
    ):
        """Test that competitive response prompt includes the claim."""
        prompt = get_competitive_response_prompt(
            competitor=sample_competitors[0],
            client_claim="Our CloudBridge platform reduces migration time by 50%",
            claim_section="Win Themes",
        )

        assert "CloudBridge platform" in prompt
        assert "50%" in prompt
        assert "Win Themes" in prompt
        assert "Counter" in prompt

    def test_incumbent_defense_prompt_structure(
        self, sample_competitors: List[Dict[str, Any]], sample_document_content: Dict[str, str]
    ):
        """Test incumbent defense prompt structure."""
        incumbent = sample_competitors[0]

        prompt = get_incumbent_defense_prompt(
            incumbent=incumbent,
            challenger_strategy=sample_document_content,
        )

        assert "incumbent" in prompt.lower()
        assert "transition risk" in prompt.lower()
        assert "Zero transition risk" in prompt
        assert "TechCorp Federal" in prompt

    def test_vulnerability_synthesis_prompt_structure(self):
        """Test vulnerability synthesis prompt structure."""
        analyses = [
            {
                "competitor_name": "TechCorp Federal",
                "vulnerabilities": [
                    {
                        "title": "Transition Risk",
                        "severity": "critical",
                        "target_section": "Transition Approach",
                        "competitor_attack": "90 days is too aggressive",
                    }
                ],
            },
            {
                "competitor_name": "CloudFirst Solutions",
                "vulnerabilities": [
                    {
                        "title": "Pricing Pressure",
                        "severity": "major",
                        "target_section": "Pricing Strategy",
                        "competitor_attack": "They can undercut by 20%",
                    }
                ],
            },
        ]

        prompt = get_vulnerability_synthesis_prompt(
            competitor_analyses=analyses,
            document_type="Proposal Strategy",
        )

        assert "TechCorp Federal" in prompt
        assert "CloudFirst Solutions" in prompt
        assert "Transition Risk" in prompt
        assert "Cross-Competitor Patterns" in prompt


# ============================================================================
# Agent Tests
# ============================================================================

class TestCompetitorSimulatorAgent:
    """Test Competitor Simulator agent functionality."""

    def test_agent_properties(self, competitor_simulator: CompetitorSimulatorAgent):
        """Test agent role and category properties."""
        assert competitor_simulator.role == AgentRole.COMPETITOR_SIMULATOR
        assert competitor_simulator.category == AgentCategory.RED

    def test_agent_default_config(self, competitor_simulator: CompetitorSimulatorAgent):
        """Test agent uses correct default configuration."""
        config = competitor_simulator.config

        assert config.role == AgentRole.COMPETITOR_SIMULATOR
        assert config.priority == 80  # Second priority red team agent
        assert config.llm_config.temperature == 0.8  # Higher for creative simulation
        assert config.llm_config.max_tokens == 4096

    def test_context_validation_requires_content(
        self, competitor_simulator: CompetitorSimulatorAgent
    ):
        """Test that context validation requires document content."""
        context = SwarmContext(
            document_type="Proposal Strategy",
            section_drafts={},  # Empty - no content
            current_draft=None,
        )

        errors = competitor_simulator.validate_context(context)
        assert len(errors) > 0
        assert any("content" in e.lower() for e in errors)

    def test_context_validation_requires_competitors(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_document_content: Dict[str, str],
    ):
        """Test that context validation requires competitor intelligence."""
        context = SwarmContext(
            document_type="Proposal Strategy",
            section_drafts=sample_document_content,
            opportunity={},  # No competitor intel
        )

        errors = competitor_simulator.validate_context(context)
        assert len(errors) > 0
        assert any("competitor" in e.lower() for e in errors)

    def test_context_validation_passes_with_all_requirements(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that context validation passes with all requirements."""
        errors = competitor_simulator.validate_context(sample_context)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_process_generates_output(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that process generates an AgentOutput."""
        output = await competitor_simulator.process(sample_context)

        assert isinstance(output, AgentOutput)
        assert output.success
        assert output.agent_role == AgentRole.COMPETITOR_SIMULATOR
        assert output.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_process_generates_critiques(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that process generates properly structured critiques."""
        output = await competitor_simulator.process(sample_context)

        assert len(output.critiques) > 0

        for critique in output.critiques:
            # Check required fields
            assert critique.get("agent") == AgentRole.COMPETITOR_SIMULATOR.value
            assert critique.get("challenge_type")
            assert critique.get("severity")
            assert critique.get("argument")
            assert critique.get("suggested_remedy")

    @pytest.mark.asyncio
    async def test_process_analyzes_multiple_competitors(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that process analyzes multiple competitors."""
        output = await competitor_simulator.process(sample_context)

        # Check metadata for competitor count
        assert output.metadata.get("competitors_analyzed", 0) >= 2

    @pytest.mark.asyncio
    async def test_single_competitor_mode(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
        sample_competitors: List[Dict[str, Any]],
    ):
        """Test single competitor deep-dive mode."""
        sample_context.custom_data["analysis_type"] = "single_competitor"
        sample_context.custom_data["target_competitor"] = sample_competitors[0]

        output = await competitor_simulator.process(sample_context)

        assert output.success
        assert output.metadata.get("competitors_analyzed") == 1

    @pytest.mark.asyncio
    async def test_incumbent_defense_mode(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test incumbent defense analysis mode."""
        sample_context.custom_data["analysis_type"] = "incumbent_defense"

        output = await competitor_simulator.process(sample_context)

        assert output.success
        # Should find the incumbent
        assert output.metadata.get("competitors_analyzed") == 1

    @pytest.mark.asyncio
    async def test_claim_counter_mode(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
        sample_competitors: List[Dict[str, Any]],
    ):
        """Test claim counter-positioning mode."""
        sample_context.custom_data["analysis_type"] = "claim_counter"
        sample_context.custom_data["claim"] = "Our CloudBridge platform reduces migration time by 50%"
        sample_context.custom_data["claim_section"] = "Win Themes"
        sample_context.custom_data["target_competitor"] = sample_competitors[0]

        output = await competitor_simulator.process(sample_context)

        assert output.success

    @pytest.mark.asyncio
    async def test_critique_section_interface(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test the critique_section interface method."""
        critiques = await competitor_simulator.critique_section(
            context=sample_context,
            section_name="Win Themes",
            section_content=sample_context.section_drafts["Win Themes"],
        )

        assert isinstance(critiques, list)
        assert len(critiques) > 0

        for critique in critiques:
            assert isinstance(critique, dict)
            assert "argument" in critique
            assert "suggested_remedy" in critique

    @pytest.mark.asyncio
    async def test_evaluate_response_accept_with_evidence(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test response evaluation with Accept disposition and evidence."""
        critique = {
            "id": "crit-001",
            "title": "Transition Risk Underestimated",
            "challenge_type": "Competitive",
        }
        response = {
            "critique_id": "crit-001",
            "disposition": "Accept",
            "action": "Added detailed transition plan with milestones",
            "evidence": "Included 30-60-90 day plan with risk mitigation",
        }

        is_acceptable = await competitor_simulator.evaluate_response(
            context=sample_context,
            critique=critique,
            response=response,
        )

        assert is_acceptable is True

    @pytest.mark.asyncio
    async def test_evaluate_response_rebut_needs_evidence(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test response evaluation with Rebut needing strong evidence."""
        critique = {
            "id": "crit-002",
            "title": "Weak Past Performance",
            "challenge_type": "Competitive",
        }
        response = {
            "critique_id": "crit-002",
            "disposition": "Rebut",
            "action": "Our past performance is actually strong",
            "evidence": "Short evidence",  # Too short
        }

        is_acceptable = await competitor_simulator.evaluate_response(
            context=sample_context,
            critique=critique,
            response=response,
        )

        # Short evidence should not be acceptable for competitive rebuttal
        assert is_acceptable is False


# ============================================================================
# Vulnerability Parsing Tests
# ============================================================================

class TestVulnerabilityParsing:
    """Test vulnerability parsing functionality."""

    def test_competitive_vulnerability_to_dict(self):
        """Test CompetitiveVulnerability serialization."""
        vuln = CompetitiveVulnerability(
            competitor_name="TechCorp Federal",
            title="Transition Risk Underestimation",
            target_section="Transition Approach",
            target_content="90-day transition",
            challenge_type=CompetitorChallengeType.INCUMBENT,
            severity="critical",
            competitor_attack="We have zero transition risk; you're introducing disruption",
            competitive_advantage="5 years of institutional knowledge",
            evidence="Incumbent recompete win rate is 60-70%",
            defensive_recommendation="Add detailed transition plan with risk mitigation",
        )

        vuln_dict = vuln.to_dict()

        assert vuln_dict["competitor_name"] == "TechCorp Federal"
        assert vuln_dict["title"] == "Transition Risk Underestimation"
        assert vuln_dict["challenge_type"] == CompetitorChallengeType.INCUMBENT
        assert vuln_dict["severity"] == "critical"
        assert "transition risk" in vuln_dict["competitor_attack"].lower()

    def test_competitive_vulnerability_to_critique(self):
        """Test conversion from CompetitiveVulnerability to Critique."""
        vuln = CompetitiveVulnerability(
            competitor_name="TechCorp Federal",
            title="Transition Risk",
            target_section="Transition Approach",
            challenge_type=CompetitorChallengeType.INCUMBENT,
            severity="critical",
            competitor_attack="We have zero transition risk",
            competitive_advantage="Existing knowledge and relationships",
            evidence="Incumbent win rates",
            defensive_recommendation="Add detailed transition plan",
        )

        critique = vuln.to_critique(
            agent="Competitor Simulator",
            round_number=2,
            document_id="doc-123",
        )

        assert isinstance(critique, Critique)
        assert "[TechCorp Federal]" in critique.title
        assert critique.round_number == 2
        assert critique.target_document_id == "doc-123"
        assert critique.severity == Severity.CRITICAL
        assert critique.challenge_type == ChallengeType.COMPETITIVE

    def test_competitor_perspective_to_dict(self):
        """Test CompetitorPerspective serialization."""
        perspective = CompetitorPerspective(
            competitor_name="CloudFirst Solutions",
            is_incumbent=False,
            estimated_strength="Moderate",
            self_assessment="We are the innovation leader",
            key_strengths=["AWS expertise", "Aggressive pricing"],
            client_threat_level="Medium",
            client_perceived_weaknesses=["Generic approach", "Higher pricing"],
            predicted_strategy="Lead with innovation, undercut on price",
            key_differentiators=["Proprietary accelerator", "AWS Premier status"],
            pricing_approach="Price 15-20% below market",
        )

        persp_dict = perspective.to_dict()

        assert persp_dict["competitor_name"] == "CloudFirst Solutions"
        assert persp_dict["is_incumbent"] is False
        assert "innovation leader" in persp_dict["self_assessment"]
        assert len(persp_dict["key_strengths"]) == 2

    def test_competitor_analysis_to_dict(self):
        """Test CompetitorAnalysis serialization."""
        perspective = CompetitorPerspective(competitor_name="TestCorp")
        vuln = CompetitiveVulnerability(
            competitor_name="TestCorp",
            title="Test Vulnerability",
            competitor_attack="Test attack",
            defensive_recommendation="Test defense",
        )

        analysis = CompetitorAnalysis(
            competitor_name="TestCorp",
            is_incumbent=True,
            perspective=perspective,
            vulnerabilities=[vuln],
            win_strategy="Defend position aggressively",
            defensive_recommendations=["Add more evidence", "Strengthen claims"],
        )

        analysis_dict = analysis.to_dict()

        assert analysis_dict["competitor_name"] == "TestCorp"
        assert analysis_dict["is_incumbent"] is True
        assert analysis_dict["perspective"] is not None
        assert len(analysis_dict["vulnerabilities"]) == 1
        assert len(analysis_dict["defensive_recommendations"]) == 2


# ============================================================================
# Result Tests
# ============================================================================

class TestCompetitorSimulatorResult:
    """Test the CompetitorSimulatorResult dataclass."""

    def test_result_initialization(self):
        """Test result initialization with defaults."""
        result = CompetitorSimulatorResult()

        assert result.success
        assert len(result.competitor_analyses) == 0
        assert len(result.critiques) == 0
        assert len(result.cross_competitor_patterns) == 0
        assert result.critique_summary is None
        assert result.overall_competitive_assessment == ""

    def test_result_to_dict(self):
        """Test result serialization to dict."""
        result = CompetitorSimulatorResult(
            overall_competitive_assessment="Strong competitive position",
            success=True,
        )

        result_dict = result.to_dict()

        assert "competitor_analyses" in result_dict
        assert "critiques" in result_dict
        assert "cross_competitor_patterns" in result_dict
        assert result_dict["overall_competitive_assessment"] == "Strong competitive position"
        assert result_dict["success"]

    def test_result_with_analyses(self):
        """Test result with populated analyses."""
        vuln = CompetitiveVulnerability(
            competitor_name="TestCorp",
            title="Test Vuln",
            competitor_attack="Attack description",
            defensive_recommendation="Defense recommendation",
        )

        analysis = CompetitorAnalysis(
            competitor_name="TestCorp",
            is_incumbent=True,
            vulnerabilities=[vuln],
        )

        result = CompetitorSimulatorResult(
            competitor_analyses=[analysis],
            cross_competitor_patterns=["Pattern 1", "Pattern 2"],
            integrated_recommendations=["Rec 1", "Rec 2"],
        )

        result_dict = result.to_dict()

        assert len(result_dict["competitor_analyses"]) == 1
        assert len(result_dict["cross_competitor_patterns"]) == 2
        assert len(result_dict["integrated_recommendations"]) == 2


# ============================================================================
# Integration Tests
# ============================================================================

class TestCompetitorSimulatorIntegration:
    """Integration tests for Competitor Simulator with other components."""

    @pytest.mark.asyncio
    async def test_output_conforms_to_schema(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that output conforms to expected schema."""
        output = await competitor_simulator.process(sample_context)

        output_dict = output.to_dict()

        assert "id" in output_dict
        assert "agent_role" in output_dict
        assert output_dict["agent_role"] == AgentRole.COMPETITOR_SIMULATOR.value
        assert "content" in output_dict
        assert "critiques" in output_dict
        assert "success" in output_dict
        assert "created_at" in output_dict

    @pytest.mark.asyncio
    async def test_critiques_conform_to_critique_model(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that critiques conform to Critique model schema."""
        output = await competitor_simulator.process(sample_context)

        for critique_dict in output.critiques:
            assert "agent" in critique_dict
            assert "challenge_type" in critique_dict
            assert "severity" in critique_dict
            assert "argument" in critique_dict
            assert "suggested_remedy" in critique_dict

    @pytest.mark.asyncio
    async def test_metadata_tracks_analysis_stats(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that metadata tracks analysis statistics."""
        output = await competitor_simulator.process(sample_context)

        assert "competitors_analyzed" in output.metadata
        assert "vulnerabilities_found" in output.metadata
        assert "critique_count" in output.metadata
        assert "critical_count" in output.metadata
        assert "major_count" in output.metadata
        assert "minor_count" in output.metadata

    @pytest.mark.asyncio
    async def test_round_number_tracked(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that round number is tracked in critiques."""
        sample_context.round_number = 3

        output = await competitor_simulator.process(sample_context)

        for critique in output.critiques:
            assert critique.get("round_number") == 3

    @pytest.mark.asyncio
    async def test_document_id_tracked(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_context: SwarmContext,
    ):
        """Test that document ID is tracked in critiques."""
        sample_context.document_id = "test-doc-456"

        output = await competitor_simulator.process(sample_context)

        for critique in output.critiques:
            assert critique.get("target_document_id") == "test-doc-456"

    @pytest.mark.asyncio
    async def test_competitors_from_custom_data(
        self,
        competitor_simulator: CompetitorSimulatorAgent,
        sample_document_content: Dict[str, str],
        sample_competitors: List[Dict[str, Any]],
    ):
        """Test that competitors can be provided via custom_data."""
        context = SwarmContext(
            document_type="Proposal Strategy",
            section_drafts=sample_document_content,
            opportunity={},  # No competitor intel in opportunity
            custom_data={
                "competitors": sample_competitors[:2],  # Only two competitors
            },
        )

        output = await competitor_simulator.process(context)

        assert output.success
        assert output.metadata.get("competitors_analyzed") <= 2


# ============================================================================
# Challenge Type Tests
# ============================================================================

class TestCompetitorChallengeTypes:
    """Test CompetitorChallengeType class."""

    def test_challenge_types_defined(self):
        """Test that all expected challenge types are defined."""
        assert CompetitorChallengeType.COMPETITIVE == "Competitive"
        assert CompetitorChallengeType.TECHNICAL == "Technical"
        assert CompetitorChallengeType.EXPERIENCE == "Experience"
        assert CompetitorChallengeType.PRICING == "Pricing"
        assert CompetitorChallengeType.RISK == "Risk"
        assert CompetitorChallengeType.INCUMBENT == "Incumbent"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
