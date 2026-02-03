# Backend Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies (core + worker group only)
RUN uv pip install --system --no-cache -e . --group worker

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "worker.py"]
