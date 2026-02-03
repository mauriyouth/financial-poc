"""Citation parser - Extract and resolve citations from agent responses."""

import re

from loguru import logger

from src.models.entities.citation_entities import Citation
from src.stores.opensearch.chunk_store import ChunkStore


class CitationParser:
    """Parse citation markers and fetch chunk metadata."""

    # Pattern to match {{cite:chunk_id}}
    CITATION_PATTERN = r"\{\{cite:([a-zA-Z0-9_-]+)\}\}"

    def __init__(self, chunk_store: ChunkStore):
        """Initialize citation parser."""
        self.chunk_store = chunk_store

    async def parse_citations(self, text: str) -> tuple[str, list[Citation]]:
        """
        Extract citations from text and fetch chunk metadata.

        Args:
            text: Agent response text with citation markers

        Returns:
            Tuple of (cleaned_text, citations_list)
            - cleaned_text: Text with {{cite:id}} replaced by [1], [2], etc.
            - citations_list: List of Citation objects with bbox info
        """
        # Find all unique citation IDs
        citation_ids = re.findall(self.CITATION_PATTERN, text)
        unique_citation_ids = list(dict.fromkeys(citation_ids))  # Preserve order

        logger.info(f"Found {len(unique_citation_ids)} unique citations")

        citations = []

        # Fetch chunks for all citations
        for idx, chunk_id in enumerate(unique_citation_ids, 1):
            try:
                chunk = await self.chunk_store.get_chunk(chunk_id)

                if chunk:
                    citations.append(
                        Citation(
                            id=f"cite_{idx}",
                            chunk_id=chunk_id,
                            source_name=chunk.source_name,
                            source_type=chunk.source_type.value,
                            content=chunk.content,
                            bbox=chunk.bbox.dict() if chunk.bbox else None,
                            metadata=chunk.metadata,
                        )
                    )
                else:
                    logger.warning(f"Chunk not found: {chunk_id}")

            except Exception as e:
                logger.error(f"Error fetching chunk {chunk_id}: {e}")

        # Replace {{cite:id}} with [1], [2], etc.
        cleaned_text = text
        for idx, chunk_id in enumerate(unique_citation_ids, 1):
            cleaned_text = cleaned_text.replace(f"{{{{cite:{chunk_id}}}}}", f"[{idx}]")

        logger.info(f"Parsed {len(citations)} citations successfully")

        return cleaned_text, citations
