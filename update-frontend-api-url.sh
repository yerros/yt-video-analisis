#!/bin/bash

# ============================================
# Update Frontend API URL and Rebuild
# ============================================
# This script updates the NEXT_PUBLIC_API_URL
# and rebuilds the frontend Docker image
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Update Frontend API URL"
echo "========================================"
echo ""

# Check if API URL is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: API URL is required${NC}"
    echo ""
    echo "Usage: bash update-frontend-api-url.sh <API_URL>"
    echo ""
    echo "Examples:"
    echo "  bash update-frontend-api-url.sh http://192.168.1.45:1945"
    echo "  bash update-frontend-api-url.sh https://yourdomain.com"
    echo ""
    exit 1
fi

API_URL="$1"

echo -e "${YELLOW}→ New API URL: ${API_URL}${NC}"
echo ""

# Update .env file
if [ -f .env ]; then
    # Check if NEXT_PUBLIC_API_URL exists in .env
    if grep -q "NEXT_PUBLIC_API_URL=" .env; then
        # Update existing line
        sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=${API_URL}|" .env
        echo -e "${GREEN}✓ Updated NEXT_PUBLIC_API_URL in .env${NC}"
    else
        # Add new line
        echo "NEXT_PUBLIC_API_URL=${API_URL}" >> .env
        echo -e "${GREEN}✓ Added NEXT_PUBLIC_API_URL to .env${NC}"
    fi
    rm -f .env.bak
else
    echo -e "${YELLOW}⚠ Warning: .env file not found, creating new one${NC}"
    echo "NEXT_PUBLIC_API_URL=${API_URL}" > .env
fi

echo ""
echo -e "${YELLOW}→ Rebuilding frontend Docker image...${NC}"
echo ""

# Rebuild frontend with new API URL
docker compose build --no-cache \
    --build-arg NEXT_PUBLIC_API_URL="${API_URL}" \
    frontend

echo ""
echo -e "${GREEN}✓ Frontend image rebuilt successfully${NC}"
echo ""
echo -e "${YELLOW}→ Restarting frontend container...${NC}"
echo ""

# Restart frontend
docker compose up -d frontend

echo ""
echo "========================================"
echo -e "${GREEN}✅ Frontend updated successfully!${NC}"
echo "========================================"
echo ""
echo "Frontend URL: http://$(hostname -I | awk '{print $1}'):1946"
echo "Backend API URL: ${API_URL}"
echo ""
echo "Test the connection:"
echo "  curl ${API_URL}/health"
echo ""
