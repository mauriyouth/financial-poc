"""ORM models package - Database table definitions managed by Alembic."""

from src.models.orm.base import SQLModel

# Import all ORM models here for Alembic auto-discovery
# from src.models.orm.chunk import ChunkORM
# from src.models.orm.message import MessageORM
# ... etc

__all__ = [
    "SQLModel",
]
