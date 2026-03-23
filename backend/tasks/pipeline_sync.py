"""Celery task for video analysis pipeline - synchronous version."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from redis import Redis
from sqlalchemy import select

from openai import OpenAI

from celery_app import celery_app
from core.config import settings
from core.exceptions import DownloadFailedError, VideoTooLongError
from db.session import sync_session_maker
from models.job import Job, JobStatus
from services.analyzer import analyze_video
from services.downloader import download_video
from services.extractor import extract_frames
from services.transcriber import transcribe_audio
from services.youtube_metadata import YouTubeMetadataService

logger = logging.getLogger(__name__)


def translate_to_english(text: str, text_type: str = "text") -> Optional[str]:
    """Translate non-English text to English using GPT-4o.
    
    Args:
        text: Text to translate.
        text_type: Type of text being translated (e.g., "title", "description").
        
    Returns:
        Translated English text, or None if translation fails.
    """
    if not text or not text.strip():
        return None
    
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        prompt = f"Translate the following {text_type} to English. Return ONLY the translated text, nothing else:\n\n{text}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use mini for cost efficiency
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the given text to English accurately and naturally."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        translation = response.choices[0].message.content.strip()
        logger.info(f"Translated {text_type} to English: {translation[:100]}...")
        return translation
    except Exception as e:
        logger.error(f"Translation failed for {text_type}: {e}")
        return None


@celery_app.task(bind=True)
def run_pipeline(self, job_id: str) -> None:
    """Run the complete video analysis pipeline using sync database operations.
    
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
    
    def update_progress(progress: int, status: JobStatus, message: str, error: Optional[str] = None) -> None:
        """Update job progress in database and publish to Redis."""
        try:
            with sync_session_maker() as session:
                result = session.execute(
                    select(Job).where(Job.id == UUID(job_id))
                )
                job = result.scalar_one_or_none()
                
                if job:
                    job.progress = progress
                    job.status = status
                    job.error_message = error
                    job.updated_at = datetime.utcnow()
                    session.commit()
            
            # Publish progress update to Redis for SSE streaming
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
        with sync_session_maker() as session:
            result = session.execute(
                select(Job).where(Job.id == UUID(job_id))
            )
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            youtube_url = job.youtube_url
            disable_transcript = job.disable_transcript
        
        # Step 0: Fetch YouTube metadata (0-5%)
        update_progress(0, JobStatus.DOWNLOADING, "Fetching YouTube metadata...")
        try:
            youtube_service = YouTubeMetadataService()
            metadata = youtube_service.get_video_metadata(youtube_url)
            
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
            with sync_session_maker() as session:
                result = session.execute(
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
                    session.commit()
            
            # Translate to English if not already in English
            if metadata:
                default_language = metadata.get("default_language", "").lower()
                detected_language = metadata.get("detected_language", "").lower()
                
                # Check if video is in English
                is_english = (
                    default_language.startswith("en") or 
                    detected_language.startswith("en") or
                    default_language == "english" or
                    detected_language == "english"
                )
                
                if not is_english:
                    logger.info(f"Job {job_id}: Video is in {default_language or detected_language}, translating to English...")
                    
                    # Translate title
                    video_title = metadata.get("title")
                    if video_title:
                        title_en = translate_to_english(video_title, "title")
                        if title_en:
                            with sync_session_maker() as session:
                                result = session.execute(
                                    select(Job).where(Job.id == UUID(job_id))
                                )
                                job = result.scalar_one_or_none()
                                if job:
                                    job.title_en = title_en
                                    job.updated_at = datetime.utcnow()
                                    session.commit()
                            logger.info(f"Job {job_id}: Translated title to English")
                    
                    # Translate description
                    description = metadata.get("description")
                    if description:
                        description_en = translate_to_english(description, "description")
                        if description_en:
                            with sync_session_maker() as session:
                                result = session.execute(
                                    select(Job).where(Job.id == UUID(job_id))
                                )
                                job = result.scalar_one_or_none()
                                if job:
                                    job.description_en = description_en
                                    job.updated_at = datetime.utcnow()
                                    session.commit()
                            logger.info(f"Job {job_id}: Translated description to English")
                else:
                    logger.info(f"Job {job_id}: Video is already in English, no translation needed")
            
            update_progress(5, JobStatus.DOWNLOADING, f"Metadata fetched: {metadata.get('title', 'Unknown')}")
            logger.info(f"Job {job_id}: YouTube metadata fetched successfully")
            
            # Validate video duration
            duration = metadata.get("duration_seconds", 0)
            if not duration or duration <= 0:
                error_msg = (
                    f"Video has invalid duration ({duration}s). "
                    f"This usually means the video is unavailable, deleted, private, "
                    f"region-locked, a live stream, or has other access restrictions."
                )
                logger.error(f"Job {job_id}: {error_msg}")
                raise DownloadFailedError(error_msg)
            
        except DownloadFailedError:
            raise  # Re-raise to fail the job properly
        except Exception as e:
            logger.error(f"Job {job_id}: Failed to fetch YouTube metadata: {e}")
            raise DownloadFailedError(f"Failed to fetch video metadata: {str(e)}")
        
        # Step 1: Download video (5-15%)
        update_progress(5, JobStatus.DOWNLOADING, "Starting download...")
        # Pass duration from metadata to skip redundant yt-dlp metadata fetch
        duration = metadata.get("duration_seconds") if metadata else None
        video_path, audio_path = download_video(youtube_url, job_id, expected_duration=duration)
        update_progress(15, JobStatus.DOWNLOADING, "Download completed")
        
        # Step 2: Transcribe audio (15-35%) - Skip if disabled
        if disable_transcript:
            logger.info(f"Job {job_id}: Transcription disabled, skipping...")
            update_progress(35, JobStatus.EXTRACTING, "Transcription skipped (disabled)")
            transcript = ""
            whisper_cost = 0
        else:
            update_progress(15, JobStatus.TRANSCRIBING, "Starting transcription...")
            transcription_result = transcribe_audio(audio_path)
            transcript = transcription_result["text"]
            whisper_cost = transcription_result["estimated_cost_usd"]
            update_progress(35, JobStatus.TRANSCRIBING, "Transcription completed")
        
        # Step 3: Extract frames (35-65%)
        update_progress(35, JobStatus.EXTRACTING, "Extracting key frames...")
        frames_result = extract_frames(video_path, job_id)
        frames_data = frames_result["frames"]
        frames_count = frames_result["count"]
        update_progress(65, JobStatus.EXTRACTING, f"Extracted {frames_count} frames")
        
        # Step 4: Analyze with GPT-4o (65-90%)
        update_progress(65, JobStatus.ANALYZING, "Analyzing video content...")
        analysis_result = analyze_video(transcript, frames_data, job_id, metadata)
        gpt_cost = analysis_result.get("ai_metadata", {}).get("estimated_cost_usd", 0)
        total_cost = whisper_cost + gpt_cost
        update_progress(90, JobStatus.ANALYZING, "Analysis completed")
        
        # Step 5: Save results (90-100%)
        update_progress(90, JobStatus.DONE, "Saving results...")
        
        with sync_session_maker() as session:
            result = session.execute(
                select(Job).where(Job.id == UUID(job_id))
            )
            job = result.scalar_one_or_none()
            
            if job:
                job.status = JobStatus.DONE
                job.progress = 100
                job.transcript = transcript
                job.frames_count = frames_count
                
                ai_usage = {
                    "gpt_model": analysis_result["ai_metadata"]["model"],
                    "gpt_prompt_tokens": analysis_result["ai_metadata"]["prompt_tokens"],
                    "gpt_completion_tokens": analysis_result["ai_metadata"]["completion_tokens"],
                    "gpt_total_tokens": analysis_result["ai_metadata"]["total_tokens"],
                    "gpt_cost_usd": gpt_cost,
                    "total_cost_usd": round(total_cost, 4)
                }
                
                # Only add whisper metadata if transcription was enabled
                if not disable_transcript:
                    ai_usage["whisper_model"] = transcription_result["model"]
                    ai_usage["whisper_duration_seconds"] = transcription_result["duration_seconds"]
                    ai_usage["whisper_cost_usd"] = whisper_cost
                else:
                    ai_usage["whisper_cost_usd"] = 0
                
                job.analysis = {
                    "summary": analysis_result,
                    "ai_usage": ai_usage
                }
                job.updated_at = datetime.utcnow()
                session.commit()
        
        update_progress(100, JobStatus.DONE, "Processing completed successfully")
        
        # Trigger embedding generation asynchronously (non-blocking)
        try:
            from tasks.embedding import generate_embedding_task
            generate_embedding_task.delay(job_id)
            logger.info(f"Triggered embedding generation task for job {job_id}")
        except Exception as e:
            # Don't fail the main pipeline if embedding task fails to queue
            logger.warning(f"Could not trigger embedding task: {e}")
        
        # Clean up temporary files
        temp_dir = Path(settings.temp_dir) / job_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")
        
    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {e}", exc_info=True)
        
        error_message = str(e)
        update_progress(0, JobStatus.FAILED, "Processing failed", error=error_message)
        
        # Clean up on failure
        temp_dir = Path(settings.temp_dir) / job_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        raise
