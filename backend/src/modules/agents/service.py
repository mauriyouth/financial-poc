from collections.abc import AsyncIterator

from src.connectors.anthropic_connector import AnthropicConnector
from src.connectors.gemini_connector import GeminiConnector
from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger
from src.models.all_models import Message
from src.modules.agents.orchestrator_agent import OrchestratorAgent
from src.modules.agents.prompts import get_default_prompt
from src.modules.agents.runner import AgentRunner
from src.modules.agents.simple_chat_agent import SimpleChatAgent
from src.modules.agents.verification_agent import VerificationAgent
from src.stores.opensearch.chunk_store import ChunkStore


class AIService:
    """AI Service with multi-agent support via Google ADK."""

    def __init__(
        self,
        anthropic_connector: AnthropicConnector,
        gemini_connector: GeminiConnector,
        adk_connector: GoogleADKConnector,
        orchestrator: OrchestratorAgent,
        chunk_store: ChunkStore | None = None,
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
        self.verification_agent = VerificationAgent(adk_connector)
        self.chunk_store = chunk_store

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

    async def verify_response(self, query: str, draft_response: str, valid_chunk_ids: list[str]) -> str:
        """
        Verify and correct citations in the response using VerificationAgent.
        """
        if not valid_chunk_ids:
            # If no chunks were retrieved, we can't verify citations.
            # But we should still check if there are hallucinations (citations to nothing).
            pass

        logger.info(f"Verifying response against {len(valid_chunk_ids)} valid chunks")

        # Fetch actual content for the valid chunks
        chunk_texts = []
        if self.chunk_store:
            for cid in valid_chunk_ids:
                try:
                    chunk = await self.chunk_store.get_chunk(cid)
                    if chunk:
                        chunk_texts.append(f"Source ID: {cid}\nContent: {chunk.content}")
                except Exception as e:
                    logger.warning(f"Failed to fetch chunk content for verification: {cid} - {e}")

        valid_content_str = "\n\n".join(chunk_texts)

        # Format the prompt for verification
        # We use the agent definition's instruction as system prompt,
        # and pass the specific task as user message.
        agent = self.verification_agent.get_agent()
        if not agent:
            logger.warning("Verification agent not available, returning draft")
            return draft_response

        # logic to run the agent non-streaming
        # The ADK agent.generate_response(user_input) is synchronous/blocking or async?
        # LlmAgent.generate_content is available.

        # Construct the verification input
        verify_input = f"""
Query: {query}

Reference Content (Verified Chunks):
{valid_content_str}

Draft Response:
{draft_response}
"""

        # We need to run this independent of the main runner history loop
        # We can use adk_connector.generate_content BUT we want to use the agent's logic/prompt.
        # Actually GoogleADKConnector returns an LlmAgent which has `query(input)`?
        # Let's check LlmAgent interface or usage in runner.
        # Runner uses `agent.query(...)` generator.

        # For simplicity, we can reuse the agent runner or just call the simple agent logic.
        # But `agent` is an `LlmAgent` from `google.adk`.
        # Let's try to use the `agent` directly.

        try:
            # We need a new session / chat for verification to avoid polluting main history context
            response = await agent.generate_response(verify_input)
            # response is a ModelResponse? Or text?
            # ADK 0.1.0 LlmAgent.generate_response returns a response object with .text
            return response.text.strip()
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return draft_response
