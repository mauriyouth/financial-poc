"""Background job for document processing - chunking and embedding."""

import asyncio
import os

from loguru import logger
from redis.asyncio import Redis

from src.configurations.opensearch import OpenSearchSettings
from src.configurations.redis import settings as redis_settings
from src.connectors.opensearch_connector import OpenSearchConnector
from src.models.all_models import ProcessingStatus
from src.modules.embeddings.gemini_embedder import GeminiEmbedder
from src.services.document_processing_service import DocumentProcessingService
from src.services.notification_service import NotificationService
from src.stores.postgres.document_store import DocumentStore
from src.stores.s3.document_s3_store import DocumentS3Store


async def process_document_job_async(document_id: str, file_path: str, file_type: str) -> None:
    """
    Background job to process uploaded document.

    Pipeline:
    1. Download file from S3
    2. Chunk with appropriate chunker
    3. Generate embeddings
    4. Index in OpenSearch
    5. Update document status

    Args:
        document_id: Document ID
        file_path: S3 path to document
        file_type: File extension (pdf, pptx, docx, xlsx)
    """
    document_store = DocumentStore()
    redis_client = None
    notification_service = None

    try:
        logger.info(f"Starting document processing job for {document_id}")

        # Initialize notification service
        redis_client = Redis.from_url(redis_settings.redis_url)
        notification_service = NotificationService(redis_client)

        # Update status to processing
        doc = await document_store.get_document(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        doc.status = ProcessingStatus.PROCESSING
        await document_store.update_document(doc)

        # Emit processing status
        await notification_service.publish_document_status(document_id=document_id, status="processing")

        # Initialize services
        opensearch_settings = OpenSearchSettings()
        opensearch_connector = OpenSearchConnector(opensearch_settings)
        opensearch_connector.create_chunks_index()  # Ensure index exists

        embedder = GeminiEmbedder()
        processing_service = DocumentProcessingService(opensearch_connector=opensearch_connector, embedder=embedder)

        # Download file from S3 to temp location
        s3_store = DocumentS3Store()

        # Create temp directory if it doesn't exist
        temp_dir = os.getenv("TEMP_DIR", "/tmp")
        os.makedirs(temp_dir, exist_ok=True)

        # Generate local file path
        local_file_path = os.path.join(temp_dir, f"{document_id}_{os.path.basename(file_path)}")

        logger.info(f"Downloading {file_path} from S3 to {local_file_path}")

        # Download file from S3
        try:
            file_data = s3_store.get_file(file_path)
            with open(local_file_path, "wb") as f:
                f.write(file_data)
            logger.info(f"Downloaded file to {local_file_path}")
        except Exception as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise ValueError(f"Could not download document from S3: {e}") from e

        # Process document
        chunk_count, summary = await processing_service.process_document(
            file_path=local_file_path, file_type=file_type, source_id=document_id, source_name=doc.filename
        )

        # Update document status
        doc.status = ProcessingStatus.COMPLETED
        doc.metadata_ = doc.metadata_ or {}
        doc.metadata_["chunk_count"] = chunk_count
        doc.metadata_["summary"] = summary
        await document_store.update_document(doc)

        # Emit completed status
        await notification_service.publish_document_status(
            document_id=document_id,
            status="completed",
            metadata={"chunk_count": chunk_count, "summary": summary[:200] + "..."},
        )

        logger.info(f"Successfully processed document {document_id}: {chunk_count} chunks")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")

        # Emit failed status
        if notification_service:
            try:
                await notification_service.publish_document_status(
                    document_id=document_id, status="failed", metadata={"error": str(e)}
                )
            except Exception as notify_error:
                logger.error(f"Failed to send failure notification: {notify_error}")

        # Update document with error
        try:
            doc = await document_store.get_document(document_id)
            if doc:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = str(e)
                await document_store.update_document(doc)
        except Exception as update_error:
            logger.error(f"Failed to update document status: {update_error}")

        raise
    finally:
        # Clean up: remove local temp file
        if "local_file_path" in locals() and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                logger.info(f"Cleaned up temp file: {local_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")

        # Clean up Redis connection
        if redis_client:
            await redis_client.close()


def process_document_job(document_id: str, file_path: str, file_type: str) -> None:
    """
    Sync wrapper for RQ worker (RQ requires sync functions).

    Args:
        document_id: Document ID
        file_path: S3 path to document
        file_type: File extension (pdf, pptx, docx, xlsx)
    """
    asyncio.run(process_document_job_async(document_id, file_path, file_type))
