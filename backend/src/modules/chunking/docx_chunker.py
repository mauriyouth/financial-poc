"""Word document chunker."""

from docx import Document
from loguru import logger

from src.models.entities.chunk_entities import BBox, ChunkCreate, SourceType
from src.modules.chunking.base_chunker import BaseChunker


class DOCXChunker(BaseChunker):
    """Chunk Word documents by paragraph."""

    def __init__(self, min_chunk_length: int = 30):
        """Initialize DOCX chunker."""
        self.min_chunk_length = min_chunk_length

    async def chunk(self, file_path: str, source_id: str, source_name: str) -> list[ChunkCreate]:
        """Extract chunks from Word document."""
        chunks = []

        try:
            doc = Document(file_path)

            for para_num, para in enumerate(doc.paragraphs):
                text = para.text.strip()
                if not text or len(text) < self.min_chunk_length:
                    continue

                chunks.append(
                    ChunkCreate(
                        source_type=SourceType.UPLOADED_FILE,
                        source_id=source_id,
                        source_name=source_name,
                        content=text,
                        bbox=BBox(
                            line_start=para_num,
                            line_end=para_num,
                        ),
                        metadata={
                            "paragraph_number": para_num,
                            "style": para.style.name if para.style else "Normal",
                        },
                    )
                )

            logger.info(f"Extracted {len(chunks)} chunks from DOCX: {source_name}")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking DOCX {source_name}: {e}")
            raise
