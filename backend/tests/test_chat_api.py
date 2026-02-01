from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from src.api.endpoints.chat import get_chat_service
from src.api.main import app
from src.services.ai_service import AIResponse
from src.services.chat_service import ChatService


# Mock dependencies
def override_get_chat_service():
    # Mock AIService
    mock_ai_service = MagicMock()
    mock_ai_service.generate = AsyncMock(return_value=AIResponse(content="Improved prompt content"))

    # Mock ChatService
    mock_chat_service = MagicMock(spec=ChatService)
    mock_chat_service.ai = mock_ai_service  # Ensure correct attribute access

    return mock_chat_service


# Apply override
app.dependency_overrides[get_chat_service] = override_get_chat_service

client = TestClient(app)


@pytest.mark.asyncio
async def test_improve_prompt():
    """Test the improve-prompt endpoint."""
    response = client.post("/chat/improve-prompt", json={"prompt": "Fix this code", "provider": "anthropic"})

    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
    assert data["improved_prompt"] == "Improved prompt content"


def test_list_models():
    client = TestClient(app)
    response = client.get("/chat/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any(m["provider"] == "anthropic" for m in data)
    assert any(m["provider"] == "google" for m in data)
