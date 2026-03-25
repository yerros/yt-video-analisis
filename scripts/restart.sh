#!/bin/bash

# restart.sh - Restart all services with verification
# This script stops all services gracefully/forcefully, then starts them with full verification

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "  Restarting Video Analysis Services"
echo "======================================"
echo ""

# Stop all services
echo "→ Stopping all services..."
"$SCRIPT_DIR/stop.sh"

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Warning: Stop script reported issues, but continuing with start..."
    echo ""
fi

# Wait a moment to ensure clean shutdown
echo ""
echo "→ Waiting 2 seconds for clean shutdown..."
sleep 2
echo ""

# Start all services
echo "→ Starting all services..."
"$SCRIPT_DIR/start.sh"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Start script failed!"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ Restart completed successfully!"
echo "======================================"
