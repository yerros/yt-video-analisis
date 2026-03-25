#!/bin/bash

# Video Analysis - Stop All Services
# This script stops all services with deep verification and force kill if needed

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
echo -e "${BLUE}  Video Analysis - Stopping All Services${NC}"
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

# Stop a process gracefully, then force kill if needed
stop_process() {
    local pid=$1
    local name=$2
    local max_wait=${3:-10}
    
    if [ -z "$pid" ]; then
        log_warning "$name: No PID provided"
        return 1
    fi
    
    if ! is_process_running "$pid"; then
        log_info "$name (PID: $pid) is not running"
        return 0
    fi
    
    log_info "Stopping $name (PID: $pid) gracefully..."
    kill -TERM "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if ! is_process_running "$pid"; then
            log_success "$name stopped gracefully"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    
    # Force kill if still running
    if is_process_running "$pid"; then
        log_warning "$name did not stop gracefully, force killing..."
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
        
        if ! is_process_running "$pid"; then
            log_success "$name force killed"
            return 0
        else
            log_error "Failed to stop $name"
            return 1
        fi
    fi
}

# Stop all processes matching a pattern
stop_processes_by_pattern() {
    local pattern=$1
    local name=$2
    
    log_info "Stopping all $name processes..."
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$pids" ]; then
        log_info "No $name processes found"
        return 0
    fi
    
    local count=0
    for pid in $pids; do
        if stop_process "$pid" "$name" 5; then
            count=$((count + 1))
        fi
    done
    
    # Verify all stopped
    sleep 1
    local remaining=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$remaining" ]; then
        log_success "All $name processes stopped ($count stopped)"
        return 0
    else
        log_warning "Some $name processes may still be running"
        # Force kill remaining
        pkill -9 -f "$pattern" 2>/dev/null || true
        sleep 1
        
        remaining=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -z "$remaining" ]; then
            log_success "All remaining $name processes force killed"
            return 0
        else
            log_error "Failed to stop all $name processes"
            return 1
        fi
    fi
}

# Stop process by port
stop_process_by_port() {
    local port=$1
    local name=$2
    
    log_info "Stopping $name on port $port..."
    
    local pids=$(lsof -ti ":$port" 2>/dev/null || true)
    
    if [ -z "$pids" ]; then
        log_info "No process found on port $port"
        return 0
    fi
    
    for pid in $pids; do
        stop_process "$pid" "$name" 5
    done
    
    # Verify port is free
    sleep 1
    if lsof -i ":$port" > /dev/null 2>&1; then
        log_warning "Port $port still in use, force killing..."
        lsof -ti ":$port" | xargs kill -9 2>/dev/null || true
        sleep 1
        
        if ! lsof -i ":$port" > /dev/null 2>&1; then
            log_success "Port $port is now free"
            return 0
        else
            log_error "Failed to free port $port"
            return 1
        fi
    else
        log_success "Port $port is free"
        return 0
    fi
}

# ============================================
# 1. Stop Frontend
# ============================================

echo -e "\n${BLUE}[1/4] Stopping Frontend${NC}"
echo "----------------------------------------"

