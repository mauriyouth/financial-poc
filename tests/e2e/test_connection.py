import os
import time
import requests
import pytest
import psycopg2
import redis
from minio import Minio

# E2E test configuration from environment
API_URL = os.getenv("API_URL", "http://localhost:8000")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_USER = os.getenv("DB_USER", "testuser")
DB_PASS = os.getenv("DB_PASS", "testpassword")
DB_NAME = os.getenv("DB_NAME", "testdb")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6380")
MINIO_HOST = os.getenv("MINIO_HOST", "localhost:9002")
MINIO_USER = os.getenv("MINIO_USER", "miniotest")
MINIO_PASS = os.getenv("MINIO_PASS", "miniotestpassword")


def test_api_health():
    """Verify that the API is up and responding."""
    # Retry a few times as it might still be starting
    for _ in range(30):
        try:
            response = requests.get(f"{API_URL}/hello")
            if response.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(2)
    pytest.fail("API failed to become healthy")


def test_database_connection():
    """Verify that we can connect to the test database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME
        )
        assert conn.status == psycopg2.extensions.STATUS_READY
        conn.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")


def test_redis_connection():
    """Verify that we can connect to Valkey/Redis."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=0)
        assert r.ping() is True
    except Exception as e:
        pytest.fail(f"Redis connection failed: {e}")


def test_minio_connection():
    """Verify that we can connect to MinIO."""
    try:
        client = Minio(
            MINIO_HOST, access_key=MINIO_USER, secret_key=MINIO_PASS, secure=False
        )
        assert client.bucket_exists("non-existent-bucket") is False
    except Exception as e:
        pytest.fail(f"MinIO connection failed: {e}")


def test_full_flow_upload_ready():
    """Basic check that the documents endpoint is ready."""
    try:
        response = requests.get(f"{API_URL}/documents")
        assert response.status_code in [
            200,
            401,
        ]  # 401 if auth is enabled, 200 if empty list
    except Exception as e:
        pytest.fail(f"Documents endpoint failed: {e}")
