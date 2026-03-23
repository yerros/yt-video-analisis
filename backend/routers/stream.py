"""SSE stream router for job progress."""

import asyncio
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.job import Job

router = APIRouter()


@router.get("/{job_id}/stream")
async def stream_job_progress(
    job_id: UUID,
) -> StreamingResponse:
    """Stream real-time job progress via SSE.
    
    Args:
        job_id: Job UUID.
        
    Returns:
        SSE stream of job progress events.
        
    Raises:
        HTTPException: If job not found.
    """
    from db.session import async_session_maker
    
    # Verify job exists first
    async with async_session_maker() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for job progress."""
        import json
        
        try:
            # Send initial connection message
            connected_msg = json.dumps({"event": "connected", "job_id": str(job_id)})
            yield f"data: {connected_msg}\n\n"
            
            last_progress = -1
            last_status = None
            
            # Poll database for updates (create new session each time)
            while True:
                async with async_session_maker() as session:
                    result = await session.execute(select(Job).where(Job.id == job_id))
                    current_job = result.scalar_one_or_none()
                    
                    if not current_job:
                        # Job deleted or not found
                        error_data = {
                            "job_id": str(job_id),
                            "error": "Job not found",
                            "status": "failed"
                        }
                        yield f"data: {json.dumps(error_data)}\n\n"
                        break
                    
                    # Check if there's an update
                    if (current_job.progress != last_progress or 
                        current_job.status != last_status):
                        
                        last_progress = current_job.progress
                        last_status = current_job.status
                        
                        progress_data = {
                            "job_id": str(job_id),
                            "progress": current_job.progress,
                            "status": current_job.status,
                            "message": current_job.error_message if current_job.status == "failed" else f"Progress: {current_job.progress}%",
                            "error": current_job.error_message,
                            "timestamp": current_job.updated_at.isoformat() if current_job.updated_at else None
                        }
                        yield f"data: {json.dumps(progress_data)}\n\n"
                    
                    # Check if job is completed or failed
                    if current_job.status in ["done", "failed"]:
                        done_msg = json.dumps({"event": "done"})
                        yield f"data: {done_msg}\n\n"
                        break
                
                # Poll every 500ms
                await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            # Client disconnected
            pass
        except Exception as e:
            error_msg = json.dumps({"error": str(e), "status": "failed"})
            yield f"data: {error_msg}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
