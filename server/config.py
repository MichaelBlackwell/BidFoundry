"""Server configuration using pydantic-settings."""

from typing import Literal
from pydantic_settings import BaseSettings


# Valid models for each provider
# Claude 4.5 models - https://docs.anthropic.com/en/docs/about-claude/models
ANTHROPIC_MODELS = [
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-5-20251101",
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-groq-70b-8192-tool-use-preview",
    "llama3-groq-8b-8192-tool-use-preview",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    # LLM Configuration
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None

    # LLM Provider Selection
    llm_provider: Literal["anthropic", "groq"] = "anthropic"
    llm_model: str = "claude-haiku-4-5-20251001"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/swarm.db"

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100

    # Generation
    max_concurrent_generations: int = 5
    generation_timeout_seconds: int = 600

    # Export
    export_temp_dir: str = "./data/exports"
    max_export_size_mb: int = 50

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()


def get_llm_settings() -> dict:
    """
    Export LLM settings for use by the agent system.

    Returns a dictionary with provider, model, and API key env var.
    """
    api_key_env_var = (
        "GROQ_API_KEY" if settings.llm_provider == "groq" else "ANTHROPIC_API_KEY"
    )
    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "api_key_env_var": api_key_env_var,
    }
