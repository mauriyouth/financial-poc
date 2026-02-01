"""Service for extracting slides from PPTX presentations."""

import copy
import io
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image
from pptx import Presentation


class SlideExtractionService:
    """Service to extract individual slides from PPTX files."""

    @staticmethod
    async def extract_slides(pptx_content: bytes, document_id: str) -> list[dict[str, Any]]:
        """
        Extract slides from a PPTX file.

        Returns list of slide data with PNG and PPTX content for each slide.

        Args:
            pptx_content: Raw bytes of the PPTX file
            document_id: Document ID for file naming

        Returns:
            List of dicts with slide_number, png_data, pptx_data, text_elements
        """
        slides_data = []

        # Create temp directory for working files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_file = tmpdir_path / "presentation.pptx"

            # Write PPTX to temp file
            input_file.write_bytes(pptx_content)

            # Load presentation
            try:
                prs = Presentation(str(input_file))
            except Exception as e:
                raise ValueError(f"Failed to load PPTX: {e!s}") from e

            # Extract each slide
            for slide_num, slide in enumerate(prs.slides, start=1):
                try:
                    slide_data = await SlideExtractionService._extract_single_slide(
                        prs=prs, slide=slide, slide_num=slide_num, tmpdir=tmpdir_path, document_id=document_id
                    )
                    slides_data.append(slide_data)
                except Exception as e:
                    print(f"Warning: Failed to extract slide {slide_num}: {e!s}")
                    # Continue with other slides

        return slides_data

    @staticmethod
    async def _extract_single_slide(
        prs: Presentation, slide: Any, slide_num: int, tmpdir: Path, document_id: str
    ) -> dict[str, Any]:
        """Extract a single slide as PNG and PPTX."""

        # 1. Create single-slide PPTX
        single_slide_pptx = SlideExtractionService._create_single_slide_pptx(
            original_prs=prs, slide=slide, slide_num=slide_num
        )

        # Save single-slide PPTX to bytes
        single_pptx_bytes = io.BytesIO()
        single_slide_pptx.save(single_pptx_bytes)
        single_pptx_bytes.seek(0)

        # 2. Convert slide to PNG using LibreOffice (if available) or fallback
        png_data = await SlideExtractionService._convert_slide_to_png(
            slide_pptx_bytes=single_pptx_bytes.read(), tmpdir=tmpdir, slide_num=slide_num
        )
        single_pptx_bytes.seek(0)

        # 3. Extract text elements with positions
        text_elements = SlideExtractionService._extract_text_elements(slide)

        return {
            "slide_number": slide_num,
            "png_data": png_data,
            "pptx_data": single_pptx_bytes.read(),
            "text_elements": text_elements,
        }

    @staticmethod
    def _create_single_slide_pptx(original_prs: Presentation, slide: Any, slide_num: int) -> Presentation:
        """Create a new PPTX with just one slide."""
        # Create new presentation
        new_prs = Presentation()

        # Copy the slide layout
        slide_layout = slide.slide_layout

        # Copy slide dimensions
        new_prs.slide_width = original_prs.slide_width
        new_prs.slide_height = original_prs.slide_height

        # Add new slide with same layout
        new_slide = new_prs.slides.add_slide(slide_layout)

        # Copy all shapes from original slide
        for shape in slide.shapes:
            try:
                # Deep copy the shape element
                el = shape.element
                new_slide.shapes._spTree.append(copy.deepcopy(el))
            except Exception as e:
                print(f"Warning: Could not copy shape in slide {slide_num}: {e!s}")

        return new_prs

    @staticmethod
    async def _convert_slide_to_png(slide_pptx_bytes: bytes, tmpdir: Path, slide_num: int) -> bytes:
        """
        Convert a single-slide PPTX to PNG.

        Uses LibreOffice if available, otherwise creates a placeholder image.
        """
        temp_pptx = tmpdir / f"slide_{slide_num}.pptx"
        output_png = tmpdir / f"slide_{slide_num}.png"

        # Write PPTX to file
        temp_pptx.write_bytes(slide_pptx_bytes)

        # Try LibreOffice conversion
        try:
            subprocess.run(
                ["soffice", "--headless", "--convert-to", "png", "--outdir", str(tmpdir), str(temp_pptx)],
                capture_output=True,
                timeout=30,
                check=True,
            )

            # LibreOffice creates slide_N.png
            if output_png.exists():
                return output_png.read_bytes()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"LibreOffice conversion failed: {e!s}, using fallback")

        # Fallback: Create placeholder image
        return SlideExtractionService._create_placeholder_image(slide_num)

    @staticmethod
    def _create_placeholder_image(slide_num: int, width: int = 1920, height: int = 1080) -> bytes:
        """Create a placeholder image for slides that can't be converted."""
        from PIL import ImageDraw, ImageFont

        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        # Draw border
        draw.rectangle([10, 10, width - 10, height - 10], outline="gray", width=5)

        # Add text
        text = f"Slide {slide_num}"
        # Use default font
        try:
            from PIL import ImageFont

            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except Exception:
            font = ImageFont.load_default()

        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((width - text_width) // 2, (height - text_height) // 2)

        draw.text(position, text, fill="black", font=font)

        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        return img_bytes.getvalue()

    @staticmethod
    def _extract_text_elements(slide: Any) -> list[dict[str, Any]]:
        """Extract text elements with their positions from a slide."""
        text_elements = []

        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                try:
                    # Convert EMUs (English Metric Units) to pixels
                    # 1 EMU = 1/914400 inch, assume 96 DPI
                    emu_to_px = 96 / 914400

                    text_elements.append(
                        {
                            "text": shape.text,
                            "x": int(shape.left * emu_to_px) if hasattr(shape, "left") else 0,
                            "y": int(shape.top * emu_to_px) if hasattr(shape, "top") else 0,
                            "width": int(shape.width * emu_to_px) if hasattr(shape, "width") else 100,
                            "height": int(shape.height * emu_to_px) if hasattr(shape, "height") else 20,
                        }
                    )
                except Exception as e:
                    print(f"Warning: Could not extract text element: {e!s}")

        return text_elements
