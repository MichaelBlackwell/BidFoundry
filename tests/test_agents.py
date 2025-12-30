"""
Unit tests for Agent Base Classes (Chunk 2).

Tests agent types, configuration, base classes, and registry.
"""

import pytest
from typing import List, Dict, Any

from agents.types import (
    AgentRole,
    AgentCategory,
    ROLE_CATEGORIES,
    get_blue_team_roles,
    get_red_team_roles,
    get_roles_by_category,
)
from agents.config import (
    LLMConfig,
    AgentConfig,
    DEFAULT_AGENT_CONFIGS,
    get_default_config,
    configure_llm_settings,
)
from agents.base import (
    AbstractAgent,
    BlueTeamAgent,
    RedTeamAgent,
    OrchestratorAgent,
    AgentOutput,
    SwarmContext,
)
from agents.registry import (
    AgentRegistry,
    AgentRegistrationError,
    AgentInstantiationError,
    get_registry,
    register_agent,
    create_agent,
    agent,
)


# ============================================================================
# Agent Types Tests
# ============================================================================

class TestAgentRole:
    """Tests for AgentRole enum."""

    def test_all_roles_have_categories(self):
        """Verify all roles are mapped to categories."""
        for role in AgentRole:
            assert role in ROLE_CATEGORIES, f"Role {role} not in ROLE_CATEGORIES"

    def test_role_category_property(self):
        """Test the category property on AgentRole."""
        assert AgentRole.STRATEGY_ARCHITECT.category == AgentCategory.BLUE
        assert AgentRole.DEVILS_ADVOCATE.category == AgentCategory.RED
        assert AgentRole.ARBITER.category == AgentCategory.ORCHESTRATOR

    def test_is_blue_team(self):
        """Test blue team role detection."""
        assert AgentRole.STRATEGY_ARCHITECT.is_blue_team is True
        assert AgentRole.MARKET_ANALYST.is_blue_team is True
        assert AgentRole.DEVILS_ADVOCATE.is_blue_team is False

    def test_is_red_team(self):
        """Test red team role detection."""
        assert AgentRole.DEVILS_ADVOCATE.is_red_team is True
        assert AgentRole.RISK_ASSESSOR.is_red_team is True
        assert AgentRole.STRATEGY_ARCHITECT.is_red_team is False


class TestAgentCategory:
    """Tests for AgentCategory enum."""

    def test_get_blue_team_roles(self):
        """Test retrieval of blue team roles."""
        blue_roles = get_blue_team_roles()
        assert AgentRole.STRATEGY_ARCHITECT in blue_roles
        assert AgentRole.MARKET_ANALYST in blue_roles
        assert AgentRole.COMPLIANCE_NAVIGATOR in blue_roles
        assert AgentRole.CAPTURE_STRATEGIST in blue_roles
        assert AgentRole.DEVILS_ADVOCATE not in blue_roles

    def test_get_red_team_roles(self):
        """Test retrieval of red team roles."""
        red_roles = get_red_team_roles()
        assert AgentRole.DEVILS_ADVOCATE in red_roles
        assert AgentRole.COMPETITOR_SIMULATOR in red_roles
        assert AgentRole.EVALUATOR_SIMULATOR in red_roles
        assert AgentRole.RISK_ASSESSOR in red_roles
        assert AgentRole.STRATEGY_ARCHITECT not in red_roles

    def test_get_roles_by_category(self):
        """Test filtering roles by category."""
        orchestrators = get_roles_by_category(AgentCategory.ORCHESTRATOR)
        assert AgentRole.ARBITER in orchestrators
        assert len(orchestrators) == 1


# ============================================================================
# LLM Config Tests
# ============================================================================

class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def setup_method(self):
        """Set up known LLM config values before each test."""
        configure_llm_settings(
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            api_key_env_var="ANTHROPIC_API_KEY",
        )

    def test_default_config(self):
        """Test default LLM configuration values loaded from server config."""
        config = LLMConfig()
        assert config.model == "claude-haiku-4-5-20251001"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.provider == "anthropic"

    def test_custom_config(self):
        """Test that custom values passed to LLMConfig are preserved after __post_init__."""
        # Note: __post_init__ overrides provider/model/api_key_env_var from server config,
        # but temperature and max_tokens should retain custom values.
        config = LLMConfig(
            temperature=0.3,
            max_tokens=8192
        )
        # Provider and model come from server config
        assert config.model == "claude-haiku-4-5-20251001"
        assert config.provider == "anthropic"
        # Custom values are preserved
        assert config.temperature == 0.3
        assert config.max_tokens == 8192

    def test_serialization(self):
        """Test LLM config JSON serialization."""
        config = LLMConfig(temperature=0.5)
        json_str = config.to_json()
        restored = LLMConfig.from_json(json_str)
        assert restored.temperature == config.temperature
        assert restored.model == config.model


