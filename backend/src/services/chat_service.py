from collections.abc import AsyncIterator

import orjson

from src.core.logging import logger
from src.models.all_models import Conversation, Message
from src.modules.agents.service import AIService
from src.services.citation_parser import CitationParser
from src.stores.opensearch.chunk_store import ChunkStore
from src.stores.postgres.conversation_store import ConversationStore
from src.stores.postgres.document_store import DocumentStore


class ChatService:
    def __init__(
        self,
        conversation_store: ConversationStore,
        ai_service: AIService,
        document_store: DocumentStore,
        chunk_store: ChunkStore | None = None,
    ):
        self.store = conversation_store
        self.doc_store = document_store
        self.ai = ai_service
        self.chunk_store = chunk_store
        self.citation_parser = CitationParser(chunk_store) if chunk_store else None
        logger.info("ChatService initialized")

    def get_available_agents(self) -> list[dict]:
        """Get list of available agents from AI service."""
        return self.ai.get_available_agents()

    async def create_conversation(self, title: str | None = None) -> Conversation:
        conv = Conversation(title=title)
        return await self.store.create_conversation(conv)

    async def stream_message(
        self,
        conversation_id: str,
        content: str,
        model: str | None = None,
        agent_name: str | None = None,
    ) -> AsyncIterator[str]:
        logger.info(
            f"Streaming message for conversation {conversation_id} with agent system (agent: {agent_name or 'orchestrator'})"
        )

        # 1. Verify Conversation
        conv = await self.store.get_conversation(conversation_id)
        if not conv:
            raise ValueError("Conversation not found")

        # 2. Persist User Message
        user_msg = Message(conversation_id=conversation_id, role="user", content=content)
        await self.store.add_message(user_msg)

        # 3. Prepare Context with Document Summaries
        # Fetch all completed documents
        # TODO: Filter by conversation if/when we add that association
        documents = await self.doc_store.list_documents()
        completed_docs = [d for d in documents if d.status.value == "completed"]

        context_str = ""
        if completed_docs:
            context_str = "\n\nAvailable Documents:\n"
            for doc in completed_docs:
                summary = (
                    doc.metadata_.get("summary", "No summary available.") if doc.metadata_ else "No summary available."
                )
                context_str += f"- {doc.filename} (ID: {doc.id}): {summary}\n"

            context_str += "\nUse the retrieval tool to verify details from these documents.\n"

        # Prepend context to content for the agent (hidden from user message persistence)
        # We perform this prompt engineering for the AI, but keeping `user_msg` clean
        augmented_content = f"{context_str}\n\nUser Query: {content}" if context_str else content

        # 3b. Fetch Conversation History for Agent Context
        history = await self.store.get_messages(conversation_id)
        # Exclude the current user message which we just added (as we are passing it as prompt)
        # Assuming the history includes it as the last item.
        # But 'prompt' is passed separately.
        # So we should pass history excluding the latest ONE if it matches 'content'
        # Or simpler: pass all previous messages.

        # history list of Message objects.
        # Filter for previous messages only
        # Actually user_msg has an ID.
        history = [m for m in history if m.id != user_msg.id]

        # 4. Stream & Accumulate AI Response using agent system
        full_content = ""
        reasoning_events = []
        agent_transitions = []
        current_agent = agent_name or "Orchestrator"  # Initial agent
        valid_chunk_ids = set()

        async for chunk in self.ai.stream_generate(
            prompt=augmented_content, model=model, agent_name=agent_name, history=history
        ):
            # Parse JSON from chunk
            try:
                event = orjson.loads(chunk.strip())

                # Track agent routing information
                if event.get("type") == "agent_start":
                    new_agent = event.get("agent_name")
                    if new_agent and new_agent != current_agent:
                        agent_transitions.append(
                            {
                                "from": current_agent,
                                "to": new_agent,
                                "reason": event.get("reason", "Routing to specialized agent"),
                            }
                        )
                        current_agent = new_agent

                    # Also add to reasoning events for timeline completeness if desired,
                    # but typically transitions are sufficient.
                    # We'll allow it in reasoning_events too for the detailed view.
                    reasoning_events.append(event)

                # Capture reasoning events
                elif event.get("type") in [
                    "thinking",
                    "tool_call",
                    "llm_error",
                    "thinking_start",
                    "agent_end",
                    "agent_info",
                ]:
                    reasoning_events.append(event)

                # Handle tool result to capture valid chunk ids
                elif event.get("type") == "tool_result":
                    reasoning_events.append(event)
                    # Extract chunk IDs from the tool output if it's a retrieval tool
                    # output is usually a string, we might need to parse it or trust the agent logic
                    # ideally the tool result event contains the structured data or we parse the text
                    # For now, let's assume valid chunks are those returned by the tool.
                    # As a heuristic, if the agent cites something, it must be in the tool outputs.
                    # We can use regex to find IDs in the tool output string.
                    import re

                    tool_output = event.get("output", "")
                    # Chunk IDs matching our format (uuids or specific patterns?)
                    # If we don't know the format, we might need to be careful.
                    # But wait, retrieval_tool returns formatted text with IDs?
                    # The retrieval tool typically returns: "Found X chunks... ID: <uuid> \n Content: ..."
                    # Let's extract UUID-like strings or whatever our ID format is.
                    # Actually, our IDs are usually UUIDs.
                    # simple uuid regex
                    ids = re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", tool_output)
                    valid_chunk_ids.update(ids)

                # Handle content
                elif event.get("type") == "content":
                    full_content += event.get("content", "")

            except (orjson.JSONDecodeError, AttributeError):
                # If not JSON, skip
                pass

            # Yield the original chunk for streaming
            yield chunk

        # 4. Resolve citations in the full content
        final_content = full_content
        message_citations = []

        # 4a. Verification Step
        # Check if citations exist
        referenced_ids = set()
        if self.citation_parser:
            # Just getting IDs first
            _, citations_list = await self.citation_parser.parse_citations(full_content)
            referenced_ids = {c.chunk_id for c in citations_list}

        # If we have citations and some are missing from valid_chunk_ids
        # (Only if we actually ran tools and got results, otherwise valid_chunk_ids is empty)
        # Note: If valid_chunk_ids is empty but we have citations, it MIGHT be a hallucination
        # OR it might be from the "Available Documents" context (which we don't strictly cite with chunks usually, but agent might).
        # The prompt says: "You may use the summaries provided... WITHOUT needing specific chunk citations".
        # So if it cites a chunk ID, it MUST be from retrieval.

        hallucinations = referenced_ids - valid_chunk_ids
        if hallucinations and valid_chunk_ids:
            logger.warning(f"Detected potential hallucinations: {hallucinations}. Running verification.")
            verified_content = await self.ai.verify_response(
                query=content, draft_response=full_content, valid_chunk_ids=list(valid_chunk_ids)
            )
            if verified_content != full_content:
                logger.info("Verification corrected the response.")
                final_content = verified_content
                # Add a verification event
                verification_event = {
                    "type": "verification",
                    "original_citations": list(referenced_ids),
                    "valid_chunks": list(valid_chunk_ids),
                    "correction": "Response was verified and corrected for citation accuracy.",
                }
                # Ensure we have a list to append to
                if reasoning_events is None:
                    reasoning_events = []
                reasoning_events.append(verification_event)

        # 4b. Re-parse citations from final (potentially verified) content
        if self.citation_parser:
            final_content, citations_list = await self.citation_parser.parse_citations(final_content)
            # Convert CID objects to dictionaries for storage
            message_citations = [c.model_dump() for c in citations_list]

        # 5. Persist AI Message with clean content and agent info
        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=final_content,  # Clean markdown content with [1], [2] citations
            citations=message_citations,
            reasoning_events=reasoning_events if reasoning_events else None,
            agent_transitions=agent_transitions if agent_transitions else None,
        )
        await self.store.add_message(ai_msg)

    async def get_history(self, conversation_id: str) -> list[Message]:
        return await self.store.get_messages(conversation_id)

    async def list_conversations(self) -> list[Conversation]:
        return await self.store.list_conversations()
