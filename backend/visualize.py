"""
Bounding Box Visualization Script

This script takes the parsed document chunks with bboxes and draws them
on the original PDF pages to verify they're correct.
"""

from docling_parser import DoclingParser
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
from pathlib import Path
import random
from typing import List, Tuple

# Color palette for different chunk types
COLORS = {
    'text': (0, 128, 255, 100),      # Blue
    'title': (255, 0, 0, 100),       # Red
    'section_header': (255, 128, 0, 100),  # Orange
    'table': (0, 255, 0, 100),       # Green
    'list_item': (255, 0, 255, 100), # Magenta
    'figure': (255, 255, 0, 100),    # Yellow
    'caption': (128, 0, 255, 100),   # Purple
    'default': (128, 128, 128, 100)  # Gray
}

def get_color_for_type(chunk_type: str) -> Tuple[int, int, int, int]:
    """Get color for a chunk type."""
    return COLORS.get(chunk_type, COLORS['default'])

def pdf_to_images(pdf_path: str, dpi: int = 150) -> List[Image.Image]:
    """Convert PDF pages to PIL Images."""
    print(f"Converting PDF to images (DPI={dpi})...")
    
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Render page to pixmap
        mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 DPI is PDF default
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
        
        print(f"  Page {page_num + 1}: {img.width}x{img.height}")
    
    doc.close()
    return images

def draw_bboxes_on_images(images: List[Image.Image], chunks, dpi: int = 150):
    """Draw bounding boxes on images."""
    print(f"\nDrawing {len(chunks)} bounding boxes...")
    
    # Create a copy of images for drawing
    annotated_images = [img.copy() for img in images]
    
    # Group chunks by page
    chunks_by_page = {}
    for chunk in chunks:
        if chunk.bbox:
            page = chunk.bbox.page
            if page not in chunks_by_page:
                chunks_by_page[page] = []
            chunks_by_page[page].append(chunk)
    
    print(f"Found chunks on {len(chunks_by_page)} pages")
    
    # Draw on each page
    for page_num, page_chunks in chunks_by_page.items():
        if page_num >= len(annotated_images):
            print(f"  Warning: Page {page_num} is out of range")
            continue
        
        img = annotated_images[page_num]
        draw = ImageDraw.Draw(img, 'RGBA')
        page_height = img.height / (dpi / 72)  # Convert pixels to points

        print(f"\n  Page {page_num}:")
        print(f"    Image size: {img.width}x{img.height}")
        print(f"    Page height (PDF points): {page_height:.1f}")
        print(f"    Number of chunks: {len(page_chunks)}")
        
        # Debug: show first chunk's coordinates in detail
        if page_chunks:
            first_bbox = page_chunks[0].bbox
            print(f"\n    Debug - First chunk bbox:")
            print(f"      PDF (BOTTOMLEFT): x=[{first_bbox.x0:.1f}, {first_bbox.x1:.1f}], y=[{first_bbox.y0:.1f}, {first_bbox.y1:.1f}]")
            print(f"      In PDF: y0={first_bbox.y0:.1f} is BOTTOM, y1={first_bbox.y1:.1f} is TOP")
        
        print()
        
        # Get page dimensions from first chunk or use image size
        
        for i, chunk in enumerate(page_chunks):
            bbox = chunk.bbox
            
            # Docling uses BOTTOMLEFT origin by default
            # Scale from PDF points to image pixels
            scale = dpi / 72
            
            # X coordinates are straightforward
            x0 = bbox.x0 * scale
            x1 = bbox.x1 * scale
            
            # Y coordinates need conversion from BOTTOMLEFT to TOPLEFT
            # In BOTTOMLEFT: y0 is bottom, y1 is top
            # In TOPLEFT (image): y0 is top, y1 is bottom
            # So we need to flip: bbox.y1 (top) becomes image y0, bbox.y0 (bottom) becomes image y1
            
            y0_top = (page_height - bbox.y1) * scale  # Top of bbox in image coords
            y1_top = (page_height - bbox.y0) * scale  # Bottom of bbox in image coords
            
            # Ensure y0 < y1 (top < bottom in image coordinates)
            if y0_top > y1_top:
                y0_top, y1_top = y1_top, y0_top
            
            # Ensure coordinates are within image bounds
            x0 = max(0, min(x0, img.width))
            x1 = max(0, min(x1, img.width))
            y0_top = max(0, min(y0_top, img.height))
            y1_top = max(0, min(y1_top, img.height))
            
            # Skip if bbox is invalid
            if x0 >= x1 or y0_top >= y1_top:
                if i < 3:
                    print(f"      Chunk {i}: SKIPPED (invalid bbox)")
                continue
            
            # Draw bounding box
            color = get_color_for_type(chunk.chunk_type)
            
            try:
                # Draw filled rectangle with transparency
                draw.rectangle(
                    [(x0, y0_top), (x1, y1_top)],
                    outline=color[:3] + (255,),  # Solid outline
                    fill=color,  # Semi-transparent fill
                    width=2
                )
                
                # Draw label
                label = f"{chunk.chunk_type[:10]}"
                
                # Use default font
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
                except:
                    font = ImageFont.load_default()
                
                # Draw text background
                text_y = max(0, y0_top - 15)
                text_bbox = draw.textbbox((x0, text_y), label, font=font)
                draw.rectangle(text_bbox, fill=(255, 255, 255, 200))
                draw.text((x0, text_y), label, fill=(0, 0, 0, 255), font=font)
                
                if i < 3:  # Show details for first 3 chunks
                    print(f"      Chunk {i}: {chunk.chunk_type}")
                    print(f"        PDF coords: ({bbox.x0:.1f}, {bbox.y0:.1f}) -> ({bbox.x1:.1f}, {bbox.y1:.1f})")
                    print(f"        Image coords: ({x0:.1f}, {y0_top:.1f}) -> ({x1:.1f}, {y1_top:.1f})")
                    print(f"        Text: {chunk.text[:50]}...")
                    
            except Exception as e:
                print(f"      Error drawing chunk {i}: {e}")
    
    return annotated_images

