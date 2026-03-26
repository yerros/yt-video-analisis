# Export/Import Feature Documentation

## Overview

Fitur Export/Import memungkinkan Anda untuk memindahkan hasil analisis video yang sudah diproses dari satu server ke server lain, atau sebagai backup data.

## Use Cases

1. **Backup Data** - Export job untuk backup sebelum maintenance atau upgrade
2. **Server Migration** - Pindah dari development ke staging/production
3. **Data Sharing** - Share hasil analisis dengan team members
4. **Disaster Recovery** - Restore data dari backup jika terjadi kehilangan data

## How It Works

### Export Process

Export akan membuat file ZIP yang berisi:
- `manifest.json` - Version info dan metadata export
- `metadata.json` - Complete database record (job, embeddings, analysis)
- `video.mp4` - File video original
- `frames/` - Semua frames yang sudah diekstrak

### Import Process

Import akan:
1. Extract file ZIP
2. Validasi manifest dan data integrity
3. Restore database records
4. Copy video dan frames ke storage
5. Skip jika job_id sudah ada (default behavior)

## API Endpoints

### 1. List Exportable Jobs

```bash
GET /api/export/jobs
```

Response:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Video Title",
    "duration": 180,
    "frames_count": 30,
    "created_at": "2026-03-26T10:00:00"
  }
]
```

### 2. Export Job

```bash
POST /api/export/jobs/{job_id}
```

Response: ZIP file download

### 3. Import Job

```bash
POST /api/export/import?skip_existing=true
Content-Type: multipart/form-data

file: <zip_file>
```

Response:
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Successfully imported job: Video Title",
  "skipped": false
}
```

## Frontend UI

### Navigation

Access Export/Import page via:
- Header navigation: Click "Export" button
- Direct URL: `http://your-domain/export`

### Export Section

1. Tampilkan list semua job yang bisa di-export (status=done dengan video dan frames)
2. Table columns:
   - Video Title
   - Duration
   - Frames count
   - Created date
   - Export button
3. Click "Export" button untuk download ZIP file
4. File akan otomatis terdownload dengan nama: `{video_title}_{job_id}.zip`

### Import Section

1. Upload area dengan drag-and-drop support
2. Checkbox: "Skip jika job sudah ada" (default: checked)
3. Upload file ZIP hasil export
4. Status message akan muncul:
   - ✅ Success - Import berhasil, link ke job page
   - ⚠️ Skipped - Job sudah ada, di-skip
   - ❌ Failed - Error message

## CLI Usage (Advanced)

### Using curl

**Export:**
```bash
curl -X POST http://localhost:1945/api/export/jobs/{job_id} \
  -o exported_job.zip
```

**Import:**
```bash
curl -X POST http://localhost:1945/api/export/import?skip_existing=true \
  -F "file=@exported_job.zip"
```

### Using Python

```python
import requests

# Export
response = requests.post(f"http://localhost:1945/api/export/jobs/{job_id}")
with open("exported_job.zip", "wb") as f:
    f.write(response.content)

# Import
with open("exported_job.zip", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:1945/api/export/import?skip_existing=true",
        files=files
    )
    print(response.json())
```

## Migration Workflow

### Scenario: Moving from Local to Production Server

**On Local Machine:**

1. Export job yang sudah diproses:
   ```bash
   # Via UI: Visit http://localhost:3000/export
   # Click "Export" on desired job
   # Save: video_title_12345678.zip
   ```

2. Copy ZIP file ke production server:
   ```bash
   scp video_title_12345678.zip user@192.168.1.45:~/imports/
   ```

**On Production Server:**

3. Import via UI:
   ```bash
   # Visit http://192.168.1.45:1946/export
   # Upload video_title_12345678.zip
   # Wait for success message
   ```

4. Or import via curl:
   ```bash
   cd ~/imports
   curl -X POST http://192.168.1.45:1945/api/export/import?skip_existing=true \
     -F "file=@video_title_12345678.zip"
   ```

5. Verify import:
   ```bash
   # Check if job appears in history
   # Visit http://192.168.1.45:1946/history
   ```

