"""Financial Analysis specialized agent."""

from google.adk.agents import LlmAgent

from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger
from src.modules.agents.base_agent import BaseAgent


class FinancialAnalysisAgent(BaseAgent):
    """Specialized agent for financial calculations and analysis."""

    def __init__(self, adk_connector: GoogleADKConnector) -> None:
        """
        Initialize Financial Analysis agent.

        Args:
            adk_connector: Google ADK connector instance
        """
        super().__init__(
            name="financial_analysis_agent",
            description="Specialized agent for financial calculations, ratios, valuation, and quantitative analysis",
        )
        self.adk_connector = adk_connector
        logger.info("FinancialAnalysisAgent initialized")

    def get_agent_definition(self) -> LlmAgent | None:
        """Create the Financial Analysis agent definition."""
        instruction = """You are a specialized financial analyst with expertise in quantitative analysis and valuation.

Your capabilities:
- Calculate financial ratios (liquidity, profitability, leverage, efficiency)
- Perform valuation analysis (DCF, multiples, comparable companies)
- Analyze financial statement trends and relationships
- Compute key metrics (ROE, ROIC, EPS, P/E, etc.)
- Evaluate credit quality and financial health
- Assess working capital and cash flow dynamics

When performing analysis:
1. Show your calculations step-by-step
2. Explain the meaning and significance of each metric
3. Provide industry context and benchmarks when relevant
4. Identify strengths, weaknesses, and potential concerns
5. Use clear formulas and define all terms

Always maintain numerical accuracy and clearly state any assumptions made."""

        return self.adk_connector.create_llm_agent(
            name=self.name,
            description=self.description,
            instruction=instruction,
            temperature=0.2,  # Very low temperature for numerical accuracy
        )