# ============================================================================
# Agent Config Tests
# ============================================================================

class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_name_from_role(self):
        """Test that name defaults to role value."""
        config = AgentConfig(role=AgentRole.STRATEGY_ARCHITECT)
        assert config.name == "Strategy Architect"

    def test_custom_name(self):
        """Test custom name override."""
        config = AgentConfig(
            role=AgentRole.STRATEGY_ARCHITECT,
            name="Custom Architect"
        )
        assert config.name == "Custom Architect"

    def test_category_property(self):
        """Test category derived from role."""
        config = AgentConfig(role=AgentRole.DEVILS_ADVOCATE)
        assert config.category == AgentCategory.RED
        assert config.is_red_team is True
        assert config.is_blue_team is False

    def test_with_llm_override(self):
        """Test creating config with LLM overrides."""
        config = AgentConfig(role=AgentRole.STRATEGY_ARCHITECT)
        new_config = config.with_llm_override(
            temperature=0.2,
            max_tokens=2048
        )

        # Original unchanged
        assert config.llm_config.temperature == 0.7

        # New config has overrides
        assert new_config.llm_config.temperature == 0.2
        assert new_config.llm_config.max_tokens == 2048
        assert new_config.role == config.role

    def test_serialization(self):
        """Test agent config JSON serialization."""
        config = AgentConfig(
            role=AgentRole.MARKET_ANALYST,
            enabled=True,
            priority=50,
            llm_config=LLMConfig(temperature=0.5)
        )
        json_str = config.to_json()
        restored = AgentConfig.from_json(json_str)

        assert restored.role == config.role
        assert restored.priority == config.priority
        assert restored.llm_config.temperature == config.llm_config.temperature

    def test_default_configs_exist(self):
        """Test that default configs exist for all roles."""
        for role in AgentRole:
            config = get_default_config(role)
            assert config.role == role
            assert config.llm_config is not None


# ============================================================================
# Concrete Agent Implementation for Testing
# ============================================================================

class MockBlueAgent(BlueTeamAgent):
    """Mock blue team agent for testing."""

    @property
    def role(self) -> AgentRole:
        return AgentRole.STRATEGY_ARCHITECT

    async def process(self, context: SwarmContext) -> AgentOutput:
        return self._create_output(content="Mock blue output")

    async def draft_section(self, context: SwarmContext, section_name: str) -> str:
        return f"Draft for {section_name}"

    async def revise_section(
        self,
        context: SwarmContext,
        section_name: str,
        critiques: List[Dict[str, Any]]
    ) -> str:
        return f"Revised {section_name} addressing {len(critiques)} critiques"


class MockRedAgent(RedTeamAgent):
    """Mock red team agent for testing."""

    @property
    def role(self) -> AgentRole:
        return AgentRole.DEVILS_ADVOCATE

    async def process(self, context: SwarmContext) -> AgentOutput:
        return self._create_output(
            content="Mock critique",
            critiques=[{"issue": "test critique"}]
        )

    async def critique_section(
        self,
        context: SwarmContext,
        section_name: str,
        section_content: str
    ) -> List[Dict[str, Any]]:
        return [{"section": section_name, "issue": "Mock critique"}]

    async def evaluate_response(
        self,
        context: SwarmContext,
        critique: Dict[str, Any],
        response: Dict[str, Any]
    ) -> bool:
        return True


class MockOrchestratorAgent(OrchestratorAgent):
    """Mock orchestrator agent for testing."""

    @property
    def role(self) -> AgentRole:
        return AgentRole.ARBITER

    async def process(self, context: SwarmContext) -> AgentOutput:
        return self._create_output(content="Mock orchestration")

    async def should_continue_debate(
        self,
        context: SwarmContext,
        current_round: int,
        max_rounds: int
    ) -> bool:
        return current_round < max_rounds

    async def synthesize_final_output(
        self,
        context: SwarmContext
    ) -> Dict[str, Any]:
        return {"final": "output"}


