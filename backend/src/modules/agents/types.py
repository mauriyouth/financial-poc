from typing import Any

from pydantic import BaseModel


class AIResponse(BaseModel):
    """AI response model."""

    content: str
    thinking_steps: list[str] = []
    function_call: dict[str, Any] | None = None
