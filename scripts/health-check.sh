#!/bin/bash

# Health Check Script for Video Analysis System
# Usage: ./scripts/health-check.sh [all|backend|frontend|database|redis|celery]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

# Functions
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

check_backend() {
    echo "Checking Backend API..."
    
    # Health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        print_status 0 "Backend health endpoint: OK"
    else
        print_status 1 "Backend health endpoint: FAILED (HTTP $response)"
        return 1
    fi
    
    # Check API docs
    response=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/docs" 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        print_status 0 "Backend API docs: OK"
    else
        print_status 1 "Backend API docs: FAILED (HTTP $response)"
    fi
}

check_frontend() {
    echo "Checking Frontend..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        print_status 0 "Frontend: OK"
    else
        print_status 1 "Frontend: FAILED (HTTP $response)"
        return 1
    fi
}

check_database() {
    echo "Checking Database..."
    
    if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
        print_status 0 "PostgreSQL: OK"
        
        # Check database exists
        db_exists=$(docker-compose exec -T postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw video_analysis && echo "yes" || echo "no")
        if [ "$db_exists" = "yes" ]; then
            print_status 0 "Database 'video_analysis': EXISTS"
            
            # Check tables
            table_count=$(docker-compose exec -T postgres psql -U postgres -d video_analysis -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)
            print_status 0 "Database tables: $table_count tables found"
        else
            print_status 1 "Database 'video_analysis': NOT FOUND"
        fi
    else
        print_status 1 "PostgreSQL: FAILED"
        return 1
    fi
}

check_redis() {
    echo "Checking Redis..."
    
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        print_status 0 "Redis: OK"
        
        # Check memory usage
        used_memory=$(docker-compose exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        print_status 0 "Redis memory usage: $used_memory"
    else
        print_status 1 "Redis: FAILED"
        return 1
    fi
}

check_celery() {
    echo "Checking Celery Worker..."
    
    # Check if worker is running
    if docker-compose ps celery-worker | grep -q "Up"; then
        print_status 0 "Celery Worker: RUNNING"
        
        # Check worker stats
        worker_stats=$(docker-compose exec -T celery-worker celery -A celery_app inspect active 2>/dev/null || echo "{}")
        print_status 0 "Celery Worker: Connected"
    else
        print_status 1 "Celery Worker: NOT RUNNING"
        return 1
    fi
    
    # Check Celery Beat
    if docker-compose ps celery-beat | grep -q "Up"; then
        print_status 0 "Celery Beat: RUNNING"
    else
        print_status 1 "Celery Beat: NOT RUNNING"
    fi
}

check_all() {
    echo "======================================"
    echo "  Video Analysis System Health Check"
    echo "======================================"
    echo ""
    
    total_checks=0
    failed_checks=0
    
    # Backend
    check_backend || ((failed_checks++))
    ((total_checks++))
    echo ""
    
    # Frontend
    check_frontend || ((failed_checks++))
    ((total_checks++))
    echo ""
    
    # Database
    check_database || ((failed_checks++))
    ((total_checks++))
    echo ""
    
    # Redis
    check_redis || ((failed_checks++))
    ((total_checks++))
    echo ""
    
    # Celery
    check_celery || ((failed_checks++))
    ((total_checks++))
    echo ""
    
    # Summary
    echo "======================================"
    echo "  Summary"
    echo "======================================"
    passed_checks=$((total_checks - failed_checks))
    echo "Passed: ${passed_checks}/${total_checks}"
    
    if [ $failed_checks -eq 0 ]; then
        echo -e "${GREEN}All systems operational!${NC}"
        exit 0
    else
        echo -e "${RED}${failed_checks} check(s) failed${NC}"
        exit 1
    fi
}

# Main
case "${1:-all}" in
    backend)
        check_backend
        ;;
    frontend)
        check_frontend
        ;;
    database|db)
        check_database
        ;;
    redis)
        check_redis
        ;;
    celery|worker)
        check_celery
        ;;
    all|*)
        check_all
        ;;
esac
