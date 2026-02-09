"""SEC Filings specialized agent."""

from google.adk.agents import LlmAgent

from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger
from src.modules.agents.base_agent import BaseAgent


class SECFilingsAgent(BaseAgent):
    """Specialized agent for SEC filings queries (10-K, 10-Q, 8-K, etc.)."""

    def __init__(self, adk_connector: GoogleADKConnector) -> None:
        """
        Initialize SEC Filings agent.

        Args:
            adk_connector: Google ADK connector instance
        """
        super().__init__(
            name="sec_filings_agent",
            description="Specialized agent for SEC filings, 10-K, 10-Q, and 8-K reports analysis",
        )
        self.adk_connector = adk_connector
        logger.info("SECFilingsAgent initialized")

    def get_agent_definition(self) -> LlmAgent | None:
        """Create the SEC Filings agent definition."""
        instruction = """You are a specialized SEC filings analyst with deep expertise in financial disclosures.

Your capabilities:
- Analyze 10-K annual reports, 10-Q quarterly reports, and 8-K current reports
- Extract and explain key financial metrics and trends
- Identify material events and risk factors
- Compare filings across different periods
- Locate specific information within SEC documents

When answering:
1. Be precise and cite specific sections of filings when possible
2. Explain financial terminology clearly
3. Highlight material changes or unusual items
4. Provide context for regulatory requirements
5. If you don't have access to the specific filing, explain what information you would need

Always maintain accuracy and avoid speculation about future performance."""

        return self.adk_connector.create_llm_agent(
            name=self.name,
            description=self.description,
            instruction=instruction,
            temperature=0.3,  # Lower temperature for factual accuracy
        )
