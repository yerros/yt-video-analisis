#!/bin/bash

# Video Analysis AI - Restart Script
# Script untuk kill semua proses dan restart dengan aman

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Log files
BACKEND_LOG="$PROJECT_ROOT/backend.log"
WORKER_LOG="$PROJECT_ROOT/worker.log"
FRONTEND_LOG="$PROJECT_ROOT/frontend.log"

# Function to print colored output
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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Function to check if a port is in use
is_port_in_use() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    log_step "Killing processes on port $port..."
    
    local pids=$(lsof -t -i :$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
        log_success "Killed processes on port $port"
    else
        log_info "No processes found on port $port"
    fi
}

# Function to kill all development processes
kill_all_processes() {
    log_step "Stopping all development processes..."
    
    # Kill by port
    kill_port 8000  # Backend
    kill_port 3000  # Frontend
    
    # Kill by process name
    log_step "Killing processes by name..."
    pkill -9 -f "uvicorn.*backend.main:app" 2>/dev/null || true
    pkill -9 -f "uvicorn.*main:app" 2>/dev/null || true
    pkill -9 -f "celery.*backend.celery_app" 2>/dev/null || true
    pkill -9 -f "celery.*celery_app" 2>/dev/null || true
    pkill -9 -f "next dev" 2>/dev/null || true
    pkill -9 -f "pnpm dev" 2>/dev/null || true
    
    sleep 2
    
    # Verify ports are free
    if is_port_in_use 8000; then
        log_warning "Port 8000 still in use, forcing kill..."
        kill_port 8000
    fi
    
    if is_port_in_use 3000; then
        log_warning "Port 3000 still in use, forcing kill..."
        kill_port 3000
    fi
    
    log_success "All development processes stopped!"
}

# Function to check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local has_error=0
    
    # Check if venv exists
    if [ ! -d "backend/venv" ]; then
        log_error "Virtual environment not found. Run 'make setup' first."
        has_error=1
    fi
    
    # Check if Redis is installed
    if ! command -v redis-server &> /dev/null; then
        log_error "Redis not found. Install with: brew install redis"
        has_error=1
    fi
    
    # Check if PostgreSQL is running
    if ! pg_isready &> /dev/null; then
        log_warning "PostgreSQL is not running. Attempting to start..."
        brew services start postgresql@16 || true
        sleep 2
        if ! pg_isready &> /dev/null; then
            log_error "Failed to start PostgreSQL"
            has_error=1
        else
            log_success "PostgreSQL started"
        fi
    fi
    
    # Check if pnpm is installed
    if ! command -v pnpm &> /dev/null; then
        log_error "pnpm not found. Install with: npm install -g pnpm"
        has_error=1
    fi
    
    if [ $has_error -eq 1 ]; then
        log_error "Prerequisites check failed!"
        exit 1
    fi
    
    log_success "Prerequisites check passed!"
}

# Function to start Redis
start_redis() {
    log_step "Starting Redis server..."
    
    # Check if Redis is already running
    if redis-cli ping &> /dev/null; then
        log_success "Redis is already running"
        return 0
    fi
    
    redis-server --daemonize yes --port 6379 &> /dev/null
    sleep 2
    
    if redis-cli ping &> /dev/null; then
        log_success "Redis started successfully"
    else
        log_error "Failed to start Redis"
        return 1
    fi
}

# Function to start backend
start_backend() {
    log_step "Starting FastAPI backend..."
    
    # Clear old log
    > "$BACKEND_LOG"
    
    cd "$PROJECT_ROOT/backend"
    venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
    local pid=$!
    cd "$PROJECT_ROOT"
    
    # Wait for backend to start
    local max_attempts=10
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        sleep 1
        if is_port_in_use 8000; then
            # Test if backend is responding
            if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
                log_success "Backend started successfully (PID: $pid) on http://localhost:8000"
                return 0
            fi
        fi
        attempt=$((attempt + 1))
    done
    
    log_error "Failed to start backend. Check $BACKEND_LOG for details:"
    tail -20 "$BACKEND_LOG"
    return 1
}

