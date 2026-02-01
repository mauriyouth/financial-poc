from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ProcessingStatus(str, Enum):
    PENDING = "pending"
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


class Message(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: list[dict] = []
    thinking_steps: list[Any] | None = None
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
