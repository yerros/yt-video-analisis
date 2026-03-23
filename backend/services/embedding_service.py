"""Embedding service for generating and managing vector embeddings."""

import logging
from typing import List, Optional

from openai import AsyncOpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.job import Job, JobStatus

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and searching vector embeddings."""

    def __init__(self):
        """Initialize embedding service."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "text-embedding-3-small"  # 1536 dimensions
        self.dimension = 1536

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_job_embedding(
        self, 
        db: AsyncSession, 
        job_id: str
    ) -> Optional[List[float]]:
        """
        Generate embedding for a job based on its content.
        
        Combines video title, transcript, and analysis into a single text
        that represents the video content for semantic search.
        
        Args:
            db: Database session
            job_id: Job ID to generate embedding for
            
        Returns:
            The generated embedding vector, or None if job not found
        """
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            logger.warning(f"Job {job_id} not found")
            return None
            
        # Build comprehensive text representation of the video
        text_parts = []
        
        if job.video_title:
            text_parts.append(f"Title: {job.video_title}")
        
        # Include YouTube metadata for richer context
        if job.channel_title:
            text_parts.append(f"Channel: {job.channel_title}")
            
        if job.description:
            # Limit description to 500 chars to avoid token limits
            description_snippet = job.description[:500]
            text_parts.append(f"Description: {description_snippet}")
            
        if job.tags and len(job.tags) > 0:
            tags_str = ", ".join(job.tags[:10])  # Limit to first 10 tags
            text_parts.append(f"Tags: {tags_str}")
            
        if job.analysis:
            # Handle nested summary structure
            if summary_data := job.analysis.get("summary"):
                if isinstance(summary_data, dict):
                    if summary_text := summary_data.get("summary"):
                        text_parts.append(f"Summary: {summary_text}")
                    
                    if topics := summary_data.get("topics"):
                        topics_str = ", ".join(topics)
                        text_parts.append(f"Topics: {topics_str}")
                        
                    if key_points := summary_data.get("key_points"):
                        key_points_str = "\n".join(f"- {kp.get('point', kp)}" for kp in key_points)
                        text_parts.append(f"Key Points:\n{key_points_str}")
                        
                    if insights := summary_data.get("insights"):
                        text_parts.append(f"Insights: {insights}")
                else:
                    text_parts.append(f"Summary: {summary_data}")
        
        # Include a portion of transcript (first 2000 chars to avoid token limits)
        if job.transcript:
            transcript_snippet = job.transcript[:2000]
            text_parts.append(f"Transcript excerpt: {transcript_snippet}")
        
        if not text_parts:
            logger.warning(f"Job {job_id} has no content to generate embedding from")
            return None
            
        full_text = "\n\n".join(text_parts)
        
        # Generate and store embedding
        try:
            embedding = await self.generate_embedding(full_text)
            
            # Update job with embedding using ORM
            job.embedding = embedding
            await db.commit()
            await db.refresh(job)
            
            logger.info(f"Generated embedding for job {job_id}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for job {job_id}: {e}")
            await db.rollback()
            return None

    async def search_similar_jobs(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Job]:
        """
        Search for jobs similar to the query using vector similarity.
        
        Uses cosine similarity to find the most relevant videos based on
        semantic meaning rather than keyword matching.
        
        Args:
            db: Database session
            query: Search query text
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1) to include
            
        Returns:
            List of Job objects ordered by similarity (most similar first)
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.generate_embedding(query)
            
            # Perform vector similarity search
            # cosine distance: 1 - cosine_similarity
            # So lower distance = higher similarity
            result = await db.execute(
                text("""
                    SELECT *, 1 - (embedding <=> :query_embedding) as similarity
                    FROM jobs
                    WHERE status = :status
                    AND embedding IS NOT NULL
                    AND 1 - (embedding <=> :query_embedding) >= :threshold
                    ORDER BY embedding <=> :query_embedding
                    LIMIT :limit
                """),
                {
                    "query_embedding": str(query_embedding),
                    "status": JobStatus.DONE.value,
                    "threshold": similarity_threshold,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            
            # Convert rows to Job objects
            jobs = []
            for row in rows:
                job = Job()
                for key, value in row._mapping.items():
                    if key != 'similarity':
                        setattr(job, key, value)
                jobs.append(job)
                logger.info(f"Found job {job.id} with similarity {row.similarity:.3f}")
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to search similar jobs: {e}")
            return []

    async def batch_generate_embeddings(
        self,
        db: AsyncSession,
        status_filter: Optional[JobStatus] = JobStatus.DONE
    ) -> int:
        """
        Generate embeddings for all jobs that don't have one yet.
        
        Useful for backfilling embeddings for existing videos.
        
        Args:
            db: Database session
            status_filter: Only generate for jobs with this status
            
        Returns:
            Number of embeddings generated
        """
        query = select(Job).where(Job.embedding.is_(None))
        
        if status_filter:
            query = query.where(Job.status == status_filter.value)
            
        result = await db.execute(query)
        jobs = list(result.scalars().all())
        
        logger.info(f"Found {len(jobs)} jobs without embeddings")
        
        count = 0
        for job in jobs:
            try:
                # Build text representation
                text_parts = []
                
                if job.video_title:
                    text_parts.append(f"Title: {job.video_title}")
                
                # Include YouTube metadata for richer context
                if job.channel_title:
                    text_parts.append(f"Channel: {job.channel_title}")
                    
                if job.description:
                    # Limit description to 500 chars to avoid token limits
                    description_snippet = job.description[:500]
                    text_parts.append(f"Description: {description_snippet}")
                    
                if job.tags and len(job.tags) > 0:
                    tags_str = ", ".join(job.tags[:10])  # Limit to first 10 tags
                    text_parts.append(f"Tags: {tags_str}")
                    
                if job.analysis:
                    # Handle nested summary structure
                    if summary_data := job.analysis.get("summary"):
                        if isinstance(summary_data, dict):
                            if summary_text := summary_data.get("summary"):
                                text_parts.append(f"Summary: {summary_text}")
                            
                            if topics := summary_data.get("topics"):
                                topics_str = ", ".join(topics)
                                text_parts.append(f"Topics: {topics_str}")
                                
                            if key_points := summary_data.get("key_points"):
                                key_points_str = "\n".join(f"- {kp.get('point', kp)}" for kp in key_points)
                                text_parts.append(f"Key Points:\n{key_points_str}")
                                
                            if insights := summary_data.get("insights"):
                                text_parts.append(f"Insights: {insights}")
                        else:
                            text_parts.append(f"Summary: {summary_data}")
                
                if job.transcript:
                    transcript_snippet = job.transcript[:2000]
                    text_parts.append(f"Transcript excerpt: {transcript_snippet}")
                
                if not text_parts:
                    logger.warning(f"Job {job.id} has no content to generate embedding from")
                    continue
                    
                full_text = "\n\n".join(text_parts)
                
                # Generate embedding
                embedding = await self.generate_embedding(full_text)
                
                # Update job
                job.embedding = embedding
                await db.commit()
                
                logger.info(f"✓ Generated embedding for job {job.id} ({job.video_title[:50]}...)")
                count += 1
                
            except Exception as e:
                logger.error(f"✗ Failed to generate embedding for job {job.id}: {e}")
                await db.rollback()
                continue
                
        logger.info(f"Generated {count} embeddings total")
        return count


# Dependency for FastAPI
async def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance."""
    return EmbeddingService()
