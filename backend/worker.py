"""
RQ Worker entry point for document parsing.

Run this with: python worker.py
"""

import os

# Fix macOS fork safety issue with minio/S3 client
# This must be set before importing any libraries
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

from redis import Redis
from rq import Worker

from src.configurations.redis import settings

if __name__ == "__main__":
    # Connect to Redis
    redis_conn = Redis.from_url(settings.redis_url)

    # Start worker
    print(f"Starting RQ worker, connected to Redis at {settings.redis_url}")
    worker = Worker(["default"], connection=redis_conn)
    worker.work()
