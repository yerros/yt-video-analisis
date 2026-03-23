"""API endpoints for serving frame images."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/frames", tags=["frames"])


@router.get("/{job_id}/{filename}")
async def get_frame_image(job_id: str, filename: str):
    """Serve a frame image file.
    
    Args:
        job_id: UUID of the job.
        filename: Name of the frame file (e.g., frame_0001.jpg).
        
    Returns:
        Frame image file.
        
    Raises:
        HTTPException: If frame file not found.
    """
    try:
        # Construct file path
        frame_path = Path(settings.storage_dir) / "frames" / job_id / filename
        
        # Validate file exists
        if not frame_path.exists():
            logger.warning(f"Frame not found: {frame_path}")
            raise HTTPException(status_code=404, detail="Frame not found")
        
        # Validate it's actually inside our storage directory (security)
        try:
            frame_path.resolve().relative_to(Path(settings.storage_dir).resolve())
        except ValueError:
            logger.error(f"Path traversal attempt: {frame_path}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Return image file
        return FileResponse(
            frame_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"}  # Cache for 1 day
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve frame {job_id}/{filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
