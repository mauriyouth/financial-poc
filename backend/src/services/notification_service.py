"""Notification service for real-time updates via Redis pub/sub."""

import json
from datetime import datetime

from loguru import logger
from redis.asyncio import Redis


class NotificationService:
    """Service for publishing real-time notifications via Redis pub/sub."""

    def __init__(self, redis_client: Redis):
        """
        Initialize notification service.

        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client

    async def publish_document_status(
        self,
        document_id: str,
        status: str,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        Publish document status update to Redis channel.

        Args:
            document_id: Document ID
            status: Document processing status (pending, processing, completed, failed)
            user_id: Optional user ID for targeted notifications
            metadata: Optional additional metadata (error message, chunk count, etc.)
        """
        message = {
            "type": "document_status",
            "document_id": document_id,
            "status": status,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            await self.redis.publish("document_status", json.dumps(message))
            logger.debug(f"Published document status: {document_id} -> {status}")
        except Exception as e:
            logger.error(f"Failed to publish document status: {e}")
