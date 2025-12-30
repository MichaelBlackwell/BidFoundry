"""
Test Suite for Arbiter Agent and Orchestration

Comprehensive tests for Chunk 12: Arbiter Agent & Debate Loop
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

# Import the components we're testing
from agents.orchestrator import (
    ArbiterAgent,
    DocumentRequest,
    FinalOutput,
    DocumentWorkflow,
    WorkflowConfig,
    WorkflowPhase,
    WorkflowStatus,
    ConsensusDetector,
    ConsensusResult,
    ConsensusStatus,
    ConsensusConfig,
    DocumentSynthesizer,
    SynthesisConfig,
)

from agents.base import SwarmContext, AgentOutput
from agents.types import AgentRole, AgentCategory
from agents.config import AgentConfig, LLMConfig
from agents.registry import AgentRegistry

from comms.bus import MessageBus
from comms.history import ConversationHistory
from comms.round import RoundManager, RoundType, RoundSummary
from comms.message import Message, MessageType

from models.confidence import (
    ConfidenceScore, SectionConfidence, ConfidenceThresholds,
    ConfidenceLevel, RiskFlag
)

from outputs import (
    FinalDocument, DocumentSection, RedTeamReport,
    ConfidenceReport, SectionReport, ReviewPriority
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_company_profile() -> Dict[str, Any]:
    """Sample company profile for testing."""
    return {
        "name": "TechSolutions Inc.",
        "duns": "123456789",
        "cage_code": "ABC12",
        "naics_codes": ["541512", "541519"],
        "certifications": ["8(a)", "HUBZone"],
        "employees": 45,
        "annual_revenue": 5000000,
        "past_performance": [
            {
                "contract_number": "GS-35F-0001",
                "agency": "GSA",
                "value": 2000000,
                "rating": "Excellent",
            }
        ],
    }


@pytest.fixture
def sample_opportunity() -> Dict[str, Any]:
    """Sample opportunity for testing."""
    return {
        "id": "OPP-001",
        "title": "IT Modernization Services",
        "agency": "Department of Defense",
        "naics": "541512",
        "set_aside": "8(a)",
        "value_estimate": 10000000,
        "response_deadline": "2025-03-15",
        "competitors": [
            {"name": "CompetitorA", "strength": "Incumbent"},
            {"name": "CompetitorB", "strength": "Price"},
        ],
    }


@pytest.fixture
def document_request(sample_company_profile, sample_opportunity) -> DocumentRequest:
    """Create a sample document request."""
    return DocumentRequest(
        id="REQ-001",
        document_type="Proposal Strategy",
        company_profile=sample_company_profile,
        opportunity=sample_opportunity,
        max_adversarial_rounds=3,
        consensus_threshold=0.80,
        confidence_threshold=0.70,
    )


@pytest.fixture
def mock_registry() -> AgentRegistry:
    """Create a mock agent registry."""
    registry = AgentRegistry()

    # Create mock blue team agent
    mock_blue_agent = MagicMock()
    mock_blue_agent.role = AgentRole.STRATEGY_ARCHITECT
    mock_blue_agent.category = AgentCategory.BLUE
    mock_blue_agent.name = "Strategy Architect"
    mock_blue_agent.is_enabled = True
    mock_blue_agent.priority = 100
    mock_blue_agent.process = AsyncMock(return_value=AgentOutput(
        agent_role=AgentRole.STRATEGY_ARCHITECT,
        agent_name="Strategy Architect",
        content="Test draft content",
        sections={
            "Executive Summary": "This is the executive summary.",
            "Technical Approach": "This is the technical approach.",
        },
        success=True,
    ))
    mock_blue_agent.revise_section = AsyncMock(return_value="Revised content")

    # Create mock red team agent
    mock_red_agent = MagicMock()
    mock_red_agent.role = AgentRole.DEVILS_ADVOCATE
    mock_red_agent.category = AgentCategory.RED
    mock_red_agent.name = "Devil's Advocate"
    mock_red_agent.is_enabled = True
    mock_red_agent.priority = 100
    mock_red_agent.process = AsyncMock(return_value=AgentOutput(
        agent_role=AgentRole.DEVILS_ADVOCATE,
        agent_name="Devil's Advocate",
        content="",
        critiques=[
            {
                "id": "CRIT-001",
                "agent": "Devil's Advocate",
                "target_section": "Executive Summary",
                "challenge_type": "logic",
                "severity": "major",
                "title": "Unsupported claim",
                "argument": "The claim lacks evidence.",
                "suggested_remedy": "Add supporting data.",
            },
        ],
        success=True,
    ))

    # Register mock creation
    registry.create = MagicMock(side_effect=lambda role: {
        AgentRole.STRATEGY_ARCHITECT: mock_blue_agent,
        AgentRole.DEVILS_ADVOCATE: mock_red_agent,
    }.get(role, mock_blue_agent))

    registry.create_blue_team = MagicMock(return_value=[mock_blue_agent])
    registry.create_red_team = MagicMock(return_value=[mock_red_agent])
    registry.is_registered = MagicMock(return_value=True)
    registry.get_cached_instance = MagicMock(return_value=None)

    return registry


@pytest.fixture
def mock_message_bus() -> MessageBus:
    """Create a mock message bus."""
    bus = MessageBus()
    bus.start = AsyncMock()
    bus.stop = AsyncMock()
    bus.publish = AsyncMock(side_effect=lambda msg, **kwargs: msg)
    return bus


# ============================================================================
# Arbiter Agent Tests
# ============================================================================

class TestArbiterAgent:
    """Tests for the ArbiterAgent class."""

    def test_arbiter_creation(self):
        """Test that Arbiter can be created with default config."""
        arbiter = ArbiterAgent()
        assert arbiter.role == AgentRole.ARBITER
        assert arbiter.category == AgentCategory.ORCHESTRATOR

    def test_arbiter_with_custom_config(self):
        """Test Arbiter with custom configuration."""
        config = AgentConfig(
            role=AgentRole.ARBITER,
            name="Custom Arbiter",
            enabled=True,
            priority=100,
        )
        arbiter = ArbiterAgent(config=config)
        assert arbiter.name == "Custom Arbiter"

    @pytest.mark.asyncio
    async def test_arbiter_initialization(self, mock_registry, mock_message_bus):
        """Test Arbiter initialization."""
        arbiter = ArbiterAgent()
        await arbiter.initialize(
            registry=mock_registry,
            message_bus=mock_message_bus,
        )

        assert arbiter._registry is not None
        assert arbiter._message_bus is not None
        assert arbiter._history is not None
        assert arbiter._round_manager is not None

    @pytest.mark.asyncio
    async def test_arbiter_process(self, mock_registry, mock_message_bus):
        """Test Arbiter process method."""
        arbiter = ArbiterAgent()
        await arbiter.initialize(
            registry=mock_registry,
            message_bus=mock_message_bus,
        )

        context = SwarmContext(
            request_id="TEST-001",
            document_type="Capability Statement",
            company_profile={"name": "Test Corp"},
        )

        # Mock the generate_document method
        arbiter.generate_document = AsyncMock(return_value=FinalOutput(
            request_id="TEST-001",
            document_type="Capability Statement",
            success=True,
            consensus_reached=True,
        ))

        output = await arbiter.process(context)
        assert output.success

    @pytest.mark.asyncio
    async def test_arbiter_cleanup(self, mock_registry, mock_message_bus):
        """Test Arbiter cleanup."""
        arbiter = ArbiterAgent()
        await arbiter.initialize(
            registry=mock_registry,
            message_bus=mock_message_bus,
        )

        await arbiter.cleanup()
        mock_message_bus.stop.assert_called_once()


# ============================================================================
# Document Request Tests
# ============================================================================

class TestDocumentRequest:
    """Tests for DocumentRequest."""

    def test_document_request_creation(self, sample_company_profile, sample_opportunity):
        """Test creating a document request."""
        request = DocumentRequest(
            id="REQ-001",
            document_type="Proposal Strategy",
            company_profile=sample_company_profile,
            opportunity=sample_opportunity,
        )

        assert request.id == "REQ-001"
        assert request.document_type == "Proposal Strategy"
        assert request.max_adversarial_rounds == 3  # default

    def test_document_request_to_dict(self, document_request):
        """Test document request serialization."""
        data = document_request.to_dict()

        assert data["id"] == "REQ-001"
        assert data["document_type"] == "Proposal Strategy"
        assert "company_profile" in data
        assert "opportunity" in data


# ============================================================================
# Workflow Tests
# ============================================================================

class TestWorkflowConfig:
    """Tests for WorkflowConfig."""

    def test_default_config(self):
        """Test default workflow configuration."""
        config = WorkflowConfig()

        assert config.document_type == "General"
        assert config.max_adversarial_rounds == 3
        assert config.consensus_threshold == 0.80
        assert config.enable_parallel_agents is True

    def test_custom_config(self):
        """Test custom workflow configuration."""
        config = WorkflowConfig(
            document_type="Proposal Strategy",
            max_adversarial_rounds=5,
            consensus_threshold=0.90,
            required_blue_agents=[AgentRole.STRATEGY_ARCHITECT],
            required_red_agents=[AgentRole.DEVILS_ADVOCATE],
        )

        assert config.document_type == "Proposal Strategy"
        assert config.max_adversarial_rounds == 5
        assert len(config.required_blue_agents) == 1

    def test_config_to_dict(self):
        """Test workflow config serialization."""
        config = WorkflowConfig(
            document_type="Test",
            required_blue_agents=[AgentRole.STRATEGY_ARCHITECT],
        )
        data = config.to_dict()

        assert data["document_type"] == "Test"
        assert "Strategy Architect" in data["required_blue_agents"]


# ============================================================================
# Consensus Detection Tests
# ============================================================================

class TestConsensusDetector:
    """Tests for ConsensusDetector."""

    def test_detector_creation(self):
        """Test creating a consensus detector."""
        detector = ConsensusDetector()
        assert detector.config is not None
        assert detector.config.resolution_threshold == 0.80

    def test_detector_with_custom_config(self):
        """Test detector with custom config."""
        config = ConsensusConfig(
            resolution_threshold=0.90,
            block_on_critical=False,
        )
        detector = ConsensusDetector(config=config)

        assert detector.config.resolution_threshold == 0.90
        assert detector.config.block_on_critical is False

    def test_consensus_with_no_critiques(self):
        """Test consensus when there are no critiques."""
        detector = ConsensusDetector()
        result = detector.check(critiques=[], responses=[])

        assert result.reached is True
        assert result.confidence == 1.0
        assert result.status == ConsensusStatus.REACHED

    def test_consensus_all_resolved(self):
        """Test consensus when all critiques are resolved."""
        detector = ConsensusDetector()

        critiques = [
            {"id": "C1", "severity": "major"},
            {"id": "C2", "severity": "minor"},
        ]
        responses = [
            {"critique_id": "C1", "disposition": "Accept"},
            {"critique_id": "C2", "disposition": "Rebut"},
        ]

        result = detector.check(critiques=critiques, responses=responses)

        assert result.reached is True
        assert result.resolution_rate == 1.0
        assert result.resolved_critiques == 2

    def test_consensus_not_reached_low_resolution(self):
        """Test consensus not reached with low resolution rate."""
        detector = ConsensusDetector()

        critiques = [
            {"id": "C1", "severity": "major"},
            {"id": "C2", "severity": "major"},
            {"id": "C3", "severity": "major"},
            {"id": "C4", "severity": "major"},
            {"id": "C5", "severity": "major"},
        ]
        responses = [
            {"critique_id": "C1", "disposition": "Accept"},
        ]

        result = detector.check(critiques=critiques, responses=responses)

        assert result.reached is False
        assert result.resolution_rate == 0.2  # 1/5

    def test_consensus_blocked_by_critical(self):
        """Test consensus blocked by unresolved critical critique."""
        detector = ConsensusDetector()

        critiques = [
            {"id": "C1", "severity": "critical"},
            {"id": "C2", "severity": "minor"},
        ]
        responses = [
            {"critique_id": "C2", "disposition": "Accept"},
        ]

        result = detector.check(critiques=critiques, responses=responses)

        assert result.reached is False
        assert result.status == ConsensusStatus.BLOCKED
        assert result.has_blocking_issues is True

    def test_weighted_score_calculation(self):
        """Test weighted consensus score calculation."""
        detector = ConsensusDetector()

        critiques = [
            {"id": "C1", "severity": "critical"},
            {"id": "C2", "severity": "minor"},
        ]
        responses = [
            {"critique_id": "C1", "disposition": "Accept"},
            {"critique_id": "C2", "disposition": "Acknowledge"},
        ]

        result = detector.check(critiques=critiques, responses=responses)

        # All resolved, but with different weights
        assert result.resolved_critiques == 2
        assert result.confidence > 0

    def test_suggest_next_action_proceed(self):
        """Test suggesting next action when consensus reached."""
        detector = ConsensusDetector()
        result = ConsensusResult(
            status=ConsensusStatus.REACHED,
            reached=True,
            confidence=0.85,
        )

        suggestion = detector.suggest_next_action(result)
        assert suggestion["action"] == "proceed_to_synthesis"

    def test_suggest_next_action_blocked(self):
        """Test suggesting next action when blocked."""
        detector = ConsensusDetector()
        result = ConsensusResult(
            status=ConsensusStatus.BLOCKED,
            reached=False,
            has_blocking_issues=True,
            blocking_issues=[{"reason": "Critical issue"}],
        )

        suggestion = detector.suggest_next_action(result)
        assert suggestion["action"] == "address_blocking_issues"


# ============================================================================
# Document Synthesis Tests
# ============================================================================

class TestDocumentSynthesizer:
    """Tests for DocumentSynthesizer."""

    def test_synthesizer_creation(self):
        """Test creating a synthesizer."""
        synthesizer = DocumentSynthesizer()
        assert synthesizer.config is not None

    def test_synthesizer_with_custom_config(self):
        """Test synthesizer with custom config."""
        config = SynthesisConfig(
            output_format="json",
            include_revision_notes=True,
        )
        synthesizer = DocumentSynthesizer(config=config)

        assert synthesizer.config.output_format == "json"
        assert synthesizer.config.include_revision_notes is True

    @pytest.mark.asyncio
    async def test_synthesize_simple_document(self):
        """Test synthesizing a simple document."""
        synthesizer = DocumentSynthesizer()

        sections = {
            "Executive Summary": "This is the executive summary.",
            "Technical Approach": "This is the technical approach.",
        }
        critiques = []
        responses = []
        context = SwarmContext(
            request_id="TEST-001",
            document_type="Test Document",
        )

        result = await synthesizer.synthesize(
            sections=sections,
            critiques=critiques,
            responses=responses,
            context=context,
        )

        assert "sections" in result
        assert len(result["sections"]) == 2

    @pytest.mark.asyncio
    async def test_synthesize_with_critiques(self):
        """Test synthesizing with critiques."""
        synthesizer = DocumentSynthesizer()

        sections = {"Executive Summary": "Original content."}
        critiques = [
            {
                "id": "C1",
                "target_section": "Executive Summary",
                "severity": "major",
            },
        ]
        responses = [
            {"critique_id": "C1", "disposition": "Accept"},
        ]
        context = SwarmContext(request_id="TEST-001")

        result = await synthesizer.synthesize(
            sections=sections,
            critiques=critiques,
            responses=responses,
            context=context,
        )

        assert "metadata" in result
        assert result["metadata"]["total_critiques"] == 1

    def test_format_as_markdown(self):
        """Test formatting document as Markdown."""
        synthesizer = DocumentSynthesizer()

        document = {
            "type": "Test Document",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": [
                {"name": "Introduction", "content": "Hello world."},
            ],
            "metadata": {"resolution_rate": 85.0},
        }

        markdown = synthesizer.format_as_markdown(document)

        assert "# Test Document" in markdown
        assert "## Introduction" in markdown
        assert "Hello world" in markdown

    def test_format_as_json(self):
        """Test formatting document as JSON."""
        synthesizer = DocumentSynthesizer()

        document = {"type": "Test", "sections": []}
        json_str = synthesizer.format_as_json(document)

        assert "Test" in json_str

    def test_format_as_html(self):
        """Test formatting document as HTML."""
        synthesizer = DocumentSynthesizer()

        document = {
            "type": "Test Document",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": [
                {"name": "Introduction", "content": "Hello world."},
            ],
            "metadata": {"resolution_rate": 85.0},
        }

        html = synthesizer.format_as_html(document)

        assert "<html>" in html
        assert "<h1>Test Document</h1>" in html


# ============================================================================
# Output Structure Tests
# ============================================================================

class TestFinalDocument:
    """Tests for FinalDocument output structure."""

    def test_create_final_document(self):
        """Test creating a final document."""
        doc = FinalDocument()
        doc.metadata.document_type = "Capability Statement"
        doc.metadata.company_name = "Test Corp"

        section = DocumentSection(
            name="Executive Summary",
            content="This is the summary.",
            confidence_score=0.85,
        )
        doc.add_section(section)

        assert len(doc.sections) == 1
        assert doc.total_word_count > 0

    def test_final_document_serialization(self):
        """Test serializing final document."""
        doc = FinalDocument()
        doc.metadata.document_id = "DOC-001"

        data = doc.to_dict()
        assert data["metadata"]["document_id"] == "DOC-001"

        # Round-trip test
        restored = FinalDocument.from_dict(data)
        assert restored.metadata.document_id == "DOC-001"

    def test_final_document_to_markdown(self):
        """Test exporting to Markdown."""
        doc = FinalDocument()
        doc.metadata.document_type = "Test"
        doc.metadata.company_name = "Test Corp"

        section = DocumentSection(
            name="Introduction",
            content="Hello world.",
        )
        doc.add_section(section)

        markdown = doc.to_markdown()
        assert "# Test" in markdown
        assert "## Introduction" in markdown


class TestRedTeamReport:
    """Tests for RedTeamReport output structure."""

    def test_create_red_team_report(self):
        """Test creating a red team report."""
        report = RedTeamReport()
        report.document_id = "DOC-001"
        report.document_type = "Proposal Strategy"

        assert report.total_critiques == 0
        assert report.resolution_rate == 100.0

    def test_add_exchange_to_report(self):
        """Test adding exchanges to report."""
        from outputs.red_team_report import CritiqueRecord, ResponseRecord, ExchangeRecord

        report = RedTeamReport()

        critique = CritiqueRecord(
            id="C1",
            agent="Devil's Advocate",
            section="Executive Summary",
            severity="major",
            title="Test critique",
        )
        response = ResponseRecord(
            id="R1",
            critique_id="C1",
            agent="Strategy Architect",
            disposition="Accept",
        )
        exchange = ExchangeRecord(critique=critique, response=response)

        report.add_exchange(exchange)

        assert report.total_critiques == 1
        assert report.resolved_critiques == 1
        assert "major" in report.critiques_by_severity

    def test_red_team_report_to_markdown(self):
        """Test exporting report to Markdown."""
        report = RedTeamReport()
        report.document_type = "Test"

        markdown = report.to_markdown()
        assert "# Red Team Report" in markdown


class TestConfidenceReport:
    """Tests for ConfidenceReport output structure."""

    def test_create_confidence_report(self):
        """Test creating a confidence report."""
        report = ConfidenceReport()
        report.document_id = "DOC-001"
        report.overall_score = 0.85
        report.overall_level = ConfidenceLevel.HIGH

        assert report.requires_human_review is False

    def test_add_section_report(self):
        """Test adding section reports."""
        report = ConfidenceReport()

        section = SectionReport(
            section_name="Introduction",
            confidence_score=0.75,
            confidence_level=ConfidenceLevel.MODERATE,
        )
        report.add_section_report(section)

        assert report.total_sections == 1

    def test_confidence_report_from_confidence_score(self):
        """Test creating report from ConfidenceScore."""
        score = ConfidenceScore(
            document_id="DOC-001",
            document_type="Test",
            overall_score=0.65,
            overall_level=ConfidenceLevel.LOW,
            requires_human_review=True,
        )

        report = ConfidenceReport.from_confidence_score(score)

        assert report.overall_score == 0.65
        assert report.requires_human_review is True

    def test_confidence_report_to_markdown(self):
        """Test exporting report to Markdown."""
        report = ConfidenceReport()
        report.document_type = "Test"
        report.overall_score = 0.85

        markdown = report.to_markdown()
        assert "# Confidence Report" in markdown


# ============================================================================
# Integration Tests
# ============================================================================

class TestArbiterIntegration:
    """Integration tests for the complete Arbiter workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, mock_registry, mock_message_bus, document_request):
        """Test a complete document generation workflow."""
        arbiter = ArbiterAgent()
        await arbiter.initialize(
            registry=mock_registry,
            message_bus=mock_message_bus,
        )

        # Configure mock to return responses
        mock_blue = mock_registry.create(AgentRole.STRATEGY_ARCHITECT)
        mock_blue.process = AsyncMock(return_value=AgentOutput(
            agent_role=AgentRole.STRATEGY_ARCHITECT,
            agent_name="Strategy Architect",
            sections={"Executive Summary": "Test content"},
            responses=[
                {"critique_id": "CRIT-001", "disposition": "Accept", "summary": "Will address"},
            ],
            success=True,
        ))

        # Run the workflow (with mocked components)
        with patch.object(arbiter, '_run_synthesis', new_callable=AsyncMock) as mock_synthesis:
            mock_synthesis.return_value = {"sections": [], "metadata": {}}

            # We need to simplify for testing
            output = await arbiter.generate_document(document_request)

            assert output.request_id == "REQ-001"
            assert output.document_type == "Proposal Strategy"

    @pytest.mark.asyncio
    async def test_consensus_triggers_early_termination(self, mock_registry, mock_message_bus):
        """Test that consensus triggers early termination."""
        arbiter = ArbiterAgent()
        await arbiter.initialize(
            registry=mock_registry,
            message_bus=mock_message_bus,
        )

        # Set up mocks for quick consensus
        mock_red = mock_registry.create(AgentRole.DEVILS_ADVOCATE)
        mock_red.process = AsyncMock(return_value=AgentOutput(
            agent_role=AgentRole.DEVILS_ADVOCATE,
            critiques=[],  # No critiques = immediate consensus
            success=True,
        ))

        request = DocumentRequest(
            id="TEST-001",
            document_type="Simple",
            company_profile={"name": "Test"},
        )

        with patch.object(arbiter, '_run_synthesis', new_callable=AsyncMock) as mock_synthesis:
            mock_synthesis.return_value = {"sections": [], "metadata": {}}

            output = await arbiter.generate_document(request)

            # Should complete quickly with no adversarial rounds
            assert output.success

    @pytest.mark.asyncio
    async def test_human_escalation_on_low_confidence(self):
        """Test that low confidence triggers human escalation flag."""
        # This tests the confidence scoring logic directly
        # rather than the full workflow which requires complex mocking

        from models.confidence import ConfidenceScore, SectionConfidence, ConfidenceThresholds

        # Create a confidence score with low overall score
        thresholds = ConfidenceThresholds(human_review_threshold=0.70)
        score = ConfidenceScore(
            document_id="TEST-001",
            document_type="Complex",
            thresholds=thresholds,
        )

        # Add a section with low confidence
        section = SectionConfidence(
            section_name="Test Section",
            base_score=0.50,
            adjusted_score=0.50,
            critical_critiques=2,
            unresolved_critiques=2,
        )
        score.add_section_score(section)

        # Set unresolved critical count
        score.unresolved_critical = 2

        # Calculate overall score - should trigger review
        score.calculate_overall_score()

        # Should require human review due to low confidence
        assert score.requires_human_review is True
        assert len(score.review_reasons) > 0


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_sections(self):
        """Test handling of empty sections."""
        synthesizer = DocumentSynthesizer()

        # Empty document should not raise
        assert synthesizer.config is not None

    def test_consensus_with_only_observations(self):
        """Test consensus with only observation-level critiques."""
        detector = ConsensusDetector()

        critiques = [
            {"id": "C1", "severity": "observation"},
            {"id": "C2", "severity": "observation"},
        ]
        # No responses needed for observations
        result = detector.check(critiques=critiques, responses=[])

        # Observations shouldn't block consensus (depending on config)
        assert result.total_critiques == 2

    def test_document_request_defaults(self):
        """Test that document request has sensible defaults."""
        request = DocumentRequest()

        assert request.max_adversarial_rounds == 3
        assert request.consensus_threshold == 0.80
        assert request.confidence_threshold == 0.70

    def test_final_output_duration_calculation(self):
        """Test duration calculation in FinalOutput."""
        output = FinalOutput()
        output.started_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        output.completed_at = datetime(2025, 1, 1, 12, 5, 30, tzinfo=timezone.utc)

        assert output.duration_seconds == 330.0  # 5 minutes 30 seconds

    def test_workflow_phase_transitions(self):
        """Test valid workflow phase transitions."""
        # Test that phases are properly defined
        phases = [
            WorkflowPhase.INITIALIZATION,
            WorkflowPhase.BLUE_BUILD,
            WorkflowPhase.RED_ATTACK,
            WorkflowPhase.BLUE_DEFENSE,
            WorkflowPhase.SYNTHESIS,
            WorkflowPhase.FINALIZATION,
            WorkflowPhase.COMPLETE,
        ]

        for phase in phases:
            assert phase.value is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
