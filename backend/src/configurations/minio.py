from pydantic_settings import BaseSettings, SettingsConfigDict


class MinIOSettings(BaseSettings):
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "documents"
    MINIO_SECURE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )
