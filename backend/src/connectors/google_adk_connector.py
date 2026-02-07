"""Google ADK connector for agent framework."""

from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

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
            generate_config = {}
            if temperature is not None:
                generate_config["temperature"] = temperature

            # Prepare planning config with Thinking

            planner = BuiltInPlanner(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True,
                    thinking_budget=500,
                )
            )
            agent = LlmAgent(
                name=name,
                model=model,
                description=description,
                instruction=instruction,
                tools=tools or [],
                sub_agents=sub_agents or [],
                planner=planner,
                generate_content_config=generate_config,
            )
            logger.info(f"Successfully created agent: {name}")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent '{name}': {e}")
            return None

    async def generate_content(self, prompt: str, model: str | None = None) -> str:
        """
        Generate content using Gemini directly (for non-agent tasks like summarization).
        """
        import google.generativeai as genai

        if not self.api_key:
            raise ValueError("Google API key not configured")

        try:
            genai.configure(api_key=self.api_key)
            model_name = model or self.default_model

            # Map ADK model names to genai model names if needed
            # For now assume they are compatible or use flash default
            if "claude" in model_name:  # Fallback for non-gemini default
                model_name = "gemini-2.0-flash"

            gemini_model = genai.GenerativeModel(model_name)
            response = await gemini_model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            raise
