#!/bin/bash

# status.sh - Check status of all services without starting or stopping them
# This script provides a comprehensive status report of all video analysis services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

API_PID_FILE="$BACKEND_DIR/api.pid"
WORKER_PID_FILE="$BACKEND_DIR/worker.pid"
MONITOR_PID_FILE="$BACKEND_DIR/monitor.pid"
FRONTEND_PID_FILE="$FRONTEND_DIR/frontend.pid"

API_PORT=8000
FRONTEND_PORT=3000

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================"
echo "  Video Analysis Services Status"
echo "======================================"
echo ""

# Function to check if process is running
check_process() {
    local pid=$1
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to get PID from port
get_pid_from_port() {
    local port=$1
    lsof -ti ":$port" 2>/dev/null || echo ""
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" | grep -q "200"; then
        return 0
    else
        return 1
    fi
}

# Check prerequisites
echo "📋 Prerequisites:"
echo "─────────────────"

# PostgreSQL
if pgrep -x postgres >/dev/null 2>&1; then
    echo -e "  PostgreSQL:       ${GREEN}✓ Running${NC}"
else
    echo -e "  PostgreSQL:       ${RED}✗ Not running${NC}"
fi

# Redis
if pgrep -x redis-server >/dev/null 2>&1; then
    echo -e "  Redis:            ${GREEN}✓ Running${NC}"
else
    echo -e "  Redis:            ${RED}✗ Not running${NC}"
fi

# Virtual environment
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo -e "  Python venv:      ${GREEN}✓ Exists${NC}"
else
    echo -e "  Python venv:      ${RED}✗ Not found${NC}"
fi

# Node modules
if [ -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "  node_modules:     ${GREEN}✓ Exists${NC}"
else
    echo -e "  node_modules:     ${RED}✗ Not found${NC}"
fi

echo ""
echo "🖥️  Services:"
echo "─────────────────"

# Backend API
if [ -f "$API_PID_FILE" ]; then
    API_PID=$(cat "$API_PID_FILE")
    if check_process "$API_PID"; then
        if check_http "http://localhost:$API_PORT/health"; then
            echo -e "  Backend API:      ${GREEN}✓ Running${NC} (PID: $API_PID, Port: $API_PORT)"
            echo -e "                    ${BLUE}→ http://localhost:$API_PORT${NC}"
        else
            echo -e "  Backend API:      ${YELLOW}⚠ Running but not responding${NC} (PID: $API_PID)"
        fi
    else
        API_PORT_PID=$(get_pid_from_port $API_PORT)
        if [ -n "$API_PORT_PID" ]; then
            echo -e "  Backend API:      ${YELLOW}⚠ Different process on port${NC} (PID: $API_PORT_PID, Port: $API_PORT)"
        else
            echo -e "  Backend API:      ${RED}✗ Not running${NC} (stale PID file)"
        fi
    fi
else
    API_PORT_PID=$(get_pid_from_port $API_PORT)
    if [ -n "$API_PORT_PID" ]; then
        echo -e "  Backend API:      ${YELLOW}⚠ Running without PID file${NC} (PID: $API_PORT_PID, Port: $API_PORT)"
    else
        echo -e "  Backend API:      ${RED}✗ Not running${NC}"
    fi
fi

# Celery Worker
if [ -f "$WORKER_PID_FILE" ]; then
    WORKER_PID=$(cat "$WORKER_PID_FILE")
    if check_process "$WORKER_PID"; then
        echo -e "  Celery Worker:    ${GREEN}✓ Running${NC} (PID: $WORKER_PID)"
    else
        WORKER_PROC_PID=$(pgrep -f "celery.*worker" | head -n1)
        if [ -n "$WORKER_PROC_PID" ]; then
            echo -e "  Celery Worker:    ${YELLOW}⚠ Different process running${NC} (PID: $WORKER_PROC_PID)"
        else
            echo -e "  Celery Worker:    ${RED}✗ Not running${NC} (stale PID file)"
        fi
    fi
else
    WORKER_PROC_PID=$(pgrep -f "celery.*worker" | head -n1)
    if [ -n "$WORKER_PROC_PID" ]; then
        echo -e "  Celery Worker:    ${YELLOW}⚠ Running without PID file${NC} (PID: $WORKER_PROC_PID)"
    else
        echo -e "  Celery Worker:    ${RED}✗ Not running${NC}"
    fi
fi

# Worker Monitor
if [ -f "$MONITOR_PID_FILE" ]; then
    MONITOR_PID=$(cat "$MONITOR_PID_FILE")
    if check_process "$MONITOR_PID"; then
        echo -e "  Worker Monitor:   ${GREEN}✓ Running${NC} (PID: $MONITOR_PID)"
    else
        MONITOR_PROC_PID=$(pgrep -f "worker_monitor.py" | head -n1)
        if [ -n "$MONITOR_PROC_PID" ]; then
            echo -e "  Worker Monitor:   ${YELLOW}⚠ Different process running${NC} (PID: $MONITOR_PROC_PID)"
        else
            echo -e "  Worker Monitor:   ${RED}✗ Not running${NC} (stale PID file)"
        fi
    fi
else
    MONITOR_PROC_PID=$(pgrep -f "worker_monitor.py" | head -n1)
    if [ -n "$MONITOR_PROC_PID" ]; then
        echo -e "  Worker Monitor:   ${YELLOW}⚠ Running without PID file${NC} (PID: $MONITOR_PROC_PID)"
    else
        echo -e "  Worker Monitor:   ${RED}✗ Not running${NC}"
    fi
fi

# Frontend
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if check_process "$FRONTEND_PID"; then
        if check_http "http://localhost:$FRONTEND_PORT"; then
            echo -e "  Frontend:         ${GREEN}✓ Running${NC} (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)"
            echo -e "                    ${BLUE}→ http://localhost:$FRONTEND_PORT${NC}"
        else
            echo -e "  Frontend:         ${YELLOW}⚠ Running but not responding${NC} (PID: $FRONTEND_PID)"
        fi
    else
        FRONTEND_PORT_PID=$(get_pid_from_port $FRONTEND_PORT)
        if [ -n "$FRONTEND_PORT_PID" ]; then
            echo -e "  Frontend:         ${YELLOW}⚠ Different process on port${NC} (PID: $FRONTEND_PORT_PID, Port: $FRONTEND_PORT)"
        else
            echo -e "  Frontend:         ${RED}✗ Not running${NC} (stale PID file)"
        fi
    fi
else
    FRONTEND_PORT_PID=$(get_pid_from_port $FRONTEND_PORT)
    if [ -n "$FRONTEND_PORT_PID" ]; then
        echo -e "  Frontend:         ${YELLOW}⚠ Running without PID file${NC} (PID: $FRONTEND_PORT_PID, Port: $FRONTEND_PORT)"
    else
        echo -e "  Frontend:         ${RED}✗ Not running${NC}"
    fi
fi

echo ""
echo "📄 Log Files:"
echo "─────────────────"

# Check log files
if [ -f "$BACKEND_DIR/api.log" ]; then
    LOG_SIZE=$(du -h "$BACKEND_DIR/api.log" | cut -f1)
    echo -e "  API Log:          ${GREEN}✓${NC} $BACKEND_DIR/api.log (${LOG_SIZE})"
else
    echo -e "  API Log:          ${YELLOW}○${NC} Not found"
fi

if [ -f "$BACKEND_DIR/worker.log" ]; then
    LOG_SIZE=$(du -h "$BACKEND_DIR/worker.log" | cut -f1)
    echo -e "  Worker Log:       ${GREEN}✓${NC} $BACKEND_DIR/worker.log (${LOG_SIZE})"
else
    echo -e "  Worker Log:       ${YELLOW}○${NC} Not found"
fi

if [ -f "$BACKEND_DIR/worker_monitor.log" ]; then
    LOG_SIZE=$(du -h "$BACKEND_DIR/worker_monitor.log" | cut -f1)
    echo -e "  Monitor Log:      ${GREEN}✓${NC} $BACKEND_DIR/worker_monitor.log (${LOG_SIZE})"
else
    echo -e "  Monitor Log:      ${YELLOW}○${NC} Not found"
fi

if [ -f "$FRONTEND_DIR/frontend.log" ]; then
    LOG_SIZE=$(du -h "$FRONTEND_DIR/frontend.log" | cut -f1)
    echo -e "  Frontend Log:     ${GREEN}✓${NC} $FRONTEND_DIR/frontend.log (${LOG_SIZE})"
else
    echo -e "  Frontend Log:     ${YELLOW}○${NC} Not found"
fi

echo ""
echo "======================================"

# Determine overall status
ALL_RUNNING=true

[ -f "$API_PID_FILE" ] && API_PID=$(cat "$API_PID_FILE") && check_process "$API_PID" || ALL_RUNNING=false
[ -f "$WORKER_PID_FILE" ] && WORKER_PID=$(cat "$WORKER_PID_FILE") && check_process "$WORKER_PID" || ALL_RUNNING=false
[ -f "$MONITOR_PID_FILE" ] && MONITOR_PID=$(cat "$MONITOR_PID_FILE") && check_process "$MONITOR_PID" || ALL_RUNNING=false
[ -f "$FRONTEND_PID_FILE" ] && FRONTEND_PID=$(cat "$FRONTEND_PID_FILE") && check_process "$FRONTEND_PID" || ALL_RUNNING=false

if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}✅ All services are running${NC}"
else
    echo -e "${YELLOW}⚠️  Some services are not running${NC}"
    echo ""
    echo "Run './scripts/start.sh' to start all services"
fi

echo "======================================"
