"""Streaming reasoning plugin for ADK agents."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from src.core.logging import logger

if TYPE_CHECKING:
    from google.adk.agents.base_agent import BaseAgent
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.agents.invocation_context import InvocationContext
    from google.adk.events.event import Event
    from google.adk.models.llm_request import LlmRequest
    from google.adk.models.llm_response import LlmResponse
    from google.adk.tools.base_tool import BaseTool
    from google.adk.tools.tool_context import ToolContext


class StreamingReasoningPlugin(BasePlugin):
    """Plugin that emits reasoning events for streaming display."""

    def __init__(self, event_queue: asyncio.Queue, name: str = "streaming_reasoning"):
        """Initialize the streaming reasoning plugin.

        Args:
            event_queue: Queue to emit reasoning events to
            name: Plugin name
        """
        super().__init__(name)
        self.event_queue = event_queue

    async def _emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event to the queue."""
        try:
            await self.event_queue.put({"type": event_type, **data})
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> Optional[types.Content]:
        """Log agent execution start."""
        await self._emit_event(
            "agent_start",
            {
                "agent_name": callback_context.agent_name,
                "invocation_id": callback_context.invocation_id,
                "description": getattr(agent, "description", None),
                "instruction": getattr(agent, "instruction", None),
            },
        )
        return None

    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> Optional[types.Content]:
        """Log agent execution completion."""
        await self._emit_event(
            "agent_end",
            {
                "agent_name": callback_context.agent_name,
                "invocation_id": callback_context.invocation_id,
            },
        )
        return None

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        """Log LLM response."""
        if llm_response.error_code:
            await self._emit_event(
                "llm_error",
                {
                    "agent_name": callback_context.agent_name,
                    "error_code": llm_response.error_code,
                    "error_message": llm_response.error_message,
                },
            )
        return None

    async def on_thought_callback(self, *, callback_context: CallbackContext, thought: str) -> None:
        """Log agent thought."""
        await self._emit_event(
            "thinking",
            {
                "agent_name": callback_context.agent_name,
                "content": thought,  # Capture the native thought
                "model": "adk-thought",  # Indicate source
            },
        )

    async def on_event_callback(self, *, invocation_context: InvocationContext, event: Event) -> Optional[Event]:
        """Inspect events for thought content and filter them out."""
        if event.content and event.content.parts:
            # Separate thoughts from content
            thought_parts = []
            content_parts = []

            for part in event.content.parts:
                # Check for native thought attribute
                # Pydantic models in the ADK/GenAI SDK use 'thought' field
                if getattr(part, "thought", False):
                    thought_parts.append(part)
                else:
                    content_parts.append(part)

            # Emit thoughts
            for part in thought_parts:
                await self._emit_event(
                    "thinking",
                    {
                        "agent_name": event.author,
                        "content": part.text,
                        "model": "adk-thought-native",
                    },
                )

            # If we filtered out any parts, update the event content
            if len(thought_parts) > 0:
                event.content.parts = content_parts
                # If there are no parts left (e.g. pure thought event),
                # we might want to return None to drop the event entirely from the session/user view
                if not content_parts and not event.is_final_response():
                    return None
                return event

        return None

    # Removed fake before_model_callback as per user request
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> Optional[dict]:
        """Log tool execution start."""
        await self._emit_event(
            "tool_call",
            {
                "tool_name": tool.name,
                "agent_name": tool_context.agent_name,
                "arguments": tool_args,
                "function_call_id": tool_context.function_call_id,
            },
        )
        return None

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict,
    ) -> Optional[dict]:
        """Log tool execution completion."""
        await self._emit_event(
            "tool_result",
            {
                "tool_name": tool.name,
                "agent_name": tool_context.agent_name,
                "function_call_id": tool_context.function_call_id,
                "result": result,
            },
        )
        return None

    async def on_tool_error_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        error: Exception,
    ) -> Optional[dict]:
        """Log tool error."""
        await self._emit_event(
            "tool_error",
            {
                "tool_name": tool.name,
                "agent_name": tool_context.agent_name,
                "error": str(error),
            },
        )
        return None
