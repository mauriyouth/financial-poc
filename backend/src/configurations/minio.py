import os
from pydantic_settings import BaseSettings


class MinIOSettings(BaseSettings):
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "documents")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() == "true"
