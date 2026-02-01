"""
System prompt management module.

This module provides utilities for loading and managing system prompts
used across the application. Prompts are stored as text files in the
prompts directory and can be retrieved by name.
"""

from pathlib import Path
from typing import Optional

from src.core.logging import logger

PROMPTS_DIR = Path(__file__).parent


class PromptManager:
    """Manages system prompts for AI interactions."""

    _cache: dict[str, str] = {}

    @classmethod
    def get_prompt(cls, name: str) -> str:
        """
        Get a system prompt by name.

        Args:
            name: Name of the prompt file (without .txt extension)

        Returns:
            The prompt text

        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        # Check cache first
        if name in cls._cache:
            logger.debug(f"Retrieved prompt '{name}' from cache")
            return cls._cache[name]

        # Load from file
        prompt_path = PROMPTS_DIR / f"{name}.txt"
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {prompt_path}")
            raise FileNotFoundError(f"Prompt '{name}' not found")

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read().strip()

            # Cache it
            cls._cache[name] = prompt_text
            logger.info(f"Loaded prompt '{name}' from {prompt_path}")
            return prompt_text

        except Exception as e:
            logger.error(f"Failed to load prompt '{name}': {e}")
            raise

    @classmethod
    def get_prompt_safe(cls, name: str, default: Optional[str] = None) -> str:
        """
        Get a system prompt by name, with fallback.

        Args:
            name: Name of the prompt file (without .txt extension)
            default: Default prompt to use if file not found

        Returns:
            The prompt text or default
        """
        try:
            return cls.get_prompt(name)
        except FileNotFoundError:
            if default is not None:
                logger.warning(f"Using default prompt for '{name}'")
                return default
            logger.warning(f"No prompt found for '{name}', using generic default")
            return "You are a helpful assistant."

    @classmethod
    def list_prompts(cls) -> list[str]:
        """List all available prompt names."""
        prompts = [p.stem for p in PROMPTS_DIR.glob("*.txt")]
        logger.debug(f"Available prompts: {prompts}")
        return prompts

    @classmethod
    def reload_prompt(cls, name: str) -> str:
        """Reload a prompt from disk, bypassing cache."""
        if name in cls._cache:
            del cls._cache[name]
            logger.debug(f"Cleared cache for prompt '{name}'")
        return cls.get_prompt(name)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached prompts."""
        cls._cache.clear()
        logger.info("Cleared prompt cache")


# Convenience functions
def get_default_prompt() -> str:
    """Get the default system prompt."""
    return PromptManager.get_prompt("default")


def get_document_qa_prompt() -> str:
    """Get the document QA system prompt."""
    return PromptManager.get_prompt("document_qa")


def get_prompt_improver_prompt() -> str:
    """Get the prompt improvement system prompt."""
    return PromptManager.get_prompt("prompt_improver")
