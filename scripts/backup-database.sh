#!/bin/bash

# Database Backup Script for Video Analysis System
# Usage: ./scripts/backup-database.sh [backup-directory]

set -e

# Configuration
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/video_analysis_${TIMESTAMP}.sql"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-video_analysis}"
RETENTION_DAYS=7

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

echo "======================================"
echo "  Database Backup"
echo "======================================"
echo "Database: ${POSTGRES_DB}"
echo "Backup file: ${BACKUP_FILE}"
echo ""

# Check if database is accessible
if ! docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER} >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL is not accessible"
    exit 1
fi

# Create backup
echo "Creating backup..."
docker-compose exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    # Compress backup
    echo "Compressing backup..."
    gzip "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    # Get file size
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    
    echo -e "${GREEN}✓${NC} Backup completed successfully"
    echo "File: ${BACKUP_FILE}"
    echo "Size: ${SIZE}"
    
    # Cleanup old backups
    echo ""
    echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
    find "${BACKUP_DIR}" -name "video_analysis_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    
    remaining=$(find "${BACKUP_DIR}" -name "video_analysis_*.sql.gz" | wc -l | xargs)
    echo "Backups remaining: ${remaining}"
else
    echo "ERROR: Backup failed"
    exit 1
fi
