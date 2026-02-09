"""
Parsing service for orchestrating document parsing with docling.
"""

from src.models.all_models import ProcessingStatus
from src.modules.converters.pptx_to_pdf import ConversionError, convert_pptx_to_pdf
from src.modules.parsers.docling_parser import parse_document
from src.stores.postgres.document_store import DocumentStore
from src.stores.s3.document_s3_store import DocumentS3Store


class ParsingService:
    """Service to orchestrate document parsing."""

    def __init__(self, document_store: DocumentStore, s3_store: DocumentS3Store) -> None:
        self.document_store = document_store
        self.s3_store = s3_store

    async def parse_document(self, doc_id: str) -> None:
        """
        Parse a document with docling.

        This is called by the queue worker.

        Args:
            doc_id: Document ID to parse
        """
        try:
            # Update status to PROCESSING
            doc = await self.document_store.get_document_by_id(doc_id)
            if not doc:
                raise ValueError(f"Document {doc_id} not found")

            doc.status = ProcessingStatus.PROCESSING
            await self.document_store.save(doc)

            # Get original file from S3
            file_path = doc.file_path
            file_bytes = self.s3_store.get_file(file_path)

            # Convert PPTX to PDF if needed
            pdf_bytes = file_bytes
            if doc.file_type and doc.file_type.lower() in [
                "pptx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ]:
                try:
                    pdf_bytes = convert_pptx_to_pdf(file_bytes)
                    # Store PDF version in S3
                    pdf_path = f"{doc_id}/document.pdf"
                    from io import BytesIO

                    self.s3_store.upload_file(pdf_path, BytesIO(pdf_bytes), len(pdf_bytes), "application/pdf")
                except ConversionError as e:
                    print(f"Warning: Failed to convert PPTX to PDF for {doc_id}: {e!s}")
                    # Continue with original file if conversion fails

            # Parse document with docling
            parse_result = parse_document(pdf_bytes)

            # Store parsed content
            self.s3_store.store_markdown(doc_id, parse_result.markdown)
            self.s3_store.store_html(doc_id, parse_result.html)

            # Update status to COMPLETED
            doc.status = ProcessingStatus.COMPLETED
            doc.error_message = None
            await self.document_store.save(doc)

        except Exception as e:
            # Update status to FAILED with error message
            doc = await self.document_store.get_document_by_id(doc_id)
            if doc:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = str(e)
                await self.document_store.save(doc)
            raise
