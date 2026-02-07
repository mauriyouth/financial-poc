"""Retrieval tool for AI agents to search document chunks."""

from typing import Optional
from loguru import logger

from src.models.entities.chunk_entities import SourceType
from src.modules.embeddings.gemini_embedder import GeminiEmbedder
from src.stores.opensearch.chunk_store import ChunkStore


def create_retrieval_tool(chunk_store: ChunkStore, embedder: GeminiEmbedder):
    """
    Create retrieval tool for agents.

    Args:
        chunk_store: OpenSearch chunk store
        embedder: Gemini embedder for query embedding

    Returns:
        Retrieval function for agents
    """

    async def retrieve_chunks(
        query: str,
        limit: int = 5,
        source_types: Optional[list[str]] = None,
    ) -> str:
        """
        Retrieve relevant document chunks for a query.

        Use this tool to search through uploaded documents, SEC filings,
        web pages, and other data sources to find relevant information.

        Args:
            query: The search query or question
            limit: Maximum number of chunks to retrieve (default: 5)
            source_types: Filter by source types (uploaded_file, web_page, sec_filing, etc.)

        Returns:
            Formatted chunks with citation markers for referencing sources
        """
        try:
            logger.info(f"Retrieval tool called with query: {query}")

            # Generate query embedding
            query_embedding = await embedder.embed_query(query)

            # Convert source types to enum if provided
            source_type_enums = None
            if source_types:
                source_type_enums = [SourceType(st) for st in source_types]

            # Semantic search in OpenSearch
            chunks = await chunk_store.semantic_search(
                embedding=query_embedding,
                source_types=source_type_enums,
                limit=limit,
            )

            if not chunks:
                return "No relevant documents found for this query."

            # Format results with citation markers
            result_parts = []
            for idx, chunk in enumerate(chunks, 1):
                result_parts.append(f"[{idx}. Source: {chunk.source_name}]\n{chunk.content}\n{{{{cite:{chunk.id}}}}}")

            formatted_result = "\n\n---\n\n".join(result_parts)
            logger.info(f"Retrieved {len(chunks)} chunks for query: {query}")

            return formatted_result

        except Exception as e:
            logger.error(f"Error in retrieval tool: {e}")
            return f"Error retrieving documents: {e!s}"

    return retrieve_chunks
