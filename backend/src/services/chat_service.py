from collections.abc import AsyncIterator

from src.core.logging import logger
from src.models.all_models import Conversation, Message
from src.services.ai_service import AIService
from src.services.citation_parser import CitationParser
from src.stores.opensearch.chunk_store import ChunkStore
from src.stores.postgres.conversation_store import ConversationStore


class ChatService:
    def __init__(
        self,
        conversation_store: ConversationStore,
        ai_service: AIService,
        chunk_store: ChunkStore | None = None,
    ):
        self.store = conversation_store
        self.ai = ai_service
        self.citation_parser = CitationParser(chunk_store) if chunk_store else None
        logger.info("ChatService initialized")

    async def create_conversation(self, title: str | None = None) -> Conversation:
        conv = Conversation(title=title)
        return await self.store.create_conversation(conv)

    async def send_message(
        self, conversation_id: str, content: str, provider: str = "adk", model: str | None = None
    ) -> Message:
        logger.info(f"Processing message for conversation {conversation_id} with provider {provider}")

        # 1. Verify Conversation
        conv = await self.store.get_conversation(conversation_id)
        if not conv:
            logger.error(f"Conversation not found: {conversation_id}")
            raise ValueError("Conversation not found")

        # 2. Persist User Message
        user_msg = Message(conversation_id=conversation_id, role="user", content=content)

        await self.store.add_message(user_msg)
        logger.debug(f"User message saved: {user_msg.id}")

        # 3. Generate AI Response
        logger.debug(f"Requesting AI response from {provider}")
        ai_response = await self.ai.generate(prompt=content, provider=provider, model=model)
        logger.debug(f"AI response received: {len(ai_response.content)} chars")

        # 4. Parse citations if citation parser is available
        response_content = ai_response.content
        citations = []
        if self.citation_parser:
            try:
                response_content, citations = await self.citation_parser.parse_citations(ai_response.content)
                logger.info(f"Parsed {len(citations)} citations")
            except Exception as e:
                logger.error(f"Error parsing citations: {e}")

        # 5. Persist AI Message with citations
        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_content,
            thinking_steps=ai_response.thinking_steps,
        )
        # Manually set citations since it's not in Message model
        ai_msg.sources = [c.dict() for c in citations]  # Store in sources for now
        await self.store.add_message(ai_msg)
        logger.info(f"Assistant message saved: {ai_msg.id}")

        return ai_msg

    async def stream_message(
        self, conversation_id: str, content: str, provider: str = "adk", model: str | None = None
    ) -> AsyncIterator[str]:
        # 1. Verify Conversation
        conv = await self.store.get_conversation(conversation_id)
        if not conv:
            raise ValueError("Conversation not found")

        # 2. Persist User Message
        user_msg = Message(conversation_id=conversation_id, role="user", content=content)

        await self.store.add_message(user_msg)

        # 3. Stream & Accumulate AI Response
        import json

        full_content = ""
        thinking_steps = []
        thinking_buffer = ""
        agent_routing_info = None

        async for chunk in self.ai.stream_generate(prompt=content, provider=provider, model=model):
            # Parse JSON from chunk
            try:
                event = json.loads(chunk.strip())

                # Track agent routing information for user visibility
                if event.get("type") == "agent_info":
                    agent_routing_info = event
                    logger.info(f"Agent routing: {event.get('agent_name')} - {event.get('routing_reason')}")
                elif event.get("type") == "thinking":
                    thinking_buffer += event.get("content", "")
                elif event.get("type") == "thinking_start":
                    thinking_buffer = ""
                elif event.get("type") == "content":
                    full_content += event.get("content", "")
                elif event.get("type") == "block_stop" and thinking_buffer:
                    thinking_steps.append(thinking_buffer)
                    thinking_buffer = ""
            except (json.JSONDecodeError, AttributeError):
                # If not JSON, skip
                pass

            # Yield the original chunk for streaming
            yield chunk

        # 4. Persist AI Message with clean content and agent info
        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_content,  # Clean markdown content only
            thinking_steps=thinking_steps if thinking_steps else None,
        )
        await self.store.add_message(ai_msg)

    async def get_history(self, conversation_id: str) -> list[Message]:
        return await self.store.get_messages(conversation_id)

    async def list_conversations(self) -> list[Conversation]:
        return await self.store.list_conversations()
