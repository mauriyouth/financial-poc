"""Base agent interface for all specialized agents."""

from abc import ABC, abstractmethod

from google.adk.agents import LlmAgent

from src.core.logging import logger


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, description: str) -> None:
        """
        Initialize base agent.

        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description
        self._agent: LlmAgent | None = None
        logger.debug(f"BaseAgent initialized: {name}")

    @abstractmethod
    def get_agent_definition(self) -> LlmAgent | None:
        """
        Get the ADK agent definition.

        This method must be implemented by all specialized agents.
        It should create and return a configured LlmAgent instance.

        Returns:
            Configured LlmAgent or None if creation failed
        """
        pass

    def get_agent(self) -> LlmAgent | None:
        """
        Get the agent instance, creating it if necessary.

        Returns:
            The agent instance or None
        """
        if self._agent is None:
            self._agent = self.get_agent_definition()
        return self._agent

    def is_available(self) -> bool:
        """
        Check if the agent is available and properly configured.

        Returns:
            True if agent is available, False otherwise
        """
        return self.get_agent() is not None
