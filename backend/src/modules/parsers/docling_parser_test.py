"""
Docling Document Parser
A comprehensive parser class that uses Docling to parse documents and extract chunks with bounding boxes.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import json

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
except ImportError:
    raise ImportError(
        "Docling is not installed. Install it with: pip install docling"
    )


@dataclass
class BoundingBox:
    """Represents a bounding box with coordinates."""
    x0: float  # left
    y0: float  # top
    x1: float  # right
    y1: float  # bottom
    page: int  # page number (0-indexed)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'x0': self.x0,
            'y0': self.y0,
            'x1': self.x1,
            'y1': self.y1,
            'page': self.page,
            'width': self.width,
            'height': self.height
        }
    
    @property
    def width(self) -> float:
        """Calculate width of bounding box."""
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        """Calculate height of bounding box."""
        return self.y1 - self.y0
    
    @property
    def area(self) -> float:
        """Calculate area of bounding box."""
        return self.width * self.height
    
    def __repr__(self) -> str:
        return f"BBox(page={self.page}, x0={self.x0:.2f}, y0={self.y0:.2f}, x1={self.x1:.2f}, y1={self.y1:.2f})"


@dataclass
class DocumentChunk:
    """Represents a chunk of document content with metadata."""
    text: str
    bbox: Optional[BoundingBox]
    chunk_type: str  # 'text', 'title', 'table', 'list', 'figure', etc.
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            'text': self.text,
            'bbox': self.bbox.to_dict() if self.bbox else None,
            'chunk_type': self.chunk_type,
            'metadata': self.metadata
        }
    
    def __repr__(self) -> str:
        text_preview = self.text[:50] + '...' if len(self.text) > 50 else self.text
        return f"Chunk(type={self.chunk_type}, text='{text_preview}', bbox={self.bbox})"


class DoclingParser:
    """
    A parser class that uses Docling to parse documents and extract chunks with bounding boxes.
    
    Supports: PDF, DOCX, PPTX, images, HTML, and more.
    """
    
    def __init__(
        self,
        extract_tables: bool = True,
        extract_images: bool = True,
        ocr_enabled: bool = True,
        chunk_by_page: bool = False,
        max_chunk_size: Optional[int] = None
    ):
        """
        Initialize the Docling parser.
        
        Args:
            extract_tables: Whether to extract tables
            extract_images: Whether to extract images
            ocr_enabled: Whether to enable OCR for images/scanned PDFs
            chunk_by_page: If True, chunks are split by page
            max_chunk_size: Maximum size of text chunks in characters (None for no limit)
        """
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.ocr_enabled = ocr_enabled
        self.chunk_by_page = chunk_by_page
        self.max_chunk_size = max_chunk_size
        
        # Initialize Docling converter with PDF pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = extract_tables
        pipeline_options.do_ocr = ocr_enabled
        
        # Create converter with format_options parameter (correct API)
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    
    def parse(self, file_path: str) -> List[DocumentChunk]:
        """
        Parse a document and return chunks with bounding boxes.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of DocumentChunk objects containing text and bounding boxes
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Convert document using Docling
        result = self.converter.convert(str(file_path))
        doc = result.document
        
        chunks = []
        
        # Use iterate_items() - the recommended Docling method
        # This gives us all items with their hierarchy level
        for item, level in doc.iterate_items():
            chunk = self._process_element(item)
            if chunk:
                chunks.append(chunk)
        
        # Apply chunking strategy if specified
        if self.max_chunk_size:
            chunks = self._apply_chunking(chunks)
        
        return chunks
    
    def _process_element(self, element) -> Optional[DocumentChunk]:
        """
        Process a document element and create a chunk.
        
        Args:
            element: Document element from Docling
            
        Returns:
            DocumentChunk or None
        """
        # Get element type
        element_type = element.__class__.__name__
        
        # Extract text content
        text = self._extract_text(element)
        if not text or not text.strip():
            return None
        
        # Extract bounding box
        bbox = self._extract_bbox(element)
        
        # Extract metadata
        metadata = self._extract_metadata(element)
        
        # Determine chunk type
        chunk_type = self._determine_chunk_type(element, element_type)
        
        return DocumentChunk(
            text=text,
            bbox=bbox,
            chunk_type=chunk_type,
            metadata=metadata
        )
    
    def _extract_text(self, element) -> str:
        """Extract text content from an element."""
        # TextItem, SectionHeaderItem, ListItem, etc. have .text attribute
        if hasattr(element, 'text') and isinstance(element.text, str):
            return element.text
        
        # TableItem - export to markdown or text
        if hasattr(element, 'export_to_markdown'):
            try:
                return element.export_to_markdown()
            except:
                pass
        
        # Try export_to_text for other items
        if hasattr(element, 'export_to_text'):
            try:
                return element.export_to_text()
            except:
                pass
        
        # GroupItem and other container items might not have text
        # Don't use __str__ as fallback - it returns repr
        return ""
    
    def _extract_bbox(self, element) -> Optional[BoundingBox]:
        """Extract bounding box from an element."""
        try:
            # Docling items have a 'prov' attribute which is a list of ProvenanceItem objects
            if not hasattr(element, 'prov'):
                return None
            
            if not element.prov:
                return None
            
            # Get the first provenance item (usually the main one)
            prov = element.prov[0] if isinstance(element.prov, list) else element.prov
            
            # ProvenanceItem has bbox and page_no attributes
            if not hasattr(prov, 'bbox'):
                return None
            
            if prov.bbox is None:
                return None
            
            bbox_obj = prov.bbox
            page_no = prov.page_no if hasattr(prov, 'page_no') else 0
            
            # Docling's BoundingBox has attributes: l (left), t (top), r (right), b (bottom)
            if not all(hasattr(bbox_obj, attr) for attr in ['l', 't', 'r', 'b']):
                return None
            
            return BoundingBox(
                x0=float(bbox_obj.l),
                y0=float(bbox_obj.t),
                x1=float(bbox_obj.r),
                y1=float(bbox_obj.b),
                page=int(page_no)
            )
                
        except Exception as e:
            # If bbox extraction fails, return None silently
            return None
        
        return None
    
    def _extract_metadata(self, element) -> Dict[str, Any]:
        """Extract metadata from an element."""
        metadata = {}
        
        # Get label if available
        if hasattr(element, 'label'):
            metadata['label'] = str(element.label)
        
        # Get page number from provenance
        if hasattr(element, 'prov') and element.prov:
            prov = element.prov[0] if isinstance(element.prov, list) else element.prov
            if hasattr(prov, 'page_no'):
                metadata['page'] = prov.page_no
        
        # Get parent reference
        if hasattr(element, 'parent') and element.parent:
            metadata['parent'] = str(element.parent)
        
        # For tables - get dimensions
        if hasattr(element, 'data'):
            table_data = element.data
            if hasattr(table_data, 'num_rows'):
                metadata['num_rows'] = table_data.num_rows
            if hasattr(table_data, 'num_cols'):
                metadata['num_cols'] = table_data.num_cols
        
        # Get self reference
        if hasattr(element, 'self_ref'):
            metadata['self_ref'] = element.self_ref
        
        return metadata
    
    def _determine_chunk_type(self, element, element_type: str) -> str:
        """Determine the type of chunk based on element properties."""
        # Map Docling element types to chunk types
        type_mapping = {
            'Title': 'title',
            'SectionHeader': 'section_header',
            'Paragraph': 'text',
            'Text': 'text',
            'Table': 'table',
            'ListItem': 'list_item',
            'Figure': 'figure',
            'Caption': 'caption',
            'Footnote': 'footnote',
            'PageHeader': 'header',
            'PageFooter': 'footer',
        }
        
        # Check label attribute
        if hasattr(element, 'label'):
            label = element.label.lower() if isinstance(element.label, str) else str(element.label)
            for key, value in type_mapping.items():
                if key.lower() in label:
                    return value
        
        # Check element type
        for key, value in type_mapping.items():
            if key.lower() in element_type.lower():
                return value
        
        return 'text'  # default
    
    def _apply_chunking(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Apply chunking strategy to split large chunks.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            List of chunks after applying chunking strategy
        """
        if not self.max_chunk_size:
            return chunks
        
        result = []
        
        for chunk in chunks:
            if len(chunk.text) <= self.max_chunk_size:
                result.append(chunk)
            else:
                # Split large chunks
                sub_chunks = self._split_chunk(chunk)
                result.extend(sub_chunks)
        
        return result
    
    def _split_chunk(self, chunk: DocumentChunk) -> List[DocumentChunk]:
        """Split a large chunk into smaller chunks."""
        text = chunk.text
        chunks = []
        
        # Split by sentences or paragraphs
        sentences = text.split('. ')
        current_text = ""
        
        for sentence in sentences:
            if len(current_text) + len(sentence) < self.max_chunk_size:
                current_text += sentence + '. '
            else:
                if current_text:
                    chunks.append(DocumentChunk(
                        text=current_text.strip(),
                        bbox=chunk.bbox,
                        chunk_type=chunk.chunk_type,
                        metadata={**chunk.metadata, 'is_split': True}
                    ))
                current_text = sentence + '. '
        
        if current_text:
            chunks.append(DocumentChunk(
                text=current_text.strip(),
                bbox=chunk.bbox,
                chunk_type=chunk.chunk_type,
                metadata={**chunk.metadata, 'is_split': True}
            ))
        
        return chunks
    
    def parse_to_json(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Parse document and save results as JSON.
        
        Args:
            file_path: Path to input document
            output_path: Path to save JSON (optional)
            
        Returns:
            JSON string of parsed chunks
        """
        chunks = self.parse(file_path)
        
        # Convert to dictionaries
        chunks_dict = [chunk.to_dict() for chunk in chunks]
        
        json_str = json.dumps(chunks_dict, indent=2, ensure_ascii=False)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def get_chunks_by_type(self, chunks: List[DocumentChunk], chunk_type: str) -> List[DocumentChunk]:
        """Filter chunks by type."""
        return [chunk for chunk in chunks if chunk.chunk_type == chunk_type]
    
    def get_chunks_by_page(self, chunks: List[DocumentChunk], page: int) -> List[DocumentChunk]:
        """Filter chunks by page number."""
        return [
            chunk for chunk in chunks 
            if chunk.bbox and chunk.bbox.page == page
        ]
    
    def export_summary(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Generate a summary of parsed chunks.
        
        Returns:
            Dictionary with statistics and information
        """
        total_chunks = len(chunks)
        chunks_with_bbox = sum(1 for c in chunks if c.bbox is not None)
        
        # Count by type
        type_counts = {}
        for chunk in chunks:
            type_counts[chunk.chunk_type] = type_counts.get(chunk.chunk_type, 0) + 1
        
        # Count by page
        page_counts = {}
        for chunk in chunks:
            if chunk.bbox:
                page = chunk.bbox.page
                page_counts[page] = page_counts.get(page, 0) + 1
        
        return {
            'total_chunks': total_chunks,
            'chunks_with_bbox': chunks_with_bbox,
            'bbox_coverage': f"{chunks_with_bbox / total_chunks * 100:.1f}%" if total_chunks > 0 else "0%",
            'chunks_by_type': type_counts,
            'chunks_by_page': page_counts,
            'total_pages': len(page_counts) if page_counts else 0
        }


def main():
    """Example usage of DoclingParser."""
    
    # Example 1: Basic usage
    print("=== Example 1: Basic Parsing ===")
    parser = DoclingParser()
    
    # Replace with your document path
    doc_path = "sample_document.pdf"
    
    try:
        chunks = parser.parse(doc_path)
        
        print(f"\nParsed {len(chunks)} chunks from document")
        
        # Display first few chunks
        for i, chunk in enumerate(chunks[:5]):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Type: {chunk.chunk_type}")
            print(f"Text: {chunk.text[:100]}...")
            print(f"BBox: {chunk.bbox}")
            print(f"Metadata: {chunk.metadata}")
        
        # Export summary
        summary = parser.export_summary(chunks)
        print("\n=== Summary ===")
        print(json.dumps(summary, indent=2))
        
        # Export to JSON
        parser.parse_to_json(doc_path, "output.json")
        print("\nResults saved to output.json")
        
    except FileNotFoundError:
        print(f"Please provide a valid document path. File not found: {doc_path}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Advanced usage with chunking
    print("\n\n=== Example 2: Advanced Parsing with Chunking ===")
    advanced_parser = DoclingParser(
        extract_tables=True,
        extract_images=True,
        ocr_enabled=True,
        max_chunk_size=500  # Split large chunks
    )
    
    # Example 3: Filter by type
    print("\n\n=== Example 3: Filter Chunks by Type ===")
    try:
        chunks = parser.parse(doc_path)
        
        # Get only tables
        tables = parser.get_chunks_by_type(chunks, 'table')
        print(f"Found {len(tables)} table chunks")
        
        # Get only titles
        titles = parser.get_chunks_by_type(chunks, 'title')
        print(f"Found {len(titles)} title chunks")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()