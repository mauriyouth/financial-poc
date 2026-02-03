"""AI Service using Google ADK multi-agent architecture."""

import json
from collections.abc import AsyncIterator
from typing import Any

from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel

from src.configurations.settings import settings
from src.connectors.anthropic_connector import AnthropicConnector
from src.connectors.gemini_connector import GeminiConnector
from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger
from src.modules.agents.orchestrator_agent import OrchestratorAgent
from src.prompts import get_default_prompt


class AIResponse(BaseModel):
    """AI response model."""

    content: str
    thinking_steps: list[str] = []
    function_call: dict[str, Any] | None = None


class AIService:
    """AI Service with multi-agent support via Google ADK."""

    def __init__(
        self,
        anthropic_connector: AnthropicConnector,
        gemini_connector: GeminiConnector,
        adk_connector: GoogleADKConnector,
        orchestrator: OrchestratorAgent,
    ) -> None:
        """
        Initialize AI Service.

        Args:
            anthropic_connector: Anthropic connector for legacy support
            gemini_connector: Gemini connector for legacy support
            adk_connector: Google ADK connector
            orchestrator: Orchestrator agent for routing
        """
        # Legacy connectors
        self.anthropic_client = anthropic_connector.get_client()
        self.gemini_connector = gemini_connector

        # ADK components
        self.adk_connector = adk_connector
        self.orchestrator = orchestrator

        logger.info("AIService initialized with multi-agent support")

    async def generate(
        self,
        prompt: str,
        provider: str = "adk",
        model: str | None = None,
        system: str | None = None,
    ) -> AIResponse:
        """
        Generate AI response.

        Args:
            prompt: User prompt
            provider: Provider to use ('adk', 'anthropic', 'google')
            model: Specific model (for legacy providers)
            system: System prompt (for legacy providers)

        Returns:
            AIResponse with content
        """
        logger.info(f"Generating AI response with provider={provider}, model={model}")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        # Use ADK agents by default
        if provider == "adk":
            return await self._generate_with_agent(prompt)

        # Legacy provider support
        if system is None:
            system = get_default_prompt()

        if provider == "anthropic":
            if not self.anthropic_client:
                return AIResponse(content="Anthropic API key not configured.")
            model = model or settings.ANTHROPIC_MODEL
            return await self._generate_anthropic(prompt, model, system)
        elif provider == "google":
            model = model or "gemini-1.5-pro"
            return await self._generate_gemini(prompt, model)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _generate_with_agent(self, prompt: str) -> AIResponse:
        """Generate response using ADK orchestrator agent."""
        logger.debug("Using ADK orchestrator agent")

        agent = self.orchestrator.get_agent()
        if not agent:
            logger.error("Orchestrator agent not available")
            return AIResponse(content="Agent system not properly configured.")

        try:
            # Create a runner for the agent
            runner = InMemoryRunner(agent=agent)

            # Convert prompt to Content type
            user_content = types.Content(parts=[types.Part(text=prompt)])

            # Create a new session/thread
            thread = runner.app.create_thread(user_id="default_user")

            # Run the agent and loop over events
            content_parts = []
            async for event in runner.run_async(user_id="default_user", session_id=thread.id, new_message=user_content):
                # Check if this is the final response
                if hasattr(event, "is_final_response") and event.is_final_response:
                    # Extract content from final response
                    if hasattr(event, "content") and event.content:
                        if hasattr(event.content, "parts"):
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    content_parts.append(part.text)

            # Combine all content parts
            content = "".join(content_parts) if content_parts else "No response generated"

            logger.info(f"Agent response: {len(content)} chars")
            return AIResponse(content=content)

        except Exception as e:
            logger.error(f"Agent error: {e}")
            import traceback

            traceback.print_exc()
            return AIResponse(content=f"Error calling agent: {e!s}")

    async def _generate_anthropic(self, prompt: str, model: str, system: str) -> AIResponse:
        """Legacy Anthropic generation."""
        logger.debug(f"Using Anthropic model: {model}")
        try:
            message = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            logger.info(f"Anthropic response: {len(message.content[0].text)} chars")
            return AIResponse(content=message.content[0].text)
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return AIResponse(content=f"Error calling Anthropic: {e!s}")

    async def stream_generate(
        self,
        prompt: str,
        provider: str = "adk",
        model: str | None = None,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream AI response.

        Args:
            prompt: User prompt
            provider: Provider to use ('adk', 'anthropic', 'google')
            model: Specific model (for legacy providers)
            system: System prompt (for legacy providers)

        Yields:
            JSON-formatted stream chunks
        """
        logger.info(f"Streaming with provider={provider}, model={model}")

        # Use ADK agents by default
        if provider == "adk":
            async for chunk in self._stream_with_agent(prompt):
                yield chunk
            return

        # Legacy streaming support
        if system is None:
            system = get_default_prompt()

        if provider == "anthropic":
            if not self.anthropic_client:
                yield json.dumps({"type": "error", "content": "Anthropic API key not configured."}) + "\n"
                return

            model = model or settings.ANTHROPIC_MODEL
            async for chunk in self._stream_anthropic(prompt, model, system):
                yield chunk

        elif provider == "google":
            model = model or "gemini-1.5-pro"
            async for chunk in self._stream_gemini(prompt, model):
                yield chunk
        else:
            yield json.dumps({"type": "error", "content": f"Unknown provider: {provider}"}) + "\n"

    async def _stream_with_agent(self, prompt: str) -> AsyncIterator[str]:
        """Stream response using ADK orchestrator agent."""
        logger.debug("Streaming with ADK orchestrator agent")

        agent = self.orchestrator.get_agent()
        if not agent:
            logger.error("Orchestrator agent not available")
            yield json.dumps({"type": "error", "content": "Agent system not properly configured."}) + "\n"
            return

        try:
            # Send agent info at start
            yield (
                json.dumps({"type": "agent_info", "agent_name": "orchestrator", "routing_reason": "Analyzing query"})
                + "\n"
            )

            # Create a runner for the agent
            runner = InMemoryRunner(agent=agent)

            # Convert prompt to Content type
            user_content = types.Content(parts=[types.Part(text=prompt)])

            # Create a new session/thread
            thread = runner.app.create_thread(user_id="default_user")

            # Stream the agent response by looping over events
            async for event in runner.run_async(user_id="default_user", session_id=thread.id, new_message=user_content):
                # Stream content parts as they arrive
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts"):
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                yield json.dumps({"type": "content", "content": part.text}) + "\n"

                # Check if this is the final response
                if hasattr(event, "is_final_response") and event.is_final_response:
                    yield json.dumps({"type": "done"}) + "\n"
                    break

            logger.info("ADK agent streaming completed")

        except Exception as e:
            logger.error(f"ADK streaming error: {e}")
            import traceback

            traceback.print_exc()
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    async def _stream_anthropic(self, prompt: str, model: str, system: str) -> AsyncIterator[str]:
        """Legacy Anthropic streaming."""
        logger.debug(f"Streaming with Anthropic model: {model}")

        try:
            stream = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                thinking={"type": "enabled", "budget_tokens": 2000},
                system=system,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            async for event in stream:
                if event.type == "content_block_start":
                    if hasattr(event.content_block, "type") and event.content_block.type == "thinking":
                        yield json.dumps({"type": "thinking_start"}) + "\n"
                elif event.type == "content_block_delta":
                    if hasattr(event.delta, "type"):
                        if event.delta.type == "thinking_delta":
                            yield json.dumps({"type": "thinking", "content": event.delta.thinking}) + "\n"
                        elif event.delta.type == "text_delta":
                            yield json.dumps({"type": "content", "content": event.delta.text}) + "\n"
                elif event.type == "content_block_stop":
                    yield json.dumps({"type": "block_stop"}) + "\n"
                elif event.type == "message_stop":
                    yield json.dumps({"type": "done"}) + "\n"

            logger.info("Anthropic streaming completed")
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    async def _stream_gemini(self, prompt: str, model: str) -> AsyncIterator[str]:
        """Legacy Gemini streaming."""
        logger.debug(f"Streaming with Google model: {model}")

        gemini_model = self.gemini_connector.get_model(model)
        if not gemini_model:
            yield json.dumps({"type": "error", "content": "Google API key not configured."}) + "\n"
            return

        try:
            response = gemini_model.generate_content(prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    yield json.dumps({"type": "content", "content": chunk.text}) + "\n"

            yield json.dumps({"type": "done"}) + "\n"
            logger.info("Google streaming completed")

        except Exception as e:
            logger.error(f"Google streaming error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    async def _generate_gemini(self, prompt: str, model: str) -> AIResponse:
        """Legacy Gemini generation."""
        logger.debug(f"Using Gemini model: {model}")
        gemini_model = self.gemini_connector.get_model(model)
        if not gemini_model:
            return AIResponse(content="Google API key not configured.")

        try:
            response = gemini_model.generate_content(prompt)
            logger.info(f"Gemini response: {len(response.text)} chars")
            return AIResponse(content=response.text)
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return AIResponse(content=f"Error calling Gemini: {e!s}")
