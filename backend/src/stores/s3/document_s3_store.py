import io
from typing import BinaryIO

from src.core.storage import ensure_bucket_exists, get_minio_client, settings


class DocumentS3Store:
    def __init__(self):
        self.bucket_name = settings.MINIO_BUCKET
        # Ensure bucket exists on init or let the method handle it
        ensure_bucket_exists()

    def upload_file(self, file_path: str, data: BinaryIO, length: int, content_type: str) -> None:
        """
        Uploads a file to the S3 compatible storage.

        Args:
            file_path: The key/path in the bucket (e.g. "doc_id/filename.pdf")
            data: The binary data stream
            length: Size of the data
            content_type: MIME type of the file
        """
        try:
            get_minio_client().put_object(self.bucket_name, file_path, data, length=length, content_type=content_type)
        except Exception as e:
            raise Exception(f"Failed to upload to S3 storage: {e!s}") from e

    def get_file(self, file_path: str) -> bytes:
        """
        Retrieves a file from S3 storage.

        Args:
            file_path: The key/path in the bucket

        Returns:
            bytes: The file content
        """
        try:
            response = get_minio_client().get_object(self.bucket_name, file_path)
            content = response.read()
            response.close()
            response.release_conn()
            return content
        except Exception as e:
            raise Exception(f"Failed to read from S3 storage: {e!s}") from e

    def list_files(self, prefix: str) -> list:
        """
        List files with a given prefix.
        Wrapper around list_objects.
        """
        return list(get_minio_client().list_objects(self.bucket_name, prefix=prefix, recursive=True))

    def get_presigned_url(self, file_path: str, expires_hours: int = 1) -> str:
        """
        Generate a presigned URL for retrieving a file.
        """
        from datetime import timedelta

        try:
            return get_minio_client().presigned_get_object(
                self.bucket_name, file_path, expires=timedelta(hours=expires_hours)
            )
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {e!s}") from e

    def delete_file(self, file_path: str) -> None:
        """
        Deletes a file from S3 storage.
        """
        try:
            get_minio_client().remove_object(self.bucket_name, file_path)
        except Exception as e:
            raise Exception(f"Failed to delete file from S3 storage: {e!s}") from e

    def store_markdown(self, doc_id: str, content: str) -> None:
        """
        Store markdown content for a document.

        Args:
            doc_id: Document ID
            content: Markdown content
        """
        file_path = f"{doc_id}/content.md"
        data = content.encode("utf-8")
        self.upload_file(file_path, io.BytesIO(data), len(data), "text/markdown")

    def store_html(self, doc_id: str, content: str) -> None:
        """
        Store HTML content for a document.

        Args:
            doc_id: Document ID
            content: HTML content
        """
        file_path = f"{doc_id}/content.html"
        data = content.encode("utf-8")
        self.upload_file(file_path, io.BytesIO(data), len(data), "text/html")

    def get_markdown(self, doc_id: str) -> str:
        """
        Retrieve markdown content for a document.

        Args:
            doc_id: Document ID

        Returns:
            Markdown content
        """
        file_path = f"{doc_id}/content.md"
        content_bytes = self.get_file(file_path)
        return content_bytes.decode("utf-8")

    def get_html(self, doc_id: str) -> str:
        """
        Retrieve HTML content for a document.

        Args:
            doc_id: Document ID

        Returns:
            HTML content
        """
        file_path = f"{doc_id}/content.html"
        content_bytes = self.get_file(file_path)
        return content_bytes.decode("utf-8")