# Function to start Celery worker
start_worker() {
    log_step "Starting Celery worker..."
    
    # Clear old log
    > "$WORKER_LOG"
    
    cd "$PROJECT_ROOT/backend"
    venv/bin/celery -A celery_app worker --loglevel=info > "$WORKER_LOG" 2>&1 &
    local pid=$!
    cd "$PROJECT_ROOT"
    
    # Wait for worker to be ready
    local max_attempts=10
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        sleep 1
        if grep -q "ready" "$WORKER_LOG" 2>/dev/null; then
            log_success "Celery worker started successfully (PID: $pid)"
            return 0
        fi
        attempt=$((attempt + 1))
    done
    
    log_error "Failed to start Celery worker. Check $WORKER_LOG for details:"
    tail -20 "$WORKER_LOG"
    return 1
}

# Function to start frontend
start_frontend() {
    log_step "Starting Next.js frontend..."
    
    # Clear old log
    > "$FRONTEND_LOG"
    
    cd "$PROJECT_ROOT/frontend"
    pnpm dev > "$FRONTEND_LOG" 2>&1 &
    local pid=$!
    cd "$PROJECT_ROOT"
    
    # Wait for frontend to start
    local max_attempts=15
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        sleep 1
        if is_port_in_use 3000; then
            log_success "Frontend started successfully (PID: $pid) on http://localhost:3000"
            return 0
        fi
        attempt=$((attempt + 1))
    done
    
    log_error "Failed to start frontend. Check $FRONTEND_LOG for details:"
    tail -20 "$FRONTEND_LOG"
    return 1
}

# Function to verify all services are running
verify_services() {
    log_step "Verifying all services..."
    echo ""
    
    local all_ok=1
    
    # Check Backend
    if is_port_in_use 8000 && curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Backend:  http://localhost:8000 (Running)"
    else
        echo -e "  ${RED}✗${NC} Backend:  http://localhost:8000 (Failed)"
        all_ok=0
    fi
    
    # Check Frontend
    if is_port_in_use 3000; then
        echo -e "  ${GREEN}✓${NC} Frontend: http://localhost:3000 (Running)"
    else
        echo -e "  ${RED}✗${NC} Frontend: http://localhost:3000 (Failed)"
        all_ok=0
    fi
    
    # Check Celery Worker
    if pgrep -f "celery.*worker" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Celery Worker (Running)"
    else
        echo -e "  ${RED}✗${NC} Celery Worker (Failed)"
        all_ok=0
    fi
    
    # Check Redis
    if redis-cli ping &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Redis (Running)"
    else
        echo -e "  ${RED}✗${NC} Redis (Failed)"
        all_ok=0
    fi
    
    # Check PostgreSQL
    if pg_isready &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL (Running)"
    else
        echo -e "  ${RED}✗${NC} PostgreSQL (Failed)"
        all_ok=0
    fi
    
    echo ""
    
    if [ $all_ok -eq 1 ]; then
        log_success "All services are running correctly!"
        return 0
    else
        log_error "Some services failed to start. Check the logs above."
        return 1
    fi
}

# Main function
main() {
    echo ""
    echo "================================================"
    echo "  Video Analysis AI - Restart Script"
    echo "================================================"
    echo ""
    
    # Step 1: Kill all existing processes
    kill_all_processes
    echo ""
    
    # Step 2: Check prerequisites
    check_prerequisites
    echo ""
    
    # Step 3: Start all services
    log_info "Starting all services..."
    echo ""
    
    if ! start_redis; then
        log_error "Failed to start Redis. Aborting."
        exit 1
    fi
    
    if ! start_backend; then
        log_error "Failed to start backend. Aborting."
        exit 1
    fi
    
    if ! start_worker; then
        log_error "Failed to start Celery worker. Aborting."
        exit 1
    fi
    
    if ! start_frontend; then
        log_error "Failed to start frontend. Aborting."
        exit 1
    fi
    
    echo ""
    echo "================================================"
    echo "  🚀 All Services Started Successfully!"
    echo "================================================"
    echo ""
    
    # Step 4: Verify all services
    verify_services
    
    echo ""
    echo "================================================"
    echo "  Service URLs:"
    echo "================================================"
    echo "  Frontend:   http://localhost:3000"
    echo "  Backend:    http://localhost:8000"
    echo "  API Docs:   http://localhost:8000/docs"
    echo ""
    echo "================================================"
    echo "  Log Files:"
    echo "================================================"
    echo "  Backend:    $BACKEND_LOG"
    echo "  Worker:     $WORKER_LOG"
    echo "  Frontend:   $FRONTEND_LOG"
    echo ""
    echo "================================================"
    echo "  To stop services: ./stop.sh or make stop"
    echo "================================================"
    echo ""
}

# Run main function
main
