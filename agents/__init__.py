"""
Agents Package

This package contains the agent base classes, types, configuration,
and registry for the adversarial agentic swarm.
"""

from .types import (
    AgentRole,
    AgentCategory,
    ROLE_CATEGORIES,
    get_blue_team_roles,
    get_red_team_roles,
    get_roles_by_category,
)
from .config import (
    LLMConfig,
    AgentConfig,
    DEFAULT_AGENT_CONFIGS,
    get_default_config,
)
from .base import (
    AbstractAgent,
    BlueTeamAgent,
    RedTeamAgent,
    OrchestratorAgent,
    AgentOutput,
    SwarmContext,
)
from .registry import (
    AgentRegistry,
    AgentRegistrationError,
    AgentInstantiationError,
    get_registry,
    register_agent,
    create_agent,
    agent,
)
from .registration import register_all_agents, ensure_agents_registered

# Blue Team Agents
from .blue import StrategyArchitectAgent

# Orchestrator Agents
from .orchestrator import (
    ArbiterAgent,
    DocumentRequest,
    FinalOutput,
    DocumentWorkflow,
    WorkflowConfig,
    ConsensusDetector,
    ConsensusResult,
    DocumentSynthesizer,
)

__all__ = [
    # Types
    "AgentRole",
    "AgentCategory",
    "ROLE_CATEGORIES",
    "get_blue_team_roles",
    "get_red_team_roles",
    "get_roles_by_category",
    # Config
    "LLMConfig",
    "AgentConfig",
    "DEFAULT_AGENT_CONFIGS",
    "get_default_config",
    # Base Classes
    "AbstractAgent",
    "BlueTeamAgent",
    "RedTeamAgent",
    "OrchestratorAgent",
    "AgentOutput",
    "SwarmContext",
    # Registry
    "AgentRegistry",
    "AgentRegistrationError",
    "AgentInstantiationError",
    "get_registry",
    "register_agent",
    "create_agent",
    "agent",
    # Registration
    "register_all_agents",
    "ensure_agents_registered",
    # Blue Team Agents
    "StrategyArchitectAgent",
    # Orchestrator Agents
    "ArbiterAgent",
    "DocumentRequest",
    "FinalOutput",
    "DocumentWorkflow",
    "WorkflowConfig",
    "ConsensusDetector",
    "ConsensusResult",
    "DocumentSynthesizer",
]
