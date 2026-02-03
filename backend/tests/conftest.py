import os

import pytest


# Set mandatory environment variables for tests AT IMPORT TIME
# to prevent Pydantic validation errors during test collection.
os.environ.update(
    {
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_DB": "test",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "test",
        "MINIO_SECRET_KEY": "test",
        "MINIO_BUCKET": "test",
        "MINIO_SECURE": "false",
        "OPENSEARCH_HOST": "localhost",
        "OPENSEARCH_PORT": "9200",
        "OPENSEARCH_USER": "admin",
        "OPENSEARCH_PASSWORD": "admin",
        "OPENSEARCH_USE_SSL": "false",
        "OPENSEARCH_VERIFY_CERTS": "false",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0",
        "ANTHROPIC_API_KEY": "test",
        "GOOGLE_API_KEY": "test",
        "ANTHROPIC_MODEL": "test",
        "ANTHROPIC_MAX_TOKENS": "1000",
        "ADK_DEFAULT_MODEL": "test",
        "ADK_DEFAULT_TEMPERATURE": "0.7",
    }
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Environment already setup at module level."""
    yield
