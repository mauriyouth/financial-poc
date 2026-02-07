from google.adk.agents import LlmAgent

from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger


class SimpleChatAgent:
    """
    Simple Chat Agent that wraps explicit providers into an ADK-like interface.
    """

    def __init__(
        self,
        adk_connector: GoogleADKConnector,
    ) -> None:
        self.adk_connector = adk_connector

    def get_agent(self, model: str, instruction: str | None = None) -> LlmAgent | None:
        """
        Create a simple ADK agent configured for the specific model.
        """
        instruction = instruction or "You are a helpful assistant."

        # Create an ephemeral agent with the requested configuration
        logger.debug(f"Creating LLM agent {model}")
        return self.adk_connector.create_llm_agent(
            name="simple_chat",
            description="Simple chat agent",
            instruction=instruction,
            model=model,
            temperature=0.7,
        )
