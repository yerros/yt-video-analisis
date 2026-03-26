"""API routes for export/import functionality."""

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from db.session import get_db
from services.export_import import ExportImportService
from pydantic import BaseModel


router = APIRouter(prefix="/export", tags=["export-import"])


class ExportableJob(BaseModel):
    """Exportable job summary."""

    id: str
    title: str
    duration: int
    frames_count: int
    created_at: str


class ImportResult(BaseModel):
    """Import operation result."""

    success: bool
    job_id: str
    message: str
    skipped: bool


@router.get("/jobs", response_model=List[ExportableJob])
async def list_exportable_jobs(db: Session = Depends(get_db)):
    """
    List all jobs that can be exported.

    Returns:
        List of exportable jobs (status=done with video and frames)
    """
    service = ExportImportService(db)
    jobs = service.list_exportable_jobs()
    return jobs


@router.post("/jobs/{job_id}")
async def export_job(job_id: str, db: Session = Depends(get_db)):
    """
    Export a job to a ZIP file.

    Args:
        job_id: Job UUID to export

    Returns:
        ZIP file containing job data, video, and frames
    """
    try:
        service = ExportImportService(db)
        zip_path = service.export_job(job_id)

        # Get video title for filename
        from models.job import Job
        from uuid import UUID

        job = db.query(Job).filter(Job.id == UUID(job_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Sanitize filename
        safe_title = "".join(c for c in job.video_title if c.isalnum() or c in (" ", "_", "-"))[:50]
        filename = f"{safe_title}_{job_id[:8]}.zip"

        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import", response_model=ImportResult)
async def import_job(
    file: UploadFile = File(...), skip_existing: bool = True, db: Session = Depends(get_db)
):
    """
    Import a job from a ZIP file.

    Args:
        file: ZIP file to import
        skip_existing: If True, skip import if job_id already exists

    Returns:
        Import result with job_id and status
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")

    # Save uploaded file to temporary location
    from core.config import settings

    temp_dir = Path(settings.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_zip_path = temp_dir / f"upload_{timestamp}.zip"

    try:
        # Write uploaded file to disk
        with temp_zip_path.open("wb") as f:
            content = await file.read()
            f.write(content)

        # Import the job
        service = ExportImportService(db)
        result = service.import_job(temp_zip_path, skip_existing=skip_existing)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    finally:
        # Cleanup temporary ZIP file
        if temp_zip_path.exists():
            temp_zip_path.unlink()
