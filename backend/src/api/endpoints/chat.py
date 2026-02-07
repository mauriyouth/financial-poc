from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import orjson

# from sqlalchemy.ext.asyncio import AsyncSession
# from src.core.database import get_db
from pydantic import BaseModel

from src.api import schemas  # We might need new schemas for Chat
from src.configurations.settings import settings
from src.connectors.anthropic_connector import AnthropicConnector
from src.connectors.gemini_connector import GeminiConnector
from src.connectors.google_adk_connector import GoogleADKConnector
from src.connectors.opensearch_connector import OpenSearchConnector
from src.configurations.opensearch import OpenSearchSettings
from src.modules.embeddings.gemini_embedder import GeminiEmbedder
from src.modules.agents.service import AIService
from src.services.chat_service import ChatService
from src.stores.postgres.conversation_store import ConversationStore

router = APIRouter()


# Dependency Injection
def get_chat_service() -> ChatService:
    """
    Dependency injection for ChatService with multi-agent support.

    This constructs the entire agent architecture:
    1. Connectors (Anthropic, Gemini, ADK)
    2. Agent registry
    3. Specialized agents (SEC, Financial, General)
    4. Orchestrator agent
    5. AI Service with agent support
    6. Chat Service
    """
    # Connectors
    anthropic = AnthropicConnector()
    gemini = GeminiConnector()
    adk_connector = GoogleADKConnector()

    # RAG Dependencies
    opensearch_settings = OpenSearchSettings()
    opensearch_connector = OpenSearchConnector(opensearch_settings)
    embedder = GeminiEmbedder()

    # Import agent classes
    from src.modules.agents.agent_registry import AgentRegistry
    from src.modules.agents.financial_analysis_agent import FinancialAnalysisAgent
    from src.modules.agents.general_chat_agent import GeneralChatAgent
    from src.modules.agents.orchestrator_agent import OrchestratorAgent
    from src.modules.agents.sec_filings_agent import SECFilingsAgent

    # Create agent registry
    registry = AgentRegistry()

    # Create and register specialized agents
    sec_agent = SECFilingsAgent(adk_connector)
    financial_agent = FinancialAnalysisAgent(adk_connector)
    general_agent = GeneralChatAgent(adk_connector, opensearch_connector, embedder)

    registry.register(sec_agent)
    registry.register(financial_agent)
    registry.register(general_agent)

    # Create orchestrator agent with sub-agents from registry
    orchestrator = OrchestratorAgent(adk_connector, registry)
    registry.register(orchestrator)

    # Create AI service with agent support
    ai_service = AIService(anthropic, gemini, adk_connector, orchestrator)

    # Create conversation store and chat service
    from src.stores.postgres.document_store import DocumentStore
    from src.stores.opensearch.chunk_store import ChunkStore

    conv_store = ConversationStore()
    doc_store = DocumentStore()
    chunk_store = ChunkStore(opensearch_connector)
    return ChatService(conv_store, ai_service, doc_store, chunk_store)


# Schemas (Ideally in schemas.py, defining here for brevity then moving if needed)
class CreateConversationRequest(BaseModel):
    title: str | None = None


class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    model: str | None = None
    agent_name: str | None = None  # Specific agent to use (optional)


class ImprovePromptRequest(BaseModel):
    prompt: str
    model: str | None = None


@router.get("/models")
async def list_models() -> list[dict]:
    """Get available AI models from YAML configuration."""
    return settings.get_available_models()


@router.get("/agents")
async def list_agents(service: ChatService = Depends(get_chat_service)) -> list[dict]:
    """Get available AI agents."""
    return service.get_available_agents()


@router.post("/improve-prompt")
async def improve_prompt(
    request: ImprovePromptRequest, service: ChatService = Depends(get_chat_service)
) -> dict[str, str]:
    """Enhance a user's prompt using AI for better clarity and effectiveness."""
    try:
        # Import prompt improver system prompt
        from src.modules.agents.prompts import get_prompt_improver_prompt

        system_prompt = get_prompt_improver_prompt()

        # Use AI service to improve the prompt
        ai_service = service.ai

        full_content = ""

        async for chunk in ai_service.stream_generate(prompt=request.prompt, model=request.model, system=system_prompt):
            try:
                event = orjson.loads(chunk.strip())
                if event.get("type") == "content":
                    full_content += event.get("content", "")
            except (orjson.JSONDecodeError, AttributeError):
                pass

        return {"improved_prompt": full_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/conversations", response_model=schemas.Conversation)  # Assuming schema exists or Any
async def create_conversation(
    request: CreateConversationRequest, service: ChatService = Depends(get_chat_service)
) -> schemas.Conversation:
    conv = await service.create_conversation(request.title)
    return conv


@router.post("/stream")
async def stream_message(
    request: SendMessageRequest, service: ChatService = Depends(get_chat_service)
) -> StreamingResponse:
    try:
        return StreamingResponse(
            service.stream_message(request.conversation_id, request.content, request.model, request.agent_name),
            media_type="text/event-stream",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversations/{conversation_id}/messages", response_model=list[schemas.Message])
async def get_history(conversation_id: str, service: ChatService = Depends(get_chat_service)) -> list[schemas.Message]:
    return await service.get_history(conversation_id)


@router.get("/conversations", response_model=list[schemas.Conversation])
async def list_conversations(service: ChatService = Depends(get_chat_service)) -> list[schemas.Conversation]:
    return await service.list_conversations()
