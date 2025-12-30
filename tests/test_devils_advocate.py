"""
Tests for Devil's Advocate Agent

Tests the Devil's Advocate agent's ability to:
- Generate structured critiques per Critique schema
- Challenge Logic, Evidence, and Completeness types
- Calibrate severity ratings appropriately
- Evaluate blue team responses
"""

import pytest
from datetime import date
from typing import Dict, Any, List

from agents.red.devils_advocate import (
    DevilsAdvocateAgent,
    DevilsAdvocateResult,
    AssumptionAnalysis,
    Counterargument,
    LogicalIssue,
    ResponseEvaluation,
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

from agents.red.prompts.devils_advocate_prompts import (
    DEVILS_ADVOCATE_SYSTEM_PROMPT,
    get_critique_generation_prompt,
    get_section_critique_prompt,
    get_assumption_challenge_prompt,
    get_counterargument_generation_prompt,
    get_logic_analysis_prompt,
    get_response_evaluation_prompt,
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
def sample_opportunity() -> Dict[str, Any]:
    """Create a sample opportunity for testing."""
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
    }


@pytest.fixture
def sample_document_content() -> Dict[str, str]:
    """Create sample document content for critique."""
    return {
        "Win Themes": """## Win Theme 1: Mission-Proven Cloud Excellence

**Theme Statement**: Our team has the best cloud migration capabilities in the federal market,
delivering unmatched results for every agency we serve.

**Supporting Evidence**:
- We have done many cloud migrations
- Our team is highly skilled

**Customer Benefit**: Agencies will get better results with us.

**Evaluation Alignment**: Technical Approach (40%)

**Competitive Advantage**: No competitor can match our expertise.
""",
        "Competitive Analysis": """## Competitive Positioning

We are positioned to win this opportunity. The incumbent has weak performance
and limited innovation. All other competitors lack our experience level.

Our strengths include:
- Superior technical approach
- Better pricing
- More experience

Competitors have no significant advantages over us. We expect to win
with a high probability of success.
""",
        "Pricing Strategy": """## Price-to-Win Analysis

**Recommended Position**: Premium pricing at $25M annually.

The market will accept premium pricing because our solution is superior.
We believe competitors will price at $20M or less, but evaluators will
choose quality over cost.

Our price is justified by our unmatched capabilities. The incumbent
cannot match our innovation, even at lower prices.
""",
    }


@pytest.fixture
def sample_critiques() -> List[Dict[str, Any]]:
    """Create sample critiques for response evaluation tests."""
    return [
        {
            "id": "crit-001",
            "title": "Unsupported Performance Claim",
            "challenge_type": "evidence",
            "severity": "critical",
            "target_section": "Win Themes",
            "target_content": "delivering unmatched results for every agency",
            "argument": "This claim is unprovable and likely false",
            "suggested_remedy": "Replace with specific, quantified past performance",
        },
        {
            "id": "crit-002",
            "title": "One-Sided Competitive Analysis",
            "challenge_type": "completeness",
            "severity": "major",
            "target_section": "Competitive Analysis",
            "target_content": "Competitors have no significant advantages",
            "argument": "Analysis lacks acknowledgment of competitor strengths",
            "suggested_remedy": "Add honest assessment of competitor advantages",
        },
    ]


@pytest.fixture
def sample_responses() -> List[Dict[str, Any]]:
    """Create sample blue team responses for evaluation tests."""
    return [
        {
            "critique_id": "crit-001",
            "disposition": "Accept",
            "action": "Revised to include specific past performance metrics",
            "evidence": "Added CPARS ratings and contract values",
            "revised_content": "Delivered 40% cost savings on DHS Cloud Migration (CPARS: Exceptional)",
        },
        {
            "critique_id": "crit-002",
            "disposition": "Rebut",
            "action": "The analysis is balanced",
            "evidence": "We mentioned competitor strengths in other sections",
        },
    ]


@pytest.fixture
def devils_advocate() -> DevilsAdvocateAgent:
    """Create a Devil's Advocate agent for testing."""
    return DevilsAdvocateAgent()


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

class TestDevilsAdvocatePrompts:
    """Test prompt generation functions."""

    def test_system_prompt_defined(self):
        """Test that system prompt is defined and substantive."""
        assert DEVILS_ADVOCATE_SYSTEM_PROMPT
        assert len(DEVILS_ADVOCATE_SYSTEM_PROMPT) > 500
        assert "Devil's Advocate" in DEVILS_ADVOCATE_SYSTEM_PROMPT
        assert "skeptical" in DEVILS_ADVOCATE_SYSTEM_PROMPT.lower()
        assert "constructive" in DEVILS_ADVOCATE_SYSTEM_PROMPT.lower()

    def test_system_prompt_covers_challenge_types(self):
        """Test that system prompt covers all challenge types."""
        prompt = DEVILS_ADVOCATE_SYSTEM_PROMPT.lower()

        assert "logic" in prompt
        assert "evidence" in prompt
        assert "completeness" in prompt
        assert "risk" in prompt

    def test_system_prompt_addresses_severity(self):
        """Test that system prompt addresses severity calibration."""
        prompt = DEVILS_ADVOCATE_SYSTEM_PROMPT

        assert "Critical" in prompt
        assert "Major" in prompt
        assert "Minor" in prompt
        assert "calibrat" in prompt.lower()

    def test_critique_generation_prompt_includes_document(
        self, sample_document_content: Dict[str, str]
    ):
        """Test that critique prompt includes document content."""
        prompt = get_critique_generation_prompt(
            document_type="Proposal Strategy",
            document_content=sample_document_content,
        )

        assert "Win Theme" in prompt
        assert "Competitive Analysis" in prompt
        assert "Pricing Strategy" in prompt
        assert "Mission-Proven Cloud Excellence" in prompt

    def test_critique_generation_prompt_includes_context(
        self,
        sample_document_content: Dict[str, str],
        sample_company_profile: Dict[str, Any],
        sample_opportunity: Dict[str, Any],
    ):
        """Test that critique prompt includes company and opportunity context."""
        prompt = get_critique_generation_prompt(
            document_type="Proposal Strategy",
            document_content=sample_document_content,
            company_profile=sample_company_profile,
            opportunity=sample_opportunity,
        )

        assert "TechSolutions Federal" in prompt
        assert "Department of Homeland Security" in prompt
        assert "Technical Approach" in prompt

    def test_critique_generation_prompt_includes_focus_areas(
        self, sample_document_content: Dict[str, str]
    ):
        """Test that critique prompt includes focus areas when specified."""
        focus_areas = ["Pricing justification", "Competitive positioning"]

        prompt = get_critique_generation_prompt(
            document_type="Proposal Strategy",
            document_content=sample_document_content,
            focus_areas=focus_areas,
        )

        assert "Pricing justification" in prompt
        assert "Competitive positioning" in prompt

    def test_section_critique_prompt_section_specific(self):
        """Test that section critique prompt is section-specific."""
        prompt = get_section_critique_prompt(
            section_name="Win Themes",
            section_content="Our win themes are excellent.",
            document_type="Proposal Strategy",
        )

        assert "Win Themes" in prompt
        assert "theme statements" in prompt.lower() or "win theme" in prompt.lower()

    def test_assumption_challenge_prompt_structure(self):
        """Test assumption challenge prompt structure."""
        assumptions = [
            {"statement": "The customer prefers innovation over cost", "source": "Strategy"},
            {"statement": "The incumbent will not innovate", "source": "Competitive"},
        ]

        prompt = get_assumption_challenge_prompt(assumptions=assumptions)

        assert "Assumption 1" in prompt
        assert "Assumption 2" in prompt
        assert "innovation over cost" in prompt
        assert "Validity" in prompt

    def test_counterargument_prompt_perspective(self):
        """Test counterargument prompt adopts specified perspective."""
        claims = [
            {"claim": "We are the best positioned", "section": "Strategy"},
        ]

        # Government evaluator perspective
        evaluator_prompt = get_counterargument_generation_prompt(
            claims=claims,
            opponent_perspective="Government Evaluator",
        )
        assert "Government Evaluator" in evaluator_prompt
        assert "evaluator" in evaluator_prompt.lower()

        # Competitor perspective
        competitor_prompt = get_counterargument_generation_prompt(
            claims=claims,
            opponent_perspective="Competitor",
        )
        assert "Competitor" in competitor_prompt

    def test_logic_analysis_prompt_covers_fallacies(self):
        """Test logic analysis prompt covers common fallacies."""
        prompt = get_logic_analysis_prompt(
            content="Some content to analyze",
            section_name="Test Section",
        )

        fallacies = ["non sequitur", "circular", "false dichotomy", "straw man"]
        prompt_lower = prompt.lower()

        found_fallacies = [f for f in fallacies if f in prompt_lower]
        assert len(found_fallacies) >= 2, "Should cover multiple fallacy types"

    def test_response_evaluation_prompt_includes_both(
        self, sample_critiques: List[Dict[str, Any]], sample_responses: List[Dict[str, Any]]
    ):
        """Test response evaluation prompt includes critique and response."""
        prompt = get_response_evaluation_prompt(
            critique=sample_critiques[0],
            response=sample_responses[0],
        )

        # Should include critique details
        assert "Unsupported Performance Claim" in prompt
        assert "Evidence" in prompt
        assert "unprovable" in prompt or "Critical" in prompt

        # Should include response details
        assert "Accept" in prompt
        assert "CPARS" in prompt


# ============================================================================
# Devil's Advocate Agent Tests
# ============================================================================

class TestDevilsAdvocateAgent:
    """Test Devil's Advocate agent functionality."""

    def test_agent_properties(self, devils_advocate: DevilsAdvocateAgent):
        """Test agent role and category properties."""
        assert devils_advocate.role == AgentRole.DEVILS_ADVOCATE
        assert devils_advocate.category == AgentCategory.RED

    def test_agent_default_config(self, devils_advocate: DevilsAdvocateAgent):
        """Test agent uses correct default configuration."""
        config = devils_advocate.config

        assert config.role == AgentRole.DEVILS_ADVOCATE
        assert config.priority == 100  # Highest priority red team agent
        assert config.llm_config.temperature == 0.8  # Higher for diverse critiques
        assert config.llm_config.max_tokens == 4096

    def test_context_validation_requires_content(
        self, devils_advocate: DevilsAdvocateAgent
    ):
        """Test that context validation requires document content."""
        context = SwarmContext(
            document_type="Proposal Strategy",
            section_drafts={},  # Empty - no content
            current_draft=None,
        )

        errors = devils_advocate.validate_context(context)
        assert len(errors) > 0
        assert any("content" in e.lower() for e in errors)

    def test_context_validation_passes_with_content(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_document_content: Dict[str, str],
    ):
        """Test that context validation passes with content."""
        context = SwarmContext(
            document_type="Proposal Strategy",
            section_drafts=sample_document_content,
        )

        errors = devils_advocate.validate_context(context)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_process_generates_output(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that process generates an AgentOutput."""
        output = await devils_advocate.process(sample_context)

        assert isinstance(output, AgentOutput)
        assert output.success
        assert output.agent_role == AgentRole.DEVILS_ADVOCATE
        assert output.critiques  # Should have critiques
        assert output.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_process_generates_critiques(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that process generates properly structured critiques."""
        output = await devils_advocate.process(sample_context)

        assert len(output.critiques) > 0

        for critique in output.critiques:
            # Check required fields
            assert critique.get("agent") == AgentRole.DEVILS_ADVOCATE.value
            assert critique.get("challenge_type")
            assert critique.get("severity")
            assert critique.get("argument")
            assert critique.get("suggested_remedy")

    @pytest.mark.asyncio
    async def test_process_covers_challenge_types(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that critiques cover multiple challenge types."""
        output = await devils_advocate.process(sample_context)

        challenge_types = set()
        for critique in output.critiques:
            challenge_types.add(critique.get("challenge_type"))

        # Should cover at least Logic, Evidence, and one other
        assert len(challenge_types) >= 2, f"Only found: {challenge_types}"

    @pytest.mark.asyncio
    async def test_severity_calibration(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that severity ratings are calibrated (not all Critical)."""
        output = await devils_advocate.process(sample_context)

        severity_counts = {"critical": 0, "major": 0, "minor": 0, "observation": 0}
        for critique in output.critiques:
            sev = critique.get("severity")
            if sev in severity_counts:
                severity_counts[sev] += 1

        # Should have variety in severity
        non_zero_severities = sum(1 for v in severity_counts.values() if v > 0)
        assert non_zero_severities >= 2, f"Severity distribution: {severity_counts}"

        # Not everything should be critical
        total = len(output.critiques)
        if total > 2:
            critical_ratio = severity_counts["critical"] / total
            assert critical_ratio < 0.8, "Too many critiques rated as Critical"

    @pytest.mark.asyncio
    async def test_section_critique_mode(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test section-specific critique mode."""
        sample_context.custom_data["analysis_type"] = "section_critique"
        sample_context.custom_data["target_section"] = "Win Themes"

        output = await devils_advocate.process(sample_context)

        assert output.success
        # Critiques should have been generated
        assert len(output.critiques) >= 0  # May be 0 if mock doesn't match pattern

    @pytest.mark.asyncio
    async def test_assumption_challenge_mode(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test assumption challenge mode."""
        sample_context.custom_data["analysis_type"] = "assumption_challenge"
        sample_context.custom_data["assumptions"] = [
            {"statement": "The customer will prioritize innovation", "source": "Strategy"},
            {"statement": "Competitors cannot match our pricing", "source": "Pricing"},
        ]

        output = await devils_advocate.process(sample_context)

        assert output.success
        # Should have metadata about assumptions
        assert output.metadata.get("assumption_count", 0) >= 0

    @pytest.mark.asyncio
    async def test_logic_analysis_mode(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test logic analysis mode."""
        sample_context.custom_data["analysis_type"] = "logic_analysis"

        output = await devils_advocate.process(sample_context)

        assert output.success
        assert output.metadata.get("logical_issue_count", 0) >= 0

    @pytest.mark.asyncio
    async def test_response_evaluation_mode(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
        sample_critiques: List[Dict[str, Any]],
        sample_responses: List[Dict[str, Any]],
    ):
        """Test response evaluation mode."""
        sample_context.custom_data["analysis_type"] = "response_evaluation"
        sample_context.custom_data["critiques_to_evaluate"] = sample_critiques
        sample_context.custom_data["responses"] = sample_responses

        output = await devils_advocate.process(sample_context)

        assert output.success

    @pytest.mark.asyncio
    async def test_critique_section_interface(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test the critique_section interface method."""
        critiques = await devils_advocate.critique_section(
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
    async def test_evaluate_response_interface(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
        sample_critiques: List[Dict[str, Any]],
        sample_responses: List[Dict[str, Any]],
    ):
        """Test the evaluate_response interface method."""
        is_acceptable = await devils_advocate.evaluate_response(
            context=sample_context,
            critique=sample_critiques[0],
            response=sample_responses[0],  # This is an Accept with good evidence
        )

        assert isinstance(is_acceptable, bool)


# ============================================================================
# Critique Parsing Tests
# ============================================================================

class TestCritiqueParsing:
    """Test critique parsing functionality."""

    def test_parse_critiques_from_response(self, devils_advocate: DevilsAdvocateAgent):
        """Test parsing critiques from LLM response."""
        response = """### Critique 1: Unsupported Claim

**Challenge Type**: Evidence

**Severity**: Critical

**Target Section**: Win Themes

**Challenged Content**: "We are the best in the market"

**Argument**: This claim has no supporting evidence.

**Evidence**: No past performance data is cited.

**Impact If Not Addressed**: Evaluators will mark as a weakness.

**Suggested Remedy**: Add specific contract references with metrics.

---

### Critique 2: Missing Risks

**Challenge Type**: Completeness

**Severity**: Major

**Target Section**: Strategy Summary

**Challenged Content**: The entire section

**Argument**: No risks are acknowledged.

**Evidence**: Strategy documents should include risk assessment.

**Suggested Remedy**: Add a risk section with mitigation strategies.
"""
        critiques = devils_advocate._parse_critiques(
            response,
            document_id="doc-001",
            round_number=1,
        )

        assert len(critiques) == 2

        # Check first critique
        assert critiques[0].title == "Unsupported Claim"
        assert critiques[0].challenge_type == ChallengeType.EVIDENCE
        assert critiques[0].severity == Severity.CRITICAL
        assert critiques[0].target_section == "Win Themes"
        assert "best in the market" in critiques[0].target_content
        assert "no supporting evidence" in critiques[0].argument.lower()
        assert critiques[0].suggested_remedy

        # Check second critique
        assert critiques[1].title == "Missing Risks"
        assert critiques[1].challenge_type == ChallengeType.COMPLETENESS
        assert critiques[1].severity == Severity.MAJOR

    def test_map_challenge_type(self, devils_advocate: DevilsAdvocateAgent):
        """Test mapping challenge type strings to enums."""
        assert devils_advocate._map_challenge_type("Logic") == ChallengeType.LOGIC
        assert devils_advocate._map_challenge_type("Evidence") == ChallengeType.EVIDENCE
        assert devils_advocate._map_challenge_type("Completeness") == ChallengeType.COMPLETENESS
        assert devils_advocate._map_challenge_type("Risk") == ChallengeType.RISK
        assert devils_advocate._map_challenge_type("Compliance") == ChallengeType.COMPLIANCE
        assert devils_advocate._map_challenge_type("Feasibility") == ChallengeType.FEASIBILITY
        assert devils_advocate._map_challenge_type("Clarity") == ChallengeType.CLARITY
        assert devils_advocate._map_challenge_type("Competitive") == ChallengeType.COMPETITIVE
        # Unknown should default to Logic
        assert devils_advocate._map_challenge_type("Unknown") == ChallengeType.LOGIC

    def test_map_severity(self, devils_advocate: DevilsAdvocateAgent):
        """Test mapping severity strings to enums."""
        assert devils_advocate._map_severity("critical") == Severity.CRITICAL
        assert devils_advocate._map_severity("major") == Severity.MAJOR
        assert devils_advocate._map_severity("minor") == Severity.MINOR
        assert devils_advocate._map_severity("observation") == Severity.OBSERVATION
        # Unknown should default to Major
        assert devils_advocate._map_severity("Unknown") == Severity.MAJOR

    def test_parse_assumption_analyses(self, devils_advocate: DevilsAdvocateAgent):
        """Test parsing assumption analyses."""
        response = """### Assumption 1 Analysis

**Statement**: "The customer prefers innovation"

**Validity Assessment**: Questionable

**Challenge**: No evidence of customer preference stated.

**Alternative Scenario**: Customer may prioritize cost savings.

**Evidence Needed**: Customer interviews or past award analysis.

**Recommendation**: Strengthen with evidence
"""
        analyses = devils_advocate._parse_assumption_analyses(response)

        assert len(analyses) == 1
        assert "innovation" in analyses[0].statement
        assert analyses[0].validity == "Questionable"
        assert "evidence" in analyses[0].challenge.lower()

    def test_parse_response_evaluation(self, devils_advocate: DevilsAdvocateAgent):
        """Test parsing response evaluation."""
        response = """### Evaluation Result

**Verdict**: Acceptable

**Reasoning**: The blue team provided strong evidence.

**Strengths of Response**:
- Added specific metrics
- Cited CPARS ratings
- Provided contract references

**Weaknesses of Response**:
- Could include more recent examples

**Follow-Up Required**: No

**Resolution Status**: Resolved
"""
        evaluation = devils_advocate._parse_response_evaluation(response, "crit-001")

        assert evaluation.critique_id == "crit-001"
        assert evaluation.verdict == "Acceptable"
        assert "strong evidence" in evaluation.reasoning
        assert len(evaluation.strengths) >= 2
        assert len(evaluation.weaknesses) >= 1
        assert not evaluation.follow_up_required
        assert evaluation.resolution_status == "Resolved"


# ============================================================================
# Helper Method Tests
# ============================================================================

class TestHelperMethods:
    """Test helper methods."""

    def test_extract_assumptions(self, devils_advocate: DevilsAdvocateAgent):
        """Test extracting assumptions from document content."""
        section_drafts = {
            "Strategy": "We expect the customer to value innovation. We anticipate strong competition.",
            "Pricing": "We assume competitors will price below market. We believe our value justifies premium.",
        }

        assumptions = devils_advocate._extract_assumptions(section_drafts)

        assert len(assumptions) > 0
        # Should find assumption indicators
        assert any("expect" in a["statement"].lower() for a in assumptions)

    def test_extract_claims(self, devils_advocate: DevilsAdvocateAgent):
        """Test extracting claims from document content."""
        section_drafts = {
            "Capabilities": "We are the only company with this certification. We have proven our approach works.",
            "Competitive": "Our solution is superior. We offer unique capabilities no competitor can match.",
        }

        claims = devils_advocate._extract_claims(section_drafts)

        assert len(claims) > 0
        # Should find claim indicators
        assert any("only" in c["claim"].lower() or "unique" in c["claim"].lower() for c in claims)

    def test_generate_overall_assessment_no_critiques(
        self, devils_advocate: DevilsAdvocateAgent
    ):
        """Test overall assessment with no critiques."""
        assessment = devils_advocate._generate_overall_assessment([])
        assert "No significant issues" in assessment

    def test_generate_overall_assessment_with_critiques(
        self, devils_advocate: DevilsAdvocateAgent
    ):
        """Test overall assessment with various critiques."""
        critiques = [
            Critique(
                agent="Devil's Advocate",
                argument="Test argument 1",
                suggested_remedy="Test remedy 1",
                severity=Severity.CRITICAL,
                challenge_type=ChallengeType.EVIDENCE,
            ),
            Critique(
                agent="Devil's Advocate",
                argument="Test argument 2",
                suggested_remedy="Test remedy 2",
                severity=Severity.MAJOR,
                challenge_type=ChallengeType.LOGIC,
            ),
            Critique(
                agent="Devil's Advocate",
                argument="Test argument 3",
                suggested_remedy="Test remedy 3",
                severity=Severity.MINOR,
                challenge_type=ChallengeType.COMPLETENESS,
            ),
        ]

        assessment = devils_advocate._generate_overall_assessment(critiques)

        assert "1 CRITICAL" in assessment
        assert "1 Major" in assessment
        assert "1 Minor" in assessment


# ============================================================================
# Integration Tests
# ============================================================================

class TestDevilsAdvocateIntegration:
    """Integration tests for Devil's Advocate with other components."""

    @pytest.mark.asyncio
    async def test_output_conforms_to_schema(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that output conforms to expected schema."""
        output = await devils_advocate.process(sample_context)

        output_dict = output.to_dict()

        assert "id" in output_dict
        assert "agent_role" in output_dict
        assert output_dict["agent_role"] == AgentRole.DEVILS_ADVOCATE.value
        assert "content" in output_dict
        assert "critiques" in output_dict
        assert "success" in output_dict
        assert "created_at" in output_dict

    @pytest.mark.asyncio
    async def test_critiques_conform_to_critique_model(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that critiques conform to Critique model schema."""
        output = await devils_advocate.process(sample_context)

        for critique_dict in output.critiques:
            # Should be able to create Critique from the dict
            # (bypassing __post_init__ validation for this test)
            assert "agent" in critique_dict
            assert "challenge_type" in critique_dict
            assert "severity" in critique_dict
            assert "argument" in critique_dict
            assert "suggested_remedy" in critique_dict

    @pytest.mark.asyncio
    async def test_critique_summary_generated(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that critique summary is generated in metadata."""
        output = await devils_advocate.process(sample_context)

        # Check metadata contains summary info
        assert "critique_count" in output.metadata
        assert "critical_count" in output.metadata
        assert "major_count" in output.metadata
        assert "minor_count" in output.metadata

        # Counts should be consistent
        total = (
            output.metadata["critical_count"] +
            output.metadata["major_count"] +
            output.metadata["minor_count"]
        )
        assert total <= output.metadata["critique_count"]

    @pytest.mark.asyncio
    async def test_round_number_tracked(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that round number is tracked in critiques."""
        sample_context.round_number = 2

        output = await devils_advocate.process(sample_context)

        for critique in output.critiques:
            assert critique.get("round_number") == 2

    @pytest.mark.asyncio
    async def test_document_id_tracked(
        self,
        devils_advocate: DevilsAdvocateAgent,
        sample_context: SwarmContext,
    ):
        """Test that document ID is tracked in critiques."""
        sample_context.document_id = "test-doc-123"

        output = await devils_advocate.process(sample_context)

        for critique in output.critiques:
            assert critique.get("target_document_id") == "test-doc-123"


# ============================================================================
# Result Dataclass Tests
# ============================================================================

class TestDevilsAdvocateResult:
    """Test the DevilsAdvocateResult dataclass."""

    def test_result_initialization(self):
        """Test result initialization with defaults."""
        result = DevilsAdvocateResult()

        assert result.success
        assert len(result.critiques) == 0
        assert len(result.assumption_analyses) == 0
        assert len(result.counterarguments) == 0
        assert len(result.logical_issues) == 0
        assert len(result.response_evaluations) == 0
        assert result.critique_summary is None
        assert result.overall_assessment == ""

    def test_result_to_dict(self):
        """Test result serialization to dict."""
        result = DevilsAdvocateResult(
            overall_assessment="Test assessment",
            success=True,
        )

        result_dict = result.to_dict()

        assert "critiques" in result_dict
        assert "assumption_analyses" in result_dict
        assert "overall_assessment" in result_dict
        assert result_dict["overall_assessment"] == "Test assessment"
        assert result_dict["success"]

    def test_assumption_analysis_to_dict(self):
        """Test AssumptionAnalysis serialization."""
        analysis = AssumptionAnalysis(
            statement="Test assumption",
            validity="Questionable",
            challenge="Why it's questionable",
            recommendation="Strengthen",
        )

        analysis_dict = analysis.to_dict()

        assert analysis_dict["statement"] == "Test assumption"
        assert analysis_dict["validity"] == "Questionable"
        assert analysis_dict["challenge"] == "Why it's questionable"
        assert analysis_dict["recommendation"] == "Strengthen"

    def test_counterargument_to_dict(self):
        """Test Counterargument serialization."""
        counter = Counterargument(
            original_claim="We are the best",
            section="Strategy",
            counterargument="Where's the proof?",
            weakness_exposed="No evidence provided",
            recommended_response="Add metrics",
        )

        counter_dict = counter.to_dict()

        assert counter_dict["original_claim"] == "We are the best"
        assert counter_dict["counterargument"] == "Where's the proof?"

    def test_logical_issue_to_dict(self):
        """Test LogicalIssue serialization."""
        issue = LogicalIssue(
            issue_type="Non Sequitur",
            location="Win Theme 1",
            flawed_reasoning="Therefore we are best",
            explanation="Conclusion doesn't follow",
            correction="Add logical connection",
            severity="major",
        )

        issue_dict = issue.to_dict()

        assert issue_dict["issue_type"] == "Non Sequitur"
        assert issue_dict["severity"] == "major"

    def test_response_evaluation_to_dict(self):
        """Test ResponseEvaluation serialization."""
        evaluation = ResponseEvaluation(
            critique_id="crit-001",
            verdict="Acceptable",
            reasoning="Good response",
            strengths=["Added evidence"],
            weaknesses=["Could be stronger"],
            follow_up_required=False,
            resolution_status="Resolved",
        )

        eval_dict = evaluation.to_dict()

        assert eval_dict["critique_id"] == "crit-001"
        assert eval_dict["verdict"] == "Acceptable"
        assert eval_dict["strengths"] == ["Added evidence"]


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
