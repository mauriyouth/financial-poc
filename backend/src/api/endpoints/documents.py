from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.api import schemas
from src.configurations.opensearch import OpenSearchSettings
from src.connectors.opensearch_connector import OpenSearchConnector
from src.core.logging import logger
from src.services.document_service import DocumentService
from src.stores.postgres.document_store import DocumentStore
from src.stores.redis.queue_store import QueueStore
from src.stores.s3.document_s3_store import DocumentS3Store

# from sqlalchemy.ext.asyncio import AsyncSession
# from src.core.database import get_db

router = APIRouter()


def get_document_service() -> DocumentService:
    # Dependency Injection
    store = DocumentStore()
    s3_store = DocumentS3Store()
    queue_store = QueueStore()
    opensearch_settings = OpenSearchSettings()
    opensearch_connector = OpenSearchConnector(opensearch_settings)
    return DocumentService(store, s3_store, queue_store, opensearch_connector)


@router.post("/", response_model=schemas.DocumentMetadata)
async def upload_document(
    file: UploadFile = File(...), thread_id: str | None = None, service: DocumentService = Depends(get_document_service)
) -> schemas.DocumentMetadata:
    try:
        # Service handles DB creation and MinIO upload
        doc = await service.upload_document(file, thread_id)
        logger.debug(f"Upload completed for doc {doc.id}")

        # Get signed URL
        download_url = await service.get_presigned_url(doc.id)
        logger.debug(f"Got download URL for doc {doc.id}")

        # Get thumbnail URL
        thumbnail_url = await service.get_thumbnail_url(doc.id)
        logger.debug(f"Got thumbnail URL for doc {doc.id}: {thumbnail_url}")

        # Convert DB model to Pydantic schema
        logger.debug(f"Creating response schema for doc {doc.id}")
        response = schemas.DocumentMetadata(
            id=doc.id,
            filename=doc.filename,
            upload_date=doc.created_at,
            status=doc.status,
            file_type=doc.file_type,
            download_url=download_url,
            thumbnail_url=thumbnail_url,
        )
        logger.info(f"Upload endpoint returning response for doc {doc.id}")
        return response
    except Exception as e:
        logger.error("Upload endpoint error: {}", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{document_id}/content", response_model=schemas.DocumentMetadata)
async def update_document_content(
    document_id: str, file: UploadFile = File(...), service: DocumentService = Depends(get_document_service)
) -> schemas.DocumentMetadata:
    """
    Update the content of an existing document.
    """
    try:
        doc = await service.update_document_content(document_id, file)
        download_url = await service.get_presigned_url(doc.id)

        return schemas.DocumentMetadata(
            id=doc.id,
            filename=doc.filename,
            upload_date=doc.created_at,
            status=doc.status,
            file_type=doc.file_type,
            download_url=download_url,
            thumbnail_url=await service.get_thumbnail_url(doc.id),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=list[schemas.DocumentMetadata])
async def list_documents(
    thread_id: str | None = None, service: DocumentService = Depends(get_document_service)
) -> list[schemas.DocumentMetadata]:
    try:
        docs = await service.list_documents(thread_id)
        # We could also fetch signed URLs here, but it might be slow for a list.
        # Making it efficient by doing it in batch or only on demand.
        # For now let's just return basic metadata for list, and require individual fetch for URL if needed,
        # OR we can generate them if it's fast. MinIO generation is local (crypto), so it is fast.

        # Let's generate them for now to make frontend easier
        response_list = []
        for doc in docs:
            download_url = await service.get_presigned_url(doc.id)
            thumbnail_url = await service.get_thumbnail_url(doc.id)
            response_list.append(
                schemas.DocumentMetadata(
                    id=doc.id,
                    filename=doc.filename,
                    upload_date=doc.created_at,
                    status=doc.status,
                    file_type=doc.file_type,
                    download_url=download_url,
                    thumbnail_url=thumbnail_url,
                )
            )
        return response_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{document_id}/download")
async def download_document(
    document_id: str, service: DocumentService = Depends(get_document_service)
) -> StreamingResponse:
    """
    Stream document content directly with caching enabled.
    """
    from src.core.logging import logger

    try:
        logger.info(f"Download request for document: {document_id}")
        # Get the stream generator
        # Note: We stream the *original* file for download, or maybe PDF for preview?
        # The user says "download", but preview uses the same URL apparently?
        # If preview uses this URL, we should use `for_preview=True`?
        # But `download` implies getting the source file.
        # Let's check `get_presigned_url` usage: `for_preview=False` in old impl.
        # However, `PDFPreview` component uses `documentUrl` which comes from metadata `download_url`.
        # And `list_documents` returns metadata with `download_url` pointing here implicitly?
        # Wait, `get_presigned_url` returns a full S3/Minio URL currently.
        # So the metadata has the S3 URL directly.
        # The `download_document` endpoint was returning a Redirect to that S3 URL.
        # If we change `download_document` to stream, we must ensure `metadata.download_url` points to THIS endpoint.

        # Currently, `list_documents` calls `service.get_presigned_url(doc.id)`.
        # This returns a MINIO URL (localhost:9000/...), NOT `localhost:8000/api/v1/documents/{id}/download`.
        # Ah! So the frontend is accessing MinIO directly via presigned URL.
        # If so, `download_document` endpoint is NOT used by current frontend `list_documents`?
        # Let's double check `documents.py` line 104-114.

        # Line 104: `download_url = await service.get_presigned_url(doc.id)`
        # `get_presigned_url` calls `self.s3_store.get_presigned_url`.
        # That returns `minio_client.presigned_get_object(...)` which is a full URL to MinIO.

        # So the Frontend uses the MinIO URL directly.
        # AND MinIO URLs change every time.

        # The user says: "fix temporary redirect for document/download also"
        # And "the app downloads the doc every time i switch the tab".

        # If the frontend uses the MinIO URL, fixing THIS endpoint won't help unless...
        # ...unless the frontend is actually using THIS endpoint?
        # Or unless we change `list_documents` to return THIS endpoint as `download_url`.

        # If I change `download_document` to stream, I MUST also change `list_documents` (and `upload_document`, `get_document`)
        # to return `/api/v1/documents/{id}/download` as the `download_url` instead of generating a presigned S3 URL.

        # Implementation:
        stream = await service.get_document_stream(document_id, for_preview=True)

        # Determine content type (simple heuristic or from DB)
        # We should ideally fetch doc metadata to set content type correctly
        doc = await service.get_document_status(document_id)
        media_type = "application/pdf"  # Default for preview
        if doc.file_type == "spreadsheet":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif doc.file_type == "presentation":
            if doc.pdf_preview_path:
                media_type = "application/pdf"
            else:
                media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        headers = {
            "Cache-Control": "private, max-age=3600",
            # "Content-Disposition": f'inline; filename="{doc.filename}"'
        }

        return StreamingResponse(stream, media_type=media_type, headers=headers)

    except HTTPException as e:
        logger.error(f"HTTPException in download for {document_id}: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download for {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{document_id}", response_model=schemas.DocumentMetadata)
async def get_document(
    document_id: str, service: DocumentService = Depends(get_document_service)
) -> schemas.DocumentMetadata:
    """
    Get document metadata by ID.
    """
    try:
        doc = await service.get_document_status(document_id)
        download_url = await service.get_presigned_url(document_id)

        return schemas.DocumentMetadata(
            id=doc.id,
            filename=doc.filename,
            upload_date=doc.created_at,
            status=doc.status,
            file_type=doc.file_type,
            download_url=download_url,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{document_id}/content")
async def get_content(
    document_id: str, format: str = "markdown", service: DocumentService = Depends(get_document_service)
) -> str | dict:
    """
    Get document content in specified format (markdown, html, json).
    """
    try:
        content = await service.get_document_content(document_id, format)

        if format == "json":
            import json

            # If content is already a dict (from service fix), return it.
            # If it's a string from old service impl, parse it.
            if isinstance(content, str):
                try:
                    return json.loads(content.replace("'", '"'))
                except Exception:
                    return {"content": content}
            return content

        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{document_id}/status", response_model=schemas.DocumentMetadata)
async def get_status(
    document_id: str, service: DocumentService = Depends(get_document_service)
) -> schemas.DocumentMetadata:
    """
    Get ONLY the status metadata.
    """
    try:
        doc = await service.get_document_status(document_id)
        return schemas.DocumentMetadata(
            id=doc.id,
            filename=doc.filename,
            upload_date=doc.created_at,
            status=doc.status,
            file_type=doc.file_type,
            thumbnail_url=await service.get_thumbnail_url(doc.id),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{document_id}")
async def delete_document(document_id: str, service: DocumentService = Depends(get_document_service)) -> dict:
    """
    Delete a document and its associated files.
    """
    try:
        await service.delete_document(document_id)
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/chunks/{chunk_id}")
async def get_chunk(chunk_id: str, service: DocumentService = Depends(get_document_service)) -> dict:
    """
    Get chunk metadata by ID.
    """
    try:
        chunk = await service.get_chunk(chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        # Return as dict/json
        return chunk.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
