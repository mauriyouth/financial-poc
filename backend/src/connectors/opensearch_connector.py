"""OpenSearch connector for chunk storage and retrieval."""

import uuid
from opensearchpy import OpenSearch
from loguru import logger
from src.configurations.opensearch import OpenSearchSettings


class OpenSearchConnector:
    """Connector for OpenSearch operations."""

    def __init__(self, settings: OpenSearchSettings):
        """Initialize OpenSearch connector settings (lazy client creation)."""
        self.settings = settings
        self.chunks_index = "chunks"
        self._client = None  # Lazy initialization
        logger.info(f"OpenSearch connector configured: {settings.OPENSEARCH_HOST}:{settings.OPENSEARCH_PORT}")

    @property
    def client(self) -> OpenSearch:
        """Get OpenSearch client (lazy initialization to avoid fork issues)."""
        if self._client is None:
            self._client = OpenSearch(
                hosts=[{"host": self.settings.OPENSEARCH_HOST, "port": self.settings.OPENSEARCH_PORT}],
                http_auth=(self.settings.OPENSEARCH_USER, self.settings.OPENSEARCH_PASSWORD),
                use_ssl=self.settings.OPENSEARCH_USE_SSL,
                verify_certs=self.settings.OPENSEARCH_VERIFY_CERTS,
            )
            logger.debug(f"OpenSearch client initialized (lazy)")
        return self._client

    def create_chunks_index(self) -> None:
        """Create chunks index with mapping for full-text and vector search."""
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "source_type": {"type": "keyword"},
                    "source_id": {"type": "keyword"},
                    "source_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "content": {"type": "text", "analyzer": "english"},
                    "start_pos": {"type": "integer"},
                    "end_pos": {"type": "integer"},
                    "metadata": {"type": "object"},
                    "embedding": {
                        "type": "knn_vector",  # For semantic search
                        "dimension": 768,  # gemini-embedding-001 dimension
                        "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "faiss",
                            "parameters": {"ef_construction": 128, "m": 24},
                        },
                    },
                    "created_at": {"type": "date"},
                }
            },
            "settings": {
                "index": {
                    "knn": True,  # Enable k-NN search
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                }
            },
        }

        if not self.client.indices.exists(index=self.chunks_index):
            self.client.indices.create(index=self.chunks_index, body=mapping)
            logger.info(f"Created OpenSearch index: {self.chunks_index}")
        else:
            logger.info(f"OpenSearch index already exists: {self.chunks_index}")

    def get_client(self) -> OpenSearch:
        """Get OpenSearch client instance."""
        return self.client
