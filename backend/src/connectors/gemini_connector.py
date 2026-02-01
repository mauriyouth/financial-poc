import google.generativeai as genai

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
            genai.configure(api_key=self.api_key)
            logger.info("Gemini connector initialized with API key")
        else:
            logger.warning("Gemini API key not configured")

    def get_model(self, model_name: str = "gemini-1.5-pro") -> genai.GenerativeModel | None:
        """Get a Gemini model by name."""
        if not self.api_key:
            logger.error("Cannot get model: Gemini API key not configured")
            return None

        logger.debug(f"Creating Gemini model: {model_name}")
        return genai.GenerativeModel(model_name)