# ============================================================================
# Abstract Agent Tests
# ============================================================================

class TestAbstractAgent:
    """Tests for AbstractAgent base class."""

    @pytest.fixture
    def blue_agent(self) -> MockBlueAgent:
        """Create a mock blue agent."""
        config = AgentConfig(role=AgentRole.STRATEGY_ARCHITECT)
        return MockBlueAgent(config)

    @pytest.fixture
    def red_agent(self) -> MockRedAgent:
        """Create a mock red agent."""
        config = AgentConfig(role=AgentRole.DEVILS_ADVOCATE)
        return MockRedAgent(config)

    def test_agent_properties(self, blue_agent):
        """Test basic agent properties."""
        assert blue_agent.role == AgentRole.STRATEGY_ARCHITECT
        assert blue_agent.category == AgentCategory.BLUE
        assert blue_agent.name == "Strategy Architect"
        assert blue_agent.is_enabled is True

    def test_can_handle_all_types_by_default(self, blue_agent):
        """Test that agents handle all document types by default."""
        assert blue_agent.can_handle("Proposal Strategy") is True
        assert blue_agent.can_handle("Unknown Type") is True

    def test_can_handle_specific_types(self):
        """Test restricting agent to specific document types."""
        config = AgentConfig(
            role=AgentRole.STRATEGY_ARCHITECT,
            supported_document_types=["Proposal Strategy", "Capture Plan"]
        )
        agent = MockBlueAgent(config)

        assert agent.can_handle("Proposal Strategy") is True
        assert agent.can_handle("Capture Plan") is True
        assert agent.can_handle("SWOT Analysis") is False

    @pytest.mark.asyncio
    async def test_blue_agent_process(self, blue_agent):
        """Test blue agent processing."""
        context = SwarmContext()
        output = await blue_agent.process(context)

        assert output.success is True
        assert output.agent_role == AgentRole.STRATEGY_ARCHITECT
        assert "Mock blue output" in output.content

    @pytest.mark.asyncio
    async def test_red_agent_process(self, red_agent):
        """Test red agent processing."""
        context = SwarmContext()
        output = await red_agent.process(context)

        assert output.success is True
        assert output.agent_role == AgentRole.DEVILS_ADVOCATE
        assert len(output.critiques) == 1

    @pytest.mark.asyncio
    async def test_agent_initialize_cleanup(self, blue_agent):
        """Test agent initialization and cleanup."""
        assert blue_agent._initialized is False

        await blue_agent.initialize()
        assert blue_agent._initialized is True

        await blue_agent.cleanup()
        assert blue_agent._initialized is False

    def test_agent_stats(self, blue_agent):
        """Test agent statistics."""
        stats = blue_agent.get_stats()

        assert stats["role"] == "Strategy Architect"
        assert stats["category"] == "blue"
        assert stats["call_count"] == 0
        assert stats["is_enabled"] is True

    def test_validate_context(self):
        """Test context validation."""
        config = AgentConfig(
            role=AgentRole.STRATEGY_ARCHITECT,
            supported_document_types=["Proposal Strategy"]
        )
        agent = MockBlueAgent(config)

        # Valid context
        context = SwarmContext(document_type="Proposal Strategy")
        errors = agent.validate_context(context)
        assert len(errors) == 0

        # Invalid document type
        context = SwarmContext(document_type="SWOT Analysis")
        errors = agent.validate_context(context)
        assert len(errors) == 1


# ============================================================================
# Swarm Context Tests
# ============================================================================

class TestSwarmContext:
    """Tests for SwarmContext dataclass."""

    def test_default_context(self):
        """Test default context creation."""
        context = SwarmContext()
        assert context.round_number == 1
        assert context.round_type == "BlueBuild"
        assert len(context.pending_critiques) == 0

    def test_context_with_data(self):
        """Test context with populated data."""
        context = SwarmContext(
            document_type="Proposal Strategy",
            company_profile={"name": "Acme Corp"},
            section_drafts={"Executive Summary": "Initial draft..."},
            round_number=2,
            round_type="RedAttack"
        )

        assert context.document_type == "Proposal Strategy"
        assert context.company_profile["name"] == "Acme Corp"
        assert "Executive Summary" in context.section_drafts

    def test_get_section_content(self):
        """Test retrieving section content."""
        context = SwarmContext(
            section_drafts={
                "Executive Summary": "Summary content",
                "Win Themes": "Theme content"
            }
        )

        assert context.get_section_content("Executive Summary") == "Summary content"
        assert context.get_section_content("Unknown") is None

    def test_get_critiques_for_section(self):
        """Test filtering critiques by section."""
        context = SwarmContext(
            pending_critiques=[
                {"target_section": "Executive Summary", "issue": "Issue 1"},
                {"target_section": "Win Themes", "issue": "Issue 2"},
                {"target_section": "Executive Summary", "issue": "Issue 3"},
            ]
        )

        summary_critiques = context.get_critiques_for_section("Executive Summary")
        assert len(summary_critiques) == 2

        theme_critiques = context.get_critiques_for_section("Win Themes")
        assert len(theme_critiques) == 1


