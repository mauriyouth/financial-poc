"""
Test script to verify bounding box extraction from Docling documents
"""

from docling_parser import DoclingParser
import json

print("="*60)
print("BBOX EXTRACTION TEST")
print("="*60)

# Test 1: Check that parser initializes
print("\n1. Initializing parser...")
try:
    parser = DoclingParser()
    print("✓ Parser initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize parser: {e}")
    exit(1)

# Test 2: Parse a document (you'll need to provide a real PDF)
print("\n2. Parsing document...")
document_path = "./tests/documents/credit-agreement.pdf"  # Replace with actual file

try:
    chunks = parser.parse(document_path)
    print(f"✓ Parsed {len(chunks)} chunks from document")
except FileNotFoundError:
    print(f"⚠️  Test file not found: {document_path}")
    print("   Please update the document_path variable with a real PDF file")
    exit(0)
except Exception as e:
    print(f"✗ Failed to parse document: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Check bbox extraction
print("\n3. Checking bounding box extraction...")
chunks_with_bbox = [c for c in chunks if c.bbox is not None]
bbox_coverage = (len(chunks_with_bbox) / len(chunks) * 100) if chunks else 0

print(f"   Total chunks: {len(chunks)}")
print(f"   Chunks with bbox: {len(chunks_with_bbox)}")
print(f"   Coverage: {bbox_coverage:.1f}%")

if len(chunks_with_bbox) == 0:
    print("\n✗ ERROR: No bounding boxes extracted!")
    print("   This indicates the bbox extraction is still not working correctly.")
    
    # Debug: Show first chunk structure
    if chunks:
        print("\n   Debug - First chunk structure:")
        first_chunk = chunks[0]
        print(f"   Text: {first_chunk.text[:100]}...")
        print(f"   Type: {first_chunk.chunk_type}")
        print(f"   BBox: {first_chunk.bbox}")
        print(f"   Metadata: {first_chunk.metadata}")
else:
    print(f"\n✓ SUCCESS: {len(chunks_with_bbox)} chunks have bounding boxes!")
    
    # Test 4: Verify bbox data looks correct
    print("\n4. Verifying bbox data structure...")
    sample_bbox = chunks_with_bbox[0].bbox
    
    print(f"   Sample bbox: {sample_bbox}")
    print(f"   - Page: {sample_bbox.page}")
    print(f"   - Coordinates: ({sample_bbox.x0:.2f}, {sample_bbox.y0:.2f}) to ({sample_bbox.x1:.2f}, {sample_bbox.y1:.2f})")
    print(f"   - Width: {sample_bbox.width:.2f}")
    print(f"   - Height: {sample_bbox.height:.2f}")
    print(f"   - Area: {sample_bbox.area:.2f}")
    
    # Check if coordinates make sense
    if sample_bbox.width > 0 and sample_bbox.height > 0:
        print("   ✓ Bbox coordinates look valid")
    else:
        print("   ✗ Bbox coordinates may be invalid (zero or negative dimensions)")

# Test 5: Page distribution
print("\n5. Checking page distribution...")
page_distribution = {}
for chunk in chunks_with_bbox:
    page = chunk.bbox.page
    page_distribution[page] = page_distribution.get(page, 0) + 1

if page_distribution:
    print(f"   Found chunks on {len(page_distribution)} pages:")
    for page, count in sorted(page_distribution.items())[:5]:  # Show first 5 pages
        print(f"   - Page {page}: {count} chunks")
    if len(page_distribution) > 5:
        print(f"   ... and {len(page_distribution) - 5} more pages")
else:
    print("   No page information found")

# Test 6: Export summary
print("\n6. Generating summary...")
summary = parser.export_summary(chunks)
print(json.dumps(summary, indent=2))

# Test 7: Save sample output
print("\n7. Saving sample output...")
try:
    # Save first 10 chunks to JSON
    sample_chunks = chunks[:10]
    output = [chunk.to_dict() for chunk in sample_chunks]
    
    with open('bbox_test_output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("   ✓ Saved sample output to bbox_test_output.json")
except Exception as e:
    print(f"   ✗ Failed to save output: {e}")

print("\n" + "="*60)
if bbox_coverage > 0:
    print("✅ TEST PASSED: Bounding boxes are being extracted!")
else:
    print("❌ TEST FAILED: No bounding boxes found")
print("="*60)