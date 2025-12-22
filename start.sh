#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting uvicorn server on port ${PORT:-8080}..."
exec uvicorn gc_registry.main:app --host 0.0.0.0 --port ${PORT:-8080}
