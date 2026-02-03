"""Excel spreadsheet chunker."""

import openpyxl
from loguru import logger

from src.models.entities.chunk_entities import BBox, ChunkCreate, SourceType
from src.modules.chunking.base_chunker import BaseChunker


class XLSXChunker(BaseChunker):
    """Chunk Excel spreadsheets by row."""

    def __init__(self, min_chunk_length: int = 10):
        """Initialize XLSX chunker."""
        self.min_chunk_length = min_chunk_length

    async def chunk(self, file_path: str, source_id: str, source_name: str) -> list[ChunkCreate]:
        """Extract chunks from Excel spreadsheet."""
        chunks = []

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)

            for sheet_idx, sheet in enumerate(wb.worksheets):
                for row_num, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                    # Join non-empty cells
                    text = " | ".join(str(cell).strip() for cell in row if cell)

                    if not text or len(text) < self.min_chunk_length:
                        continue

                    chunks.append(
                        ChunkCreate(
                            source_type=SourceType.UPLOADED_FILE,
                            source_id=source_id,
                            source_name=source_name,
                            content=text,
                            bbox=BBox(
                                page=sheet_idx + 1,  # Sheet number
                                y=row_num,  # Row number
                            ),
                            metadata={
                                "sheet_name": sheet.title,
                                "sheet_index": sheet_idx,
                                "row_number": row_num,
                            },
                        )
                    )

            logger.info(f"Extracted {len(chunks)} chunks from XLSX: {source_name}")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking XLSX {source_name}: {e}")
            raise
