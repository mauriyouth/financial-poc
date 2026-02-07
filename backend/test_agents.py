"""Test script to verify multi-agent system is working."""

import asyncio

from src.connectors.anthropic_connector import AnthropicConnector
from src.connectors.gemini_connector import GeminiConnector
from src.connectors.google_adk_connector import GoogleADKConnector
from src.modules.agents.agent_registry import AgentRegistry
from src.modules.agents.financial_analysis_agent import FinancialAnalysisAgent
from src.modules.agents.general_chat_agent import GeneralChatAgent
from src.modules.agents.orchestrator_agent import OrchestratorAgent
from src.modules.agents.sec_filings_agent import SECFilingsAgent
from src.services.ai_service import AIService


async def test_agent_system() -> None:
    """Test the multi-agent system."""
    print("=" * 60)
    print("MULTI-AGENT SYSTEM TEST")
    print("=" * 60)

    # 1. Initialize connectors
    print("\n1. Initializing connectors...")
    anthropic = AnthropicConnector()
    gemini = GeminiConnector()
    adk_connector = GoogleADKConnector()

    if not adk_connector.is_configured():
        print("✗ Google API key not configured. Please set GOOGLE_API_KEY in .env")
        return

    print("✓ Connectors initialized")

    # 2. Create agent registry
    print("\n2. Creating agent registry...")
    registry = AgentRegistry()
    print("✓ Registry created")

    # 3. Register specialized agents
    print("\n3. Registering specialized agents...")
    sec_agent = SECFilingsAgent(adk_connector)
    financial_agent = FinancialAnalysisAgent(adk_connector)
    general_agent = GeneralChatAgent(adk_connector)

    registry.register(sec_agent)
    registry.register(financial_agent)
    registry.register(general_agent)

    available_agents = registry.get_available_agents()
    print(f"✓ Registered {len(available_agents)} agents:")
    for agent_name in available_agents:
        print(f"   - {agent_name}  ")

    # 4. Create orchestrator
    print("\n4. Creating orchestrator agent...")
    orchestrator = OrchestratorAgent(adk_connector, registry)
    registry.register(orchestrator)

    if not orchestrator.is_available():
        print("✗ Orchestrator agent failed to initialize")
        return

    print("✓ Orchestrator agent created with sub-agents")

    # 5. Create AI Service
    print("\n5. Creating AI Service...")
    ai_service = AIService(anthropic, gemini, adk_connector, orchestrator)
    print("✓ AI Service initialized")

    # 6. Test queries
    print("\n6. Testing agent routing with sample queries...")

    test_queries = [
        "What is a 10-K filing?",
        "Calculate the P/E ratio if price is $50 and EPS is $5",
        "Hello, how are you?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: '{query}'")
        print("   Streaming response:")
        print("   " + "-" * 50)

        try:
            chunk_count = 0
            async for chunk in ai_service.stream_generate(query, provider="adk"):
                chunk_count += 1
                if chunk_count <= 5:  # Show first 5 chunks
                    print(f"   {chunk.strip()}")

            print(f"   ... (total {chunk_count} chunks)")
            print("   ✓ Query completed successfully")

        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_agent_system())