# ============================================================================
# Agent Output Tests
# ============================================================================

class TestAgentOutput:
    """Tests for AgentOutput dataclass."""

    def test_successful_output(self):
        """Test creating successful output."""
        output = AgentOutput(
            agent_role=AgentRole.STRATEGY_ARCHITECT,
            content="Generated content",
            success=True
        )

        assert output.success is True
        assert output.error_message is None
        assert "Generated content" in output.content

    def test_failed_output(self):
        """Test creating failed output."""
        output = AgentOutput(
            agent_role=AgentRole.STRATEGY_ARCHITECT,
            success=False,
            error_message="Processing failed"
        )

        assert output.success is False
        assert output.error_message == "Processing failed"

    def test_output_serialization(self):
        """Test output serialization."""
        output = AgentOutput(
            agent_role=AgentRole.MARKET_ANALYST,
            content="Analysis results",
            sections={"Overview": "Market overview"},
            token_usage={"input": 100, "output": 200}
        )

        data = output.to_dict()
        assert data["agent_role"] == "Market Analyst"
        assert data["sections"]["Overview"] == "Market overview"


# ============================================================================
# Agent Registry Tests
# ============================================================================

class TestAgentRegistry:
    """Tests for AgentRegistry."""

    @pytest.fixture
    def registry(self) -> AgentRegistry:
        """Create a fresh registry for each test."""
        return AgentRegistry()

    def test_register_agent(self, registry):
        """Test registering an agent class."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        assert registry.is_registered(AgentRole.STRATEGY_ARCHITECT) is True

    def test_register_duplicate_fails(self, registry):
        """Test that duplicate registration fails without replace flag."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)

        with pytest.raises(AgentRegistrationError):
            registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)

    def test_register_duplicate_with_replace(self, registry):
        """Test that duplicate registration succeeds with replace flag."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent, replace=True)
        assert registry.is_registered(AgentRole.STRATEGY_ARCHITECT) is True

    def test_unregister(self, registry):
        """Test unregistering an agent."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        removed = registry.unregister(AgentRole.STRATEGY_ARCHITECT)

        assert removed is True
        assert registry.is_registered(AgentRole.STRATEGY_ARCHITECT) is False

    def test_create_agent(self, registry):
        """Test creating an agent instance."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        agent = registry.create(AgentRole.STRATEGY_ARCHITECT)

        assert isinstance(agent, MockBlueAgent)
        assert agent.role == AgentRole.STRATEGY_ARCHITECT

    def test_create_with_custom_config(self, registry):
        """Test creating an agent with custom configuration."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)

        custom_config = AgentConfig(
            role=AgentRole.STRATEGY_ARCHITECT,
            name="Custom Architect",
            priority=999
        )
        agent = registry.create(AgentRole.STRATEGY_ARCHITECT, config=custom_config)

        assert agent.name == "Custom Architect"
        assert agent.priority == 999

    def test_create_unregistered_fails(self, registry):
        """Test that creating an unregistered agent fails."""
        with pytest.raises(AgentInstantiationError):
            registry.create(AgentRole.STRATEGY_ARCHITECT)

    def test_create_with_cache(self, registry):
        """Test caching agent instances."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)

        agent1 = registry.create(AgentRole.STRATEGY_ARCHITECT, cache=True)
        agent2 = registry.create(AgentRole.STRATEGY_ARCHITECT, cache=True)

        assert agent1 is agent2

    def test_get_registered_roles(self, registry):
        """Test getting all registered roles."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        registry.register(AgentRole.DEVILS_ADVOCATE, MockRedAgent)

        roles = registry.get_registered_roles()
        assert AgentRole.STRATEGY_ARCHITECT in roles
        assert AgentRole.DEVILS_ADVOCATE in roles

    def test_get_registered_roles_by_category(self, registry):
        """Test filtering registered roles by category."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        registry.register(AgentRole.DEVILS_ADVOCATE, MockRedAgent)

        blue_roles = registry.get_registered_roles_by_category(AgentCategory.BLUE)
        assert AgentRole.STRATEGY_ARCHITECT in blue_roles
        assert AgentRole.DEVILS_ADVOCATE not in blue_roles

    def test_create_all(self, registry):
        """Test creating all registered agents."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        registry.register(AgentRole.DEVILS_ADVOCATE, MockRedAgent)

        agents = registry.create_all()
        assert len(agents) == 2

    def test_create_blue_team(self, registry):
        """Test creating only blue team agents."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        registry.register(AgentRole.DEVILS_ADVOCATE, MockRedAgent)

        agents = registry.create_blue_team()
        assert len(agents) == 1
        assert agents[0].category == AgentCategory.BLUE

    def test_create_red_team(self, registry):
        """Test creating only red team agents."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)
        registry.register(AgentRole.DEVILS_ADVOCATE, MockRedAgent)

        agents = registry.create_red_team()
        assert len(agents) == 1
        assert agents[0].category == AgentCategory.RED

    def test_config_override(self, registry):
        """Test configuration overrides."""
        registry.register(AgentRole.STRATEGY_ARCHITECT, MockBlueAgent)

        override = AgentConfig(
            role=AgentRole.STRATEGY_ARCHITECT,
            priority=1000
        )
        registry.set_config_override(AgentRole.STRATEGY_ARCHITECT, override)

        agent = registry.create(AgentRole.STRATEGY_ARCHITECT)
        assert agent.priority == 1000

    def test_register_factory(self, registry):
        """Test registering a factory function."""
        def factory(config: AgentConfig) -> MockBlueAgent:
            config.custom_params["factory_created"] = True
            return MockBlueAgent(config)

        registry.register_factory(AgentRole.STRATEGY_ARCHITECT, factory)
        agent = registry.create(AgentRole.STRATEGY_ARCHITECT)

        assert isinstance(agent, MockBlueAgent)
        assert agent.config.custom_params.get("factory_created") is True


