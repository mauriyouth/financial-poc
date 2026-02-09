"""Orchestrator agent that routes requests to specialized agents."""

from google.adk.agents import LlmAgent

from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger
from src.modules.agents.agent_registry import AgentRegistry
from src.modules.agents.base_agent import BaseAgent


class OrchestratorAgent(BaseAgent):
    """Root agent that intelligently routes user queries to specialized agents."""

    def __init__(self, adk_connector: GoogleADKConnector, registry: AgentRegistry) -> None:
        """
        Initialize Orchestrator agent.

        Args:
            adk_connector: Google ADK connector instance
            registry: Agent registry containing all specialized agents
        """
        super().__init__(
            name="orchestrator",
            description="Root coordinator that routes queries to specialized financial agents",
        )
        self.adk_connector = adk_connector
        self.registry = registry
        logger.info("OrchestratorAgent initialized")

    def get_agent_definition(self) -> LlmAgent | None:
        """Create the orchestrator agent with sub-agents."""
        instruction = """You are an intelligent orchestrator for a financial analysis system.

Your role:
- Analyze incoming user queries
- Route questions to the most appropriate specialized agent:
  * General Chat Agent: For document analysis, uploaded files, RAG queries, general questions
  * SEC Filings Agent: For questions about 10-K, 10-Q, 8-K reports, SEC disclosures
  * Financial Analysis Agent: For calculations, ratios, valuations, quantitative analysis

Routing guidelines:
1. **ALWAYS route document/upload-related queries to General Chat Agent** (has retrieval tool)
2. Route SEC filing-specific questions to SEC Filings Agent
3. Route quantitative calculations to Financial Analysis Agent
4. If a question spans multiple domains, route to the agent covering the primary focus
5. Default to General Chat Agent for ambiguous queries

When delegating:
- Provide clear context to the sub-agent
- Ensure the sub-agent has all necessary information
- Let the specialized agent handle the detailed response"""

        # Get available sub-agents from registry (excluding orchestrator itself to avoid recursion)
        all_agents = self.registry.get_all_agents()
        sub_agents = []

        for agent_name, agent in all_agents.items():
            # Don't include the orchestrator itself to avoid recursion
            if agent_name == self.name:
                continue

            # Check if agent is available
            if not agent.is_available():
                logger.warning(f"Agent '{agent_name}' is not available, skipping")
                continue

            adk_agent = agent.get_agent()
            if adk_agent:
                sub_agents.append(adk_agent)
                logger.debug(f"Added sub-agent to orchestrator: {agent_name}")

        if not sub_agents:
            logger.warning("No sub-agents available for orchestrator")
            return None

        logger.info(f"Creating orchestrator with {len(sub_agents)} sub-agents")

        return self.adk_connector.create_llm_agent(
            name=self.name,
            description=self.description,
            instruction=instruction,
            temperature=0.1,  # Very low temperature for consistent routing
            sub_agents=sub_agents,
        )
