"""
PPTX to PDF converter module using LibreOffice.
"""

import subprocess
import tempfile
from pathlib import Path


class ConversionError(Exception):
    """Raised when PPTX to PDF conversion fails."""

    pass


def convert_pptx_to_pdf(pptx_bytes: bytes) -> bytes:
    """
    Convert PPTX file to PDF using LibreOffice.

    Args:
        pptx_bytes: PPTX file content as bytes

    Returns:
        PDF file content as bytes

    Raises:
        ConversionError: If conversion fails
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pptx_file = tmpdir_path / "input.pptx"
        pdf_file = tmpdir_path / "input.pdf"

        # Write PPTX to temp file
        pptx_file.write_bytes(pptx_bytes)

        try:
            # Run LibreOffice conversion
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(tmpdir_path),
                    str(pptx_file),
                ],
                capture_output=True,
                timeout=60,
                check=True,
            )

            # Check if PDF was created
            if not pdf_file.exists():
                raise ConversionError(f"PDF file not created. LibreOffice output: {result.stdout.decode()}")

            return pdf_file.read_bytes()

        except subprocess.TimeoutExpired as e:
            raise ConversionError("LibreOffice conversion timed out") from e
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"LibreOffice conversion failed: {e.stderr.decode()}") from e
        except FileNotFoundError as e:
            raise ConversionError(
                "LibreOffice not found. Please install LibreOffice: apt-get install libreoffice"
            ) from e
