"""Agent registry for managing all available agents."""

from src.core.logging import logger
from src.modules.agents.base_agent import BaseAgent


class AgentRegistry:
    """Singleton registry for managing all agents in the system."""

    _instance: "AgentRegistry | None" = None
    _initialized: bool = False

    def __new__(cls) -> "AgentRegistry":
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry (only once)."""
        # Prevent re-initialization
        if AgentRegistry._initialized:
            return

        self._agents: dict[str, BaseAgent] = {}
        AgentRegistry._initialized = True
        logger.info("AgentRegistry initialized")

    def register(self, agent: BaseAgent) -> None:
        """
        Register a new agent.

        Args:
            agent: The agent to register
        """
        if agent.name in self._agents:
            logger.warning(f"Agent '{agent.name}' already registered, overwriting")

        self._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    def get_agent(self, name: str) -> BaseAgent | None:
        """
        Get an agent by name.

        Args:
            name: The agent name

        Returns:
            The agent or None if not found
        """
        agent = self._agents.get(name)
        if agent is None:
            logger.warning(f"Agent '{name}' not found in registry")
        return agent

    def get_all_agents(self) -> dict[str, BaseAgent]:
        """
        Get all registered agents.

        Returns:
            Dictionary of all agents
        """
        return self._agents.copy()

    def get_available_agents(self) -> dict[str, BaseAgent]:
        """
        Get all agents that are currently available (properly configured).

        Returns:
            Dictionary of available agents
        """
        return {name: agent for name, agent in self._agents.items() if agent.is_available()}

    def list_agent_names(self) -> list[str]:
        """
        Get list of all registered agent names.

        Returns:
            List of agent names
        """
        return list(self._agents.keys())

    def clear(self) -> None:
        """Clear all registered agents (useful for testing)."""
        self._agents.clear()
        logger.debug("Agent registry cleared")
