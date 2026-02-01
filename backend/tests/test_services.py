"""
Service layer tests for the financial POC backend.
"""

from src.services.ai_service import AIResponse


def test_ai_response_model():
    """Test AIResponse model creation."""
    response = AIResponse(content="Test response", thinking_steps=["step1", "step2"])
    assert response.content == "Test response"
    assert len(response.thinking_steps) == 2
    assert response.thinking_steps[0] == "step1"


def test_ai_response_empty_thinking():
    """Test AIResponse with no thinking steps."""
    response = AIResponse(content="Test", thinking_steps=[])
    assert response.content == "Test"
    assert response.thinking_steps == []


# Add more service tests here as the application grows
# Examples:
# - Test chat service message creation
# - Test document processing
# - Test AI provider integration (with mocks)
