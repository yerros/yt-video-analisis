#!/bin/bash

# Video Analysis AI - Development Server Runner
# This script starts all services and manages them together

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# PID file to track running processes
PID_FILE="$PROJECT_ROOT/.dev-pids"

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

# Function to check if a process is running
is_running() {
    local pid=$1
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to stop all services
stop_services() {
    log_info "Stopping all services..."
    
    if [ -f "$PID_FILE" ]; then
        while IFS= read -r pid; do
            if is_running "$pid"; then
                log_info "Stopping process $pid"
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    
    # Force kill any remaining processes
    pkill -f "uvicorn backend.main:app" 2>/dev/null || true
    pkill -f "celery.*backend.celery_app" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    
    log_success "All services stopped!"
}

# Trap Ctrl+C and cleanup
trap 'echo ""; log_info "Received shutdown signal..."; stop_services; exit 0' INT TERM

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if venv exists
    if [ ! -d "backend/venv" ]; then
        log_error "Virtual environment not found. Run 'make setup' first."
        exit 1
    fi
    
    # Check if Redis is installed
    if ! command -v redis-server &> /dev/null; then
        log_error "Redis not found. Install with: brew install redis"
        exit 1
    fi
    
    # Check if PostgreSQL is running
    if ! pg_isready &> /dev/null; then
        log_warning "PostgreSQL is not running. Starting..."
        brew services start postgresql@16 || true
    fi
    
    log_success "Prerequisites check passed!"
}

# Function to start Redis
start_redis() {
    log_info "Starting Redis server..."
    
    # Check if Redis is already running
    if redis-cli ping &> /dev/null; then
        log_success "Redis is already running"
        return 0
    fi
    
    redis-server --daemonize yes --port 6379 &> /dev/null
    sleep 1
    
    if redis-cli ping &> /dev/null; then
        log_success "Redis started successfully"
    else
        log_error "Failed to start Redis"
        exit 1
    fi
}

# Function to start backend
start_backend() {
    log_info "Starting FastAPI backend..."
    
    backend/venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 \
        > /tmp/video-analysis-backend.log 2>&1 &
    local pid=$!
    echo "$pid" >> "$PID_FILE"
    
    sleep 5
    
    if is_running "$pid"; then
        log_success "Backend started successfully (PID: $pid)"
    else
        log_error "Failed to start backend. Check /tmp/video-analysis-backend.log"
        cat /tmp/video-analysis-backend.log
        exit 1
    fi
}

# Function to start Celery worker
start_worker() {
    log_info "Starting Celery worker..."
    
    backend/venv/bin/celery -A backend.celery_app worker --loglevel=info \
        > /tmp/video-analysis-worker.log 2>&1 &
    local pid=$!
    echo "$pid" >> "$PID_FILE"
    
    sleep 3
    
    if is_running "$pid"; then
        log_success "Celery worker started successfully (PID: $pid)"
    else
        log_error "Failed to start Celery worker. Check /tmp/video-analysis-worker.log"
        cat /tmp/video-analysis-worker.log
        exit 1
    fi
}

# Function to start frontend
start_frontend() {
    log_info "Starting Next.js frontend..."
    
    cd frontend
    pnpm dev > /tmp/video-analysis-frontend.log 2>&1 &
    local pid=$!
    cd ..
    echo "$pid" >> "$PID_FILE"
    
    sleep 5
    
    if is_running "$pid"; then
        log_success "Frontend started successfully (PID: $pid)"
    else
        log_error "Failed to start frontend. Check /tmp/video-analysis-frontend.log"
        exit 1
    fi
}

# Main function
main() {
    echo ""
    echo "================================================"
    echo "  Video Analysis AI - Development Server"
    echo "================================================"
    echo ""
    
    # Clean up any existing PID file
    rm -f "$PID_FILE"
    
    # Check prerequisites
    check_prerequisites
    
    # Start services
    start_redis
    start_backend
    start_worker
    start_frontend
    
    echo ""
    echo "================================================"
    echo "  🚀 All services started successfully!"
    echo "================================================"
    echo ""
    echo "  Frontend:   http://localhost:3000"
    echo "  Backend:    http://localhost:8000"
    echo "  API Docs:   http://localhost:8000/docs"
    echo ""
    echo "  Logs:"
    echo "    Backend:  /tmp/video-analysis-backend.log"
    echo "    Worker:   /tmp/video-analysis-worker.log"
    echo "    Frontend: /tmp/video-analysis-frontend.log"
    echo ""
    echo "================================================"
    echo "  Press Ctrl+C to stop all services"
    echo "================================================"
    echo ""
    
    # Wait for all processes
    while true; do
        sleep 1
        
        # Check if any process died
        while IFS= read -r pid; do
            if ! is_running "$pid"; then
                log_error "A service died unexpectedly (PID: $pid)"
                stop_services
                exit 1
            fi
        done < "$PID_FILE"
    done
}

# Run main function
main
