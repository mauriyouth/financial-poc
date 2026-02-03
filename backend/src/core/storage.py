from minio import Minio

from src.configurations.settings import settings

# Lazy initialization to avoid fork safety issues on macOS with RQ
# The client will be created when first accessed, not at import time
_minio_client = None


def get_minio_client() -> Minio:
    """Get or create minio client instance (lazy initialization)."""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _minio_client


def ensure_bucket_exists() -> None:
    """Ensure the configured bucket exists, create if not."""
    client = get_minio_client()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)
