# Worker Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Sync dependencies using uv
# We use --no-install-project because the source code isn't copied yet
RUN uv sync --no-dev --no-install-project --group worker

# Ensure the virtual environment is used
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY backend/ .

# Copy and set entrypoint
COPY infra/images/worker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Environment variables
ENV PYTHONUNBUFFERED=1

# Use entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
