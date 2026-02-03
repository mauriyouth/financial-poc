"""Google ADK connector for agent framework."""

from google.adk.agents import LlmAgent

from src.configurations.settings import settings
from src.core.logging import logger


class GoogleADKConnector:
    """Connector for Google ADK (Agent Development Kit)."""

    def __init__(self) -> None:
        """Initialize the Google ADK connector."""
        self.api_key = settings.GOOGLE_API_KEY
        if not self.api_key:
            logger.warning("Google API key not configured for ADK")
        else:
            logger.info("Google ADK connector initialized")

        # Store default model configuration
        self.default_model = settings.ADK_DEFAULT_MODEL
        self.default_temperature = settings.ADK_DEFAULT_TEMPERATURE

    def is_configured(self) -> bool:
        """Check if ADK is properly configured."""
        return bool(self.api_key)

    def create_llm_agent(
        self,
        name: str,
        description: str,
        instruction: str,
        model: str | None = None,
        temperature: float | None = None,
        tools: list | None = None,
        sub_agents: list | None = None,
    ) -> LlmAgent | None:
        """
        Create an LLM agent with Google ADK.

        Args:
            name: Agent name
            description: Agent description
            instruction: System instruction for the agent
            model: Model name (defaults to settings.ADK_DEFAULT_MODEL)
            temperature: Model temperature (defaults to settings.ADK_DEFAULT_TEMPERATURE)
            tools: List of tools for the agent
            sub_agents: List of sub-agents for orchestration

        Returns:
            LlmAgent instance or None if not configured
        """
        if not self.is_configured():
            logger.error(f"Cannot create agent '{name}': Google API key not configured")
            return None

        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature

        logger.debug(f"Creating LLM agent: {name} with model {model}")

        try:
            # Prepare generation config if temperature is specified
            generate_config = None
            if temperature is not None:
                generate_config = {"temperature": temperature}

            agent = LlmAgent(
                name=name,
                model=model,
                description=description,
                instruction=instruction,
                tools=tools or [],
                sub_agents=sub_agents or [],
                generate_content_config=generate_config,
            )
            logger.info(f"Successfully created agent: {name}")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent '{name}': {e}")
            return None
