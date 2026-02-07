from google import genai

from src.configurations.settings import settings
from src.core.logging import logger


class GeminiConnector:
    def __init__(self):
        """
        Initializes the Gemini client using settings.
        Configuration is handled here.
        """
        self.api_key = settings.GOOGLE_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini connector initialized with API key")
        else:
            self.client = None
            logger.warning("Gemini API key not configured")

    def get_client(self) -> genai.Client | None:
        """Get the Gemini client."""
        return self.client

    def get_model(self, model_name: str = "gemini-1.5-pro") -> genai.Client | None:
        """
        Get a configurator or client for specific model.
        In new SDK, we mostly use client directly with model name.
        This method is kept for compatibility but returns the client.
        """
        if not self.client:
            logger.error("Cannot get model: Gemini API key not configured")
            return None

        return self.client
