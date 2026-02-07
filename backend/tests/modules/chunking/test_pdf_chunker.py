"""Test PDF chunker with mock document."""

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.models.entities.chunk_entities import SourceType
from src.modules.chunking.pdf_chunker import PDFChunker


@pytest.fixture
def mock_pdf_path(tmp_path):
    """Create a mock PDF document for testing."""
    pdf_path = tmp_path / "test_document.pdf"

    # Create a simple PDF with reportlab
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Page 1
    c.drawString(100, 750, "Financial Report Q4 2023")
    c.drawString(100, 700, "Total revenue was $394.3 billion, an increase of 8% year over year.")
    c.drawString(100, 650, "Operating income reached $120 billion with strong margins.")
    c.showPage()

    # Page 2
    c.drawString(100, 750, "Market Analysis")
    c.drawString(100, 700, "The company expanded into new markets with significant growth potential.")
    c.drawString(100, 650, "Customer satisfaction scores improved by 15% across all segments.")
    c.showPage()

    c.save()

    return str(pdf_path)


@pytest.mark.asyncio
async def test_pdf_chunker_basic(mock_pdf_path):
    """Test basic PDF chunking functionality."""
    chunker = PDFChunker()

    chunks = await chunker.chunk(file_path=mock_pdf_path, source_id="test_pdf_001", source_name="test_document.pdf")

    # Should extract 2 chunks (one per page)
    assert len(chunks) == 2

    # Verify first chunk
    assert chunks[0].source_type == SourceType.UPLOADED_FILE
    assert chunks[0].source_id == "test_pdf_001"
    assert chunks[0].source_name == "test_document.pdf"
    assert "Financial Report" in chunks[0].content
    assert "394.3 billion" in chunks[0].content

    # Verify bbox exists
    assert chunks[0].bbox is not None
    assert chunks[0].bbox.page == 1
    assert chunks[0].bbox.x == 0
    assert chunks[0].bbox.y == 0
    assert chunks[0].bbox.width > 0
    assert chunks[0].bbox.height > 0

    # Verify metadata
    assert chunks[0].metadata["page_number"] == 1


@pytest.mark.asyncio
async def test_pdf_chunker_bbox_coordinates(mock_pdf_path):
    """Test that bbox coordinates are properly extracted."""
    chunker = PDFChunker()

    chunks = await chunker.chunk(file_path=mock_pdf_path, source_id="test_pdf_002", source_name="test_document.pdf")

    # Check that each chunk has different page numbers
    page_numbers = [chunk.bbox.page for chunk in chunks]
    assert page_numbers == [1, 2]

    # Verify page dimensions are captured
    for chunk in chunks:
        assert chunk.metadata["page_width"] > 0
        assert chunk.metadata["page_height"] > 0


@pytest.mark.asyncio
async def test_pdf_chunker_min_length_filter(tmp_path):
    """Test minimum chunk length filtering."""
    # Create PDF with very short text
    pdf_path = tmp_path / "short_text.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "Short")
    c.save()

    chunker = PDFChunker(min_chunk_length=50)

    chunks = await chunker.chunk(file_path=str(pdf_path), source_id="test_pdf_003", source_name="short_text.pdf")

    # Should not create chunks for text shorter than min_chunk_length
    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_pdf_chunker_error_handling():
    """Test error handling for invalid PDF."""
    chunker = PDFChunker()

    with pytest.raises(Exception):
        await chunker.chunk(file_path="/nonexistent/file.pdf", source_id="test_pdf_999", source_name="nonexistent.pdf")
