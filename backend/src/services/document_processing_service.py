"""Document processing service - Orchestrates chunking, embedding, and indexing."""

from loguru import logger

from src.connectors.opensearch_connector import OpenSearchConnector
from src.modules.chunking import DOCXChunker, PDFChunker, PPTXChunker, XLSXChunker
from src.modules.embeddings.gemini_embedder import GeminiEmbedder
from src.stores.opensearch.chunk_store import ChunkStore


class DocumentProcessingService:
    """Orchestrate document parsing, chunking, embedding, and indexing."""

    def __init__(
        self,
        opensearch_connector: OpenSearchConnector,
        embedder: GeminiEmbedder,
    ):
        """Initialize document processing service."""
        self.chunk_store = ChunkStore(opensearch_connector)
        self.embedder = embedder

        # Initialize chunkers
        self.chunkers = {
            "pdf": PDFChunker(),
            "pptx": PPTXChunker(),
            "docx": DOCXChunker(),
            "xlsx": XLSXChunker(),
            "doc": DOCXChunker(),  # Use same chunker for .doc
            "xls": XLSXChunker(),  # Use same chunker for .xls
        }

    async def process_document(
        self,
        file_path: str,
        file_type: str,
        source_id: str,
        source_name: str,
    ) -> int:
        """
        Complete pipeline: chunk → embed → index.

        Args:
            file_path: Path to the document file
            file_type: Type of file (pdf, pptx, docx, xlsx)
            source_id: Unique identifier for the source
            source_name: Display name for the source

        Returns:
            Number of chunks indexed
        """
        try:
            logger.info(f"Starting document processing: {source_name} ({file_type})")

            # 1. Chunk document
            chunker = self.chunkers.get(file_type.lower())
            if not chunker:
                raise ValueError(f"Unsupported file type: {file_type}")

            chunks = await chunker.chunk(file_path, source_id, source_name)
            logger.info(f"Extracted {len(chunks)} chunks from {source_name}")

            if not chunks:
                logger.warning(f"No chunks extracted from {source_name}")
                return 0

            # 2. Generate embeddings
            texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedder.embed_batch(texts)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # 3. Add embeddings to chunk metadata
            for chunk, embedding in zip(chunks, embeddings):
                # Store embedding separately for OpenSearch k-NN
                chunk.metadata["has_embedding"] = True

            # 4. Index in OpenSearch (with embeddings)
            # Note: We need to update ChunkStore to handle embeddings
            from src.models.entities.chunk_entities import Chunk

            # Create chunks with embeddings
            chunks_with_embeddings = []
            for chunk_create, embedding in zip(chunks, embeddings):
                chunk_dict = chunk_create.model_dump()
                chunk_dict["id"] = f"chunk_{source_id}_{len(chunks_with_embeddings)}"
                chunk_dict["embedding"] = embedding
                chunks_with_embeddings.append(chunk_dict)

            # Bulk index
            from opensearchpy import helpers as os_helpers

            actions = [
                {
                    "_index": self.chunk_store.index,
                    "_id": chunk["id"],
                    "_source": chunk,
                }
                for chunk in chunks_with_embeddings
            ]

            os_helpers.bulk(self.chunk_store.client, actions, refresh=True)

            logger.info(f"Successfully indexed {len(chunks)} chunks for {source_name}")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error processing document {source_name}: {e}")
            raise
