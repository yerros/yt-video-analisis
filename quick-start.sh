#!/bin/bash

# Quick start script for Docker deployment
# Usage: ./quick-start.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "======================================"
echo "  Video Analysis System"
echo "  Docker Quick Start"
echo "======================================"
echo -e "${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Creating .env from .env.production template..."
    cp .env.production .env
    
    echo ""
    echo -e "${YELLOW}IMPORTANT: Please edit .env file and add your API keys:${NC}"
    echo "  - OPENAI_API_KEY"
    echo "  - YOUTUBE_API_KEY"
    echo "  - POSTGRES_PASSWORD"
    echo ""
    echo "Press Enter after you've updated the .env file..."
    read
fi

# Verify required environment variables
source .env
missing_vars=()

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    missing_vars+=("OPENAI_API_KEY")
fi

if [ -z "$YOUTUBE_API_KEY" ] || [ "$YOUTUBE_API_KEY" = "your-youtube-api-key-here" ]; then
    missing_vars+=("YOUTUBE_API_KEY")
fi

if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_password_here" ]; then
    missing_vars+=("POSTGRES_PASSWORD")
fi

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo -e "${RED}ERROR: Missing required environment variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please update .env file with proper values"
    exit 1
fi

echo -e "${GREEN}✓${NC} Environment variables configured"

# Stop existing containers
echo ""
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Pull latest images
echo ""
echo "Pulling base images..."
docker-compose pull postgres redis 2>/dev/null || true

# Build containers
echo ""
echo "Building containers..."
docker-compose build --no-cache

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to start..."
sleep 10

# Check services
echo ""
echo "Checking services..."

# Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend API is running"
else
    echo -e "${YELLOW}⚠${NC} Backend API is starting (may take a few more seconds)"
fi

# Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend is running"
else
    echo -e "${YELLOW}⚠${NC} Frontend is starting (may take a few more seconds)"
fi

# Database
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL is running"
else
    echo -e "${RED}✗${NC} PostgreSQL is not responding"
fi

# Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is running"
else
    echo -e "${RED}✗${NC} Redis is not responding"
fi

echo ""
echo -e "${GREEN}======================================"
echo "  Deployment Complete!"
echo "======================================${NC}"
echo ""
echo "Access your application:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  View logs:       docker-compose logs -f"
echo "  Stop services:   docker-compose down"
echo "  Restart:         docker-compose restart"
echo "  Health check:    ./scripts/health-check.sh"
echo ""
echo "For production deployment with nginx:"
echo "  docker-compose --profile production up -d"
echo ""
echo "Read full documentation: ./DEPLOYMENT.md"
echo ""
