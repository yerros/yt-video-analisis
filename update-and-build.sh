#!/bin/bash
# Script untuk update dan build Docker images di server
# Run dengan: bash update-and-build.sh

set -e  # Exit on error

echo "======================================="
echo "  Update & Build Docker Images"
echo "======================================="
echo ""

echo "📥 Step 1: Pull latest changes from git..."
git pull origin main
echo "✓ Git pull completed"
echo ""

echo "📋 Step 2: Verify required files exist..."
MISSING_FILES=0

if [ ! -f "backend/requirements.txt" ]; then
    echo "✗ backend/requirements.txt NOT FOUND!"
    MISSING_FILES=1
else
    echo "✓ backend/requirements.txt found"
    PYDANTIC_VERSION=$(grep "^pydantic==" backend/requirements.txt)
    echo "  → $PYDANTIC_VERSION"
fi

if [ ! -f "backend/.dockerignore" ]; then
    echo "✗ backend/.dockerignore NOT FOUND!"
    MISSING_FILES=1
else
    echo "✓ backend/.dockerignore found"
fi

if [ ! -f "frontend/.dockerignore" ]; then
    echo "✗ frontend/.dockerignore NOT FOUND!"
    MISSING_FILES=1
else
    echo "✓ frontend/.dockerignore found"
fi

if [ ! -f "frontend/lib/api.ts" ]; then
    echo "✗ frontend/lib/api.ts NOT FOUND!"
    MISSING_FILES=1
else
    echo "✓ frontend/lib/api.ts found"
fi

if [ ! -f "frontend/lib/types.ts" ]; then
    echo "✗ frontend/lib/types.ts NOT FOUND!"
    MISSING_FILES=1
else
    echo "✓ frontend/lib/types.ts found"
fi

if [ ! -f "frontend/tsconfig.json" ]; then
    echo "✗ frontend/tsconfig.json NOT FOUND!"
    MISSING_FILES=1
else
    echo "✓ frontend/tsconfig.json found"
fi

if [ $MISSING_FILES -eq 1 ]; then
    echo ""
    echo "❌ ERROR: Some required files are missing!"
    echo "Please check the files above and ensure they exist."
    exit 1
fi

echo ""
echo "🧹 Step 3: Clean Docker cache..."
docker-compose down
docker system prune -f
echo "✓ Docker cache cleaned"
echo ""

echo "🔨 Step 4: Build Docker images..."
echo ""
echo "Building backend..."
docker-compose build --no-cache backend
echo "✓ Backend built successfully"
echo ""

echo "Building frontend..."
docker-compose build --no-cache frontend
echo "✓ Frontend built successfully"
echo ""

echo "======================================="
echo "✅ All images built successfully!"
echo "======================================="
echo ""
echo "📊 Docker images:"
docker images | grep -E "REPOSITORY|video-analysis|yt-video-analis"
echo ""
echo "🚀 Ready to deploy! Run:"
echo "   docker-compose up -d"
echo ""
