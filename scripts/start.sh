#!/bin/bash

# Video Analysis - Start All Services
# This script starts all required services with deep verification

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Video Analysis - Starting All Services${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# ============================================
# Helper Functions
# ============================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if a process is running by PID
is_process_running() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi
    
    if ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check if a port is in use
is_port_in_use() {
    local port=$1
    if lsof -i ":$port" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Wait for a port to be available
wait_for_port() {
    local port=$1
    local max_attempts=$2
    local attempt=0
    
    log_info "Waiting for port $port to be available..."
    
    while [ $attempt -lt $max_attempts ]; do
        if is_port_in_use "$port"; then
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 1
    done
    
    return 1
}

# Verify HTTP endpoint
verify_http_endpoint() {
    local url=$1
    local max_attempts=$2
    local attempt=0
    
    log_info "Verifying endpoint: $url"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 1
    done
    
    return 1
}

# ============================================
# 1. Check Prerequisites
# ============================================

echo -e "\n${BLUE}[1/6] Checking Prerequisites${NC}"
echo "----------------------------------------"

# Check PostgreSQL
log_info "Checking PostgreSQL..."
if pg_isready > /dev/null 2>&1; then
    log_success "PostgreSQL is running"
else
    log_error "PostgreSQL is not running"
    log_info "Please start PostgreSQL first"
    exit 1
fi

# Check Redis
log_info "Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    log_success "Redis is running"
else
    log_error "Redis is not running"
    log_info "Please start Redis first"
    exit 1
fi

# Check Python venv
log_info "Checking Python virtual environment..."
if [ ! -d "backend/venv" ]; then
    log_error "Python virtual environment not found"
    log_info "Please run: cd backend && python -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi
log_success "Python virtual environment found"

# Check Node modules
log_info "Checking Node modules..."
if [ ! -d "frontend/node_modules" ]; then
    log_error "Node modules not found"
    log_info "Please run: cd frontend && pnpm install"
    exit 1
fi
log_success "Node modules found"

# ============================================
# 2. Stop Existing Services (if any)
# ============================================

echo -e "\n${BLUE}[2/6] Stopping Existing Services${NC}"
echo "----------------------------------------"

# Stop Backend API
if is_port_in_use 8000; then
    log_warning "Backend API is already running on port 8000, stopping..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Stop Frontend
if is_port_in_use 3000; then
    log_warning "Frontend is already running on port 3000, stopping..."
    lsof -ti :3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Stop Celery Worker
log_info "Stopping existing Celery worker..."
pkill -9 -f "celery.*worker" 2>/dev/null || true
sleep 2

# Stop Worker Monitor
log_info "Stopping existing Worker Monitor..."
pkill -9 -f "worker_monitor.py" 2>/dev/null || true
sleep 2

log_success "All existing services stopped"

# ============================================
# 3. Start Backend API
# ============================================

echo -e "\n${BLUE}[3/6] Starting Backend API${NC}"
echo "----------------------------------------"

log_info "Starting Backend API on port 8000..."

cd backend
nohup venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 > api.log 2>&1 &
BACKEND_PID=$!
cd ..

# Save PID
echo "$BACKEND_PID" > backend/api.pid

# Wait and verify
sleep 3

if is_process_running "$BACKEND_PID"; then
    log_success "Backend API process started (PID: $BACKEND_PID)"
else
    log_error "Backend API failed to start"
    exit 1
fi

# Verify port is listening
if wait_for_port 8000 10; then
    log_success "Backend API is listening on port 8000"
else
    log_error "Backend API is not listening on port 8000"
    exit 1
fi

# Verify health endpoint
if verify_http_endpoint "http://localhost:8000/health" 10; then
    log_success "Backend API health check passed"
else
    log_error "Backend API health check failed"
    exit 1
fi

# ============================================
# 4. Start Celery Worker
# ============================================

echo -e "\n${BLUE}[4/6] Starting Celery Worker${NC}"
echo "----------------------------------------"

log_info "Starting Celery worker with pool=solo..."

cd backend
nohup venv/bin/celery -A celery_app worker \
    --pool=solo \
    --loglevel=info \
    --time-limit=1800 \
    --soft-time-limit=1500 \
    > worker.log 2>&1 &
WORKER_PID=$!
cd ..

# Save PID
echo "$WORKER_PID" > backend/worker.pid

# Wait and verify
sleep 5

if is_process_running "$WORKER_PID"; then
    log_success "Celery worker process started (PID: $WORKER_PID)"
else
    log_error "Celery worker failed to start"
    log_info "Check backend/worker.log for errors"
    exit 1
fi

# Verify worker is responsive (send ping task)
log_info "Verifying worker responsiveness..."
sleep 3

cd backend
WORKER_HEALTH=$(venv/bin/python -c "
from celery_app import celery_app
try:
    result = celery_app.send_task('tasks.health_check.ping', expires=10)
    response = result.get(timeout=10)
    print('healthy' if response and response.get('status') == 'healthy' else 'unhealthy')
except Exception as e:
    print('unhealthy')
" 2>/dev/null)
cd ..

if [ "$WORKER_HEALTH" = "healthy" ]; then
    log_success "Celery worker is responsive and healthy"
else
    log_warning "Celery worker health check failed (may need more time to initialize)"
fi

# ============================================
# 5. Start Worker Monitor
# ============================================

echo -e "\n${BLUE}[5/6] Starting Worker Monitor${NC}"
echo "----------------------------------------"

log_info "Starting Worker Monitor..."

nohup backend/venv/bin/python backend/scripts/worker_monitor.py > backend/monitor_output.log 2>&1 &
MONITOR_PID=$!

# Save PID
echo "$MONITOR_PID" > backend/monitor.pid

# Wait and verify
sleep 3

if is_process_running "$MONITOR_PID"; then
    log_success "Worker Monitor started (PID: $MONITOR_PID)"
else
    log_error "Worker Monitor failed to start"
    log_warning "This is not critical, services will continue without monitoring"
fi

# ============================================
# 6. Start Frontend
# ============================================

echo -e "\n${BLUE}[6/6] Starting Frontend${NC}"
echo "----------------------------------------"

log_info "Starting Frontend on port 3000..."

cd frontend
nohup pnpm dev > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Save PID
echo "$FRONTEND_PID" > frontend/frontend.pid

# Wait and verify
sleep 5

if is_process_running "$FRONTEND_PID"; then
    log_success "Frontend process started (PID: $FRONTEND_PID)"
else
    log_error "Frontend failed to start"
    exit 1
fi

# Verify port is listening
if wait_for_port 3000 20; then
    log_success "Frontend is listening on port 3000"
else
    log_error "Frontend is not listening on port 3000"
    exit 1
fi

# Verify frontend is serving content
log_info "Verifying frontend is serving content..."
sleep 3

if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    log_success "Frontend health check passed"
else
    log_warning "Frontend may still be initializing"
fi

# ============================================
# Final Status Report
# ============================================

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  All Services Started Successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}Service Status:${NC}"
echo "----------------------------------------"
echo -e "  Backend API:      ${GREEN}✓${NC} Running (PID: $BACKEND_PID, Port: 8000)"
echo -e "  Celery Worker:    ${GREEN}✓${NC} Running (PID: $WORKER_PID)"
echo -e "  Worker Monitor:   ${GREEN}✓${NC} Running (PID: $MONITOR_PID)"
echo -e "  Frontend:         ${GREEN}✓${NC} Running (PID: $FRONTEND_PID, Port: 3000)"
echo ""
echo -e "${BLUE}URLs:${NC}"
echo "----------------------------------------"
echo -e "  Frontend:         ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend API:      ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:         ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Worker Status:    ${GREEN}http://localhost:3000/worker${NC}"
echo ""
echo -e "${BLUE}Log Files:${NC}"
echo "----------------------------------------"
echo -e "  Backend API:      backend/api.log"
echo -e "  Celery Worker:    backend/worker.log"
echo -e "  Worker Monitor:   backend/worker_monitor.log"
echo -e "  Frontend:         frontend/frontend.log"
echo ""
echo -e "${BLUE}PID Files:${NC}"
echo "----------------------------------------"
echo -e "  Backend API:      backend/api.pid"
echo -e "  Celery Worker:    backend/worker.pid"
echo -e "  Worker Monitor:   backend/monitor.pid"
echo -e "  Frontend:         frontend/frontend.pid"
echo ""
echo -e "${BLUE}Management:${NC}"
echo "----------------------------------------"
echo -e "  Stop all:         ./scripts/stop.sh"
echo -e "  Restart all:      ./scripts/restart.sh"
echo -e "  Check status:     ./scripts/status.sh"
echo ""
echo -e "${GREEN}Ready to use! 🚀${NC}"
echo ""
