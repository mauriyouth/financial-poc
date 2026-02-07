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
    """Load settings."""
    return Settings()


settings = get_settings()
