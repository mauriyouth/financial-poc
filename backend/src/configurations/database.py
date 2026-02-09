from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    POSTGRES_USER: str = Field(..., description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(..., description="PostgreSQL host")
    POSTGRES_PORT: str = Field(..., description="PostgreSQL port")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return self.ASYNC_DATABASE_URL

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
