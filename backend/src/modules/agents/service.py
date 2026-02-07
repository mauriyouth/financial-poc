from collections.abc import AsyncIterator

from src.connectors.anthropic_connector import AnthropicConnector
from src.connectors.gemini_connector import GeminiConnector
from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger
from src.modules.agents.orchestrator_agent import OrchestratorAgent
from src.modules.agents.runner import AgentRunner
from src.modules.agents.prompts import get_default_prompt
from src.modules.agents.simple_chat_agent import SimpleChatAgent
from src.models.all_models import Message


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
        self.agent_runner = AgentRunner(orchestrator)
        self.simple_chat_agent = SimpleChatAgent(adk_connector)

        # Kept for compatibility if accessed directly, but logic is moved
        self.adk_connector = adk_connector
        self.orchestrator = orchestrator

        logger.info("AIService initialized with multi-agent support")

    def get_available_agents(self) -> list[dict]:
        """Get list of available agents from the orchestrator's registry."""
        return self.agent_runner.get_available_agents()

    async def stream_generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        agent_name: str | None = None,
        history: list[Message] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream AI response.
        """
        logger.info(f"Streaming with model={model}, agent_name={agent_name}")

        # 1. If agent_name is specified, delegate to AgentRunner to run that specific agent
        # The agent definition itself handles the model configuration
        if agent_name:
            async for chunk in self.agent_runner.stream_generate(prompt, agent_name, history=history):
                yield chunk
            return

        # 2. If model is specified (and no agent_name), use SimpleChatAgent (Ephemeral)
        if model:
            if system is None:
                system = get_default_prompt()

            # Create ad-hoc agent
            agent = self.simple_chat_agent.get_agent(model=model, instruction=system)

            # Stream using AgentRunner's specific agent method
            async for chunk in self.agent_runner.stream_specific_agent(agent, prompt, history=history):
                yield chunk
            return

        # 3. Otherwise, delegate to AgentRunner (auto-routing/orchestrator)
        async for chunk in self.agent_runner.stream_generate(prompt, agent_name=None, history=history):
            yield chunk
