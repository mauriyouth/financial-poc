import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.runners import InMemoryRunner
from google.genai import types

from src.core.logging import logger
from src.models.all_models import Message
from src.modules.agents.orchestrator_agent import OrchestratorAgent
from src.modules.agents.plugins.streaming_reasoning_plugin import StreamingReasoningPlugin
from src.modules.agents.types import AIResponse


class AgentRunner:
    """Runner for ADK agents."""

    def __init__(self, orchestrator: OrchestratorAgent) -> None:
        self.orchestrator = orchestrator
        self.background_tasks: set[asyncio.Task] = set()

    def get_available_agents(self) -> list[dict]:
        """Get list of available agents from the orchestrator's registry."""
        agents_info = []
        try:
            registry = self.orchestrator.registry

            for agent_name in registry.list_agent_names():
                try:
                    agent_instance = registry.get_agent(agent_name)
                    if agent_instance:
                        agents_info.append(
                            {
                                "name": agent_name,
                                "description": getattr(agent_instance, "description", "No description available"),
                            }
                        )
                except Exception as e:
                    logger.error(f"Error getting agent {agent_name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error getting available agents: {e}")

        return agents_info

    async def generate(
        self, prompt: str, agent_name: str | None = None, history: list[Message] | None = None
    ) -> AIResponse:
        """Generate response using ADK agent system."""
        # If specific agent requested, use it; otherwise use orchestrator
        if agent_name:
            logger.debug(f"Using specific ADK agent: {agent_name}")
            agent_wrapper = self.orchestrator.registry.get_agent(agent_name)
            if agent_wrapper:
                # Get the actual ADK agent from the wrapper
                agent = agent_wrapper.get_agent()
            else:
                agent = None
        else:
            logger.debug("Using ADK orchestrator agent")
            agent = self.orchestrator.get_agent()

        if not agent:
            logger.error("Agent not available")
            return AIResponse(content="Agent system not properly configured.")

        try:
            # Use agent directly with InMemoryRunner
            runner = InMemoryRunner(agent=agent)

            # Create session explicitly
            user_id = "default_user"
            session_id = "default_session"
            await runner.session_service.create_session(
                app_name=runner.app_name, user_id=user_id, session_id=session_id
            )

            # Convert prompt to Content type
            user_content = types.Content(parts=[types.Part(text=prompt)])

            # Run the agent and loop over events
            content_parts = []
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
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

    async def run_specific_agent(self, agent: Any, prompt: str) -> AIResponse:
        """Run a specific agent instance (not from orchestrator)."""
        if not agent:
            return AIResponse(content="Agent not configured.")

        # Re-use logic from generate but with passed agent
        # We can refactor generate to calculate agent and call this method
        try:
            runner = InMemoryRunner(agent=agent)

            # Create session explicitly
            user_id = "default_user_simple"
            session_id = "default_session_simple"
            await runner.session_service.create_session(
                app_name=runner.app_name, user_id=user_id, session_id=session_id
            )

            user_content = types.Content(parts=[types.Part(text=prompt)])
            content_parts = []
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
                if hasattr(event, "is_final_response") and event.is_final_response:
                    if hasattr(event, "content") and event.content:
                        if hasattr(event.content, "parts"):
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    content_parts.append(part.text)

            content = "".join(content_parts) if content_parts else "No response generated"
            logger.info(f"Specific Agent response: {len(content)} chars")
            return AIResponse(content=content)
        except Exception as e:
            logger.error(f"Specific Agent error: {e}")
            import traceback

            traceback.print_exc()
            return AIResponse(content=f"Error calling specific agent: {e!s}")

    async def stream_generate(
        self, prompt: str, agent_name: str | None = None, history: list[Message] | None = None
    ) -> AsyncIterator[str]:
        """Stream response using ADK agent system."""
        # If specific agent requested, use it; otherwise use orchestrator
        if agent_name:
            logger.debug(f"Streaming with specific ADK agent: {agent_name}")
            agent_wrapper = self.orchestrator.registry.get_agent(agent_name)
            if agent_wrapper:
                # Get the actual ADK agent from the wrapper
                agent = agent_wrapper.get_agent()
            else:
                agent = None
        else:
            logger.debug("Streaming with ADK orchestrator agent")
            agent = self.orchestrator.get_agent()

        if not agent:
            logger.error("Agent not available")
            yield json.dumps({"type": "error", "content": "Agent system not properly configured."}) + "\n"
            return

        # Helper to avoid code duplication with stream_specific_agent
        # Ideally we would just call stream_specific_agent here, but we are inside the class
        # so we can simply delegate
        async for chunk in self.stream_specific_agent(agent, prompt, history=history):
            yield chunk

    async def stream_specific_agent(
        self, agent: Any, prompt: str, history: list[Message] | None = None
    ) -> AsyncIterator[str]:
        """Stream from a specific agent instance."""
        if not agent:
            yield json.dumps({"type": "error", "content": "Agent not configured."}) + "\n"
            return

        # Re-use logic from stream_generate
        try:
            event_queue: asyncio.Queue = asyncio.Queue()
            logging_plugin = LoggingPlugin()
            streaming_plugin = StreamingReasoningPlugin(event_queue)

            runner = InMemoryRunner(agent=agent, plugins=[logging_plugin, streaming_plugin])

            user_content = types.Content(parts=[types.Part(text=prompt)])
            user_id = "default_user_simple"
            session_id = "stream_session_simple"

            output_queue: asyncio.Queue = asyncio.Queue()
            STOP_SIGNAL = object()

            async def plugin_consumer() -> None:
                while True:
                    try:
                        event = await event_queue.get()
                        await output_queue.put(json.dumps(event) + "\n")
                        event_queue.task_done()
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Plugin consumer error: {e}")
                        break

            async def agent_runner() -> None:
                try:
                    logger.info(f"Starting ADK runner with specific agent: {type(agent).__name__}")
                    await runner.session_service.create_session(
                        app_name=runner.app_name, user_id=user_id, session_id=session_id
                    )

                    async for event in runner.run_async(
                        user_id=user_id, session_id=session_id, new_message=user_content
                    ):
                        if hasattr(event, "content") and event.content:
                            if hasattr(event.content, "parts"):
                                for part in event.content.parts:
                                    if hasattr(part, "text") and part.text:
                                        await output_queue.put(
                                            json.dumps({"type": "content", "content": part.text}) + "\n"
                                        )
                        if hasattr(event, "is_final_response") and event.is_final_response:
                            await output_queue.put(json.dumps({"type": "done"}) + "\n")
                except Exception as e:
                    logger.error(f"Agent runner error: {e}")
                    await output_queue.put(json.dumps({"type": "error", "content": str(e)}) + "\n")
                finally:
                    await output_queue.put(STOP_SIGNAL)

            plugin_task = asyncio.create_task(plugin_consumer())
            self.background_tasks.add(plugin_task)
            plugin_task.add_done_callback(self.background_tasks.discard)

            agent_task = asyncio.create_task(agent_runner())
            self.background_tasks.add(agent_task)
            agent_task.add_done_callback(self.background_tasks.discard)

            while True:
                item = await output_queue.get()
                if item is STOP_SIGNAL:
                    break
                yield item
                output_queue.task_done()

            plugin_task.cancel()
            try:
                await plugin_task
            except asyncio.CancelledError:
                pass
        except Exception as e:
            logger.error(f"ADK specific streaming error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
        """Stream response using ADK agent system with reasoning."""
        # If specific agent requested, use it; otherwise use orchestrator
        logger.debug(f"Streaming with ADK orchestrator agent. Prompt length: {len(prompt)}")
        # Get the actual ADK agent from the orchestrator wrapper (this method isn't used here but copied comment)
        # Actually this method streams from a SPECIFIC agent passed as arg, so we don't look up by name.

        if not agent:
            logger.error("Agent not available")
            yield json.dumps({"type": "error", "content": "Agent system not properly configured."}) + "\n"
            return

        try:
            # Create event queue for reasoning events
            event_queue: asyncio.Queue = asyncio.Queue()

            # Create plugins
            logging_plugin = LoggingPlugin()
            streaming_plugin = StreamingReasoningPlugin(event_queue)

            # Create a runner with plugins
            runner = InMemoryRunner(agent=agent, plugins=[logging_plugin, streaming_plugin])

            # Convert prompt to Content type with explicit role
            user_content = types.Content(role="user", parts=[types.Part(text=prompt)])

            # Create a new session
            user_id = "default_user"
            session_id = "stream_session"

            # Create a shared output queue for merging streams
            output_queue: asyncio.Queue = asyncio.Queue()
            STOP_SIGNAL = object()

            # Task to consume plugin events (reasoning, tools, etc.)
            async def plugin_consumer() -> None:
                while True:
                    try:
                        # Wait for events from the plugin
                        event = await event_queue.get()
                        await output_queue.put(json.dumps(event) + "\n")
                        event_queue.task_done()
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Plugin consumer error: {e}")
                        break

            # Task to run agent and produce content events
            async def agent_runner() -> None:
                try:
                    logger.info(f"Starting ADK runner with agent: {type(agent).__name__}")
                    await runner.session_service.create_session(
                        app_name=runner.app_name, user_id=user_id, session_id=session_id
                    )

                    async for event in runner.run_async(
                        user_id=user_id, session_id=session_id, new_message=user_content
                    ):
                        # Log basic event reception
                        logger.debug(f"Runner received event: {type(event).__name__}")

                        # Stream content parts as they arrive
                        if hasattr(event, "content") and event.content:
                            if hasattr(event.content, "parts"):
                                for part in event.content.parts:
                                    if hasattr(part, "text") and part.text:
                                        await output_queue.put(
                                            json.dumps({"type": "content", "content": part.text}) + "\n"
                                        )

                        # Check if this is the final response
                        if hasattr(event, "is_final_response") and event.is_final_response:
                            await output_queue.put(json.dumps({"type": "done"}) + "\n")
                except Exception as e:
                    logger.error(f"Agent runner error: {e}")
                    await output_queue.put(json.dumps({"type": "error", "content": str(e)}) + "\n")
                finally:
                    # Signal that agent is done
                    await output_queue.put(STOP_SIGNAL)

            # Start background tasks
            plugin_task = asyncio.create_task(plugin_consumer())
            self.background_tasks.add(plugin_task)
            plugin_task.add_done_callback(self.background_tasks.discard)

            agent_task = asyncio.create_task(agent_runner())
            self.background_tasks.add(agent_task)
            agent_task.add_done_callback(self.background_tasks.discard)

            # Yield events from the output queue as they arrive
            while True:
                item = await output_queue.get()
                if item is STOP_SIGNAL:
                    break
                yield item
                output_queue.task_done()

            # Cleanup
            plugin_task.cancel()
            try:
                await plugin_task
            except asyncio.CancelledError:
                pass

            logger.info("ADK agent streaming completed")

        except Exception as e:
            logger.error(f"ADK streaming error: {e}")
            import traceback

            traceback.print_exc()
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
