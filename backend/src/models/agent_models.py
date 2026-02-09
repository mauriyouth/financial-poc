"""Pydantic models for agent interactions."""

from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Standardized input for agent requests."""

    prompt: str = Field(..., description="User's question or request")
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list, description="Previous messages in the conversation"
    )
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context for the agent")


class AgentRoutingInfo(BaseModel):
    """Metadata about agent routing decisions."""

    agent_name: str = Field(..., description="Name of the agent that handled the request")
    routing_reason: str = Field(..., description="Reason for routing to this agent")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in routing decision")


class AgentResponse(BaseModel):
    """Standardized output from agents."""

    content: str = Field(..., description="Agent's response content")
    routing_info: AgentRoutingInfo | None = Field(None, description="Information about routing decision")
    thinking_steps: list[str] = Field(default_factory=list, description="Agent's reasoning steps if available")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class StreamChunk(BaseModel):
    """Typed streaming response chunk."""

    type: str = Field(..., description="Type of chunk: 'agent_info', 'content', 'thinking', 'done', 'error'")
    content: str | None = Field(None, description="Content for this chunk")
    agent_name: str | None = Field(None, description="Agent name for agent_info chunks")
    routing_reason: str | None = Field(None, description="Routing reason for agent_info chunks")
    error: str | None = Field(None, description="Error message for error chunks")
