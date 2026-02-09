from sqlmodel import select

from src.core.database import AsyncSessionLocal
from src.models.all_models import Document


class DocumentStore:
    async def create_document(self, document: Document) -> Document:
        async with AsyncSessionLocal() as session:
            session.add(document)
            await session.commit()
            await session.refresh(document)
            return document

    async def get_document(self, document_id: str) -> Document | None:
        async with AsyncSessionLocal() as session:
            return await session.get(Document, document_id)

    async def update_document(self, document: Document) -> Document:
        async with AsyncSessionLocal() as session:
            session.add(document)
            await session.commit()
            await session.refresh(document)
            return document

    async def list_documents(self, thread_id: str | None = None) -> list[Document]:
        async with AsyncSessionLocal() as session:
            statement = select(Document)
            if thread_id:
                statement = statement.where(Document.thread_id == thread_id)
            result = await session.execute(statement)
            return result.scalars().all()

    async def delete_document(self, document_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            doc = await session.get(Document, document_id)
            if doc:
                await session.delete(doc)
                await session.commit()
                return True
            return False
