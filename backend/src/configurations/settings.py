from pydantic_settings import BaseSettings
from src.configurations.database import DatabaseSettings
from src.configurations.minio import MinIOSettings
from src.configurations.opensearch import OpenSearchSettings
from src.configurations.ai import AISettings
from src.configurations.redis import RedisSettings


class Settings(DatabaseSettings, MinIOSettings, OpenSearchSettings, AISettings, RedisSettings, BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
