"""Database models for jobs."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from db.session import Base


class JobStatus(str, Enum):
    """Job status enum."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    DONE = "done"
    FAILED = "failed"


class Job(Base):
    """Job model representing a video analysis task."""

    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    youtube_url = Column(Text, nullable=False)
    video_title = Column(Text, nullable=True)
    video_duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # YouTube Metadata (from YouTube Data API v3)
    youtube_metadata = Column(JSON, nullable=True)  # Complete YouTube metadata
    channel_title = Column(Text, nullable=True)
    channel_id = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    category_id = Column(String(50), nullable=True)
    published_at = Column(DateTime, nullable=True)
    view_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    comment_count = Column(Integer, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    
    # English translations for non-English content
    title_en = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    
    # Processing options
    disable_transcript = Column(Boolean, nullable=False, default=False)
    
    status = Column(String(20), nullable=False, default=JobStatus.PENDING.value)
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    transcript = Column(Text, nullable=True)
    frames_count = Column(Integer, nullable=True)
    analysis = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)  # Vector embedding for semantic search
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Job(id={self.id}, status={self.status}, url={self.youtube_url})>"
