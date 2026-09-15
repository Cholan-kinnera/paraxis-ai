# ==============================================================================
# Paraxis AI Core Platform (Django + DRF) Production Dockerfile
# ==============================================================================
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend/core \
    PORT=8000 \
    GUNICORN_WORKERS=2

# Install system dependencies required for psycopg2 and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for optimal layer caching
COPY backend/core/requirements.txt /app/backend/core/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/core/requirements.txt

# Copy backend core source code
COPY backend/core /app/backend/core

WORKDIR /app/backend/core

# Collect static files for Django Admin / DRF API browsable interface
RUN python manage.py collectstatic --noinput

# Ensure entrypoint script is executable
RUN chmod +x /app/backend/core/entrypoint.sh

# Expose default HTTP port
EXPOSE 8000

# Set entrypoint to run migrations before Gunicorn
ENTRYPOINT ["/app/backend/core/entrypoint.sh"]
