"""
Test script for vector similarity search.

Tests semantic search functionality by searching for videos
using natural language queries.

Usage:
    python -m scripts.test_vector_search
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from services.embedding_service import EmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_search(query: str):
    """Test semantic search with a query."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Query: '{query}'")
    logger.info(f"{'='*60}")
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Initialize embedding service
    embedding_service = EmbeddingService()
    
    try:
        async with async_session() as session:
            # Search for similar videos
            jobs = await embedding_service.search_similar_jobs(
                db=session,
                query=query,
                limit=3,
                similarity_threshold=0.3  # Lower threshold for testing
            )
            
            if not jobs:
                logger.info("❌ No similar videos found")
            else:
                logger.info(f"✅ Found {len(jobs)} similar video(s):\n")
                for idx, job in enumerate(jobs, 1):
                    logger.info(f"{idx}. Title: {job.video_title or 'No title'}")
                    logger.info(f"   ID: {job.id}")
                    if job.analysis and "summary" in job.analysis:
                        summary_data = job.analysis["summary"]
                        if isinstance(summary_data, dict):
                            summary_text = summary_data.get("summary", "No summary")[:200]
                            topics = summary_data.get("topics", [])
                            logger.info(f"   Summary: {summary_text}...")
                            logger.info(f"   Topics: {', '.join(topics)}")
                    logger.info("")
                    
    except Exception as e:
        logger.error(f"❌ Search failed: {e}", exc_info=True)
    finally:
        await engine.dispose()


async def main():
    """Run multiple search tests."""
    test_queries = [
        "animals and wildlife",
        "elephants at the zoo",
        "music videos",
        "toys and marble runs",
        "funny content",
    ]
    
    for query in test_queries:
        await test_search(query)
        await asyncio.sleep(1)  # Rate limiting


if __name__ == "__main__":
    asyncio.run(main())
