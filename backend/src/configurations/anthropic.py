from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnthropicSettings(BaseSettings):
    model: str = "claude-sonnet-4-0"
    API_KEY: str
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ANTHROPIC_",
        extra="ignore",
    )

    def get_model(self) -> AnthropicModel:
        return AnthropicModel("claude-sonnet-4-5", provider=AnthropicProvider(api_key=self.API_KEY))
