"""WebSocket endpoint for real-time notifications."""

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from redis.asyncio import Redis

from src.configurations.redis import settings as redis_settings

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections and broadcast messages."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """
        Broadcast a message to all active connections.

        Args:
            message: Message dictionary to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time notifications.

    Listens to Redis pub/sub and forwards messages to connected clients.
    """
    await manager.connect(websocket)

    # Create Redis pub/sub client
    redis_client = Redis.from_url(redis_settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("document_status")

    try:
        # Listen for messages from Redis and client
        while True:
            # Check for Redis pub/sub messages
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                await manager.broadcast(data)

            # Check for client messages (ping/pong)
            try:
                client_message = await websocket.receive_text()
                if client_message == "ping":
                    await websocket.send_text("pong")
            except Exception:
                # No message from client, continue
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
    finally:
        await pubsub.unsubscribe("document_status")
        await redis_client.close()
