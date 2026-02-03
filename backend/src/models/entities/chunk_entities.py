"""Chunk entities - Business logic models."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional


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
    page: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

    # For web pages
    selector: Optional[str] = None  # CSS/DOM selector
    xpath: Optional[str] = None  # XPath for precise location
    offset: Optional[int] = None  # Character offset in element

    # For text-based documents
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None

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

    bbox: Optional[BBox] = None  # Bounding box for precise location
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
    bbox: Optional[BBox] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkSearchRequest(BaseModel):
    """DTO for chunk search."""

    query: str
    source_types: list[SourceType] | None = None
    limit: int = Field(default=10, ge=1, le=100)
