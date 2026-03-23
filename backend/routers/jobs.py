"""Jobs API router."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.job import Job, JobStatus
from schemas.job import JobCreate, JobListResponse, JobResponse
from tasks.pipeline_sync import run_pipeline
from services.storage_service import storage_service
from services.youtube_metadata import YouTubeMetadataService

router = APIRouter()


class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete request."""
    job_ids: List[UUID]


class ChannelVideosRequest(BaseModel):
    """Schema for fetching channel videos."""
    channel_url: str
    max_results: Optional[int] = None  # None = all videos
    order: str = "date"


class BulkAnalyzeRequest(BaseModel):
    """Schema for bulk analyze request."""
    channel_url: str
    max_results: Optional[int] = None  # None = all videos
    skip_existing: bool = True  # Skip URLs that already exist in database
    disable_transcript: bool = True  # Skip audio transcription (disabled by default)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    body: JobCreate,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Create a new video analysis job.
    
    If the URL already exists in the database, returns the existing job instead of creating a duplicate.
    
    Args:
        body: Job creation request with YouTube URL.
        db: Database session.
        
    Returns:
        Created or existing job details.
    """
    youtube_url = str(body.youtube_url)
    
    # Check if URL already exists
    result = await db.execute(
        select(Job).where(Job.youtube_url == youtube_url)
    )
    existing_job = result.scalar_one_or_none()
    
    if existing_job:
        # Return existing job instead of creating duplicate
        return JobResponse(
            id=existing_job.id,
            youtube_url=existing_job.youtube_url,
            video_title=existing_job.video_title,
            video_duration=existing_job.video_duration,
            status=existing_job.status,
            progress=existing_job.progress,
            transcript=existing_job.transcript,
            frames_count=existing_job.frames_count,
            analysis=existing_job.analysis,
            error_message=existing_job.error_message,
            created_at=existing_job.created_at,
            updated_at=existing_job.updated_at,
            youtube_metadata=existing_job.youtube_metadata,
            channel_title=existing_job.channel_title,
            channel_id=existing_job.channel_id,
            description=existing_job.description,
            tags=existing_job.tags,
            category_id=existing_job.category_id,
            published_at=existing_job.published_at,
            view_count=existing_job.view_count,
            like_count=existing_job.like_count,
            comment_count=existing_job.comment_count,
            thumbnail_url=existing_job.thumbnail_url,
            title_en=existing_job.title_en,
            description_en=existing_job.description_en,
            disable_transcript=existing_job.disable_transcript,
        )
    
    # Create new job if URL doesn't exist
    job = Job(
        youtube_url=youtube_url,
        status=JobStatus.PENDING,
        progress=0,
        disable_transcript=body.disable_transcript,
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Start Celery task asynchronously
    run_pipeline.delay(str(job.id))
    
    return JobResponse(
        id=job.id,
        youtube_url=job.youtube_url,
        video_title=job.video_title,
        video_duration=job.video_duration,
        status=job.status,
        progress=job.progress,
        transcript=job.transcript,
        frames_count=job.frames_count,
        analysis=job.analysis,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        youtube_metadata=job.youtube_metadata,
        channel_title=job.channel_title,
        channel_id=job.channel_id,
        description=job.description,
        tags=job.tags,
        category_id=job.category_id,
        published_at=job.published_at,
        view_count=job.view_count,
        like_count=job.like_count,
        comment_count=job.comment_count,
        thumbnail_url=job.thumbnail_url,
    )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """List all jobs with pagination.
    
    Args:
        limit: Maximum number of jobs to return.
        offset: Number of jobs to skip.
        db: Database session.
        
    Returns:
        List of jobs with pagination info.
    """
    # Get total count
    count_result = await db.execute(select(func.count(Job.id)))
    total = count_result.scalar_one()
    
    # Get jobs with pagination
    result = await db.execute(
        select(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    jobs = result.scalars().all()
    
    return JobListResponse(
        items=[
            JobResponse(
                id=job.id,
                youtube_url=job.youtube_url,
                video_title=job.video_title,
                video_duration=job.video_duration,
                status=job.status,
                progress=job.progress,
                transcript=job.transcript,
                frames_count=job.frames_count,
                analysis=job.analysis,
                error_message=job.error_message,
                created_at=job.created_at,
                updated_at=job.updated_at,
                youtube_metadata=job.youtube_metadata,
                channel_title=job.channel_title,
                channel_id=job.channel_id,
                description=job.description,
                tags=job.tags,
                category_id=job.category_id,
                published_at=job.published_at,
                view_count=job.view_count,
                like_count=job.like_count,
                comment_count=job.comment_count,
                thumbnail_url=job.thumbnail_url,
            )
            for job in jobs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Get job details by ID.
    
    Args:
        job_id: Job UUID.
        db: Database session.
        
    Returns:
        Job details.
        
    Raises:
        HTTPException: If job not found.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    return JobResponse(
        id=job.id,
        youtube_url=job.youtube_url,
        video_title=job.video_title,
        video_duration=job.video_duration,
        status=job.status,
        progress=job.progress,
        transcript=job.transcript,
        frames_count=job.frames_count,
        analysis=job.analysis,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        youtube_metadata=job.youtube_metadata,
        channel_title=job.channel_title,
        channel_id=job.channel_id,
        description=job.description,
        tags=job.tags,
        category_id=job.category_id,
        published_at=job.published_at,
        view_count=job.view_count,
        like_count=job.like_count,
        comment_count=job.comment_count,
        thumbnail_url=job.thumbnail_url,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a job and its associated files.
    
    This will also delete:
    - All frames from Supabase Storage
    - Job record from database
    
    Args:
        job_id: Job UUID.
        db: Database session.
        
    Raises:
        HTTPException: If job not found.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    # Delete frames from Supabase Storage
    try:
        deleted = storage_service.delete_job_frames(str(job_id))
        if deleted:
            print(f"Deleted Supabase frames for job {job_id}")
        else:
            print(f"Warning: Could not delete Supabase frames for job {job_id}")
    except Exception as e:
        print(f"Error deleting Supabase frames for job {job_id}: {e}")
        # Continue with job deletion even if frame deletion fails
    
    # Delete job from database
    await db.delete(job)
    await db.commit()


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
async def bulk_delete_jobs(
    body: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete multiple jobs and their associated files.
    
    This will delete for each job:
    - All frames from Supabase Storage
    - Job record from database
    
    Args:
        body: List of job IDs to delete.
        db: Database session.
        
    Returns:
        Summary of deleted jobs.
    """
    if not body.job_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No job IDs provided",
        )
    
    deleted_count = 0
    failed_count = 0
    failed_ids = []
    
    for job_id in body.job_ids:
        try:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            
            if not job:
                failed_count += 1
                failed_ids.append(str(job_id))
                continue
            
            # Delete frames from Supabase Storage
            try:
                deleted = storage_service.delete_job_frames(str(job_id))
                if deleted:
                    print(f"Deleted Supabase frames for job {job_id}")
                else:
                    print(f"Warning: Could not delete Supabase frames for job {job_id}")
            except Exception as e:
                print(f"Error deleting Supabase frames for job {job_id}: {e}")
                # Continue with job deletion even if frame deletion fails
            
            # Delete job from database
            await db.delete(job)
            deleted_count += 1
        except Exception as e:
            failed_count += 1
            failed_ids.append(str(job_id))
            print(f"Error deleting job {job_id}: {e}")
    
    # Commit all deletions
    await db.commit()
    
    return {
        "deleted_count": deleted_count,
        "failed_count": failed_count,
        "failed_ids": failed_ids,
        "total_requested": len(body.job_ids),
    }


