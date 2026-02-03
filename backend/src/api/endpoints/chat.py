from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

# from sqlalchemy.ext.asyncio import AsyncSession
# from src.core.database import get_db
from pydantic import BaseModel

from src.api import schemas  # We might need new schemas for Chat
from src.configurations.settings import settings
from src.connectors.anthropic_connector import AnthropicConnector
from src.connectors.gemini_connector import GeminiConnector
from src.connectors.google_adk_connector import GoogleADKConnector
from src.services.ai_service import AIService
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
    general_agent = GeneralChatAgent(adk_connector)

    registry.register(sec_agent)
    registry.register(financial_agent)
    registry.register(general_agent)

    # Create orchestrator agent with sub-agents from registry
    orchestrator = OrchestratorAgent(adk_connector, registry)
    registry.register(orchestrator)

    # Create AI service with agent support
    ai_service = AIService(anthropic, gemini, adk_connector, orchestrator)

    # Create conversation store and chat service
    conv_store = ConversationStore()
    return ChatService(conv_store, ai_service)


# Schemas (Ideally in schemas.py, defining here for brevity then moving if needed)
class CreateConversationRequest(BaseModel):
    title: str | None = None


class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    provider: str = "adk"  # Use multi-agent system by default
    model: str | None = None


class ImprovePromptRequest(BaseModel):
    prompt: str
    provider: str = "anthropic"
    model: str | None = None


@router.get("/models")
async def list_models() -> list[dict]:
    """Get available AI models from YAML configuration."""
    return settings.get_available_models()


@router.post("/improve-prompt")
async def improve_prompt(
    request: ImprovePromptRequest, service: ChatService = Depends(get_chat_service)
) -> dict[str, str]:
    """Enhance a user's prompt using AI for better clarity and effectiveness."""
    try:
        # Import prompt improver system prompt
        from src.prompts import get_prompt_improver_prompt

        system_prompt = get_prompt_improver_prompt()

        # Use AI service to improve the prompt
        ai_service = service.ai
        response = await ai_service.generate(
            prompt=request.prompt, provider=request.provider, model=request.model, system=system_prompt
        )

        return {"improved_prompt": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/conversations", response_model=schemas.Conversation)  # Assuming schema exists or Any
async def create_conversation(
    request: CreateConversationRequest, service: ChatService = Depends(get_chat_service)
) -> schemas.Conversation:
    conv = await service.create_conversation(request.title)
    return conv


@router.post("/messages", response_model=schemas.Message)
async def send_message(
    request: SendMessageRequest, service: ChatService = Depends(get_chat_service)
) -> schemas.Message:
    try:
        msg = await service.send_message(request.conversation_id, request.content, request.provider, request.model)
        return msg
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stream")
async def stream_message(
    request: SendMessageRequest, service: ChatService = Depends(get_chat_service)
) -> StreamingResponse:
    try:
        return StreamingResponse(
            service.stream_message(request.conversation_id, request.content, request.provider, request.model),
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
