from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"  # Document is queued for processing
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    upload_date: datetime
    status: ProcessingStatus
    file_type: str | None = None
    page_count: int | None = None
    error_message: str | None = None
    download_url: str | None = None
    thumbnail_url: str | None = None


class CitationSchema(BaseModel):
    """Citation with source information and bbox for highlighting."""

    id: str
    chunk_id: str
    source_name: str
    source_type: str
    content: str
    bbox: dict | None = None  # BBox information for frontend highlighting
    metadata: dict = {}


class Message(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: list[dict] = []
    citations: list[CitationSchema] | None = None  # NEW: Citations with bbox (optional)
    thinking_steps: list[Any] | None = None
    reasoning_events: list[Any] | None = None
    agent_transitions: list[Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class Conversation(BaseModel):
    id: str
    title: str | None = None
    created_at: datetime
    messages: list[Message] = []

    class Config:
        from_attributes = True
