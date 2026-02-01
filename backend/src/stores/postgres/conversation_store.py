from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.core.database import AsyncSessionLocal
from src.models.all_models import Conversation, Message


class ConversationStore:
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        async with AsyncSessionLocal() as session:
            session.add(conversation)
            await session.commit()

            # Re-query with eager load to avoid DetachedInstanceError on messages relationship
            statement = (
                select(Conversation)
                .where(Conversation.id == conversation.id)
                .options(selectinload(Conversation.messages))
            )
            result = await session.execute(statement)
            return result.scalars().first()

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        async with AsyncSessionLocal() as session:
            statement = (
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .options(selectinload(Conversation.messages))
            )
            result = await session.execute(statement)
            return result.scalars().first()

    async def add_message(self, message: Message) -> Message:
        async with AsyncSessionLocal() as session:
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message

    async def get_messages(self, conversation_id: str) -> list[Message]:
        async with AsyncSessionLocal() as session:
            statement = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
            result = await session.execute(statement)
            return result.scalars().all()

    async def list_conversations(self) -> list[Conversation]:
        async with AsyncSessionLocal() as session:
            statement = (
                select(Conversation)
                .order_by(Conversation.created_at.desc())
                .options(selectinload(Conversation.messages))
            )
            result = await session.execute(statement)
            return result.scalars().all()