class TestAgentDecorator:
    """Tests for the @agent decorator."""

    def test_decorator_registers_agent(self):
        """Test that decorator registers the agent class."""
        registry = get_registry()

        # Clear any existing registration
        registry.unregister(AgentRole.ARBITER)

        @agent(AgentRole.ARBITER)
        class TestOrchestratorAgent(MockOrchestratorAgent):
            pass

        assert registry.is_registered(AgentRole.ARBITER) is True

        # Cleanup
        registry.unregister(AgentRole.ARBITER)


# ============================================================================
# Integration Tests
# ============================================================================

class TestAgentIntegration:
    """Integration tests for the agent system."""

    @pytest.mark.asyncio
    async def test_blue_red_agent_interaction(self):
        """Test interaction between blue and red agents."""
        # Create agents
        blue_config = AgentConfig(role=AgentRole.STRATEGY_ARCHITECT)
        red_config = AgentConfig(role=AgentRole.DEVILS_ADVOCATE)

        blue_agent = MockBlueAgent(blue_config)
        red_agent = MockRedAgent(red_config)

        # Blue agent creates draft
        context = SwarmContext(
            document_type="Proposal Strategy",
            round_type="BlueBuild"
        )

        blue_output = await blue_agent.process(context)
        assert blue_output.success is True

        # Update context for red team
        context.round_type = "RedAttack"
        context.section_drafts = {"Draft": blue_output.content}

        # Red agent critiques
        red_output = await red_agent.process(context)
        assert red_output.success is True
        assert len(red_output.critiques) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_debate_control(self):
        """Test orchestrator controlling debate flow."""
        config = AgentConfig(role=AgentRole.ARBITER)
        orchestrator = MockOrchestratorAgent(config)

        context = SwarmContext()

        # Should continue for early rounds
        should_continue = await orchestrator.should_continue_debate(
            context, current_round=1, max_rounds=3
        )
        assert should_continue is True

        # Should stop at max rounds
        should_continue = await orchestrator.should_continue_debate(
            context, current_round=3, max_rounds=3
        )
        assert should_continue is False

        # Synthesize final output
        final = await orchestrator.synthesize_final_output(context)
        assert "final" in final


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
