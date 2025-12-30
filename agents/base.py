"""
Abstract Agent Base Class

Defines the interface and common behaviors for all agents in the adversarial swarm.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional, List, Dict, Any, TYPE_CHECKING, Union
import asyncio
import logging
import os
import uuid

# Ensure .env is loaded before anything else
from dotenv import load_dotenv
load_dotenv()

import anthropic
import groq

from .types import AgentRole, AgentCategory
from .config import AgentConfig

if TYPE_CHECKING:
    from models.document_types import DocumentType


@dataclass
class AgentOutput:
    """
    Structured output from an agent's processing.

    Contains the agent's contribution to the document or debate,
    along with metadata about the processing.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_role: AgentRole = AgentRole.STRATEGY_ARCHITECT
    agent_name: str = ""

    # Output content
    content: str = ""
    content_type: str = "text"  # text, json, markdown

    # Structured outputs (optional)
    sections: Dict[str, str] = field(default_factory=dict)
    critiques: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Processing info
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    model_used: str = ""

    # Status
    success: bool = True
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # Timestamp
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_role": self.agent_role.value,
            "agent_name": self.agent_name,
            "content": self.content,
            "content_type": self.content_type,
            "sections": self.sections,
            "critiques": self.critiques,
            "responses": self.responses,
            "metadata": self.metadata,
            "processing_time_ms": self.processing_time_ms,
            "token_usage": self.token_usage,
            "model_used": self.model_used,
            "success": self.success,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SwarmContext:
    """
    Shared context passed to agents during processing.

    Contains all the information an agent needs to perform its task,
    including the company profile, opportunity, current document state,
    and debate history.
    """

    # Request identification
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None

    # Document being generated
    document_type: Optional[str] = None
    document_id: Optional[str] = None

    # Input data (serialized as dicts for flexibility)
    company_profile: Optional[Dict[str, Any]] = None
    opportunity: Optional[Dict[str, Any]] = None

    # Current document state
    current_draft: Optional[Dict[str, Any]] = None
    section_drafts: Dict[str, str] = field(default_factory=dict)

    # Debate context
    round_number: int = 1
    round_type: str = "BlueBuild"  # BlueBuild, RedAttack, BlueDefense, Synthesis
    previous_outputs: List[Dict[str, Any]] = field(default_factory=list)
    pending_critiques: List[Dict[str, Any]] = field(default_factory=list)
    resolved_critiques: List[Dict[str, Any]] = field(default_factory=list)

    # Agent coordination
    requesting_agent: Optional[str] = None
    target_sections: List[str] = field(default_factory=list)

    # Custom data
    custom_data: Dict[str, Any] = field(default_factory=dict)

    # Timestamp
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Ensure custom_data is always a dict."""
        if not isinstance(self.custom_data, dict):
            self.custom_data = {}

    def get_section_content(self, section_name: str) -> Optional[str]:
        """Get the current content for a section."""
        return self.section_drafts.get(section_name)

    def get_critiques_for_section(self, section_name: str) -> List[Dict[str, Any]]:
        """Get pending critiques for a specific section."""
        return [
            c for c in self.pending_critiques
            if c.get("target_section") == section_name
        ]

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "document_type": self.document_type,
            "document_id": self.document_id,
            "company_profile": self.company_profile,
            "opportunity": self.opportunity,
            "current_draft": self.current_draft,
            "section_drafts": self.section_drafts,
            "round_number": self.round_number,
            "round_type": self.round_type,
            "previous_outputs": self.previous_outputs,
            "pending_critiques": self.pending_critiques,
            "resolved_critiques": self.resolved_critiques,
            "requesting_agent": self.requesting_agent,
            "target_sections": self.target_sections,
            "custom_data": self.custom_data,
            "created_at": self.created_at.isoformat(),
        }


class AbstractAgent(ABC):
    """
    Abstract base class for all agents in the adversarial swarm.

    All agent implementations must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the agent with its configuration.

        Args:
            config: Agent configuration including LLM settings and behavior params
        """
        self._config = config
        self._logger = logging.getLogger(f"agent.{config.role.value}")
        self._initialized = False
        self._call_count = 0
        self._total_tokens = 0
        self._stream_callback: Optional[Callable[[str], None]] = None
        self._provider = config.llm_config.provider

        # Initialize LLM client based on provider
        api_key = os.getenv(config.llm_config.api_key_env_var)
        if api_key:
            if self._provider == "groq":
                self._llm_client: Union[anthropic.AsyncAnthropic, groq.AsyncGroq, None] = groq.AsyncGroq(
                    api_key=api_key,
                    timeout=config.llm_config.timeout,
                )
            else:
                self._llm_client = anthropic.AsyncAnthropic(
                    api_key=api_key,
                    timeout=config.llm_config.timeout,
                )
        else:
            self._llm_client = None
            logging.getLogger(__name__).warning(
                f"Agent {self.name}: No API key found in env var '{config.llm_config.api_key_env_var}'. "
                f"LLM calls will fail. Make sure .env file is loaded and contains the key for provider '{self._provider}'."
            )

    @property
    def config(self) -> AgentConfig:
        """Get the agent's configuration."""
        return self._config

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """
        Get the agent's role.

        Returns:
            The AgentRole enum value for this agent
        """
        pass

    @property
    @abstractmethod
    def category(self) -> AgentCategory:
        """
        Get the agent's category.

        Returns:
            The AgentCategory (Blue, Red, Specialist, or Orchestrator)
        """
        pass

    @property
    def name(self) -> str:
        """Get the agent's display name."""
        return self._config.name or self.role.value

    @property
    def is_enabled(self) -> bool:
        """Check if the agent is enabled."""
        return self._config.enabled

    @property
    def priority(self) -> int:
        """Get the agent's priority for ordering."""
        return self._config.priority

    def set_stream_callback(self, callback: Optional[Callable[[str], None]]) -> None:
        """
        Set a callback to receive streaming LLM output.

        The callback is invoked with each text chunk as it's generated.
        This enables real-time streaming to the frontend.

        Args:
            callback: Function that receives each text chunk, or None to disable
        """
        self._stream_callback = callback

    @abstractmethod
    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and produce output.

        This is the main entry point for agent execution. Implementations
        should handle their specific logic for drafting, critiquing, or
        responding based on their role.

        Args:
            context: The SwarmContext containing all relevant information

        Returns:
            AgentOutput containing the agent's contribution
        """
        pass

    def can_handle(self, document_type: str) -> bool:
        """
        Check if this agent can handle a given document type.

        Args:
            document_type: The document type to check

        Returns:
            True if the agent can handle this document type
        """
        # If no specific types are configured, handle all
        if not self._config.supported_document_types:
            return True
        return document_type in self._config.supported_document_types

    async def initialize(self) -> None:
        """
        Initialize the agent before first use.

        Override this method to perform any async initialization
        such as loading resources or validating API keys.
        """
        self._initialized = True
        self._logger.debug(f"Agent {self.name} initialized")

    async def cleanup(self) -> None:
        """
        Clean up resources when the agent is no longer needed.

        Override this method to perform any cleanup operations.
        """
        self._initialized = False
        self._logger.debug(f"Agent {self.name} cleaned up")

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate that the context contains required information.

        Override this method to add agent-specific validation.

        Args:
            context: The context to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if context.document_type and not self.can_handle(context.document_type):
            errors.append(
                f"Agent {self.name} cannot handle document type: {context.document_type}"
            )

        return errors

    def log_info(self, message: str) -> None:
        """Log an info message."""
        self._logger.info(f"[{self.name}] {message}")

    def log_debug(self, message: str) -> None:
        """Log a debug message."""
        self._logger.debug(f"[{self.name}] {message}")

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self._logger.warning(f"[{self.name}] {message}")

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self._logger.error(f"[{self.name}] {message}")

    def _create_output(
        self,
        content: str = "",
        success: bool = True,
        error_message: Optional[str] = None,
        **kwargs
    ) -> AgentOutput:
        """
        Create an AgentOutput with common fields populated.

        Args:
            content: The main output content
            success: Whether processing succeeded
            error_message: Error message if failed
            **kwargs: Additional fields to set on the output

        Returns:
            AgentOutput instance
        """
        return AgentOutput(
            agent_role=self.role,
            agent_name=self.name,
            content=content,
            model_used=self._config.llm_config.model,
            success=success,
            error_message=error_message,
            **kwargs
        )

    def _track_usage(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Track token usage for monitoring."""
        self._call_count += 1
        self._total_tokens += input_tokens + output_tokens

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Call the LLM to generate content.

        Supports both Anthropic and Groq APIs with retry logic and error handling.
        Configuration is pulled from the agent's LLMConfig.

        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt with the specific request
            stream_callback: Optional callback for streaming chunks

        Returns:
            Dictionary with:
                - success: bool indicating if the call succeeded
                - content: The generated text content
                - usage: Dict with input_tokens and output_tokens
                - error: Optional error message if success is False
        """
        if not self._llm_client:
            self.log_error("LLM client not initialized - API key may be missing")
            api_key_var = "GROQ_API_KEY" if self._provider == "groq" else "ANTHROPIC_API_KEY"
            return {
                "success": False,
                "content": "",
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "error": f"LLM client not initialized. Check {api_key_var}.",
            }

        llm_config = self._config.llm_config
        last_error: Optional[Exception] = None

        for attempt in range(llm_config.max_retries):
            try:
                self.log_debug(
                    f"Calling LLM [{self._provider}] (attempt {attempt + 1}/{llm_config.max_retries})"
                )

                # Use streaming if callback provided or set on agent
                effective_callback = stream_callback or self._stream_callback
                if effective_callback:
                    return await self._call_llm_streaming(
                        system_prompt, user_prompt, effective_callback
                    )

                # Route to appropriate provider
                if self._provider == "groq":
                    return await self._call_groq(system_prompt, user_prompt, llm_config)
                else:
                    return await self._call_anthropic(system_prompt, user_prompt, llm_config)

            except (anthropic.RateLimitError, groq.RateLimitError) as e:
                last_error = e
                wait_time = llm_config.retry_delay * (2 ** attempt)
                self.log_warning(
                    f"Rate limited, waiting {wait_time}s before retry"
                )
                await asyncio.sleep(wait_time)

            except (anthropic.APIStatusError, groq.APIStatusError) as e:
                last_error = e
                if hasattr(e, 'status_code') and e.status_code >= 500:
                    # Server error - retry
                    wait_time = llm_config.retry_delay * (2 ** attempt)
                    self.log_warning(
                        f"API server error ({e.status_code}), retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Client error - don't retry
                    self.log_error(f"API client error: {e}")
                    break

            except (anthropic.APIConnectionError, groq.APIConnectionError) as e:
                last_error = e
                wait_time = llm_config.retry_delay * (2 ** attempt)
                self.log_warning(
                    f"Connection error, retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)

            except Exception as e:
                last_error = e
                self.log_error(f"Unexpected error calling LLM: {e}")
                break

        # All retries exhausted
        error_msg = str(last_error) if last_error else "Unknown error"
        self.log_error(f"LLM call failed after {llm_config.max_retries} attempts: {error_msg}")

        return {
            "success": False,
            "content": "",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "error": error_msg,
        }

    async def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        llm_config: Any,
    ) -> Dict[str, Any]:
        """Call Anthropic Claude API."""
        response = await self._llm_client.messages.create(
            model=llm_config.model,
            max_tokens=llm_config.max_tokens,
            temperature=llm_config.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            stop_sequences=llm_config.stop_sequences or None,
        )

        # Extract content from response
        content = ""
        if response.content:
            content = "".join(
                block.text
                for block in response.content
                if hasattr(block, "text")
            )

        # Track usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        self._track_usage(input_tokens, output_tokens)

        self.log_debug(
            f"Anthropic call successful: {input_tokens} input, {output_tokens} output tokens"
        )

        return {
            "success": True,
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }

    async def _call_groq(
        self,
        system_prompt: str,
        user_prompt: str,
        llm_config: Any,
    ) -> Dict[str, Any]:
        """Call Groq API (OpenAI-compatible)."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self._llm_client.chat.completions.create(
            model=llm_config.model,
            max_tokens=llm_config.max_tokens,
            temperature=llm_config.temperature,
            messages=messages,
            stop=llm_config.stop_sequences or None,
        )

        # Extract content from response
        content = ""
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content or ""

        # Track usage
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        self._track_usage(input_tokens, output_tokens)

        self.log_debug(
            f"Groq call successful: {input_tokens} input, {output_tokens} output tokens"
        )

        return {
            "success": True,
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }

    async def _call_llm_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        stream_callback: Callable[[str], None],
    ) -> Dict[str, Any]:
        """
        Call the LLM with streaming enabled.

        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt with the specific request
            stream_callback: Callback invoked with each text chunk

        Returns:
            Dictionary with success, content, usage, and optional error
        """
        if self._provider == "groq":
            return await self._call_groq_streaming(system_prompt, user_prompt, stream_callback)
        else:
            return await self._call_anthropic_streaming(system_prompt, user_prompt, stream_callback)

    async def _call_anthropic_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        stream_callback: Callable[[str], None],
    ) -> Dict[str, Any]:
        """Call Anthropic API with streaming enabled."""
        llm_config = self._config.llm_config
        content_parts: List[str] = []
        input_tokens = 0
        output_tokens = 0

        try:
            async with self._llm_client.messages.stream(
                model=llm_config.model,
                max_tokens=llm_config.max_tokens,
                temperature=llm_config.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                stop_sequences=llm_config.stop_sequences or None,
            ) as stream:
                async for text in stream.text_stream:
                    content_parts.append(text)
                    stream_callback(text)

                # Get final message for usage stats
                final_message = await stream.get_final_message()
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens

            content = "".join(content_parts)
            self._track_usage(input_tokens, output_tokens)

            self.log_debug(
                f"Anthropic streaming call successful: {input_tokens} input, {output_tokens} output tokens"
            )

            return {
                "success": True,
                "content": content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            }

        except Exception as e:
            self.log_error(f"Anthropic streaming call failed: {e}")
            return {
                "success": False,
                "content": "".join(content_parts),
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
                "error": str(e),
            }

    async def _call_groq_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        stream_callback: Callable[[str], None],
    ) -> Dict[str, Any]:
        """Call Groq API with streaming enabled."""
        llm_config = self._config.llm_config
        content_parts: List[str] = []
        input_tokens = 0
        output_tokens = 0

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            stream = await self._llm_client.chat.completions.create(
                model=llm_config.model,
                max_tokens=llm_config.max_tokens,
                temperature=llm_config.temperature,
                messages=messages,
                stop=llm_config.stop_sequences or None,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content_parts.append(delta.content)
                        stream_callback(delta.content)
                # Capture usage from the final chunk (when stream_options include_usage is True)
                if chunk.usage is not None:
                    input_tokens = chunk.usage.prompt_tokens or 0
                    output_tokens = chunk.usage.completion_tokens or 0

            content = "".join(content_parts)
            self._track_usage(input_tokens, output_tokens)

            self.log_debug(
                f"Groq streaming call successful: {input_tokens} input, {output_tokens} output tokens"
            )

            return {
                "success": True,
                "content": content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            }

        except Exception as e:
            self.log_error(f"Groq streaming call failed: {e}")
            return {
                "success": False,
                "content": "".join(content_parts),
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
                "error": str(e),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get agent usage statistics."""
        return {
            "role": self.role.value,
            "name": self.name,
            "category": self.category.value,
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
            "is_enabled": self.is_enabled,
            "is_initialized": self._initialized,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(role={self.role.value}, name={self.name})"


class BlueTeamAgent(AbstractAgent):
    """
    Base class for blue team (constructive) agents.

    Blue team agents are responsible for creating and defending
    document content.
    """

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.BLUE

    async def draft_section(
        self,
        context: SwarmContext,
        section_name: str
    ) -> str:
        """
        Draft content for a specific section.

        Override this method to implement section-specific drafting logic.

        Args:
            context: The swarm context
            section_name: Name of the section to draft

        Returns:
            The drafted content for the section
        """
        raise NotImplementedError("Subclasses must implement draft_section")

    async def revise_section(
        self,
        context: SwarmContext,
        section_name: str,
        critiques: List[Dict[str, Any]]
    ) -> str:
        """
        Revise a section based on accepted critiques.

        Override this method to implement revision logic.

        Args:
            context: The swarm context
            section_name: Name of the section to revise
            critiques: List of critiques to address

        Returns:
            The revised content for the section
        """
        raise NotImplementedError("Subclasses must implement revise_section")


class RedTeamAgent(AbstractAgent):
    """
    Base class for red team (adversarial) agents.

    Red team agents are responsible for critiquing and challenging
    blue team outputs.
    """

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.RED

    async def critique_section(
        self,
        context: SwarmContext,
        section_name: str,
        section_content: str
    ) -> List[Dict[str, Any]]:
        """
        Generate critiques for a specific section.

        Override this method to implement critique logic.

        Args:
            context: The swarm context
            section_name: Name of the section to critique
            section_content: Current content of the section

        Returns:
            List of critique dictionaries
        """
        raise NotImplementedError("Subclasses must implement critique_section")

    async def evaluate_response(
        self,
        context: SwarmContext,
        critique: Dict[str, Any],
        response: Dict[str, Any]
    ) -> bool:
        """
        Evaluate whether a blue team response adequately addresses a critique.

        Args:
            context: The swarm context
            critique: The original critique
            response: The blue team's response

        Returns:
            True if the response is acceptable, False otherwise
        """
        raise NotImplementedError("Subclasses must implement evaluate_response")


class OrchestratorAgent(AbstractAgent):
    """
    Base class for orchestrator agents.

    Orchestrator agents coordinate the overall workflow and
    make decisions about debate progression and synthesis.
    """

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.ORCHESTRATOR

    async def should_continue_debate(
        self,
        context: SwarmContext,
        current_round: int,
        max_rounds: int
    ) -> bool:
        """
        Determine if the debate should continue or conclude.

        Args:
            context: The swarm context
            current_round: Current debate round number
            max_rounds: Maximum allowed rounds

        Returns:
            True if debate should continue, False to conclude
        """
        raise NotImplementedError("Subclasses must implement should_continue_debate")

    async def synthesize_final_output(
        self,
        context: SwarmContext
    ) -> Dict[str, Any]:
        """
        Synthesize the final document from all debate rounds.

        Args:
            context: The swarm context with complete debate history

        Returns:
            Dictionary containing the final document and metadata
        """
        raise NotImplementedError("Subclasses must implement synthesize_final_output")