class RetryJobRequest(BaseModel):
    """Schema for retry job request."""
    force: bool = False  # Force retry even if job appears to be running


@router.post("/{job_id}/retry", response_model=JobResponse, status_code=status.HTTP_200_OK)
async def retry_job(
    job_id: UUID,
    body: Optional[RetryJobRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Retry any job (failed, stuck, or completed).
    
    This will:
    - Reset job status to pending
    - Clear error message
    - Reset progress to 0
    - Restart the Celery task
    
    Args:
        job_id: Job UUID to retry.
        body: Optional request body with force flag.
        db: Database session.
        
    Returns:
        Updated job details.
        
    Raises:
        HTTPException: If job not found.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    # Default to allowing retry unless explicitly checking freshly created pending jobs
    force = body.force if body else False
    
    # Only block retry if job was just created (pending with 0 progress and no error)
    # This prevents accidental double-submission
    if not force and job.status == JobStatus.PENDING and job.progress == 0 and job.error_message is None:
        # Check if job was created very recently (within last 30 seconds)
        time_since_creation = (datetime.utcnow() - job.created_at.replace(tzinfo=None)).total_seconds()
        if time_since_creation < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job was just created {int(time_since_creation)} seconds ago. Please wait or use force=true.",
            )
    
    # Reset job to pending state
    job.status = JobStatus.PENDING
    job.progress = 0
    job.error_message = None
    job.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(job)
    
    # Restart Celery task
    run_pipeline.delay(str(job.id))
    
    return JobResponse(
        id=job.id,
        youtube_url=job.youtube_url,
        video_title=job.video_title,
        video_duration=job.video_duration,
        status=job.status,
        progress=job.progress,
        transcript=job.transcript,
        frames_count=job.frames_count,
        analysis=job.analysis,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        youtube_metadata=job.youtube_metadata,
        channel_title=job.channel_title,
        channel_id=job.channel_id,
        description=job.description,
        tags=job.tags,
        category_id=job.category_id,
        published_at=job.published_at,
        view_count=job.view_count,
        like_count=job.like_count,
        comment_count=job.comment_count,
        thumbnail_url=job.thumbnail_url,
        title_en=job.title_en,
        description_en=job.description_en,
        disable_transcript=job.disable_transcript,
    )


@router.post("/retry-failed", status_code=status.HTTP_200_OK)
async def retry_all_failed_jobs(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retry all failed jobs.
    
    This will reset all jobs with status 'failed' to 'pending' and restart them.
    
    Args:
        db: Database session.
        
    Returns:
        Summary of retried jobs.
    """
    # Get all failed jobs
    result = await db.execute(
        select(Job).where(Job.status == JobStatus.FAILED)
    )
    failed_jobs = result.scalars().all()
    
    if not failed_jobs:
        return {
            "retried_count": 0,
            "message": "No failed jobs found",
        }
    
    retried_count = 0
    
    for job in failed_jobs:
        # Reset job to pending state
        job.status = JobStatus.PENDING
        job.progress = 0
        job.error_message = None
        job.updated_at = datetime.utcnow()
        
        # Restart Celery task
        run_pipeline.delay(str(job.id))
        retried_count += 1
    
    await db.commit()
    
    return {
        "retried_count": retried_count,
        "message": f"Successfully retried {retried_count} failed job(s)",
    }


@router.post("/channel-videos", status_code=status.HTTP_200_OK)
async def get_channel_videos(
    body: ChannelVideosRequest,
) -> Dict[str, Any]:
    """Fetch videos from a YouTube channel.
    
    Args:
        body: Channel URL and options.
        
    Returns:
        Dictionary containing channel info and list of videos.
    """
    try:
        youtube_service = YouTubeMetadataService()
        result = youtube_service.get_channel_videos(
            channel_url=body.channel_url,
            max_results=body.max_results,
            order=body.order
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/bulk-analyze", status_code=status.HTTP_200_OK)
async def bulk_analyze_channel(
    body: BulkAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Bulk analyze all videos from a YouTube channel.
    
    This will:
    1. Fetch all videos from the channel
    2. Check which videos already exist in database (by URL)
    3. Create jobs for new videos (skip existing if skip_existing=True)
    4. Save jobs as PENDING in database (NOT start processing immediately)
    
    IMPORTANT: Jobs are NOT processed immediately to avoid YouTube bot detection.
    After creating jobs, use the /process-queue endpoint to start processing
    jobs one by one with delays between each job.
    
    Args:
        body: Channel URL and options.
        db: Database session.
        
    Returns:
        Summary of created jobs, skipped videos, and errors.
    """
    try:
        # Fetch channel videos
        youtube_service = YouTubeMetadataService()
        channel_data = youtube_service.get_channel_videos(
            channel_url=body.channel_url,
            max_results=body.max_results,
            order="date"
        )
        
        videos = channel_data.get("videos", [])
        if not videos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No videos found in channel",
            )
        
        created_jobs = []
        skipped_urls = []
        errors = []
        
        for video in videos:
            video_url = video["video_url"]
            
            try:
                # Check if URL already exists in database
                if body.skip_existing:
                    result = await db.execute(
                        select(Job).where(Job.youtube_url == video_url)
                    )
                    existing_job = result.scalar_one_or_none()
                    
                    if existing_job:
                        skipped_urls.append({
                            "url": video_url,
                            "title": video["title"],
                            "reason": "already_exists",
                            "job_id": str(existing_job.id),
                        })
                        continue
                
                # Create new job (only save to database, don't start processing yet)
                # Jobs will be processed one by one with delays to avoid bot detection
                job = Job(
                    youtube_url=video_url,
                    status=JobStatus.PENDING,
                    progress=0,
                    disable_transcript=body.disable_transcript,
                )
                
                db.add(job)
                await db.flush()  # Get job ID without committing
                
                created_jobs.append({
                    "job_id": str(job.id),
                    "video_url": video_url,
                    "title": video["title"],
                })
                
            except Exception as e:
                errors.append({
                    "url": video_url,
                    "title": video.get("title", "Unknown"),
                    "error": str(e),
                })
        
        # Commit all new jobs
        await db.commit()
        
        return {
            "channel_id": channel_data.get("channel_id"),
            "channel_title": channel_data.get("channel_title"),
            "total_videos_found": len(videos),
            "jobs_created": len(created_jobs),
            "videos_skipped": len(skipped_urls),
            "errors": len(errors),
            "created_jobs": created_jobs,
            "skipped_videos": skipped_urls,
            "error_details": errors,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk analyze channel: {str(e)}",
        )


@router.post("/process-queue", status_code=status.HTTP_200_OK)
async def process_pending_jobs_queue(
    delay_seconds: int = 30,  # Delay between jobs to avoid bot detection
    batch_size: int = 10,  # Number of jobs to process in this batch
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Start processing pending jobs one by one with delays to avoid bot detection.
    
    This endpoint will:
    1. Find pending jobs (status=PENDING, progress=0)
    2. Queue them to Celery with delays between each job
    3. Return info about queued jobs
    
    Args:
        delay_seconds: Delay in seconds between each job (default: 30s)
        batch_size: Maximum number of jobs to queue in this request (default: 10)
        db: Database session.
        
    Returns:
        Information about queued jobs.
    """
    import asyncio
    
    try:
        # Find pending jobs
        result = await db.execute(
            select(Job)
            .where(Job.status == JobStatus.PENDING)
            .where(Job.progress == 0)
            .order_by(Job.created_at)
            .limit(batch_size)
        )
        pending_jobs = result.scalars().all()
        
        if not pending_jobs:
            return {
                "message": "No pending jobs found",
                "jobs_queued": 0,
                "remaining_pending": 0,
            }
        
        # Get total remaining pending jobs
        count_result = await db.execute(
            select(func.count())
            .select_from(Job)
            .where(Job.status == JobStatus.PENDING)
            .where(Job.progress == 0)
        )
        total_pending = count_result.scalar()
        
        queued_jobs = []
        
        # Queue jobs one by one with delays
        for i, job in enumerate(pending_jobs):
            # Calculate eta (estimated time of arrival) for staggered execution
            import time as time_module
            eta_timestamp = time_module.time() + (i * delay_seconds)
            
            # Queue the job with ETA to stagger execution
            run_pipeline.apply_async(
                args=[str(job.id)],
                countdown=i * delay_seconds  # Delay execution by i * delay_seconds
            )
            
            queued_jobs.append({
                "job_id": str(job.id),
                "video_url": job.youtube_url,
                "video_title": job.video_title,
                "eta_seconds": i * delay_seconds,
            })
        
        return {
            "message": f"Queued {len(queued_jobs)} jobs with {delay_seconds}s delay between each",
            "jobs_queued": len(queued_jobs),
            "remaining_pending": total_pending - len(queued_jobs),
            "delay_seconds": delay_seconds,
            "queued_jobs": queued_jobs,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process queue: {str(e)}",
        )
