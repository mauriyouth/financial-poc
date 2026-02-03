"""PDF chunker with bounding box extraction."""

import pdfplumber
from loguru import logger

from src.models.entities.chunk_entities import BBox, ChunkCreate, SourceType
from src.modules.chunking.base_chunker import BaseChunker


class PDFChunker(BaseChunker):
    """Chunk PDF documents with precise bounding box information."""

    def __init__(self, min_chunk_length: int = 50):
        """Initialize PDF chunker."""
        self.min_chunk_length = min_chunk_length

    async def chunk(self, file_path: str, source_id: str, source_name: str) -> list[ChunkCreate]:
        """Extract chunks from PDF with bbox coordinates."""
        chunks = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text with coordinates
                    text = page.extract_text()

                    if not text or len(text.strip()) < self.min_chunk_length:
                        continue

                    # Get page dimensions for bbox
                    page_width = page.width
                    page_height = page.height

                    # For now, create one chunk per page
                    # TODO: Implement paragraph-level chunking with word bboxes
                    chunks.append(
                        ChunkCreate(
                            source_type=SourceType.UPLOADED_FILE,
                            source_id=source_id,
                            source_name=source_name,
                            content=text,
                            bbox=BBox(
                                page=page_num + 1,
                                x=0,
                                y=0,
                                width=page_width,
                                height=page_height,
                            ),
                            metadata={
                                "page_number": page_num + 1,
                                "page_width": page_width,
                                "page_height": page_height,
                            },
                        )
                    )

            logger.info(f"Extracted {len(chunks)} chunks from PDF: {source_name}")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking PDF {source_name}: {e}")
            raise
