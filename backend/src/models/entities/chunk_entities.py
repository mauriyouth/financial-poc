"""Chunk entities - Business logic models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Supported data source types."""

    UPLOADED_FILE = "uploaded_file"
    WEB_PAGE = "web_page"
    SEC_FILING = "sec_filing"
    CAPIQ = "capiq"
    ALPHASENSE = "alphasense"
    INTERNAL_KB = "internal_kb"


class BBox(BaseModel):
    """Bounding box for precise content location."""

    # For PDFs and documents
    page: int | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None

    # For web pages
    selector: str | None = None  # CSS/DOM selector
    xpath: str | None = None  # XPath for precise location
    offset: int | None = None  # Character offset in element

    # For text-based documents
    line_start: int | None = None
    line_end: int | None = None
    char_start: int | None = None
    char_end: int | None = None

    class Config:
        extra = "allow"  # Allow additional fields for flexibility


class Chunk(BaseModel):
    """Chunk entity for business logic."""

    id: str
    source_type: SourceType
    source_id: str
    source_name: str

    content: str
    start_pos: int | None = None
    end_pos: int | None = None

    bbox: BBox | None = None  # Bounding box for precise location
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class ChunkCreate(BaseModel):
    """DTO for creating chunks."""

    source_type: SourceType
    source_id: str
    source_name: str
    content: str
    start_pos: int | None = None
    end_pos: int | None = None
    bbox: BBox | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkSearchRequest(BaseModel):
    """DTO for chunk search."""

    query: str
    source_types: list[SourceType] | None = None
    limit: int = Field(default=10, ge=1, le=100)
