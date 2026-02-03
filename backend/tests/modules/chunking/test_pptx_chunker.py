"""Test PPTX chunker with mock presentation."""

import pytest
from pptx import Presentation
from pptx.util import Inches

from src.modules.chunking.pptx_chunker import PPTXChunker
from src.models.entities.chunk_entities import SourceType


@pytest.fixture
def mock_pptx_path(tmp_path):
    """Create a mock PowerPoint presentation for testing."""
    pptx_path = tmp_path / "test_presentation.pptx"

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title slide
    slide1 = prs.slides.add_slide(prs.slide_layouts[5])  # Blank layout
    txBox = slide1.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
    tf = txBox.text_frame
    tf.text = "Q4 2023 Financial Results Presentation"

    # Slide 2: Content slide
    slide2 = prs.slides.add_slide(prs.slide_layouts[5])
    txBox2 = slide2.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(2))
    tf2 = txBox2.text_frame
    tf2.text = "Revenue grew 15% year-over-year to $500M with strong customer retention"

    txBox3 = slide2.shapes.add_textbox(Inches(1), Inches(4.5), Inches(8), Inches(1.5))
    tf3 = txBox3.text_frame
    tf3.text = "Operating margin improved to 25% driven by operational efficiency"

    prs.save(str(pptx_path))

    return str(pptx_path)


@pytest.mark.asyncio
async def test_pptx_chunker_basic(mock_pptx_path):
    """Test basic PPTX chunking functionality."""
    chunker = PPTXChunker()

    chunks = await chunker.chunk(
        file_path=mock_pptx_path, source_id="test_pptx_001", source_name="test_presentation.pptx"
    )

    # Should extract 3 chunks (one per text box)
    assert len(chunks) == 3

    # Verify first chunk
    assert chunks[0].source_type == SourceType.UPLOADED_FILE
    assert chunks[0].source_id == "test_pptx_001"
    assert "Financial Results" in chunks[0].content

    # Verify bbox exists with slide number
    assert chunks[0].bbox is not None
    assert chunks[0].bbox.page == 1  # Slide 1
    assert chunks[0].bbox.x is not None
    assert chunks[0].bbox.y is not None
    assert chunks[0].bbox.width > 0
    assert chunks[0].bbox.height > 0


@pytest.mark.asyncio
async def test_pptx_chunker_slide_metadata(mock_pptx_path):
    """Test that slide metadata is properly captured."""
    chunker = PPTXChunker()

    chunks = await chunker.chunk(
        file_path=mock_pptx_path, source_id="test_pptx_002", source_name="test_presentation.pptx"
    )

    # Verify metadata
    assert chunks[0].metadata["slide_number"] == 1
    assert chunks[1].metadata["slide_number"] == 2
    assert "shape_index" in chunks[0].metadata


@pytest.mark.asyncio
async def test_pptx_chunker_min_length(tmp_path):
    """Test minimum chunk length filtering."""
    pptx_path = tmp_path / "short_presentation.pptx"

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(2), Inches(1))
    txBox.text_frame.text = "Short"
    prs.save(str(pptx_path))

    chunker = PPTXChunker(min_chunk_length=50)

    chunks = await chunker.chunk(file_path=str(pptx_path), source_id="test_pptx_003", source_name="short.pptx")

    # Should filter out short text
    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_pptx_chunker_coordinates_conversion(mock_pptx_path):
    """Test that EMU coordinates are properly converted to points."""
    chunker = PPTXChunker()

    chunks = await chunker.chunk(file_path=mock_pptx_path, source_id="test_pptx_004", source_name="test.pptx")

    # Verify coordinates are in reasonable range (points, not EMUs)
    for chunk in chunks:
        # Points should be much smaller than EMUs
        assert chunk.bbox.x < 10000  # EMUs would be in millions
        assert chunk.bbox.y < 10000
        assert chunk.bbox.width < 10000
        assert chunk.bbox.height < 10000