## Export/Import Data Structure

### ZIP File Structure
```
exported_job.zip
├── manifest.json          # Export metadata
├── metadata.json          # Complete job database record
├── video.mp4             # Original video file
└── frames/               # Extracted frames
    ├── frame_000001.jpg
    ├── frame_000002.jpg
    └── ...
```

### manifest.json
```json
{
  "version": "1.0",
  "exported_at": "2026-03-26T10:30:00",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_title": "Video Title"
}
```

### metadata.json (excerpt)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "youtube_url": "https://youtube.com/watch?v=...",
  "video_title": "Video Title",
  "video_duration": 180,
  "status": "done",
  "frames_count": 30,
  "analysis": { ... },
  "embedding": [0.1, 0.2, ...],  // 1536 dimensions
  "youtube_metadata": { ... },
  "transcript": "...",
  ...
}
```

## Error Handling

### Common Errors

**Export Errors:**

1. `Job {job_id} not found` - Job doesn't exist in database
2. `Job {job_id} is not completed` - Can only export jobs with status=done
3. `Video file not found` - Video has been deleted from temp storage
4. `No frames found` - Frames directory is empty or deleted

**Import Errors:**

1. `File must be a ZIP archive` - Uploaded file is not .zip format
2. `Invalid export file: manifest.json not found` - Corrupted or invalid ZIP
3. `Invalid export file: video.mp4 not found` - ZIP missing video file
4. `Invalid export file: no frames found` - ZIP missing frames

### Troubleshooting

**Export fails with "Video file not found":**
- Video files are stored in `/tmp/video-analysis/{job_id}/video.mp4`
- They may be cleaned up after some time
- Re-download video by retrying the job first

**Import fails with database error:**
- Check PostgreSQL connection
- Ensure pgvector extension is enabled
- Check disk space on target server

**Import succeeds but frames don't appear:**
- Check `/tmp/video-analysis/storage/frames/{job_id}/`
- Verify file permissions
- Check disk space

## Performance Considerations

### Export Time
- Depends on video size and number of frames
- Typical: 5-30 seconds for 5-minute video with 30 frames
- ZIP compression adds ~10-20% to file size reduction

### Import Time
- Depends on upload speed and extraction time
- Typical: 10-60 seconds for 50-200MB ZIP file
- Database restore is fast (<1 second)

### Storage Requirements
- Export ZIP: ~10-50MB per minute of video
- Import requires 2x space temporarily (ZIP + extracted)
- Cleanup happens automatically after import

## Security Considerations

1. **ZIP File Contents** - Contains original video and complete metadata
2. **Embeddings** - 1536-dimensional vectors included in export
3. **YouTube Metadata** - May contain sensitive channel info
4. **Access Control** - No authentication on API endpoints (add if needed)

## Future Enhancements

Potential improvements:
- [ ] Batch export (multiple jobs at once)
- [ ] Selective export (choose what to include)
- [ ] Export format versioning and backward compatibility
- [ ] Encryption for sensitive exports
- [ ] Cloud storage integration (S3, Google Drive)
- [ ] Scheduled automatic backups
- [ ] Export/import audit logs

## Troubleshooting Commands

**Check if job is exportable:**
```bash
curl http://localhost:1945/api/export/jobs | jq
```

**Test export:**
```bash
curl -X POST http://localhost:1945/api/export/jobs/{job_id} \
  -o test_export.zip && \
unzip -l test_export.zip
```

**Verify ZIP contents:**
```bash
unzip -l exported_job.zip
# Should show: manifest.json, metadata.json, video.mp4, frames/
```

**Import and check response:**
```bash
curl -X POST http://localhost:1945/api/export/import?skip_existing=true \
  -F "file=@exported_job.zip" | jq
```

## Support

For issues or questions:
1. Check backend logs: `docker compose logs backend -f`
2. Check celery logs: `docker compose logs celery-worker -f`
3. Verify storage paths: `ls -lah /tmp/video-analysis/`
4. Check database: `docker compose exec postgres psql -U postgres -d video_analysis -c "SELECT id, video_title, status FROM jobs;"`
