"""Base chunker interface for document processing."""

from abc import ABC, abstractmethod

from src.models.entities.chunk_entities import ChunkCreate


class BaseChunker(ABC):
    """Abstract base class for document chunkers."""

    @abstractmethod
    async def chunk(self, file_path: str, source_id: str, source_name: str) -> list[ChunkCreate]:
        """
        Parse document and extract chunks with bounding boxes.

        Args:
            file_path: Path to the document file
            source_id: Unique identifier for the source
            source_name: Display name for the source

        Returns:
            List of chunk creation objects with bbox information
        """
        pass
