"""
Agent Types

Defines the roles and categories for agents in the adversarial swarm.
"""

from enum import Enum, auto
from typing import Set


class AgentCategory(str, Enum):
    """
    Categories of agents in the adversarial swarm.

    Categories determine the agent's primary function in the debate workflow.
    """

    BLUE = "blue"  # Constructive agents that build and defend
    RED = "red"  # Adversarial agents that challenge and critique
    SPECIALIST = "specialist"  # Domain-specific support agents
    ORCHESTRATOR = "orchestrator"  # Workflow coordination agents


class AgentRole(str, Enum):
    """
    Specific roles for agents in the swarm.

    Each role corresponds to a specific agent implementation with
    defined responsibilities and behaviors.
    """

    # Blue Team Agents (Constructive)
    STRATEGY_ARCHITECT = "Strategy Architect"
    MARKET_ANALYST = "Market Analyst"
    COMPLIANCE_NAVIGATOR = "Compliance Navigator"
    CAPTURE_STRATEGIST = "Capture Strategist"

    # Red Team Agents (Adversarial)
    DEVILS_ADVOCATE = "Devil's Advocate"
    COMPETITOR_SIMULATOR = "Competitor Simulator"
    EVALUATOR_SIMULATOR = "Evaluator Simulator"
    RISK_ASSESSOR = "Risk Assessor"

    # Orchestration
    ARBITER = "Arbiter"

    @property
    def category(self) -> AgentCategory:
        """Get the category for this role."""
        return ROLE_CATEGORIES.get(self, AgentCategory.SPECIALIST)

    @property
    def is_blue_team(self) -> bool:
        """Check if this role is on the blue team."""
        return self.category == AgentCategory.BLUE

    @property
    def is_red_team(self) -> bool:
        """Check if this role is on the red team."""
        return self.category == AgentCategory.RED

    @property
    def is_orchestrator(self) -> bool:
        """Check if this role is an orchestrator."""
        return self.category == AgentCategory.ORCHESTRATOR


# Mapping of roles to their categories
ROLE_CATEGORIES: dict[AgentRole, AgentCategory] = {
    # Blue Team
    AgentRole.STRATEGY_ARCHITECT: AgentCategory.BLUE,
    AgentRole.MARKET_ANALYST: AgentCategory.BLUE,
    AgentRole.COMPLIANCE_NAVIGATOR: AgentCategory.BLUE,
    AgentRole.CAPTURE_STRATEGIST: AgentCategory.BLUE,
    # Red Team
    AgentRole.DEVILS_ADVOCATE: AgentCategory.RED,
    AgentRole.COMPETITOR_SIMULATOR: AgentCategory.RED,
    AgentRole.EVALUATOR_SIMULATOR: AgentCategory.RED,
    AgentRole.RISK_ASSESSOR: AgentCategory.RED,
    # Orchestration
    AgentRole.ARBITER: AgentCategory.ORCHESTRATOR,
}


def get_blue_team_roles() -> Set[AgentRole]:
    """Get all blue team agent roles."""
    return {role for role, cat in ROLE_CATEGORIES.items() if cat == AgentCategory.BLUE}


def get_red_team_roles() -> Set[AgentRole]:
    """Get all red team agent roles."""
    return {role for role, cat in ROLE_CATEGORIES.items() if cat == AgentCategory.RED}


def get_roles_by_category(category: AgentCategory) -> Set[AgentRole]:
    """Get all roles in a given category."""
    return {role for role, cat in ROLE_CATEGORIES.items() if cat == category}
