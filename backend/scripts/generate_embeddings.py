"""
Script to generate embeddings for existing videos in the database.

This script will:
1. Find all completed jobs that don't have embeddings
2. Generate embeddings for each video based on title, transcript, and analysis
3. Store the embeddings in the database

Usage:
    python -m scripts.generate_embeddings
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


async def main():
    """Generate embeddings for all existing videos."""
    logger.info("Starting embedding generation...")
    
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )
    
    # Create session factory
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    # Initialize embedding service
    embedding_service = EmbeddingService()
    
    try:
        async with async_session() as session:
            # Generate embeddings for all completed jobs
            count = await embedding_service.batch_generate_embeddings(session)
            logger.info(f"✓ Successfully generated {count} embeddings")
            
    except Exception as e:
        logger.error(f"✗ Failed to generate embeddings: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await engine.dispose()
    
    logger.info("Embedding generation complete!")


if __name__ == "__main__":
    asyncio.run(main())
