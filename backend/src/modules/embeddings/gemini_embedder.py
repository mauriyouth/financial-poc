"""Gemini embedding generation."""

from google import genai
from loguru import logger

from src.configurations.settings import settings


class GeminiEmbedder:
    """Generate embeddings using Gemini (new google.genai client)."""

    def __init__(self):
        """Initialize Gemini embedder with new API."""
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = "gemini-embedding-001"

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector (gemini-embedding-001)
        """
        try:
            result = self.client.models.embed_content(model=self.model, contents=[text])
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of 1536-dimensional embedding vectors
        """
        embeddings = []

        for text in texts:
            try:
                embedding = await self.embed_text(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.warning(f"Failed to embed text, using zero vector: {e}")
                # Use zero vector as fallback (768 dimensions for gemini-embedding-001)
                embeddings.append([0.0] * 768)

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for search query.

        Args:
            query: Search query

        Returns:
            768-dimensional embedding vector
        """
        try:
            result = self.client.models.embed_content(model=self.model, contents=[query])
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
