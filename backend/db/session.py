"""Database session configuration."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from core.config import settings

# Create async engine for FastAPI
engine = create_async_engine(
    settings.database_url,
    echo=True,
    future=True,
)

# Create sync engine for Celery (convert asyncpg to psycopg2)
sync_database_url = settings.database_url.replace("+asyncpg", "").replace("postgresql", "postgresql+psycopg2")
sync_engine = create_engine(
    sync_database_url,
    echo=True,
    future=True,
)

# Create async session factory for FastAPI
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync session factory for Celery
SyncSessionLocal = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
)

# Alias for Celery tasks (keep old name for backwards compatibility)
async_session_maker = AsyncSessionLocal
sync_session_maker = SyncSessionLocal

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> Session:
    """Get synchronous database session for Celery tasks."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
