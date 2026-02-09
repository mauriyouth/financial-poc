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
                    words = page.extract_words()
                    current_chunk_words = []

                    # Simple paragraph detection based on vertical distance
                    if not words:
                        continue

                    # Group words into lines/paragraphs
                    # This is a naive implementation: valid for continuous text
                    last_bottom = 0

                    for word in words:
                        # If vertical gap is large (> 2x line height estimate), start new chunk
                        # Average word height is approx bottom - top
                        word_height = word["bottom"] - word["top"]
                        gap = word["top"] - last_bottom

                        if current_chunk_words and gap > word_height * 1.5:
                            # Finalize current chunk
                            text = " ".join([w["text"] for w in current_chunk_words])
                            if len(text) >= self.min_chunk_length:
                                # Calculate bbox
                                x0 = min(w["x0"] for w in current_chunk_words)
                                top = min(w["top"] for w in current_chunk_words)
                                x1 = max(w["x1"] for w in current_chunk_words)
                                bottom = max(w["bottom"] for w in current_chunk_words)

                                chunks.append(
                                    ChunkCreate(
                                        source_type=SourceType.UPLOADED_FILE,
                                        source_id=source_id,
                                        source_name=source_name,
                                        content=text,
                                        bbox=BBox(
                                            page=page_num + 1,
                                            x=x0,
                                            y=top,
                                            width=x1 - x0,
                                            height=bottom - top,
                                        ),
                                        metadata={
                                            "page_number": page_num + 1,
                                            "page_width": page.width,
                                            "page_height": page.height,
                                        },
                                    )
                                )
                            current_chunk_words = []

                        current_chunk_words.append(word)
                        last_bottom = word["bottom"]

                    # Add remaining words
                    if current_chunk_words:
                        text = " ".join([w["text"] for w in current_chunk_words])
                        if len(text) >= self.min_chunk_length:
                            x0 = min(w["x0"] for w in current_chunk_words)
                            top = min(w["top"] for w in current_chunk_words)
                            x1 = max(w["x1"] for w in current_chunk_words)
                            bottom = max(w["bottom"] for w in current_chunk_words)

                            chunks.append(
                                ChunkCreate(
                                    source_type=SourceType.UPLOADED_FILE,
                                    source_id=source_id,
                                    source_name=source_name,
                                    content=text,
                                    bbox=BBox(
                                        page=page_num + 1,
                                        x=x0,
                                        y=top,
                                        width=x1 - x0,
                                        height=bottom - top,
                                    ),
                                    metadata={
                                        "page_number": page_num + 1,
                                        "page_width": page.width,
                                        "page_height": page.height,
                                    },
                                )
                            )

            logger.info(f"Extracted {len(chunks)} chunks from PDF: {source_name}")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking PDF {source_name}: {e}")
            raise
