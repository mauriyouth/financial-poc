import pytest
from fastapi.testclient import TestClient

from src.api.main import app


# Client is initialized below


client = TestClient(app)


@pytest.mark.asyncio
async def test_improve_prompt():
    """Test the improve-prompt endpoint."""
    response = client.post("/chat/improve-prompt", json={"prompt": "Fix this code"})

    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
    assert data["improved_prompt"]  # Just check it's not empty


def test_list_models():
    client = TestClient(app)
    response = client.get("/chat/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any(m["provider"] == "anthropic" for m in data)
    assert any(m["provider"] == "google" for m in data)
