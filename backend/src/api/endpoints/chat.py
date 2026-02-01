from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

# from sqlalchemy.ext.asyncio import AsyncSession
# from src.core.database import get_db
from pydantic import BaseModel

from src.api import schemas  # We might need new schemas for Chat
from src.connectors.anthropic_connector import AnthropicConnector
from src.connectors.gemini_connector import GeminiConnector
from src.services.ai_service import AIService
from src.services.chat_service import ChatService
from src.stores.postgres.conversation_store import ConversationStore
from src.configurations.settings import settings

router = APIRouter()


# Dependency Injection
def get_chat_service() -> ChatService:
    conv_store = ConversationStore()

    # AI Service construction
    anthropic = AnthropicConnector()
    gemini = GeminiConnector()
    ai_service = AIService(anthropic, gemini)

    return ChatService(conv_store, ai_service)


# Schemas (Ideally in schemas.py, defining here for brevity then moving if needed)
class CreateConversationRequest(BaseModel):
    title: str | None = None


class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    provider: str = "anthropic"
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
