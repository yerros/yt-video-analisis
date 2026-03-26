#!/bin/bash
set -e

echo "Starting Video Analysis Backend..."

# Check if this is a worker/beat/monitor (skip DB setup)
if [[ "$1" == "celery" ]] || [[ "$1" == "python" && "$2" == *"worker_monitor"* ]]; then
    echo "Detected worker/monitor service, skipping database setup..."
    exec "$@"
    exit 0
fi

# Wait for database to be ready (only for backend)
echo "Waiting for PostgreSQL to be ready..."
python -c "
import time
import psycopg2
from psycopg2 import OperationalError
import os
import re

max_retries = 30
retry_count = 0

# Parse DATABASE_URL if available, otherwise use individual env vars
db_url = os.getenv('DATABASE_URL', '')
if db_url:
    # Parse postgresql+asyncpg://user:pass@host:port/dbname
    match = re.match(r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if match:
        db_user, db_password, db_host, db_port, db_name = match.groups()
    else:
        # Fallback if parsing fails
        db_host = 'postgres'
        db_port = '5432'
        db_name = 'video_analysis'
        db_user = 'postgres'
        db_password = 'postgres'
else:
    db_host = os.getenv('POSTGRES_HOST', 'postgres')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'video_analysis')
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        conn.close()
        print('PostgreSQL is ready!')
        break
    except OperationalError:
        retry_count += 1
        print(f'PostgreSQL not ready yet, retrying... ({retry_count}/{max_retries})')
        time.sleep(2)

if retry_count >= max_retries:
    print('Failed to connect to PostgreSQL after maximum retries')
    exit(1)
"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Check if we should auto-import data
IMPORT_FLAG_FILE="/tmp/.db_imported"
SQL_IMPORT_FILE="/app/export_jobs_*.sql"

# Find the SQL file (expand glob)
SQL_FILE=$(ls $SQL_IMPORT_FILE 2>/dev/null | head -n 1)

if [ -f "$IMPORT_FLAG_FILE" ]; then
    echo "Database already imported previously (flag file exists)"
elif [ -n "$SQL_FILE" ] && [ -f "$SQL_FILE" ]; then
    echo "Found SQL import file: $SQL_FILE"
    echo "Checking if database has existing jobs..."
    
    # Check if database already has data
    JOB_COUNT=$(python -c "
import os
import sys
sys.path.insert(0, '/app')
from sqlalchemy import create_engine, text

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM jobs'))
    count = result.scalar()
    print(count)
" 2>/dev/null || echo "0")

    echo "Current job count in database: $JOB_COUNT"

    if [ "$JOB_COUNT" -eq "0" ]; then
        echo "Database is empty, importing data from $SQL_FILE..."
        PYTHONPATH=/app python /app/scripts/db_export.py import-db "$SQL_FILE"
        
        if [ $? -eq 0 ]; then
            echo "Data import completed successfully!"
            touch "$IMPORT_FLAG_FILE"
            echo "Created flag file to prevent re-import"
        else
            echo "WARNING: Data import failed, but continuing startup..."
        fi
    else
        echo "Database already has $JOB_COUNT jobs, skipping import"
        touch "$IMPORT_FLAG_FILE"
    fi
else
    echo "No SQL import file found, skipping auto-import"
fi

# Show final database statistics
echo "Current database statistics:"
PYTHONPATH=/app python /app/scripts/db_export.py stats || echo "Could not retrieve stats"

# Start the application
echo "Starting application..."
exec "$@"
