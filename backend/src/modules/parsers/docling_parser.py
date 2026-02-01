"""
Docling parser module for document parsing.
"""

import io
from dataclasses import dataclass

from docling.document_converter import DocumentConverter


@dataclass
class ParseResult:
    """Result of document parsing."""

    markdown: str
    html: str


def parse_document(pdf_bytes: bytes) -> ParseResult:
    """
    Parse PDF document using docling.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        ParseResult with markdown and HTML content

    Raises:
        Exception: If parsing fails
    """
    try:
        # Initialize docling converter
        converter = DocumentConverter()

        # Convert bytes to file-like object
        pdf_buffer = io.BytesIO(pdf_bytes)

        # Parse document
        result = converter.convert(pdf_buffer)

        # Export to markdown and HTML
        markdown_content = result.document.export_to_markdown()
        html_content = result.document.export_to_html()

        return ParseResult(markdown=markdown_content, html=html_content)

    except Exception as e:
        raise Exception(f"Failed to parse document with docling: {e!s}") from e
