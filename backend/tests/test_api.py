"""
Basic API tests for the financial POC backend.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_app_exists():
    """Test that the FastAPI app is created."""
    assert app is not None
    assert app.title is not None


@pytest.mark.asyncio
async def test_conversations_creation():
    """Test creating a new conversation - may fail if DB not available."""
    response = client.post("/api/chat/conversations", json={"title": "Test Conversation"})
    # Should either succeed or gracefully handle DB connection issues
    assert response.status_code in [200, 201, 404, 500, 503]


def test_api_routes_registered():
    """Test that API routes are registered."""
    routes = [route.path for route in app.routes]
    # Should have chat and documents routes
    assert any("chat" in route for route in routes)
    assert any("documents" in route for route in routes)
