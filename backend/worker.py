"""
RQ Worker entry point for document parsing.

Run this with: python worker.py
"""

import os

# Fix macOS fork safety issue with minio/S3 client
# This must be set before importing any libraries
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

import logging
import sys

# Import loguru and interception handler
from src.core.logging import logger, InterceptHandler
from redis import Redis
from rq import Worker

from src.configurations.redis import settings

# Redirect standard logging to Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0)

# Aggressively suppress verbose logging from libraries
for lib in ["opensearch", "urllib3", "pdfminer", "pdfplumber", "google", "httpcore", "httpx", "botocore", "s3transfer"]:
    logging.getLogger(lib).setLevel(logging.WARNING)

if __name__ == "__main__":
    # Connect to Redis
    redis_conn = Redis.from_url(settings.redis_url)

    # Start worker
    logger.info(f"Starting RQ worker, connected to Redis at {settings.redis_url}")
    worker = Worker(["default"], connection=redis_conn)
    worker.work()
