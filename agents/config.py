"""
Agent Configuration

Defines configuration structures for agent instantiation and behavior.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal
import json
import os

from .types import AgentRole, AgentCategory


# Module-level cache for server LLM settings
_server_llm_settings: Optional[dict] = None


def _load_server_llm_settings() -> dict:
    """
    Load LLM settings from server config at startup.

    Falls back to environment variables if server config is not available.
    """
    global _server_llm_settings
    if _server_llm_settings is not None:
        return _server_llm_settings

    try:
        from server.config import get_llm_settings
        _server_llm_settings = get_llm_settings()
    except ImportError:
        # Server config not available, use environment variables as fallback
        env_provider = os.getenv("LLM_PROVIDER", "anthropic")
        env_model = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
        api_key_env_var = "GROQ_API_KEY" if env_provider == "groq" else "ANTHROPIC_API_KEY"
        _server_llm_settings = {
            "provider": env_provider,
            "model": env_model,
            "api_key_env_var": api_key_env_var,
        }

    return _server_llm_settings


def configure_llm_settings(provider: str, model: str, api_key_env_var: str) -> None:
    """
    Inject LLM settings programmatically.

    This allows the orchestrator to configure agent LLM settings at runtime.
    """
    global _server_llm_settings
    _server_llm_settings = {
        "provider": provider,
        "model": model,
        "api_key_env_var": api_key_env_var,
    }


# Provider type
LLMProvider = Literal["anthropic", "groq"]


@dataclass
class LLMConfig:
    """
    Configuration for the LLM backend used by an agent.

    Supports various LLM parameters for fine-tuning agent behavior.
    """

    # Provider selection (loaded from environment or settings)
    provider: LLMProvider = "anthropic"
    model: str = "claude-haiku-4-5-20251001"
    temperature: float = 0.7
    max_tokens: int = 1500
    top_p: float = 1.0
    stop_sequences: List[str] = field(default_factory=list)

    # API configuration
    api_key_env_var: str = "ANTHROPIC_API_KEY"
    base_url: Optional[str] = None
    timeout: int = 120  # seconds

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0

    def __post_init__(self):
        """Load provider and model from server config at startup."""
        settings = _load_server_llm_settings()

        self.provider = settings["provider"]
        self.model = settings["model"]
        self.api_key_env_var = settings["api_key_env_var"]

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop_sequences": self.stop_sequences,
            "api_key_env_var": self.api_key_env_var,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LLMConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "LLMConfig":
        return cls.from_dict(json.loads(json_str))


@dataclass
class AgentConfig:
    """
    Configuration for an agent instance.

    Controls agent behavior, LLM settings, and operational parameters.
    """

    # Identity
    role: AgentRole = AgentRole.STRATEGY_ARCHITECT
    name: Optional[str] = None  # Custom name override
    description: Optional[str] = None  # Custom description

    # LLM Configuration
    llm_config: LLMConfig = field(default_factory=LLMConfig)

    # Behavioral Configuration
    enabled: bool = True
    priority: int = 0  # Higher priority agents run first within their phase

    # Prompt Configuration
    system_prompt_template: Optional[str] = None
    additional_instructions: Optional[str] = None

    # Operational Limits
    max_output_tokens: int = 1500
    max_input_context: int = 100000  # tokens
    max_iterations: int = 5  # for iterative refinement

    # Critique/Response Configuration (for red/blue team agents)
    max_critiques_per_section: int = 3
    min_critique_severity: Optional[str] = None  # "Minor", "Major", "Critical"

    # Document Type Handling
    supported_document_types: List[str] = field(default_factory=list)  # Empty = all types

    # Custom Parameters
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default name from role if not provided."""
        if self.name is None:
            self.name = self.role.value

    @property
    def category(self) -> AgentCategory:
        """Get the agent's category from its role."""
        return self.role.category

    @property
    def is_blue_team(self) -> bool:
        """Check if this agent is on the blue team."""
        return self.role.is_blue_team

    @property
    def is_red_team(self) -> bool:
        """Check if this agent is on the red team."""
        return self.role.is_red_team

    def with_llm_override(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> "AgentConfig":
        """
        Create a new config with LLM parameter overrides.

        Returns a new AgentConfig instance with the specified overrides.
        """
        new_llm_config = LLMConfig(
            provider=self.llm_config.provider,
            model=model or self.llm_config.model,
            temperature=temperature if temperature is not None else self.llm_config.temperature,
            max_tokens=max_tokens or self.llm_config.max_tokens,
            top_p=self.llm_config.top_p,
            stop_sequences=self.llm_config.stop_sequences.copy(),
            api_key_env_var=self.llm_config.api_key_env_var,
            base_url=self.llm_config.base_url,
            timeout=self.llm_config.timeout,
            max_retries=self.llm_config.max_retries,
            retry_delay=self.llm_config.retry_delay,
        )

        return AgentConfig(
            role=self.role,
            name=self.name,
            description=self.description,
            llm_config=new_llm_config,
            enabled=self.enabled,
            priority=self.priority,
            system_prompt_template=self.system_prompt_template,
            additional_instructions=self.additional_instructions,
            max_output_tokens=self.max_output_tokens,
            max_input_context=self.max_input_context,
            max_iterations=self.max_iterations,
            max_critiques_per_section=self.max_critiques_per_section,
            min_critique_severity=self.min_critique_severity,
            supported_document_types=self.supported_document_types.copy(),
            custom_params=self.custom_params.copy(),
        )

    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "name": self.name,
            "description": self.description,
            "llm_config": self.llm_config.to_dict(),
            "enabled": self.enabled,
            "priority": self.priority,
            "system_prompt_template": self.system_prompt_template,
            "additional_instructions": self.additional_instructions,
            "max_output_tokens": self.max_output_tokens,
            "max_input_context": self.max_input_context,
            "max_iterations": self.max_iterations,
            "max_critiques_per_section": self.max_critiques_per_section,
            "min_critique_severity": self.min_critique_severity,
            "supported_document_types": self.supported_document_types,
            "custom_params": self.custom_params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        llm_config = LLMConfig.from_dict(data.get("llm_config", {}))
        return cls(
            role=AgentRole(data.get("role", "Strategy Architect")),
            name=data.get("name"),
            description=data.get("description"),
            llm_config=llm_config,
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            system_prompt_template=data.get("system_prompt_template"),
            additional_instructions=data.get("additional_instructions"),
            max_output_tokens=data.get("max_output_tokens", 4096),
            max_input_context=data.get("max_input_context", 100000),
            max_iterations=data.get("max_iterations", 5),
            max_critiques_per_section=data.get("max_critiques_per_section", 3),
            min_critique_severity=data.get("min_critique_severity"),
            supported_document_types=data.get("supported_document_types", []),
            custom_params=data.get("custom_params", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentConfig":
        return cls.from_dict(json.loads(json_str))


# Default configurations for each agent role
DEFAULT_AGENT_CONFIGS: Dict[AgentRole, AgentConfig] = {
    AgentRole.STRATEGY_ARCHITECT: AgentConfig(
        role=AgentRole.STRATEGY_ARCHITECT,
        description="Primary document drafter; synthesizes inputs into strategic narratives.",
        llm_config=LLMConfig(temperature=0.7, max_tokens=1500),
        priority=100,  # Highest priority in blue team
    ),
    AgentRole.MARKET_ANALYST: AgentConfig(
        role=AgentRole.MARKET_ANALYST,
        description="Government market intelligence and trend analysis.",
        llm_config=LLMConfig(temperature=0.5, max_tokens=1500),
        priority=80,
    ),
    AgentRole.COMPLIANCE_NAVIGATOR: AgentConfig(
        role=AgentRole.COMPLIANCE_NAVIGATOR,
        description="Regulatory and eligibility expertise.",
        llm_config=LLMConfig(temperature=0.3, max_tokens=1500),
        priority=90,
    ),
    AgentRole.CAPTURE_STRATEGIST: AgentConfig(
        role=AgentRole.CAPTURE_STRATEGIST,
        description="Win strategy and competitive positioning.",
        llm_config=LLMConfig(temperature=0.6, max_tokens=1500),
        priority=85,
    ),
    AgentRole.DEVILS_ADVOCATE: AgentConfig(
        role=AgentRole.DEVILS_ADVOCATE,
        description="Systematic contrarian challenge to surface logical flaws.",
        llm_config=LLMConfig(temperature=0.8, max_tokens=1500),
        priority=100,  # Highest priority in red team
    ),
    AgentRole.COMPETITOR_SIMULATOR: AgentConfig(
        role=AgentRole.COMPETITOR_SIMULATOR,
        description="Role-play likely competitors to expose vulnerabilities.",
        llm_config=LLMConfig(temperature=0.8, max_tokens=1500),
        priority=80,
    ),
    AgentRole.EVALUATOR_SIMULATOR: AgentConfig(
        role=AgentRole.EVALUATOR_SIMULATOR,
        description="Simulate government Source Selection Evaluation Board perspective.",
        llm_config=LLMConfig(temperature=0.5, max_tokens=1500),
        priority=90,
    ),
    AgentRole.RISK_ASSESSOR: AgentConfig(
        role=AgentRole.RISK_ASSESSOR,
        description="Identify failure modes and stress-test assumptions.",
        llm_config=LLMConfig(temperature=0.6, max_tokens=1500),
        priority=85,
    ),
    AgentRole.ARBITER: AgentConfig(
        role=AgentRole.ARBITER,
        description="Orchestrate the full adversarial workflow and synthesize final output.",
        llm_config=LLMConfig(temperature=0.4, max_tokens=1500),
        priority=100,
    ),
}


def get_default_config(role: AgentRole) -> AgentConfig:
    """
    Get the default configuration for an agent role.

    Args:
        role: The agent role

    Returns:
        A copy of the default AgentConfig for that role
    """
    if role in DEFAULT_AGENT_CONFIGS:
        config = DEFAULT_AGENT_CONFIGS[role]
        # Return a copy to prevent mutation of defaults
        return AgentConfig.from_dict(config.to_dict())
    else:
        return AgentConfig(role=role)
