"""LLM Settings API endpoints."""

import os
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from server.config import settings, ANTHROPIC_MODELS, GROQ_MODELS


router = APIRouter()


class LLMSettingsResponse(BaseModel):
    """Response model for LLM settings."""
    provider: Literal["anthropic", "groq"]
    model: str
    available_providers: list[dict]
    anthropic_configured: bool
    groq_configured: bool


class LLMSettingsUpdate(BaseModel):
    """Request model for updating LLM settings."""
    provider: Literal["anthropic", "groq"]
    model: str


class ModelsResponse(BaseModel):
    """Response model for available models."""
    anthropic: list[str]
    groq: list[str]


@router.get("", response_model=LLMSettingsResponse)
async def get_llm_settings() -> LLMSettingsResponse:
    """Get current LLM settings and available options."""
    # Check which API keys are configured
    anthropic_configured = bool(os.getenv("ANTHROPIC_API_KEY"))
    groq_configured = bool(os.getenv("GROQ_API_KEY"))

    # Get current provider and model from environment or defaults
    current_provider = os.getenv("LLM_PROVIDER", settings.llm_provider)
    current_model = os.getenv("LLM_MODEL", settings.llm_model)

    available_providers = [
        {
            "id": "anthropic",
            "name": "Anthropic (Claude)",
            "configured": anthropic_configured,
            "models": ANTHROPIC_MODELS,
        },
        {
            "id": "groq",
            "name": "Groq",
            "configured": groq_configured,
            "models": GROQ_MODELS,
        },
    ]

    return LLMSettingsResponse(
        provider=current_provider,
        model=current_model,
        available_providers=available_providers,
        anthropic_configured=anthropic_configured,
        groq_configured=groq_configured,
    )


@router.put("", response_model=LLMSettingsResponse)
async def update_llm_settings(data: LLMSettingsUpdate) -> LLMSettingsResponse:
    """
    Update LLM settings.

    Note: This updates the environment variables for the current session.
    For persistent changes, update the .env file.
    """
    # Validate provider
    if data.provider not in ("anthropic", "groq"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PROVIDER",
                "message": f"Invalid provider: {data.provider}. Must be 'anthropic' or 'groq'.",
            },
        )

    # Validate model for the selected provider
    valid_models = ANTHROPIC_MODELS if data.provider == "anthropic" else GROQ_MODELS
    if data.model not in valid_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_MODEL",
                "message": f"Invalid model '{data.model}' for provider '{data.provider}'.",
                "valid_models": valid_models,
            },
        )

    # Check if API key is configured for the selected provider
    api_key_var = "ANTHROPIC_API_KEY" if data.provider == "anthropic" else "GROQ_API_KEY"
    if not os.getenv(api_key_var):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "API_KEY_NOT_CONFIGURED",
                "message": f"API key not configured for provider '{data.provider}'. Set {api_key_var} in your .env file.",
            },
        )

    # Update environment variables (session-level)
    os.environ["LLM_PROVIDER"] = data.provider
    os.environ["LLM_MODEL"] = data.model

    # Return updated settings
    return await get_llm_settings()


@router.get("/models", response_model=ModelsResponse)
async def get_available_models() -> ModelsResponse:
    """Get list of available models for each provider."""
    return ModelsResponse(
        anthropic=ANTHROPIC_MODELS,
        groq=GROQ_MODELS,
    )
