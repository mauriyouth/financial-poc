"""General Chat agent for non-specialized queries."""

from google.adk.agents import LlmAgent

from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger
from src.modules.agents.base_agent import BaseAgent


class GeneralChatAgent(BaseAgent):
    """General purpose chat agent for non-specialized queries."""

    def __init__(self, adk_connector: GoogleADKConnector) -> None:
        """
        Initialize General Chat agent.

        Args:
            adk_connector: Google ADK connector instance
        """
        super().__init__(
            name="general_chat_agent",
            description="General purpose assistant for conversational queries and general questions",
        )
        self.adk_connector = adk_connector
        logger.info("GeneralChatAgent initialized")

    def get_agent_definition(self) -> LlmAgent | None:
        """Create the General Chat agent definition."""
        instruction = """You are a helpful and knowledgeable assistant.

Your role:
- Answer general questions about various topics
- Provide explanations and clarifications
- Engage in natural conversation
- Help users understand concepts
- Redirect specialized financial or SEC questions to note that dedicated agents handle those

When responding:
1. Be clear, concise, and helpful
2. Use natural, conversational language
3. Ask clarifying questions when needed
4. Admit when you don't know something
5. Provide sources or suggest where to find more information when relevant

Maintain a friendly, professional tone."""

        return self.adk_connector.create_llm_agent(
            name=self.name,
            description=self.description,
            instruction=instruction,
            temperature=0.7,  # Higher temperature for natural conversation
        )
