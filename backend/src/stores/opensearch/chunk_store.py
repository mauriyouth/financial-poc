"""Chunk store using OpenSearch for full-text and vector search."""

import uuid
from datetime import datetime

from loguru import logger

from src.connectors.opensearch_connector import OpenSearchConnector
from src.models.entities.chunk_entities import Chunk, ChunkCreate, SourceType


class ChunkStore:
    """Store for chunk operations using OpenSearch."""

    def __init__(self, opensearch_connector: OpenSearchConnector):
        """Initialize chunk store with OpenSearch connector."""
        self.client = opensearch_connector.get_client()
        self.index = opensearch_connector.chunks_index
        logger.info(f"ChunkStore initialized with index: {self.index}")

    async def add_chunk(self, chunk_create: ChunkCreate) -> Chunk:
        """
        Add a chunk to OpenSearch.

        Args:
            chunk_create: Chunk creation data

        Returns:
            Created chunk with ID
        """
        chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"

        doc = {
            "id": chunk_id,
            "source_type": chunk_create.source_type.value
            if isinstance(chunk_create.source_type, SourceType)
            else chunk_create.source_type,
            "source_id": chunk_create.source_id,
            "source_name": chunk_create.source_name,
            "content": chunk_create.content,
            "start_pos": chunk_create.start_pos,
            "end_pos": chunk_create.end_pos,
            "metadata": chunk_create.metadata,
            "created_at": datetime.utcnow().isoformat(),
        }

        self.client.index(
            index=self.index,
            id=chunk_id,
            body=doc,
            refresh=True,  # Make immediately searchable
        )

        logger.info(f"Indexed chunk {chunk_id} from {chunk_create.source_name}")
        return Chunk(**doc)

    async def add_chunks_bulk(self, chunks: list[ChunkCreate]) -> list[Chunk]:
        """
        Bulk add multiple chunks to OpenSearch.

        Args:
            chunks: List of chunks to create

        Returns:
            List of created chunks
        """
        from opensearchpy import helpers as os_helpers

        actions = []
        created_chunks = []

        for chunk_create in chunks:
            chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"

            doc = {
                "id": chunk_id,
                "source_type": chunk_create.source_type.value
                if isinstance(chunk_create.source_type, SourceType)
                else chunk_create.source_type,
                "source_id": chunk_create.source_id,
                "source_name": chunk_create.source_name,
                "content": chunk_create.content,
                "start_pos": chunk_create.start_pos,
                "end_pos": chunk_create.end_pos,
                "metadata": chunk_create.metadata,
                "created_at": datetime.utcnow().isoformat(),
            }

            actions.append({"_index": self.index, "_id": chunk_id, "_source": doc})

            created_chunks.append(Chunk(**doc))

        os_helpers.bulk(self.client, actions, refresh=True)
        logger.info(f"Bulk indexed {len(chunks)} chunks")

        return created_chunks

    async def get_chunk(self, chunk_id: str) -> Chunk | None:
        """
        Retrieve chunk by ID.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Chunk if found, None otherwise
        """
        try:
            result = self.client.get(index=self.index, id=chunk_id)
            return Chunk(**result["_source"])
        except Exception as e:
            logger.warning(f"Chunk {chunk_id} not found: {e}")
            return None

    async def search_chunks(
        self,
        query: str,
        source_types: list[SourceType] | None = None,
        source_ids: list[str] | None = None,
        limit: int = 10,
    ) -> list[Chunk]:
        """
        Full-text search for chunks.

        Args:
            query: Search query
            source_types: Filter by source types
            source_ids: Filter by specific sources
            limit: Maximum results

        Returns:
            List of matching chunks
        """
        must_clauses = [
            {"multi_match": {"query": query, "fields": ["content^2", "source_name"], "type": "best_fields"}}
        ]

        filter_clauses = []

        if source_types:
            source_type_values = [st.value if isinstance(st, SourceType) else st for st in source_types]
            filter_clauses.append({"terms": {"source_type": source_type_values}})

        if source_ids:
            filter_clauses.append({"terms": {"source_id": source_ids}})

        search_query = {
            "query": {"bool": {"must": must_clauses, "filter": filter_clauses}},
            "size": limit,
            "sort": ["_score"],
        }

        results = self.client.search(index=self.index, body=search_query)

        chunks = [Chunk(**hit["_source"]) for hit in results["hits"]["hits"]]

        logger.info(f"Found {len(chunks)} chunks for query: {query}")
        return chunks

    async def semantic_search(
        self, embedding: list[float], source_types: list[SourceType] | None = None, limit: int = 10
    ) -> list[Chunk]:
        """
        Semantic search using vector similarity.

        Args:
            embedding: Query embedding vector
            source_types: Filter by source types
            limit: Maximum results

        Returns:
            List of similar chunks
        """
        search_query = {"size": limit, "query": {"knn": {"embedding": {"vector": embedding, "k": limit}}}}

        if source_types:
            source_type_values = [st.value if isinstance(st, SourceType) else st for st in source_types]
            search_query["query"] = {
                "bool": {"must": [search_query["query"]], "filter": {"terms": {"source_type": source_type_values}}}
            }

        results = self.client.search(index=self.index, body=search_query)

        chunks = [Chunk(**hit["_source"]) for hit in results["hits"]["hits"]]

        logger.info(f"Found {len(chunks)} chunks via semantic search")
        return chunks

    async def delete_chunks_by_source(self, source_id: str) -> int:
        """
        Delete all chunks from a specific source.

        Args:
            source_id: Source identifier

        Returns:
            Number of chunks deleted
        """
        delete_query = {"query": {"term": {"source_id": source_id}}}

        result = self.client.delete_by_query(index=self.index, body=delete_query, refresh=True)

        deleted = result.get("deleted", 0)
        logger.info(f"Deleted {deleted} chunks from source: {source_id}")
        return deleted
