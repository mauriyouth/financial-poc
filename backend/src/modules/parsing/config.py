from dataclasses import dataclass
from typing import Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import TableFormerMode, RapidOcrOptions, OcrOptions

ALLOWED_FORMATS = [
    InputFormat.PDF,
    InputFormat.IMAGE,
    InputFormat.DOCX,
    InputFormat.HTML,
    InputFormat.PPTX,
    InputFormat.CSV,
    InputFormat.XLSX,
    InputFormat.MD,
]


@dataclass
class ParserConfig:
    # --- PIPELINE STEPS ---
    do_table_structure: bool = True
    do_ocr: bool = True
    force_backend_text: bool = False

    do_code_enrichment: bool = False
    do_formula_enrichment: bool = True

    do_picture_classification: bool = True
    do_picture_description: bool = False

    # --- PAGINATED IMAGE CONFIGS ---
    images_scale: float = 4.0
    generate_page_images: bool = True
    generate_picture_images: bool = True
    generate_parsed_pages: bool = True

    # --- VLM CONFIGS ---
    vlm_repo: Optional[str] = None
    prompt: str = "Describe this image in a few sentences."
    max_new_tokens: int = 200
    do_sample: bool = False

    # --- LAYOUT & OCR CONFIGS ---
    table_parsing_mode: TableFormerMode = TableFormerMode.ACCURATE
    create_orphan_clusters: bool = True  # Whether to create clusters for orphaned cells
    ocr_options: OcrOptions = RapidOcrOptions()

    # --- PERFORMANCE CONFIGS ---
    num_threads: int = 4
    cuda_use_flash_attention2: bool = False
    document_timeout: Optional[float] = None

    # --- SECURITY CONFIGS ---
    enable_remote_services: bool = True

    # --- THREADED PIPELINE CONFIGS ---
    ocr_batch_size: int = 64
    layout_batch_size: int = 64
    table_batch_size: int = 64

    # Timing control
    batch_polling_interval_seconds: float = 0.25

    # Backpressure and queue control
    queue_max_size: int = 100
