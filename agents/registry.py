"""
Agent Registry

Provides agent discovery, registration, and instantiation.
Implements the registry pattern for managing agent types.
"""

from typing import Dict, Type, Optional, List, Set, Callable, Any
import logging

from .types import AgentRole, AgentCategory, get_roles_by_category
from .config import AgentConfig, get_default_config
from .base import AbstractAgent, BlueTeamAgent, RedTeamAgent, OrchestratorAgent


logger = logging.getLogger(__name__)


class AgentRegistrationError(Exception):
    """Raised when there's an error registering an agent."""
    pass


class AgentInstantiationError(Exception):
    """Raised when there's an error instantiating an agent."""
    pass


class AgentRegistry:
    """
    Registry for agent types and instances.

    Provides methods to register agent classes, discover available agents,
    and instantiate agents with proper configuration.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._agent_classes: Dict[AgentRole, Type[AbstractAgent]] = {}
        self._agent_factories: Dict[AgentRole, Callable[[AgentConfig], AbstractAgent]] = {}
        self._instances: Dict[str, AbstractAgent] = {}
        self._config_overrides: Dict[AgentRole, AgentConfig] = {}

    def register(
        self,
        role: AgentRole,
        agent_class: Type[AbstractAgent],
        replace: bool = False
    ) -> None:
        """
        Register an agent class for a role.

        Args:
            role: The agent role to register
            agent_class: The agent class to associate with this role
            replace: If True, replace existing registration

        Raises:
            AgentRegistrationError: If role is already registered and replace=False
        """
        if role in self._agent_classes and not replace:
            raise AgentRegistrationError(
                f"Role {role.value} is already registered. Use replace=True to override."
            )

        # Validate that the class is a proper agent
        if not issubclass(agent_class, AbstractAgent):
            raise AgentRegistrationError(
                f"Agent class must inherit from AbstractAgent, got {agent_class}"
            )

        self._agent_classes[role] = agent_class
        logger.debug(f"Registered agent class {agent_class.__name__} for role {role.value}")

    def register_factory(
        self,
        role: AgentRole,
        factory: Callable[[AgentConfig], AbstractAgent],
        replace: bool = False
    ) -> None:
        """
        Register a factory function for creating agents.

        Useful when agent instantiation requires complex setup.

        Args:
            role: The agent role
            factory: Callable that takes AgentConfig and returns AbstractAgent
            replace: If True, replace existing factory

        Raises:
            AgentRegistrationError: If role already has a factory and replace=False
        """
        if role in self._agent_factories and not replace:
            raise AgentRegistrationError(
                f"Role {role.value} already has a factory. Use replace=True to override."
            )

        self._agent_factories[role] = factory
        logger.debug(f"Registered factory for role {role.value}")

    def unregister(self, role: AgentRole) -> bool:
        """
        Unregister an agent role.

        Args:
            role: The role to unregister

        Returns:
            True if the role was registered and removed, False otherwise
        """
        removed = False
        if role in self._agent_classes:
            del self._agent_classes[role]
            removed = True
        if role in self._agent_factories:
            del self._agent_factories[role]
            removed = True
        return removed

    def is_registered(self, role: AgentRole) -> bool:
        """Check if a role is registered."""
        return role in self._agent_classes or role in self._agent_factories

    def get_registered_roles(self) -> Set[AgentRole]:
        """Get all registered roles."""
        return set(self._agent_classes.keys()) | set(self._agent_factories.keys())

    def get_registered_roles_by_category(
        self,
        category: AgentCategory
    ) -> Set[AgentRole]:
        """Get registered roles filtered by category."""
        registered = self.get_registered_roles()
        category_roles = get_roles_by_category(category)
        return registered & category_roles

    def set_config_override(self, role: AgentRole, config: AgentConfig) -> None:
        """
        Set a configuration override for a role.

        This config will be used instead of the default when creating agents.

        Args:
            role: The role to override
            config: The configuration to use
        """
        self._config_overrides[role] = config

    def clear_config_override(self, role: AgentRole) -> None:
        """Clear a configuration override."""
        self._config_overrides.pop(role, None)

    def get_config(self, role: AgentRole) -> AgentConfig:
        """
        Get the effective configuration for a role.

        Returns the override if set, otherwise the default config.

        Args:
            role: The agent role

        Returns:
            The effective AgentConfig
        """
        if role in self._config_overrides:
            return self._config_overrides[role]
        return get_default_config(role)

    def create(
        self,
        role: AgentRole,
        config: Optional[AgentConfig] = None,
        cache: bool = False
    ) -> AbstractAgent:
        """
        Create an agent instance for a role.

        Args:
            role: The agent role to create
            config: Optional custom configuration (uses default/override if not provided)
            cache: If True, cache the instance for reuse

        Returns:
            An instance of the agent

        Raises:
            AgentInstantiationError: If the role is not registered or creation fails
        """
        # Check if we have a cached instance
        cache_key = f"{role.value}_{id(config) if config else 'default'}"
        if cache and cache_key in self._instances:
            return self._instances[cache_key]

        # Get the effective configuration
        effective_config = config or self.get_config(role)

        # Try factory first
        if role in self._agent_factories:
            try:
                agent = self._agent_factories[role](effective_config)
                if cache:
                    self._instances[cache_key] = agent
                return agent
            except Exception as e:
                raise AgentInstantiationError(
                    f"Factory failed for role {role.value}: {e}"
                ) from e

        # Fall back to class instantiation
        if role in self._agent_classes:
            try:
                agent = self._agent_classes[role](effective_config)
                if cache:
                    self._instances[cache_key] = agent
                return agent
            except Exception as e:
                raise AgentInstantiationError(
                    f"Failed to instantiate {role.value}: {e}"
                ) from e

        raise AgentInstantiationError(
            f"Role {role.value} is not registered. "
            f"Available roles: {[r.value for r in self.get_registered_roles()]}"
        )

    def create_all(
        self,
        category: Optional[AgentCategory] = None,
        enabled_only: bool = True
    ) -> List[AbstractAgent]:
        """
        Create instances of all registered agents.

        Args:
            category: If provided, only create agents in this category
            enabled_only: If True, skip agents that are not enabled

        Returns:
            List of agent instances, sorted by priority
        """
        agents = []

        roles = self.get_registered_roles()
        if category:
            roles = roles & get_roles_by_category(category)

        for role in roles:
            try:
                agent = self.create(role)
                if enabled_only and not agent.is_enabled:
                    continue
                agents.append(agent)
            except AgentInstantiationError as e:
                logger.warning(f"Skipping {role.value}: {e}")

        # Sort by priority (higher first)
        agents.sort(key=lambda a: a.priority, reverse=True)
        return agents

    def create_blue_team(self, enabled_only: bool = True) -> List[AbstractAgent]:
        """Create all blue team agents."""
        return self.create_all(category=AgentCategory.BLUE, enabled_only=enabled_only)

    def create_red_team(self, enabled_only: bool = True) -> List[AbstractAgent]:
        """Create all red team agents."""
        return self.create_all(category=AgentCategory.RED, enabled_only=enabled_only)

    def clear_cache(self) -> None:
        """Clear all cached agent instances."""
        self._instances.clear()

    def get_cached_instance(self, role: AgentRole) -> Optional[AbstractAgent]:
        """Get a cached instance if available."""
        for key, agent in self._instances.items():
            if agent.role == role:
                return agent
        return None

    def __len__(self) -> int:
        """Get the number of registered roles."""
        return len(self.get_registered_roles())

    def __contains__(self, role: AgentRole) -> bool:
        """Check if a role is registered."""
        return self.is_registered(role)


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry.

    Creates the registry on first access.

    Returns:
        The global AgentRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def register_agent(
    role: AgentRole,
    agent_class: Type[AbstractAgent],
    replace: bool = False
) -> None:
    """
    Register an agent class with the global registry.

    Args:
        role: The agent role
        agent_class: The agent class
        replace: If True, replace existing registration
    """
    get_registry().register(role, agent_class, replace=replace)


def create_agent(
    role: AgentRole,
    config: Optional[AgentConfig] = None
) -> AbstractAgent:
    """
    Create an agent using the global registry.

    Args:
        role: The agent role
        config: Optional custom configuration

    Returns:
        An agent instance
    """
    return get_registry().create(role, config=config)


def agent(role: AgentRole, replace: bool = False):
    """
    Decorator to register an agent class.

    Usage:
        @agent(AgentRole.STRATEGY_ARCHITECT)
        class StrategyArchitectAgent(BlueTeamAgent):
            ...

    Args:
        role: The role to register
        replace: If True, replace existing registration

    Returns:
        Decorator function
    """
    def decorator(cls: Type[AbstractAgent]) -> Type[AbstractAgent]:
        register_agent(role, cls, replace=replace)
        return cls
    return decorator
