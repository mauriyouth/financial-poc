from pathlib import Path
from typing import Union, Iterable, Dict, Any

from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionVlmOptions,
    TableStructureOptions,
    LayoutOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

from backend.modules.parsing.config import ParserConfig, ALLOWED_FORMATS


class Parser:
    """Parser for converting documents using Docling library."""

    def __init__(self, config: ParserConfig):
        """
        Initialize the parser with the given configuration.

        Args:
            config: ParserConfig instance containing all parser settings
        """
        self.config = config
        self.pdf_options = self._create_pdf_pipeline_options(config)
        self.converter = self._create_document_converter()

    @staticmethod
    def _create_pdf_pipeline_options(config: ParserConfig) -> PdfPipelineOptions:
        """Create and configure PdfPipelineOptions from config."""
        return PdfPipelineOptions(
            document_timeout=config.document_timeout,
            accelerator_options=AcceleratorOptions(
                num_threads=config.num_threads,
                cuda_use_flash_attention2=config.cuda_use_flash_attention2,
            ),
            enable_remote_services=config.enable_remote_services,
            do_picture_classification=config.do_picture_classification,
            do_picture_description=config.do_picture_description,
            picture_description_options=PictureDescriptionVlmOptions(
                repo_id=config.vlm_repo,
                prompt=config.prompt,
                generation_config={
                    "max_new_tokens": config.max_new_tokens,
                    "do_sample": config.do_sample,
                },
            ),
            images_scale=config.images_scale,
            generate_page_images=config.generate_page_images,
            generate_picture_images=config.generate_picture_images,
            do_table_structure=config.do_table_structure,
            do_ocr=config.do_ocr,
            do_code_enrichment=config.do_code_enrichment,
            do_formula_enrichment=config.do_formula_enrichment,
            force_backend_text=config.force_backend_text,
            table_structure_options=TableStructureOptions(mode=config.table_parsing_mode),
            ocr_options=config.ocr_options,
            layout_options=LayoutOptions(create_orphan_clusters=config.create_orphan_clusters),
            generate_parsed_pages=config.generate_parsed_pages,
            ocr_batch_size=config.ocr_batch_size,
            layout_batch_size=config.layout_batch_size,
            table_batch_size=config.table_batch_size,
            batch_polling_interval_seconds=config.batch_polling_interval_seconds,
            queue_max_size=config.queue_max_size,
        )

    def _create_document_converter(self) -> DocumentConverter:
        """Create and configure DocumentConverter with format options."""
        return DocumentConverter(
            allowed_formats=ALLOWED_FORMATS,
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=self.pdf_options),
                # Note: Additional format support (IMAGE, DOCX, HTML, PPTX, CSV, XLSX, MD)
                # can be added by creating corresponding format options and pipeline options
            },
        )

    @staticmethod
    def _format_result(result: ConversionResult) -> Dict[str, Any]:
        status = result.status
        num_pages = len(result.pages)
        conf = result.confidence.mean_score
        doc = result.document

        return {
            "status": status,
            "num_pages": num_pages,
            "conf": conf,
            "document": doc,
        }

    def parse(self, source: Union[Path, str, DocumentStream]):
        """Parse the given file and return a Document object."""
        result = self.converter.convert(source)
        return self._format_result(result)

    def parse_all(self, source: Iterable[Union[Path, str, DocumentStream]]):
        """Parse all the given files and return a list of Document objects."""
        results = self.converter.convert_all(source)
        for result in results:
            yield self._format_result(result)
