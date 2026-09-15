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

# Expose default HTTP port
EXPOSE 8000

# Run production WSGI server with dynamic Render $PORT support
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-2} --timeout 120 --access-logfile - --error-logfile -"]
