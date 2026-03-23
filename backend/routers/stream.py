"""SSE stream router for job progress."""

import asyncio
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.session import get_db
from models.job import Job

router = APIRouter()


@router.get("/{job_id}/stream")
async def stream_job_progress(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream real-time job progress via SSE.
    
    Args:
        job_id: Job UUID.
        db: Database session.
        
    Returns:
        SSE stream of job progress events.
        
    Raises:
        HTTPException: If job not found.
    """
    # Verify job exists
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for job progress."""
        import json
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        channel = f"job:{job_id}"
        
        try:
            # Check if job is already completed
            result = await db.execute(select(Job).where(Job.id == job_id))
            current_job = result.scalar_one_or_none()
            
            if current_job and current_job.status in ["done", "failed"]:
                # Job already finished, send completion message immediately
                connected_msg = json.dumps({"event": "connected", "job_id": str(job_id)})
                yield f"data: {connected_msg}\n\n"
                
                completion_data = {
                    "job_id": str(job_id),
                    "progress": current_job.progress,
                    "status": current_job.status.value,
                    "message": "Job already completed" if current_job.status == "done" else "Job failed",
                    "error": current_job.error_message,
                    "timestamp": current_job.updated_at.isoformat() if current_job.updated_at else None
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
                done_msg = json.dumps({"event": "done"})
                yield f"data: {done_msg}\n\n"
                return
            
            # Subscribe to job-specific channel
            pubsub.subscribe(channel)
            
            # Send initial connection message
            connected_msg = json.dumps({"event": "connected", "job_id": str(job_id)})
            yield f"data: {connected_msg}\n\n"
            
            # Listen for messages
            while True:
                message = pubsub.get_message(timeout=1.0)
                
                if message and message["type"] == "message":
                    data = message["data"]
                    yield f"data: {data}\n\n"
                    
                    # Check if job is completed or failed
                    try:
                        progress_data = json.loads(data)
                        if progress_data.get("status") in ["done", "failed"]:
                            # Send final message and close
                            done_msg = json.dumps({"event": "done"})
                            yield f"data: {done_msg}\n\n"
                            break
                    except json.JSONDecodeError:
                        pass
                
                # Allow other tasks to run
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            # Client disconnected
            pass
        finally:
            pubsub.unsubscribe(channel)
            pubsub.close()
            redis_client.close()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
