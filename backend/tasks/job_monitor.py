"""Background task for monitoring and processing pending jobs."""

import logging
from datetime import datetime, timedelta

from celery import current_app
from redis import Redis
from sqlalchemy import select

from celery_app import celery_app
from core.config import settings
from db.session import sync_session_maker
from models.job import Job, JobStatus

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.job_monitor.process_pending_jobs")
def process_pending_jobs():
    """Check for pending jobs and queue them if worker is idle.
    
    This task runs periodically (every 30 seconds) to:
    1. Check if there are pending jobs
    2. Check if worker is idle (no active tasks)
    3. Queue the oldest pending job for processing
    
    This ensures jobs are processed automatically without manual triggering.
    """
    try:
        # Check if there are any active tasks
        inspector = current_app.control.inspect()
        active_tasks = inspector.active()
        
        if not active_tasks:
            logger.debug("No active workers found")
            return {"status": "no_workers", "message": "No active workers"}
        
        # Count total active tasks across all workers
        total_active = sum(len(tasks) for tasks in active_tasks.values())
        
        # If worker is busy, skip
        if total_active > 0:
            logger.debug(f"Worker is busy with {total_active} tasks, skipping")
            return {
                "status": "busy",
                "active_tasks": total_active,
                "message": f"Worker busy with {total_active} tasks"
            }
        
        # Worker is idle, check for pending jobs
        logger.info("Worker is idle, checking for pending jobs...")
        
        with sync_session_maker() as session:
            # Get oldest pending job (created more than 5 seconds ago to avoid race conditions)
            result = session.execute(
                select(Job)
                .where(Job.status == JobStatus.PENDING)
                .where(Job.progress == 0)
                .where(Job.created_at < datetime.utcnow() - timedelta(seconds=5))
                .order_by(Job.created_at)
                .limit(1)
            )
            pending_job = result.scalar_one_or_none()
            
            if not pending_job:
                logger.debug("No pending jobs found")
                return {"status": "idle", "message": "No pending jobs"}
            
            # Queue the job
            from tasks.pipeline_sync import run_pipeline
            
            job_id = str(pending_job.id)
            logger.info(f"Queueing pending job {job_id} ({pending_job.youtube_url})")
            
            run_pipeline.delay(job_id)
            
            return {
                "status": "queued",
                "job_id": job_id,
                "youtube_url": pending_job.youtube_url,
                "message": f"Queued job {job_id}"
            }
            
    except Exception as e:
        logger.error(f"Error in process_pending_jobs: {e}")
        return {"status": "error", "message": str(e)}