# Stop by PID file
if [ -f "frontend/frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend/frontend.pid)
    stop_process "$FRONTEND_PID" "Frontend" 10
    rm -f frontend/frontend.pid
fi

# Stop by port
stop_process_by_port 3000 "Frontend"

# Stop by pattern (catch any remaining Next.js processes)
stop_processes_by_pattern "next.*dev" "Next.js dev server"

log_success "Frontend stopped"

# ============================================
# 2. Stop Worker Monitor
# ============================================

echo -e "\n${BLUE}[2/4] Stopping Worker Monitor${NC}"
echo "----------------------------------------"

# Stop by PID file
if [ -f "backend/monitor.pid" ]; then
    MONITOR_PID=$(cat backend/monitor.pid)
    stop_process "$MONITOR_PID" "Worker Monitor" 5
    rm -f backend/monitor.pid
fi

# Stop by pattern
stop_processes_by_pattern "worker_monitor.py" "Worker Monitor"

log_success "Worker Monitor stopped"

# ============================================
# 3. Stop Celery Worker
# ============================================

echo -e "\n${BLUE}[3/4] Stopping Celery Worker${NC}"
echo "----------------------------------------"

# Stop by PID file
if [ -f "backend/worker.pid" ]; then
    WORKER_PID=$(cat backend/worker.pid)
    stop_process "$WORKER_PID" "Celery Worker" 10
    rm -f backend/worker.pid
fi

# Stop by pattern
stop_processes_by_pattern "celery.*worker" "Celery Worker"

# Extra verification - check for any python processes running celery
log_info "Verifying no Celery processes remain..."
if pgrep -f "celery" > /dev/null 2>&1; then
    log_warning "Found remaining Celery processes, force killing..."
    pkill -9 -f "celery" 2>/dev/null || true
    sleep 1
fi

log_success "Celery Worker stopped"

# ============================================
# 4. Stop Backend API
# ============================================

echo -e "\n${BLUE}[4/4] Stopping Backend API${NC}"
echo "----------------------------------------"

# Stop by PID file
if [ -f "backend/api.pid" ]; then
    API_PID=$(cat backend/api.pid)
    stop_process "$API_PID" "Backend API" 10
    rm -f backend/api.pid
fi

# Stop by port
stop_process_by_port 8000 "Backend API"

# Stop by pattern (catch any remaining uvicorn processes)
stop_processes_by_pattern "uvicorn.*main:app" "Uvicorn server"

log_success "Backend API stopped"

# ============================================
# Final Verification
# ============================================

echo -e "\n${BLUE}Final Verification${NC}"
echo "----------------------------------------"

ERRORS=0

# Check port 3000 (Frontend)
if lsof -i :3000 > /dev/null 2>&1; then
    log_error "Port 3000 is still in use"
    lsof -i :3000
    ERRORS=$((ERRORS + 1))
else
    log_success "Port 3000 is free"
fi

# Check port 8000 (Backend)
if lsof -i :8000 > /dev/null 2>&1; then
    log_error "Port 8000 is still in use"
    lsof -i :8000
    ERRORS=$((ERRORS + 1))
else
    log_success "Port 8000 is free"
fi

# Check for Celery processes
if pgrep -f "celery" > /dev/null 2>&1; then
    log_error "Celery processes still running"
    pgrep -f "celery"
    ERRORS=$((ERRORS + 1))
else
    log_success "No Celery processes running"
fi

# Check for Worker Monitor processes
if pgrep -f "worker_monitor" > /dev/null 2>&1; then
    log_error "Worker Monitor still running"
    pgrep -f "worker_monitor"
    ERRORS=$((ERRORS + 1))
else
    log_success "No Worker Monitor processes running"
fi

# Check for Next.js processes
if pgrep -f "next.*dev" > /dev/null 2>&1; then
    log_error "Next.js processes still running"
    pgrep -f "next.*dev"
    ERRORS=$((ERRORS + 1))
else
    log_success "No Next.js processes running"
fi

# Check for Uvicorn processes
if pgrep -f "uvicorn" > /dev/null 2>&1; then
    log_error "Uvicorn processes still running"
    pgrep -f "uvicorn"
    ERRORS=$((ERRORS + 1))
else
    log_success "No Uvicorn processes running"
fi

# ============================================
# Final Status Report
# ============================================

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  All Services Stopped Successfully!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo -e "${GREEN}✓${NC} All processes terminated"
    echo -e "${GREEN}✓${NC} All ports freed"
    echo -e "${GREEN}✓${NC} System is clean"
    echo ""
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}  Stop Completed with Errors!${NC}"
    echo -e "${RED}================================================${NC}"
    echo ""
    echo -e "${RED}✗${NC} $ERRORS verification check(s) failed"
    echo -e "${YELLOW}Some processes may still be running${NC}"
    echo ""
    echo -e "${BLUE}You may need to manually kill remaining processes:${NC}"
    echo "  pkill -9 -f celery"
    echo "  pkill -9 -f uvicorn"
    echo "  pkill -9 -f next"
    echo "  pkill -9 -f worker_monitor"
    echo ""
    exit 1
fi

echo -e "${BLUE}To start services again:${NC}"
echo "  ./scripts/start.sh"
echo ""
