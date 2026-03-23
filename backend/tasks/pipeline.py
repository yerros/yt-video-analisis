"""Celery task for video analysis pipeline."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy import select

from celery_app import celery_app
from core.config import settings
from db.session import async_session_maker
from models.job import Job, JobStatus
from services.analyzer import analyze_video
from services.downloader import download_video
from services.extractor import extract_frames
from services.transcriber import transcribe_audio
from services.youtube_metadata import YouTubeMetadataService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def run_pipeline(self, job_id: str) -> None:
    """Run the complete video analysis pipeline.
    
    Pipeline steps:
    0. Fetch YouTube metadata (5%)
    1. Download video and extract audio (15%)
    2. Transcribe audio to text (35%)
    3. Extract key frames from video (65%)
    4. Analyze with GPT-4o (90%)
    5. Save results to database (100%)
    
    Args:
        self: Celery task instance.
        job_id: UUID of the job to process.
    """
    import asyncio
    
    # Run async operations in sync context
    asyncio.run(_run_pipeline_async(self, job_id))


async def _run_pipeline_async(task, job_id: str) -> None:
    """Async implementation of pipeline."""
    
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    # Create thread pool for blocking operations
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    
    async def update_progress(progress: int, status: JobStatus, message: str, error: Optional[str] = None) -> None:
        """Update job progress in database and publish to Redis."""
        try:
            async with async_session_maker() as session:
                async with session.begin():
                    result = await session.execute(
                        select(Job).where(Job.id == UUID(job_id))
                    )
                    job = result.scalar_one_or_none()
                    
                    if job:
                        job.progress = progress
                        job.status = status
                        job.error_message = error
                        job.updated_at = datetime.utcnow()
                        # Commit is automatic with session.begin() context manager
            
            # Publish progress update to Redis for SSE streaming
            from redis import Redis
            redis_client = Redis.from_url(settings.redis_url)
            progress_data = {
                "job_id": job_id,
                "progress": progress,
                "status": status.value,
                "message": message,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }
            redis_client.publish(f"job:{job_id}", json.dumps(progress_data))
            redis_client.close()
            
            logger.info(f"Job {job_id}: {progress}% - {message}")
        except Exception as e:
            logger.error(f"Failed to update progress for job {job_id}: {e}")
    
    try:
        # Get job from database
        async with async_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    select(Job).where(Job.id == UUID(job_id))
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return
                
                youtube_url = job.youtube_url
        
        # Step 0: Fetch YouTube metadata (0-5%)
        await update_progress(0, JobStatus.DOWNLOADING, "Fetching YouTube metadata...")
        try:
            youtube_service = YouTubeMetadataService()
            metadata = await loop.run_in_executor(executor, youtube_service.get_video_metadata, youtube_url)
            
            # Convert datetime objects to ISO format strings for JSON serialization
            def serialize_metadata(data):
                """Recursively serialize datetime objects to ISO format strings."""
                if isinstance(data, dict):
                    return {k: serialize_metadata(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [serialize_metadata(item) for item in data]
                elif isinstance(data, datetime):
                    return data.isoformat()
                else:
                    return data
            
            serialized_metadata = serialize_metadata(metadata)
            
            # Save metadata to database
            async with async_session_maker() as session:
                async with session.begin():
                    result = await session.execute(
                        select(Job).where(Job.id == UUID(job_id))
                    )
                    job = result.scalar_one_or_none()
                    
                    if job:
                        job.youtube_metadata = serialized_metadata
                        job.video_title = metadata.get("title")
                        job.channel_title = metadata.get("channel_title")
                        job.channel_id = metadata.get("channel_id")
                        job.description = metadata.get("description")
                        job.tags = metadata.get("tags", [])
                        job.category_id = metadata.get("category_id")
                        job.published_at = metadata.get("published_at")
                        job.view_count = metadata.get("view_count")
                        job.like_count = metadata.get("like_count")
                        job.comment_count = metadata.get("comment_count")
                        job.thumbnail_url = metadata.get("thumbnail_url")
                        job.video_duration = metadata.get("duration_seconds")
                        job.updated_at = datetime.utcnow()
            
            await update_progress(5, JobStatus.DOWNLOADING, f"Metadata fetched: {metadata.get('title', 'Unknown')}")
            logger.info(f"Job {job_id}: YouTube metadata fetched successfully")
        except Exception as e:
            logger.warning(f"Job {job_id}: Could not fetch YouTube metadata: {e}")
            metadata = None
            # Continue pipeline even if metadata fetch fails
            await update_progress(5, JobStatus.DOWNLOADING, "Metadata fetch failed, continuing...")
        
        # Step 1: Download video (5-15%)
        await update_progress(5, JobStatus.DOWNLOADING, "Starting download...")
        video_path, audio_path = await loop.run_in_executor(executor, download_video, youtube_url, job_id)
        await update_progress(15, JobStatus.DOWNLOADING, "Download completed")
        
        # Step 2: Transcribe audio (15-35%)
        await update_progress(15, JobStatus.TRANSCRIBING, "Starting transcription...")
        transcript = await loop.run_in_executor(executor, transcribe_audio, audio_path)
        await update_progress(35, JobStatus.TRANSCRIBING, "Transcription completed")
        
        # Step 3: Extract frames (35-65%)
        await update_progress(35, JobStatus.EXTRACTING, "Extracting key frames...")
        frame_paths = await loop.run_in_executor(executor, extract_frames, video_path, job_id)
        await update_progress(65, JobStatus.EXTRACTING, f"Extracted {len(frame_paths)} frames")
        
        # Step 4: Analyze with GPT-4o (65-90%)
        await update_progress(65, JobStatus.ANALYZING, "Analyzing video content...")
        
        # Get metadata for context
        async with async_session_maker() as session:
            result = await session.execute(
                select(Job).where(Job.id == UUID(job_id))
            )
            job = result.scalar_one_or_none()
            metadata_context = job.youtube_metadata if job else None
        
        analysis_result = await loop.run_in_executor(
            executor, analyze_video, transcript, frame_paths, metadata_context
        )
        await update_progress(90, JobStatus.ANALYZING, "Analysis completed")
        
        # Step 5: Save results (90-100%)
        await update_progress(90, JobStatus.DONE, "Saving results...")
        
        async with async_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    select(Job).where(Job.id == UUID(job_id))
                )
                job = result.scalar_one_or_none()
                
                if job:
                    job.status = JobStatus.DONE
                    job.progress = 100
                    job.transcript = transcript
                    job.frames_count = len(frame_paths)
                    job.analysis = {
                        "summary": analysis_result
                    }
                    job.updated_at = datetime.utcnow()
                    # Commit is automatic with session.begin() context manager
        
        await update_progress(100, JobStatus.DONE, "Processing completed successfully")
        
        # Clean up temporary files
        temp_dir = Path(settings.temp_dir) / job_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")
        
    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {e}", exc_info=True)
        
        error_message = str(e)
        await update_progress(0, JobStatus.FAILED, "Processing failed", error=error_message)
        
        # Clean up on failure
        temp_dir = Path(settings.temp_dir) / job_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        raise
