from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """Configuration for a single AI model."""

    id: str = Field(..., description="Model ID used by the provider")
    name: str = Field(..., description="Human-readable model name")
    max_tokens: int = Field(default=4096, description="Maximum tokens for this model")
    supports_thinking: bool = Field(default=False, description="Whether model supports thinking/reasoning")
    description: str = Field(default="", description="Model description")
    enabled: bool = Field(default=True, description="Whether this model is enabled for use")


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""

    models: list[ModelConfig] = Field(default_factory=list, description="List of available models")


class ModelConfigurations:
    """Loads and manages model configurations from YAML file."""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            # Default to configurations/model_configurations.yaml
            config_path = Path(__file__).parent / "model_configurations.yaml"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.providers: dict[str, ProviderConfig] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Model configuration file not found: {self.config_path}")

        with open(self.config_path) as f:
            data = yaml.safe_load(f)

        # Parse providers and models
        providers_data = data.get("providers", {})
        for provider_name, provider_data in providers_data.items():
            self.providers[provider_name] = ProviderConfig(**provider_data)

    def get_all_models(self) -> list[dict[str, any]]:
        """Get all enabled models from all providers as a list of dicts."""
        models = []
        for provider_name, provider_config in self.providers.items():
            for model in provider_config.models:
                # Only include enabled models
                if not getattr(model, "enabled", True):
                    continue

                models.append(
                    {
                        "id": f"{provider_name}:{model.id}",
                        "name": f"{model.name} ({provider_name.title()})",
                        "provider": provider_name,
                        "model_id": model.id,
                        "max_tokens": model.max_tokens,
                        "supports_thinking": model.supports_thinking,
                        "description": model.description,
                        "enabled": getattr(model, "enabled", True),
                    }
                )
        return models

    def get_model_config(self, provider: str, model_id: str) -> ModelConfig | None:
        """Get configuration for a specific model."""
        provider_config = self.providers.get(provider)
        if not provider_config:
            return None

        for model in provider_config.models:
            if model.id == model_id:
                return model
        return None

    def get_provider_models(self, provider: str) -> list[ModelConfig]:
        """Get all models for a specific provider."""
        provider_config = self.providers.get(provider)
        if not provider_config:
            return []
        return provider_config.models


class AISettings(BaseSettings):
    """AI provider settings with API keys."""

    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key")
    GOOGLE_API_KEY: str = Field(..., description="Google Gemini API key")

    # Model settings
    ANTHROPIC_MODEL: str = Field(..., description="Anthropic model ID")
    ANTHROPIC_MAX_TOKENS: int = Field(..., description="Maximum tokens for Anthropic")

    # Google ADK configuration
    ADK_DEFAULT_MODEL: str = Field(..., description="Default model for Google ADK")
    ADK_DEFAULT_TEMPERATURE: float = Field(..., description="Default temperature for Google ADK")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load model configurations from YAML
        self._model_configs = ModelConfigurations()

    def get_available_models(self) -> list[dict[str, any]]:
        """Get all available models from configuration file."""
        return self._model_configs.get_all_models()

    def get_model_config(self, provider: str, model_id: str) -> ModelConfig | None:
        """Get configuration for a specific model."""
        return self._model_configs.get_model_config(provider, model_id)

    def get_provider_models(self, provider: str) -> list[ModelConfig]:
        """Get all models for a specific provider."""
        return self._model_configs.get_provider_models(provider)
