"""Citation entities."""

from pydantic import BaseModel


class Citation(BaseModel):
    """Citation referencing a chunk."""

    id: str  # cite_1, cite_2
    chunk_id: str
    excerpt: str  # Preview of cited text
    relevance_score: float | None = None


class CitationWithSource(Citation):
    """Citation with full source metadata."""

    source_type: str
    source_name: str
    metadata: dict
