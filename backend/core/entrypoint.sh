#!/bin/sh
set -eu

echo "==> Running Django migrations..."
python manage.py migrate --noinput

echo "==> Starting Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers ${GUNICORN_WORKERS:-2} \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
