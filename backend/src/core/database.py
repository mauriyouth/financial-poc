from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlmodel import SQLModel, create_engine

from src.configurations.settings import settings

# Async Engine (Legacy/FastAPI usage if needed)
async_engine = create_async_engine(settings.DATABASE_URL)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


# Sync Engine (For Stores/SQLModel)
# Convert async url to sync if needed, or just use asyncpg with SQLModel's async features.
# However, standard SQLModel tutorial uses sync sqlite/postgres widely.
# Let's adjust URL scheme: postgresql+asyncpg -> postgresql
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
engine = create_engine(SYNC_DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
