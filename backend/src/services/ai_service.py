from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from src.connectors.anthropic_connector import AnthropicConnector
from src.connectors.gemini_connector import GeminiConnector
from src.configurations.settings import settings
from src.core.logging import logger
from src.prompts import get_default_prompt


class AIResponse(BaseModel):
    content: str
    thinking_steps: list[str] = []
    function_call: dict[str, Any] | None = None


class AIService:
    def __init__(self, anthropic_connector: AnthropicConnector, gemini_connector: GeminiConnector):
        # Dependencies injected
        self.anthropic_client = anthropic_connector.get_client()
        self.gemini_connector = gemini_connector
        logger.info("AIService initialized")

    async def generate(
        self,
        prompt: str,
        provider: str = "anthropic",
        model: str | None = None,
        system: str | None = None,
    ) -> AIResponse:
        logger.info(f"Generating AI response with provider={provider}, model={model}")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        # Use default prompt if not provided
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

    async def _generate_anthropic(self, prompt: str, model: str, system: str) -> AIResponse:
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
        provider: str = "anthropic",
        model: str | None = None,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        logger.info(f"Streaming with provider={provider}, model={model}")

        # Use default prompt if not provided
        if system is None:
            system = get_default_prompt()

        if provider == "anthropic":
            if not self.anthropic_client:
                yield '{"type": "error", "content": "Anthropic API key not configured."}\n'
                return

            model = model or settings.ANTHROPIC_MODEL
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
                        # Track if this is a thinking block
                        if hasattr(event.content_block, "type") and event.content_block.type == "thinking":
                            yield '{"type": "thinking_start"}\n'
                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, "type"):
                            if event.delta.type == "thinking_delta":
                                # Stream thinking content
                                import json

                                yield json.dumps({"type": "thinking", "content": event.delta.thinking}) + "\n"
                            elif event.delta.type == "text_delta":
                                # Stream regular text content
                                import json

                                yield json.dumps({"type": "content", "content": event.delta.text}) + "\n"
                    elif event.type == "content_block_stop":
                        yield '{"type": "block_stop"}\n'
                    elif event.type == "message_stop":
                        yield '{"type": "done"}\n'

                logger.info("Anthropic streaming completed")
            except Exception as e:
                import json

                logger.error(f"Anthropic streaming error: {e}")
                yield json.dumps({"type": "error", "content": str(e)}) + "\n"

        elif provider == "google":
            model = model or "gemini-1.5-pro"
            logger.debug(f"Streaming with Google model: {model}")

            gemini_model = self.gemini_connector.get_model(model)
            if not gemini_model:
                yield '{"type": "error", "content": "Google API key not configured."}\n'
                return

            try:
                import json

                # Generate content with streaming
                response = gemini_model.generate_content(prompt, stream=True)

                for chunk in response:
                    if chunk.text:
                        yield json.dumps({"type": "content", "content": chunk.text}) + "\n"

                yield '{"type": "done"}\n'
                logger.info("Google streaming completed")

            except Exception as e:
                import json

                logger.error(f"Google streaming error: {e}")
                yield json.dumps({"type": "error", "content": str(e)}) + "\n"
        else:
            yield '{"type": "error", "content": "Unknown provider: ' + provider + '"}\n'

    async def _generate_gemini(self, prompt: str, model: str) -> AIResponse:
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
