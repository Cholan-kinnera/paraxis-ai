# ==============================================================================
# Paraxis AI Intelligence Platform (FastAPI + LangGraph) Production Dockerfile
# ==============================================================================
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8001

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for optimal layer caching
COPY backend/intelligence/requirements.txt /app/backend/intelligence/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/intelligence/requirements.txt

# Copy backend intelligence source code
COPY backend/intelligence /app/backend/intelligence

# Expose default HTTP port
EXPOSE 8001

# Run ASGI server with single-worker mandate (required for in-process LangGraph MemorySaver)
CMD ["sh", "-c", "uvicorn backend.intelligence.main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 1"]
