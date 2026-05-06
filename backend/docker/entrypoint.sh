#!/bin/sh
# Docker entrypoint: run migrations then start the server.
# 'set -e' ensures any command failure stops the script immediately.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --no-access-log
