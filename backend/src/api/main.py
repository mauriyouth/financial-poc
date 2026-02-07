import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.endpoints import chat, documents, hello, websocket
from src.configurations.settings import settings
from src.core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Ensure tables exist
    create_db_and_tables()

    # Ensure GOOGLE_API_KEY is set in environment for ADK internal usage
    # ADK's google_llm.py instantiates genai.Client() without args,
    # relying on env vars.
    if settings.GOOGLE_API_KEY and "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

    yield


app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check for K8s."""
    return {"status": "healthy"}


app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(websocket.router, tags=["websocket"])  # WebSocket endpoint
