# Database Export/Import Tool

Simple CLI tool untuk export dan import data jobs analysis tanpa perlu ZIP files atau video files. Hanya export data analysis (metadata, embeddings, transcripts, dll) ke SQL file.

## Features

- ✅ Export jobs data ke SQL file
- ✅ Include embeddings (vector 1536 dimensions)
- ✅ Include semua analysis dan metadata
- ✅ ON CONFLICT handling (skip existing jobs)
- ✅ Statistics command untuk cek database

## Installation

```bash
cd backend
pip install click  # Already installed
```

## Usage

### 1. Check Database Stats

```bash
cd backend
PYTHONPATH=. python scripts/db_export.py stats
```

Output:
```
📊 Database Statistics:
   Total jobs: 28
   ✅ Done: 25
   ⏳ Pending: 0
   ❌ Failed: 3
```

### 2. Export Jobs to SQL

**Export all done jobs (default):**
```bash
PYTHONPATH=. python scripts/db_export.py export-db
```

**Export with custom output file:**
```bash
PYTHONPATH=. python scripts/db_export.py export-db --output my_export.sql
```

**Export all jobs (including pending/failed):**
```bash
PYTHONPATH=. python scripts/db_export.py export-db --status ""
```

Output:
```
✅ Exported 25 jobs to: export_jobs_20260326_160424.sql
📦 File size: 346.71 KB
```

### 3. Import Jobs from SQL

**Import with conflict handling (recommended):**
```bash
PYTHONPATH=. python scripts/db_export.py import-db export_jobs_20260326_160424.sql
```

**Dry run (preview without executing):**
```bash
PYTHONPATH=. python scripts/db_export.py import-db export_jobs_20260326_160424.sql --dry-run
```

Output:
```
📥 Importing from: export_jobs_20260326_160424.sql
   Processed 10/25 statements...
   Processed 20/25 statements...
✅ Import completed successfully!
```

## Migration Workflow

### Scenario: Moving from Local to Production Server

**On Local Machine:**

1. Export completed jobs:
   ```bash
   cd backend
   PYTHONPATH=. python scripts/db_export.py export-db --status done
   ```

2. Copy SQL file to production server:
   ```bash
   scp export_jobs_*.sql user@192.168.1.45:~/
   ```

**On Production Server:**

3. Import SQL file:
   ```bash
   cd ~/yt-video-analisis/backend
   source venv/bin/activate  # or use docker exec
   PYTHONPATH=. python scripts/db_export.py import-db ~/export_jobs_*.sql
   ```

4. Verify import:
   ```bash
   PYTHONPATH=. python scripts/db_export.py stats
   ```

### Using Docker

**Export from running Docker container:**
```bash
docker exec -it video-analysis-backend bash -c "cd /app && python scripts/db_export.py export-db"
docker cp video-analysis-backend:/app/export_jobs_*.sql ./
```

**Import to Docker container:**
```bash
docker cp export_jobs_*.sql video-analysis-backend:/app/
docker exec -it video-analysis-backend bash -c "cd /app && python scripts/db_export.py import-db /app/export_jobs_*.sql"
```

## What's Exported?

The SQL file includes:
- ✅ Job ID, URL, title, duration
- ✅ YouTube metadata (views, likes, comments, etc)
- ✅ Complete analysis (summary, topics, key_points, sentiment)
- ✅ Vector embeddings (1536 dimensions)
- ✅ Transcripts
- ✅ Frame metadata (paths, timestamps)
- ✅ AI usage costs
- ✅ Created/updated timestamps

## What's NOT Exported?

- ❌ Video files (original downloads)
- ❌ Frame image files (only metadata/paths)
- ❌ Audio files

## Conflict Handling

The export uses `ON CONFLICT (id) DO UPDATE` which means:
- If job_id already exists → Update only specific fields (title, status, progress, analysis)
- If job_id doesn't exist → Insert new record
- No duplicate errors
- Safe to run multiple times

## File Size

Typical file sizes:
- 25 jobs ≈ 350 KB
- 100 jobs ≈ 1.4 MB
- 1000 jobs ≈ 14 MB

Much smaller than ZIP files with videos and frames!

## Tips

**1. Regular Backups:**
```bash
# Daily backup
PYTHONPATH=. python scripts/db_export.py export-db --output backup_$(date +%Y%m%d).sql
```

**2. Filter by Status:**
```bash
# Only export successful jobs
PYTHONPATH=. python scripts/db_export.py export-db --status done

# Export all (including failed)
PYTHONPATH=. python scripts/db_export.py export-db --status ""
```

**3. Test Before Production:**
```bash
# Always test with dry-run first
PYTHONPATH=. python scripts/db_export.py import-db export.sql --dry-run
```

## Troubleshooting

**Error: "No module named 'db'"**
```bash
# Make sure to set PYTHONPATH
PYTHONPATH=. python scripts/db_export.py ...
```

**Error: Connection refused**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check DATABASE_URL in .env
cat ../.env | grep DATABASE_URL
```

**Error: "duplicate key value violates unique constraint"**
```
# This should NOT happen because of ON CONFLICT
# But if it does, check the SQL file format
head -100 export.sql
```

## Advanced Usage

**Export specific job IDs:**

Edit `db_export.py` and add:
```python
@cli.command()
@click.argument('job_ids', nargs=-1)
def export_ids(job_ids):
    """Export specific job IDs."""
    session = SyncSessionLocal()
    jobs = session.query(Job).filter(Job.id.in_(job_ids)).all()
    # ... export logic
```

**Export to JSON instead of SQL:**

Similar structure but output as JSON for other tools:
```python
import json
with open('export.json', 'w') as f:
    json.dump([serialize_job(j) for j in jobs], f, indent=2)
```

## Integration with Frontend

You can add UI buttons to trigger export/import via API endpoints that call these scripts. Example:

```python
# In backend/routers/admin.py
@router.post("/export-db")
async def export_database():
    import subprocess
    result = subprocess.run(
        ["python", "scripts/db_export.py", "export-db"],
        capture_output=True,
        cwd="/app"
    )
    # Return file path or content
```

## See Also

- Original export/import feature: `backend/services/export_import.py` (exports with video files)
- This tool: `backend/scripts/db_export.py` (data only, no video files)
