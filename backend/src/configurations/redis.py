from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Redis configuration settings for queue management."""

    REDIS_HOST: str = Field(..., description="Redis/Valkey host")
    REDIS_PORT: int = Field(..., description="Redis/Valkey port")
    REDIS_DB: int = Field(..., description="Redis/Valkey database index")
    REDIS_PASSWORD: str | None = Field(None, description="Redis/Valkey password")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def redis_url(self) -> str:
        """Generate Redis URL from settings."""
        # Handle cases where password might be empty string or empty quotes from env
        p = self.REDIS_PASSWORD
        if p is None:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

        # Strip common quote wrappers if present
        p = p.strip().strip("'").strip('"')

        if not p:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

        return f"redis://:{p}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Create singleton instance
settings = RedisSettings()
