"""Citation entities."""

from pydantic import BaseModel


class Citation(BaseModel):
    """Citation referencing a chunk with full metadata."""

    id: str  # cite_1, cite_2
    chunk_id: str
    source_name: str
    source_type: str
    content: str
    bbox: dict | None = None
    metadata: dict = {}
    relevance_score: float | None = None


# Keep for backward compatibility if needed, but Citation is now complete
class CitationWithSource(Citation):
    """Citation with full source metadata."""

    pass
