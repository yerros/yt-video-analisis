"""Celery task for generating embeddings."""

import asyncio
import logging
from uuid import UUID

from celery import Task

from celery_app import celery_app
from db.session import async_session_maker
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """Base task with async support."""
    
    def __call__(self, *args, **kwargs):
        """Run the async task."""
        return asyncio.run(self.run_async(*args, **kwargs))


@celery_app.task(base=AsyncTask, name="tasks.generate_embedding")
async def generate_embedding_task(job_id: str):
    """
    Generate embedding for a completed video analysis job.
    
    This task is triggered automatically after a video analysis is complete.
    It generates a vector embedding based on the video's content (title,
    transcript, analysis results) for semantic search functionality.
    
    Args:
        job_id: UUID of the job to generate embedding for
    """
    logger.info(f"Starting embedding generation for job {job_id}")
    
    try:
        embedding_service = EmbeddingService()
        
        async with async_session_maker() as session:
            embedding = await embedding_service.generate_job_embedding(
                db=session,
                job_id=job_id
            )
            
            if embedding:
                logger.info(f"✓ Successfully generated embedding for job {job_id}")
                return {"status": "success", "job_id": job_id}
            else:
                logger.warning(f"⚠ No embedding generated for job {job_id} (may lack content)")
                return {"status": "skipped", "job_id": job_id, "reason": "no_content"}
                
    except Exception as e:
        logger.error(f"✗ Failed to generate embedding for job {job_id}: {e}", exc_info=True)
        return {"status": "failed", "job_id": job_id, "error": str(e)}
