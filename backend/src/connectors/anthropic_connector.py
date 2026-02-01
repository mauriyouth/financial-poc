import anthropic

from src.configurations.settings import settings


class AnthropicConnector:
    def __init__(self):
        """
        Initializes the Anthropic client using settings.
        Configuration is handled here.
        """
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    def get_client(self) -> anthropic.AsyncAnthropic | None:
        return self.client
