#!/bin/bash

# Video Analysis AI - Stop Script
# Script untuk stop semua proses development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
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
    local service_name=$2
    
    if is_port_in_use $port; then
        log_info "Stopping $service_name on port $port..."
        local pids=$(lsof -t -i :$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
            sleep 1
            
            if is_port_in_use $port; then
                log_warning "$service_name still running, forcing kill..."
                echo "$pids" | xargs kill -9 2>/dev/null || true
                sleep 1
            fi
            
            log_success "$service_name stopped"
        fi
    else
        log_info "$service_name not running on port $port"
    fi
}

# Main function
main() {
    echo ""
    echo "================================================"
    echo "  Video Analysis AI - Stop All Services"
    echo "================================================"
    echo ""
    
    log_info "Stopping all development processes..."
    echo ""
    
    # Kill by port
    kill_port 8000 "Backend"
    kill_port 3000 "Frontend"
    
    # Kill by process name
    log_info "Stopping Celery workers..."
    pkill -9 -f "celery.*celery_app" 2>/dev/null && log_success "Celery workers stopped" || log_info "No Celery workers running"
    pkill -9 -f "celery.*worker" 2>/dev/null || true
    
    log_info "Stopping uvicorn processes..."
    pkill -9 -f "uvicorn.*main:app" 2>/dev/null && log_success "Uvicorn stopped" || log_info "No uvicorn processes running"
    pkill -9 -f "uvicorn" 2>/dev/null || true
    
    log_info "Stopping Next.js processes..."
    pkill -9 -f "next dev" 2>/dev/null && log_success "Next.js stopped" || log_info "No Next.js processes running"
    pkill -9 -f "pnpm dev" 2>/dev/null || true
    pkill -9 -f "node.*next" 2>/dev/null || true
    
    sleep 2
    
    # Final verification
    echo ""
    log_info "Verifying services are stopped..."
    echo ""
    
    local all_stopped=1
    
    if is_port_in_use 8000; then
        echo -e "  ${RED}✗${NC} Backend still running on port 8000"
        all_stopped=0
    else
        echo -e "  ${GREEN}✓${NC} Backend stopped"
    fi
    
    if is_port_in_use 3000; then
        echo -e "  ${RED}✗${NC} Frontend still running on port 3000"
        all_stopped=0
    else
        echo -e "  ${GREEN}✓${NC} Frontend stopped"
    fi
    
    if pgrep -f "celery.*worker" > /dev/null 2>&1; then
        echo -e "  ${RED}✗${NC} Celery worker still running"
        all_stopped=0
    else
        echo -e "  ${GREEN}✓${NC} Celery worker stopped"
    fi
    
    echo ""
    
    if [ $all_stopped -eq 1 ]; then
        log_success "All services stopped successfully!"
    else
        log_warning "Some services are still running. You may need to stop them manually."
    fi
    
    echo ""
    echo "================================================"
    echo "  To start services: ./restart.sh or make dev-all"
    echo "================================================"
    echo ""
}

# Run main function
main
