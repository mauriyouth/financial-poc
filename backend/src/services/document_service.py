import io
import os
import uuid
from collections.abc import Iterator

from fastapi import HTTPException, UploadFile

from src.connectors.opensearch_connector import OpenSearchConnector
from src.core.logging import logger
from src.models.all_models import Document, ProcessingStatus
from src.models.entities.chunk_entities import Chunk
from src.stores.opensearch.chunk_store import ChunkStore
from src.stores.postgres.document_store import DocumentStore
from src.stores.redis.queue_store import QueueStore
from src.stores.s3.document_s3_store import DocumentS3Store


class DocumentService:
    def __init__(
        self,
        document_store: DocumentStore,
        s3_store: DocumentS3Store,
        queue_store: QueueStore,
        opensearch_connector: OpenSearchConnector,
    ) -> None:
        self.store = document_store
        self.s3_store = s3_store
        self.queue_store = queue_store
        self.chunk_store = ChunkStore(opensearch_connector)

        logger.info("DocumentService initialized")

    async def upload_document(self, file: UploadFile, thread_id: str | None = None) -> Document:
        doc_id = str(uuid.uuid4())
        logger.info(f"Starting document upload: {file.filename} (ID: {doc_id})")

        # 1. Upload to MinIO
        file_content = await file.read()
        file_path = f"{doc_id}/{file.filename or 'untitled'}"
        logger.debug(f"File size: {len(file_content)} bytes, path: {file_path}")

        temp_path = f"/tmp/{doc_id}_{file.filename or 'untitled'}"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(file_content)

        try:
            with open(temp_path, "rb") as f:
                # MinIO upload is sync - that's OK in async function
                logger.debug(f"Uploading to S3: {file_path}")
                self.s3_store.upload_file(
                    file_path, f, len(file_content), file.content_type or "application/octet-stream"
                )

            os.remove(temp_path)
            logger.info(f"Successfully uploaded file to S3: {file_path}")
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename} to S3: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise Exception(f"Failed to upload to storage: {e!s}") from e

        # Detect file type
        filename = file.filename
        file_type = None
        if filename:
            ext = filename.lower().split(".")[-1] if "." in filename else None
            if ext in ["pdf"]:
                file_type = "pdf"
            elif ext in ["xlsx", "xls", "csv"]:
                file_type = "spreadsheet"
            elif ext in ["pptx", "ppt"]:
                file_type = "presentation"
            elif ext in ["docx", "doc", "txt", "md"]:
                file_type = "document"

        # 2. Create initial DB record
        doc = Document(
            id=doc_id,
            filename=filename or "untitled",
            file_path=file_path,
            status=ProcessingStatus.PENDING,
            file_type=file_type,
            thread_id=thread_id,
        )
        created_doc = await self.store.create_document(doc)
        logger.info(f"Created document in DB: {doc_id} (Thread: {thread_id})")

        # 3. If PPTX, convert to PDF for preview
        pdf_path = None
        if file_type == "presentation":
            try:
                pdf_path = await self._convert_pptx_to_pdf(doc_id, filename, temp_path)
                # Update document with PDF preview path
                created_doc.pdf_preview_path = pdf_path
                await self.store.update_document(created_doc)
                logger.info(f"Converted PPTX to PDF and saved path: {pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to convert PPTX to PDF for {doc_id}: {e}")
                # Continue even if conversion fails - preview won't work but download will

        # 4. Enqueue document for processing (chunking, embedding, indexing)
        try:
            # Determine file type from extension
            file_extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

            job_id = self.queue_store.enqueue_document_processing(
                document_id=doc_id,
                file_path=file_path,  # S3 path for worker to download
                file_type=file_extension,
            )
            created_doc.parsing_job_id = job_id
            # Keep status as PENDING - worker will update to PROCESSING then COMPLETED
            await self.store.update_document(created_doc)
            logger.info(f"Enqueued processing job {job_id} for document {doc_id}")
        except Exception as e:
            # If queue fails, document is still uploaded but not queued
            logger.warning(f"Failed to enqueue processing job for {doc_id}: {e}")

        return created_doc

    async def update_document_content(self, doc_id: str, file: UploadFile) -> Document:
        doc = await self.store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Upload new file content to same path
        file_content = await file.read()
        temp_path = f"/tmp/{doc_id}_{file.filename}"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(file_content)

        try:
            with open(temp_path, "rb") as f:
                self.s3_store.upload_file(
                    doc.file_path, f, len(file_content), file.content_type or "application/octet-stream"
                )

            os.remove(temp_path)
        except Exception as e:
            raise Exception(f"Failed to update storage: {e!s}") from e

        # Update metadata
        doc.file_size = len(file_content)
        doc.file_type = file.content_type
        await self.store.update_document(doc)

        # Re-queue parsing
        job_id = self.queue_store.enqueue_parsing(doc_id)
        doc.parsing_job_id = job_id
        doc.status = ProcessingStatus.QUEUED
        await self.store.update_document(doc)

        return doc

    async def list_documents(self, thread_id: str | None = None) -> list[Document]:
        return await self.store.list_documents(thread_id)

    async def get_document(self, doc_id: str) -> Document | None:
        return await self.store.get_document(doc_id)

    async def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Get chunk by ID."""
        return await self.chunk_store.get_chunk(chunk_id)

    async def get_document_content(self, doc_id: str, format: str = "markdown") -> str:
        """
        Get parsed document content in specified format.

        Args:
            doc_id: Document ID
            format: 'markdown' or 'html'

        Returns:
            Parsed content

        Raises:
            HTTPException: If document not found or content not yet parsed
        """
        doc = await self.store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if doc.status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Document not yet parsed. Status: {doc.status.value}",
            )

        try:
            if format == "markdown":
                return self.s3_store.get_markdown(doc_id)
            elif format == "html":
                return self.s3_store.get_html(doc_id)
            else:
                raise HTTPException(status_code=400, detail="Invalid format. Use 'markdown' or 'html'")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Parsed content not found: {e!s}") from e

    async def get_parsing_status(self, doc_id: str) -> dict:
        """
        Get parsing status for a document.

        Args:
            doc_id: Document ID

        Returns:
            Status dict with status, progress, and error message
        """
        doc = await self.store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        result = {
            "status": doc.status.value,
            "progress": 0,
            "error": doc.error_message,
        }

        # If queued or processing, check job status
        if doc.parsing_job_id and doc.status in [ProcessingStatus.QUEUED, ProcessingStatus.PROCESSING]:
            try:
                _, progress, error = self.queue_store.get_job_status(doc.parsing_job_id)
                result["progress"] = progress
                if error:
                    result["error"] = error
            except Exception:
                # Job not found or error checking status
                pass
        elif doc.status == ProcessingStatus.COMPLETED:
            result["progress"] = 100

        return result

    async def get_presigned_url(self, doc_id: str, for_preview: bool = True) -> str:
        """
        Get presigned URL for document access.

        Args:
            doc_id: Document ID
            for_preview: If True and document is a presentation, returns PDF URL for preview
                        If False, always returns original file URL

        Returns:
            Presigned URL for accessing the document
        """
        logger.debug(f"Getting presigned URL for doc {doc_id}, for_preview={for_preview}")
        doc = await self.store.get_document(doc_id)
        if not doc:
            logger.error(f"Document not found: {doc_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        logger.debug(
            f"Document {doc_id}: file_type={doc.file_type}, file_path={doc.file_path}, pdf_preview_path={doc.pdf_preview_path}"
        )

        # For presentations with PDF preview, use PDF for preview mode
        if for_preview and doc.file_type == "presentation" and doc.pdf_preview_path:
            logger.info(f"Using PDF preview for presentation {doc_id}: {doc.pdf_preview_path}")
            return self.s3_store.get_presigned_url(doc.pdf_preview_path)

        # Otherwise use original file
        logger.info(f"Using original file for {doc_id}: {doc.file_path}")
        return self.s3_store.get_presigned_url(doc.file_path)

    async def get_document_stream(self, doc_id: str, for_preview: bool = True) -> Iterator[bytes]:
        """
        Get file stream for document content.

        Args:
            doc_id: Document ID
            for_preview: If True and document is a presentation, streams PDF preview

        Returns:
            generator: File content stream
        """
        doc = await self.store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Determine path (preview PDF or original file)
        file_path = doc.file_path
        if for_preview and doc.file_type == "presentation" and doc.pdf_preview_path:
            file_path = doc.pdf_preview_path

        logger.info(f"Streaming file for {doc_id}: {file_path}")
        return self.s3_store.get_file_stream(file_path)

    async def get_document_status(self, doc_id: str) -> Document:
        """
        Get document metadata and status.

        Args:
            doc_id: Document ID

        Returns:
            Document model with metadata

        Raises:
            HTTPException: If document not found
        """
        doc = await self.store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    async def get_thumbnail_url(self, doc_id: str) -> str | None:
        """
        Get thumbnail URL for a document (PNG/JPG of first page).

        Args:
            doc_id: Document ID

        Returns:
            Presigned URL for thumbnail image, or None if not generated

        TODO: Implement thumbnail generation:
            - Extract first page from PDF using pdf2image
            - Convert to PNG/JPG (200x300px)
            - Store in S3: {doc_id}/thumbnail.png
            - Return presigned URL
        """
        return None  # Thumbnail generation not yet implemented

    async def delete_document(self, doc_id: str) -> None:
        """
        Delete a document and its associated files.
        """
        doc = await self.store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from S3 (best effort cleanup)
        try:
            # We try to delete known artifacts
            files_to_delete = [
                doc.file_path,
                f"{doc_id}/content.md",
                f"{doc_id}/content.html",
                f"{doc_id}/thumbnail.png",
            ]
            if doc.pdf_preview_path:
                files_to_delete.append(doc.pdf_preview_path)

            # TODO: Ideally list all objects in {doc_id}/ prefix and remove them
            # For now this covers most cases

            for file_path in files_to_delete:
                try:
                    self.s3_store.delete_file(file_path)
                except Exception:
                    # Ignore if file doesn't exist
                    pass
        except Exception as e:
            logger.warning(f"Error cleaning up S3 files for {doc_id}: {e}")

        # Delete from OpenSearch
        try:
            await self.chunk_store.delete_chunks_by_source(doc_id)
            logger.info(f"Deleted chunks for document {doc_id} from OpenSearch")
        except Exception as e:
            logger.warning(f"Error cleaning up OpenSearch chunks for {doc_id}: {e}")

        # Delete from DB
        await self.store.delete_document(doc_id)
        logger.info(f"Deleted document {doc_id}")

    async def _convert_pptx_to_pdf(self, doc_id: str, filename: str, pptx_path: str) -> str:
        """
        Convert a PPTX file to PDF using LibreOffice.

        Args:
            doc_id: Document ID
            filename: Original filename
            pptx_path: Path to the PPTX file on disk

        Returns:
            S3 path of the converted PDF

        Raises:
            Exception: If conversion fails
        """
        import os
        import subprocess

        try:
            # Create output directory
            output_dir = f"/tmp/{doc_id}_pdf"
            os.makedirs(output_dir, exist_ok=True)

            # Convert using LibreOffice
            # --headless: run without GUI
            # --convert-to pdf: convert to PDF format
            # --outdir: output directory
            result = subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    output_dir,
                    pptx_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                check=False,
            )

            if result.returncode != 0:
                logger.error(f"LibreOffice conversion failed: {result.stderr}")
                raise Exception(f"LibreOffice conversion failed: {result.stderr}")

            # Find the generated PDF
            pdf_filename = filename.rsplit(".", 1)[0] + ".pdf"
            pdf_local_path = os.path.join(output_dir, pdf_filename)

            if not os.path.exists(pdf_local_path):
                raise Exception(f"PDF file not found after conversion: {pdf_local_path}")

            # Upload PDF to S3
            pdf_s3_path = f"{doc_id}/{pdf_filename}"
            with open(pdf_local_path, "rb") as pdf_file:
                file_content = pdf_file.read()
                self.s3_store.upload_file(
                    pdf_s3_path,
                    io.BytesIO(file_content),
                    len(file_content),
                    "application/pdf",
                )

            # Cleanup
            os.remove(pdf_local_path)
            os.rmdir(output_dir)

            logger.info(f"Successfully converted PPTX to PDF: {pdf_s3_path}")
            return pdf_s3_path

        except subprocess.TimeoutExpired as e:
            logger.error(f"LibreOffice conversion timed out for {doc_id}")
            raise Exception("PDF conversion timed out") from e
        except Exception as e:
            logger.error(f"Failed to convert PPTX to PDF: {e}")
            raise Exception(f"Failed to convert PPTX to PDF: {e!r}") from e
