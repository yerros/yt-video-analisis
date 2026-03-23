"""API endpoints for usage statistics."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.job import Job, JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/usage")
async def get_usage_statistics(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get overall usage statistics across all jobs.
    
    Returns:
        Statistics including:
        - Total jobs processed
        - Total tokens used (Whisper + GPT-4o)
        - Total cost (USD)
        - Breakdown by model
        - Average cost per job
    """
    try:
        # Get all completed jobs with analysis data
        result = await db.execute(
            select(Job).where(Job.status == JobStatus.DONE)
        )
        jobs = result.scalars().all()
        
        # Initialize counters
        total_jobs = len(jobs)
        total_whisper_duration = 0.0
        total_whisper_cost = 0.0
        total_gpt_prompt_tokens = 0
        total_gpt_completion_tokens = 0
        total_gpt_total_tokens = 0
        total_gpt_cost = 0.0
        total_embedding_tokens = 0
        total_embedding_cost = 0.0
        total_cost = 0.0
        
        jobs_with_usage = 0
        jobs_with_embeddings = 0
        total_frames_extracted = 0
        
        # Aggregate statistics
        for job in jobs:
            if job.analysis and 'ai_usage' in job.analysis:
                ai_usage = job.analysis['ai_usage']
                jobs_with_usage += 1
                
                # Whisper stats
                whisper_duration = ai_usage.get('whisper_duration_seconds', 0)
                whisper_cost = ai_usage.get('whisper_cost_usd', 0)
                total_whisper_duration += whisper_duration
                total_whisper_cost += whisper_cost
                
                # GPT-4o stats
                gpt_prompt = ai_usage.get('gpt_prompt_tokens', 0)
                gpt_completion = ai_usage.get('gpt_completion_tokens', 0)
                gpt_total = ai_usage.get('gpt_total_tokens', 0)
                gpt_cost = ai_usage.get('gpt_cost_usd', 0)
                
                total_gpt_prompt_tokens += gpt_prompt
                total_gpt_completion_tokens += gpt_completion
                total_gpt_total_tokens += gpt_total
                total_gpt_cost += gpt_cost
                
                # Total cost
                job_total_cost = ai_usage.get('total_cost_usd', 0)
                total_cost += job_total_cost
            
            # Count frames
            if job.frames_count:
                total_frames_extracted += job.frames_count
            
            # Count embeddings (estimate cost)
            if job.embedding is not None:
                jobs_with_embeddings += 1
                # text-embedding-3-small: $0.00002 per 1K tokens
                # Estimate ~500 tokens per embedding based on content length
                estimated_tokens = 500
                total_embedding_tokens += estimated_tokens
                total_embedding_cost += (estimated_tokens / 1000) * 0.00002
        
        # Calculate averages
        avg_cost_per_job = total_cost / jobs_with_usage if jobs_with_usage > 0 else 0
        avg_whisper_duration = total_whisper_duration / jobs_with_usage if jobs_with_usage > 0 else 0
        avg_frames_per_job = total_frames_extracted / total_jobs if total_jobs > 0 else 0
        
        # Add embedding cost to total
        total_cost_with_embeddings = total_cost + total_embedding_cost
        
        # Get failed jobs count
        failed_result = await db.execute(
            select(func.count(Job.id)).where(Job.status == JobStatus.FAILED)
        )
        total_failed = failed_result.scalar() or 0
        
        # Get pending/processing jobs count
        processing_result = await db.execute(
            select(func.count(Job.id)).where(
                Job.status.in_([
                    JobStatus.PENDING,
                    JobStatus.DOWNLOADING,
                    JobStatus.TRANSCRIBING,
                    JobStatus.EXTRACTING,
                    JobStatus.ANALYZING
                ])
            )
        )
        total_processing = processing_result.scalar() or 0
        
        return {
            "overview": {
                "total_jobs_completed": total_jobs,
                "total_jobs_failed": total_failed,
                "total_jobs_processing": total_processing,
                "jobs_with_ai_usage": jobs_with_usage,
                "total_frames_extracted": total_frames_extracted,
                "avg_frames_per_job": round(avg_frames_per_job, 1)
            },
            "whisper": {
                "total_duration_seconds": round(total_whisper_duration, 2),
                "total_duration_minutes": round(total_whisper_duration / 60, 2),
                "total_cost_usd": round(total_whisper_cost, 4),
                "avg_duration_per_job_seconds": round(avg_whisper_duration, 2),
                "model": "whisper-1"
            },
            "gpt4o": {
                "total_prompt_tokens": total_gpt_prompt_tokens,
                "total_completion_tokens": total_gpt_completion_tokens,
                "total_tokens": total_gpt_total_tokens,
                "total_cost_usd": round(total_gpt_cost, 4),
                "avg_tokens_per_job": round(total_gpt_total_tokens / jobs_with_usage, 0) if jobs_with_usage > 0 else 0,
                "model": "gpt-4o"
            },
            "embeddings": {
                "total_embeddings_generated": jobs_with_embeddings,
                "total_tokens": total_embedding_tokens,
                "total_cost_usd": round(total_embedding_cost, 4),
                "model": "text-embedding-3-small"
            },
            "total": {
                "total_cost_usd": round(total_cost_with_embeddings, 4),
                "avg_cost_per_job_usd": round(avg_cost_per_job, 4),
                "cost_breakdown": {
                    "whisper_percentage": round((total_whisper_cost / total_cost_with_embeddings * 100) if total_cost_with_embeddings > 0 else 0, 1),
                    "gpt4o_percentage": round((total_gpt_cost / total_cost_with_embeddings * 100) if total_cost_with_embeddings > 0 else 0, 1),
                    "embeddings_percentage": round((total_embedding_cost / total_cost_with_embeddings * 100) if total_cost_with_embeddings > 0 else 0, 1)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage statistics: {e}")
        # Return empty statistics on error
        return {
            "overview": {
                "total_jobs_completed": 0,
                "total_jobs_failed": 0,
                "total_jobs_processing": 0,
                "jobs_with_ai_usage": 0,
                "total_frames_extracted": 0,
                "avg_frames_per_job": 0
            },
            "whisper": {
                "total_duration_seconds": 0,
                "total_duration_minutes": 0,
                "total_cost_usd": 0,
                "avg_duration_per_job_seconds": 0,
                "model": "whisper-1"
            },
            "gpt4o": {
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "avg_tokens_per_job": 0,
                "model": "gpt-4o"
            },
            "embeddings": {
                "total_embeddings_generated": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "model": "text-embedding-3-small"
            },
            "total": {
                "total_cost_usd": 0,
                "avg_cost_per_job_usd": 0,
                "cost_breakdown": {
                    "whisper_percentage": 0,
                    "gpt4o_percentage": 0,
                    "embeddings_percentage": 0
                }
            }
        }
