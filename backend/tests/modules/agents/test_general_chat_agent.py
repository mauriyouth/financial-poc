import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.modules.agents.general_chat_agent import GeneralChatAgent
from src.connectors.google_adk_connector import GoogleADKConnector
from src.connectors.opensearch_connector import OpenSearchConnector
from src.modules.embeddings.gemini_embedder import GeminiEmbedder
from src.models.entities.chunk_entities import Chunk, SourceType
from uuid import uuid4


@pytest.fixture
def mock_adk_connector():
    connector = MagicMock(spec=GoogleADKConnector)
    connector.create_llm_agent = MagicMock(return_value=MagicMock())
    return connector


@pytest.fixture
def mock_opensearch_connector():
    connector = MagicMock(spec=OpenSearchConnector)
    connector.create_chunks_index = MagicMock()
    # Mock chunks_index property which is accessed by ChunkStore
    type(connector).chunks_index = MagicMock()
    return connector


@pytest.fixture
def mock_embedder():
    embedder = MagicMock(spec=GeminiEmbedder)
    embedder.embed_query = AsyncMock(return_value=[0.1] * 768)
    return embedder


@pytest.fixture
def general_chat_agent(mock_adk_connector, mock_opensearch_connector, mock_embedder):
    return GeneralChatAgent(
        adk_connector=mock_adk_connector, opensearch_connector=mock_opensearch_connector, embedder=mock_embedder
    )


@pytest.mark.asyncio
async def test_initialization(general_chat_agent, mock_adk_connector):
    """Test agent initialization and definition creation."""
    assert general_chat_agent.name == "general_chat_agent"

    agent_def = general_chat_agent.get_agent_definition()

    assert agent_def is not None
    mock_adk_connector.create_llm_agent.assert_called_once()
    call_args = mock_adk_connector.create_llm_agent.call_args[1]
    assert call_args["name"] == "general_chat_agent"
    assert "tools" in call_args
    assert len(call_args["tools"]) == 1  # retrieval tool


@pytest.mark.asyncio
async def test_retrieval_tool_usage(general_chat_agent, mock_opensearch_connector, mock_embedder):
    """Test that the retrieval tool correctly queries OpenSearch."""
    # Setup mock chunk store response
    mock_chunk = Chunk(
        id=str(uuid4()),
        content="This is test content",
        source_name="test_doc.pdf",
        source_type=SourceType.UPLOADED_FILE.value,
        source_id=str(uuid4()),
        embedding=[0.1] * 768,
        metadata={},
    )

    # We need to access the retrieval tool created inside get_agent_definition
    # Since it's a closure, we can't easily access it directly from the agent instance without
    # intercepting the create_llm_agent call or modifying the class to expose it.
    # However, for unit testing the TOOL logic specifically, we can import the create_retrieval_tool function.

    from src.modules.agents.tools.retrieval_tool import create_retrieval_tool

    # Mock ChunkStore inside the tool
    with patch("src.modules.agents.tools.retrieval_tool.ChunkStore") as MockChunkStore:
        mock_store_instance = MockChunkStore.return_value
        mock_store_instance.semantic_search = AsyncMock(return_value=[mock_chunk])

        retrieval_tool = create_retrieval_tool(mock_store_instance, mock_embedder)

        # Test the tool function
        query = "test query"
        result = await retrieval_tool(query=query)

        # Verify interactions
        mock_embedder.embed_query.assert_called_with(query)
        mock_store_instance.semantic_search.assert_called_once()

        # Verify result format (citation check)
        assert "This is test content" in result
        assert f"{{{{cite:{mock_chunk.id}}}}}" in result


@pytest.mark.asyncio
async def test_hallucination_prevention_empty_results(general_chat_agent, mock_embedder):
    """Test that the tool returns a standard 'not found' message when no chunks are found."""
    from src.modules.agents.tools.retrieval_tool import create_retrieval_tool

    with patch("src.modules.agents.tools.retrieval_tool.ChunkStore") as MockChunkStore:
        mock_store_instance = MockChunkStore.return_value
        mock_store_instance.semantic_search = AsyncMock(return_value=[])  # Empty results

        retrieval_tool = create_retrieval_tool(mock_store_instance, mock_embedder)

        result = await retrieval_tool(query="unknown topic")

        assert "No relevant documents found" in result
        # Ensure no fake citations are generated
        assert "{{cite:" not in result


@pytest.mark.asyncio
async def test_extreme_scenario_tool_error(general_chat_agent, mock_embedder):
    """Test tool behavior when underlying services fail (extreme scenario)."""
    from src.modules.agents.tools.retrieval_tool import create_retrieval_tool

    with patch("src.modules.agents.tools.retrieval_tool.ChunkStore") as MockChunkStore:
        mock_store_instance = MockChunkStore.return_value
        mock_store_instance.semantic_search = AsyncMock(side_effect=Exception("Database down"))

        retrieval_tool = create_retrieval_tool(mock_store_instance, mock_embedder)

        result = await retrieval_tool(query="crash test")

        assert "Error retrieving documents" in result
        assert "Database down" in result


@pytest.mark.asyncio
async def test_extreme_scenario_large_input(general_chat_agent, mock_embedder):
    """Test tool handling of very large queries (boundary test)."""
    from src.modules.agents.tools.retrieval_tool import create_retrieval_tool

    large_query = "word " * 10000

    with patch("src.modules.agents.tools.retrieval_tool.ChunkStore") as MockChunkStore:
        mock_store_instance = MockChunkStore.return_value
        mock_store_instance.semantic_search = AsyncMock(return_value=[])

        retrieval_tool = create_retrieval_tool(mock_store_instance, mock_embedder)

        # Should not crash
        await retrieval_tool(query=large_query)

        mock_embedder.embed_query.assert_called_once()