def save_annotated_pages(images: List[Image.Image], output_dir: str = "annotated_pages"):
    """Save annotated images."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\nSaving annotated pages to {output_dir}/")
    
    for i, img in enumerate(images):
        output_file = output_path / f"page_{i+1}_annotated.png"
        img.save(output_file, "PNG")
        print(f"  Saved: {output_file}")
    
    print(f"\n✓ Saved {len(images)} annotated pages")

def create_side_by_side_comparison(original_images: List[Image.Image], 
                                   annotated_images: List[Image.Image],
                                   output_dir: str = "annotated_pages"):
    """Create side-by-side comparison images."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\nCreating side-by-side comparisons...")
    
    for i, (orig, annot) in enumerate(zip(original_images, annotated_images)):
        # Create new image with double width
        combined = Image.new('RGB', (orig.width * 2, orig.height))
        combined.paste(orig, (0, 0))
        combined.paste(annot, (orig.width, 0))
        
        # Draw dividing line
        draw = ImageDraw.Draw(combined)
        draw.line([(orig.width, 0), (orig.width, orig.height)], fill=(0, 0, 0), width=3)
        
        output_file = output_path / f"page_{i+1}_comparison.png"
        combined.save(output_file, "PNG")
        print(f"  Saved: {output_file}")

def main():
    """Main function to visualize bboxes."""
    print("="*70)
    print("BOUNDING BOX VISUALIZATION TOOL")
    print("="*70)
    
    # Configuration
    pdf_path = "./tests/documents/credit-agreement.pdf"  # UPDATE THIS

    output_dir = "annotated_pages"
    dpi = 150  # Resolution for rendering
    
    # Step 1: Parse document
    print("\n1. Parsing document with DoclingParser...")
    try:
        parser = DoclingParser()
        chunks = parser.parse(pdf_path)
        print(f"✓ Parsed {len(chunks)} chunks")
    except FileNotFoundError:
        print(f"✗ File not found: {pdf_path}")
        print("  Please update pdf_path with your actual PDF file")
        return
    except Exception as e:
        print(f"✗ Error parsing document: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Filter chunks with bboxes
    chunks_with_bbox = [c for c in chunks if c.bbox is not None]
    print(f"\n2. Found {len(chunks_with_bbox)} chunks with bounding boxes")
    
    if len(chunks_with_bbox) == 0:
        print("\n✗ ERROR: No bounding boxes to visualize!")
        print("  The parser is not extracting bboxes correctly.")
        print("  Run inspect_docling.py first to debug.")
        return
    
    # Show statistics
    print("\n   Statistics:")
    bbox_coverage = len(chunks_with_bbox) / len(chunks) * 100 if chunks else 0
    print(f"   - Coverage: {bbox_coverage:.1f}%")
    
    type_counts = {}
    page_counts = {}
    for chunk in chunks_with_bbox:
        type_counts[chunk.chunk_type] = type_counts.get(chunk.chunk_type, 0) + 1
        page_counts[chunk.bbox.page] = page_counts.get(chunk.bbox.page, 0) + 1
    
    print(f"   - Types: {dict(list(type_counts.items())[:5])}")
    print(f"   - Pages with bboxes: {len(page_counts)}")
    
    # Step 3: Convert PDF to images
    print(f"\n3. Converting PDF to images...")
    try:
        images = pdf_to_images(pdf_path, dpi=dpi)
        print(f"✓ Converted {len(images)} pages")
    except Exception as e:
        print(f"✗ Error converting PDF: {e}")
        print("  Make sure PyMuPDF (fitz) is installed: pip install PyMuPDF")
        return
    
    # Step 4: Draw bboxes
    print(f"\n4. Drawing bounding boxes...")
    try:
        annotated_images = draw_bboxes_on_images(images, chunks_with_bbox, dpi=dpi)
        print(f"✓ Drew bboxes on {len(annotated_images)} pages")
    except Exception as e:
        print(f"✗ Error drawing bboxes: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Save results
    print(f"\n5. Saving results...")
    try:
        save_annotated_pages(annotated_images, output_dir)
        create_side_by_side_comparison(images, annotated_images, output_dir)
        print(f"✓ All results saved to {output_dir}/")
    except Exception as e:
        print(f"✗ Error saving results: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Final summary
    print("\n" + "="*70)
    print("✅ VISUALIZATION COMPLETE!")
    print("="*70)
    print(f"\nCheck the '{output_dir}' folder for:")
    print(f"  - page_N_annotated.png : Pages with bboxes drawn")
    print(f"  - page_N_comparison.png : Side-by-side original vs annotated")
    print("\nColor Legend:")
    for chunk_type, color in list(COLORS.items())[:7]:
        print(f"  {chunk_type:15} : RGB{color[:3]}")
    print("="*70)

if __name__ == "__main__":
    main()