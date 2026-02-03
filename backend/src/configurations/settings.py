import os
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configurations.ai import AISettings
from src.configurations.database import DatabaseSettings
from src.configurations.minio import MinIOSettings
from src.configurations.opensearch import OpenSearchSettings
from src.configurations.redis import RedisSettings


class Settings(DatabaseSettings, MinIOSettings, OpenSearchSettings, AISettings, RedisSettings, BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.test"),
        extra="ignore",
    )


def get_settings() -> Settings:
    """Load settings with a fallback for testing."""
    try:
        return Settings()
    except Exception:
        # If loading fails (likely due to missing mandatory env vars during test collection)
        # and we are in a test environment, try to load with dummy values
        if "pytest" in str(os.environ.get("_", "")) or "PYTEST_CURRENT_TEST" in os.environ:
            # This is a bit hacky but helps with collection

            os.environ.setdefault("POSTGRES_USER", "test")
            os.environ.setdefault("POSTGRES_PASSWORD", "test")
            os.environ.setdefault("POSTGRES_DB", "test")
            os.environ.setdefault("POSTGRES_HOST", "localhost")
            os.environ.setdefault("POSTGRES_PORT", "5432")
            os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
            os.environ.setdefault("MINIO_ACCESS_KEY", "test")
            os.environ.setdefault("MINIO_SECRET_KEY", "test")
            os.environ.setdefault("MINIO_BUCKET", "test")
            os.environ.setdefault("MINIO_SECURE", "false")
            os.environ.setdefault("OPENSEARCH_HOST", "localhost")
            os.environ.setdefault("OPENSEARCH_PORT", "9200")
            os.environ.setdefault("OPENSEARCH_USER", "admin")
            os.environ.setdefault("OPENSEARCH_PASSWORD", "admin")
            os.environ.setdefault("OPENSEARCH_USE_SSL", "false")
            os.environ.setdefault("OPENSEARCH_VERIFY_CERTS", "false")
            os.environ.setdefault("REDIS_HOST", "localhost")
            os.environ.setdefault("REDIS_PORT", "6379")
            os.environ.setdefault("REDIS_DB", "0")
            os.environ.setdefault("REDIS_PASSWORD", "")
            os.environ.setdefault("ANTHROPIC_API_KEY", "test")
            os.environ.setdefault("GOOGLE_API_KEY", "test")
            os.environ.setdefault("ANTHROPIC_MODEL", "test")
            os.environ.setdefault("ANTHROPIC_MAX_TOKENS", "1000")
            os.environ.setdefault("ADK_DEFAULT_MODEL", "test")
            os.environ.setdefault("ADK_DEFAULT_TEMPERATURE", "0.7")
            return Settings()
        raise


settings = get_settings()
