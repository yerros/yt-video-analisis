"""Sequential queue processor for bulk video analysis.

This module implements a true sequential queue system where jobs are processed
one at a time with delays between each job to avoid YouTube bot detection.
"""

import time
from typing import List
from celery import chain
from celery_app import celery_app
from tasks.pipeline_sync import run_pipeline


@celery_app.task(name="tasks.queue_processor.process_sequential_queue")
def process_sequential_queue(job_ids: List[str], delay_seconds: int = 30) -> dict:
    """Process jobs sequentially with delays between each job.
    
    This task processes one job at a time, waiting for each to complete
    before starting the next one. There's a configurable delay between jobs.
    
    Args:
        job_ids: List of job IDs to process sequentially.
        delay_seconds: Delay in seconds between each job (default: 30).
        
    Returns:
        Summary of processed jobs.
    """
    if not job_ids:
        return {
            "status": "no_jobs",
            "message": "No jobs to process",
            "processed": 0,
            "failed": 0,
        }
    
    processed_count = 0
    failed_count = 0
    results = []
    
    for i, job_id in enumerate(job_ids):
        try:
            # Log start
            print(f"[Sequential Queue] Processing job {i+1}/{len(job_ids)}: {job_id}")
            
            # Run the pipeline synchronously (wait for completion)
            result = run_pipeline(job_id)
            
            processed_count += 1
            results.append({
                "job_id": job_id,
                "status": "success",
                "result": result,
            })
            
            print(f"[Sequential Queue] Job {job_id} completed successfully")
            
            # Delay before next job (but not after the last one)
            if i < len(job_ids) - 1:
                print(f"[Sequential Queue] Waiting {delay_seconds}s before next job...")
                time.sleep(delay_seconds)
                
        except Exception as e:
            failed_count += 1
            error_msg = str(e)
            results.append({
                "job_id": job_id,
                "status": "failed",
                "error": error_msg,
            })
            
            print(f"[Sequential Queue] Job {job_id} failed: {error_msg}")
            
            # Continue with next job even if this one failed
            # Still apply delay to avoid hammering YouTube
            if i < len(job_ids) - 1:
                print(f"[Sequential Queue] Waiting {delay_seconds}s before next job...")
                time.sleep(delay_seconds)
    
    return {
        "status": "completed",
        "message": f"Processed {processed_count} jobs, {failed_count} failed",
        "total_jobs": len(job_ids),
        "processed": processed_count,
        "failed": failed_count,
        "delay_seconds": delay_seconds,
        "results": results,
    }


@celery_app.task(name="tasks.queue_processor.start_next_job")
def start_next_job(delay_seconds: int = 30) -> dict:
    """Start processing the next pending job in queue.
    
    This task finds the oldest pending job and processes it.
    After completion, it can chain to process the next job.
    
    Args:
        delay_seconds: Delay before starting next job (default: 30).
        
    Returns:
        Status of the processed job.
    """
    from db.session import sync_session_maker
    from models.job import Job, JobStatus
    from sqlalchemy import select
    
    # Get the next pending job
    with sync_session_maker() as db:
        result = db.execute(
            select(Job)
            .where(Job.status == JobStatus.PENDING)
            .where(Job.progress == 0)
            .order_by(Job.created_at)
            .limit(1)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return {
                "status": "no_jobs",
                "message": "No pending jobs in queue",
            }
        
        job_id = str(job.id)
        
        # Check if there are more pending jobs
        count_result = db.execute(
            select(Job)
            .where(Job.status == JobStatus.PENDING)
            .where(Job.progress == 0)
        )
        remaining_jobs = len(count_result.scalars().all())
    
    try:
        # Process this job
        print(f"[Queue] Processing job: {job_id}")
        result = run_pipeline(job_id)
        
        print(f"[Queue] Job {job_id} completed. Remaining: {remaining_jobs - 1}")
        
        # If there are more jobs, schedule the next one with delay
        if remaining_jobs > 1:
            print(f"[Queue] Scheduling next job in {delay_seconds}s...")
            start_next_job.apply_async(
                args=[delay_seconds],
                countdown=delay_seconds
            )
        
        return {
            "status": "success",
            "job_id": job_id,
            "remaining": remaining_jobs - 1,
            "result": result,
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Queue] Job {job_id} failed: {error_msg}")
        
        # Even if failed, continue with next job
        if remaining_jobs > 1:
            print(f"[Queue] Scheduling next job in {delay_seconds}s...")
            start_next_job.apply_async(
                args=[delay_seconds],
                countdown=delay_seconds
            )
        
        return {
            "status": "failed",
            "job_id": job_id,
            "remaining": remaining_jobs - 1,
            "error": error_msg,
        }
