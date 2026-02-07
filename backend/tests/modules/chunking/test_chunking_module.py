"""Test chunking module init and integration."""


from src.modules.chunking import (
    BaseChunker,
    DOCXChunker,
    PDFChunker,
    PPTXChunker,
    XLSXChunker,
)


def test_chunker_imports():
    """Test that all chunkers are properly exported."""
    assert BaseChunker is not None
    assert PDFChunker is not None
    assert PPTXChunker is not None
    assert DOCXChunker is not None
    assert XLSXChunker is not None


def test_chunker_inheritance():
    """Test that all chunkers inherit from BaseChunker."""
    assert issubclass(PDFChunker, BaseChunker)
    assert issubclass(PPTXChunker, BaseChunker)
    assert issubclass(DOCXChunker, BaseChunker)
    assert issubclass(XLSXChunker, BaseChunker)


def test_chunker_instantiation():
    """Test that all chunkers can be instantiated."""
    pdf_chunker = PDFChunker()
    pptx_chunker = PPTXChunker()
    docx_chunker = DOCXChunker()
    xlsx_chunker = XLSXChunker()

    assert pdf_chunker is not None
    assert pptx_chunker is not None
    assert docx_chunker is not None
    assert xlsx_chunker is not None


def test_chunker_min_length_param():
    """Test that min_chunk_length parameter works."""
    pdf_chunker = PDFChunker(min_chunk_length=100)
    assert pdf_chunker.min_chunk_length == 100

    pptx_chunker = PPTXChunker(min_chunk_length=50)
    assert pptx_chunker.min_chunk_length == 50
