"""Queue worker module for processing document parsing jobs."""

from src.services.parsing_service import ParsingService
from src.stores.postgres.document_store import DocumentStore
from src.stores.s3.document_s3_store import DocumentS3Store


async def process_document_task(document_id: str) -> None:
    """
    RQ worker task for processing document parsing.

    Args:
        document_id: Document ID to process
    """
    # Initialize dependencies
    document_store = DocumentStore()
    s3_store = DocumentS3Store()
    parsing_service = ParsingService(document_store, s3_store)

    # Parse document
    await parsing_service.parse_document(document_id)
