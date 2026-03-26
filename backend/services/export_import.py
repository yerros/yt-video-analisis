"""Export/Import service for video analysis data."""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.config import settings
from models.job import Job


class ExportImportService:
    """Service for exporting and importing video analysis data."""

    EXPORT_VERSION = "1.0"
    MANIFEST_FILE = "manifest.json"
    METADATA_FILE = "metadata.json"
    VIDEO_FILE = "video.mp4"
    FRAMES_DIR = "frames"

    def __init__(self, db: Session):
        """Initialize export/import service."""
        self.db = db
        self.storage_dir = Path(settings.storage_dir)
        self.temp_dir = Path(settings.temp_dir)

    def export_job(self, job_id: str, output_path: Optional[Path] = None) -> Path:
        """
        Export a job with all its data to a ZIP file.

        Args:
            job_id: Job UUID to export
            output_path: Optional custom output path for the ZIP file

        Returns:
            Path to the created ZIP file

        Raises:
            ValueError: If job not found or has no video/frames
        """
        # Get job from database
        job = self.db.query(Job).filter(Job.id == UUID(job_id)).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status != "done":
            raise ValueError(f"Job {job_id} is not completed (status: {job.status})")

        # Prepare paths
        job_temp_dir = self.temp_dir / str(job_id)
        frames_dir = self.storage_dir / "frames" / str(job_id)

        # Check if video and frames exist
        video_path = job_temp_dir / "video.mp4"
        if not video_path.exists():
            raise ValueError(f"Video file not found for job {job_id}")

        if not frames_dir.exists() or not any(frames_dir.iterdir()):
            raise ValueError(f"No frames found for job {job_id}")

        # Create output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.temp_dir / f"export_{job_id}_{timestamp}.zip"

        # Create temporary export directory
        export_temp_dir = self.temp_dir / f"export_temp_{job_id}"
        export_temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create manifest
            manifest = {
                "version": self.EXPORT_VERSION,
                "exported_at": datetime.utcnow().isoformat(),
                "job_id": str(job_id),
                "video_title": job.video_title,
            }
            manifest_path = export_temp_dir / self.MANIFEST_FILE
            manifest_path.write_text(json.dumps(manifest, indent=2))

            # Create metadata (database records)
            metadata = self._serialize_job(job)
            metadata_path = export_temp_dir / self.METADATA_FILE
            metadata_path.write_text(json.dumps(metadata, indent=2))

            # Copy video
            video_dest = export_temp_dir / self.VIDEO_FILE
            shutil.copy2(video_path, video_dest)

            # Copy frames
            frames_dest = export_temp_dir / self.FRAMES_DIR
            shutil.copytree(frames_dir, frames_dest)

            # Create ZIP file
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in export_temp_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(export_temp_dir)
                        zipf.write(file_path, arcname)

            return output_path

        finally:
            # Cleanup temporary directory
            if export_temp_dir.exists():
                shutil.rmtree(export_temp_dir)

    def import_job(self, zip_path: Path, skip_existing: bool = True) -> Dict[str, Any]:
        """
        Import a job from a ZIP file.

        Args:
            zip_path: Path to the ZIP file to import
            skip_existing: If True, skip import if job_id already exists

        Returns:
            Dict with import results: {
                "success": bool,
                "job_id": str,
                "message": str,
                "skipped": bool (if existing job was skipped)
            }

        Raises:
            ValueError: If ZIP file is invalid or corrupted
        """
        if not zip_path.exists():
            raise ValueError(f"ZIP file not found: {zip_path}")

        # Create temporary import directory
        import_temp_dir = self.temp_dir / f"import_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import_temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(import_temp_dir)

            # Validate manifest
            manifest_path = import_temp_dir / self.MANIFEST_FILE
            if not manifest_path.exists():
                raise ValueError("Invalid export file: manifest.json not found")

            manifest = json.loads(manifest_path.read_text())
            job_id = manifest.get("job_id")
            if not job_id:
                raise ValueError("Invalid manifest: job_id not found")

            # Check if job already exists
            existing_job = self.db.query(Job).filter(Job.id == UUID(job_id)).first()
            if existing_job and skip_existing:
                return {
                    "success": True,
                    "job_id": job_id,
                    "message": f"Job {job_id} already exists, skipped",
                    "skipped": True,
                }

            # Load metadata
            metadata_path = import_temp_dir / self.METADATA_FILE
            if not metadata_path.exists():
                raise ValueError("Invalid export file: metadata.json not found")

            metadata = json.loads(metadata_path.read_text())

            # Validate video and frames
            video_path = import_temp_dir / self.VIDEO_FILE
            frames_dir = import_temp_dir / self.FRAMES_DIR

            if not video_path.exists():
                raise ValueError("Invalid export file: video.mp4 not found")

            if not frames_dir.exists() or not any(frames_dir.iterdir()):
                raise ValueError("Invalid export file: no frames found")

            # Create job in database (or update if exists)
            if existing_job:
                # Update existing job
                job = existing_job
                for key, value in metadata.items():
                    if key not in ["id", "created_at"]:  # Don't update these
                        setattr(job, key, value)
            else:
                # Create new job
                job = Job(**metadata)
                self.db.add(job)

            self.db.commit()
            self.db.refresh(job)

            # Copy video to temp directory
            job_temp_dir = self.temp_dir / str(job_id)
            job_temp_dir.mkdir(parents=True, exist_ok=True)
            video_dest = job_temp_dir / "video.mp4"
            shutil.copy2(video_path, video_dest)

            # Copy frames to storage
            frames_dest = self.storage_dir / "frames" / str(job_id)
            if frames_dest.exists():
                shutil.rmtree(frames_dest)
            shutil.copytree(frames_dir, frames_dest)

            return {
                "success": True,
                "job_id": str(job.id),
                "message": f"Successfully imported job: {job.video_title}",
                "skipped": False,
            }

        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Import failed: {str(e)}")

        finally:
            # Cleanup temporary directory
            if import_temp_dir.exists():
                shutil.rmtree(import_temp_dir)

    def _serialize_job(self, job: Job) -> Dict[str, Any]:
        """Serialize job model to dictionary for export."""
        # Convert vector embedding to list for JSON serialization
        embedding_list = None
        if job.embedding is not None:
            # pgvector stores as string, need to parse it
            embedding_str = str(job.embedding)
            # Remove brackets and split by comma
            embedding_list = [float(x) for x in embedding_str.strip("[]").split(",")]

        return {
            "id": str(job.id),
            "youtube_url": job.youtube_url,
            "video_title": job.video_title,
            "video_duration": job.video_duration,
            "youtube_metadata": job.youtube_metadata,
            "channel_title": job.channel_title,
            "channel_id": job.channel_id,
            "description": job.description,
            "tags": job.tags,
            "category_id": job.category_id,
            "published_at": job.published_at.isoformat() if job.published_at else None,
            "view_count": job.view_count,
            "like_count": job.like_count,
            "comment_count": job.comment_count,
            "thumbnail_url": job.thumbnail_url,
            "title_en": job.title_en,
            "description_en": job.description_en,
            "disable_transcript": job.disable_transcript,
            "status": job.status,
            "progress": job.progress,
            "transcript": job.transcript,
            "frames_count": job.frames_count,
            "analysis": job.analysis,
            "error_message": job.error_message,
            "embedding": embedding_list,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }

    def list_exportable_jobs(self) -> List[Dict[str, Any]]:
        """
        List all jobs that can be exported (status=done with video and frames).

        Returns:
            List of job summaries
        """
        jobs = self.db.query(Job).filter(Job.status == "done").all()
        exportable = []

        for job in jobs:
            job_temp_dir = self.temp_dir / str(job.id)
            frames_dir = self.storage_dir / "frames" / str(job.id)
            video_path = job_temp_dir / "video.mp4"

            # Check if video and frames exist
            if video_path.exists() and frames_dir.exists() and any(frames_dir.iterdir()):
                exportable.append(
                    {
                        "id": str(job.id),
                        "title": job.video_title,
                        "duration": job.video_duration,
                        "frames_count": job.frames_count,
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                    }
                )

        return exportable
