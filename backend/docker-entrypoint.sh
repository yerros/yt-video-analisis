#!/bin/bash
# Backend entrypoint script for Docker container

set -e

echo "========================================"
echo "  Video Analysis - Backend Starting"
echo "========================================"
echo ""

# Wait for database to be ready
echo "→ Waiting for PostgreSQL..."
until pg_isready -h postgres -U ${POSTGRES_USER:-postgres} > /dev/null 2>&1; do
    echo "  PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "✓ PostgreSQL is ready"
echo ""

# Wait for Redis to be ready
echo "→ Waiting for Redis..."
until redis-cli -h redis ping > /dev/null 2>&1; do
    echo "  Redis is unavailable - sleeping"
    sleep 2
done
echo "✓ Redis is ready"
echo ""

# Run database migrations
echo "→ Running database migrations..."
alembic upgrade head
echo "✓ Migrations completed"
echo ""

# Start the application
echo "→ Starting backend server..."
echo "========================================"
exec "$@"
