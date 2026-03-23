"""Pydantic schemas for job API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class JobCreate(BaseModel):
    """Schema for creating a new job."""

    youtube_url: HttpUrl = Field(..., description="YouTube video URL")
    disable_transcript: bool = Field(True, description="Skip audio transcription to save time and costs")


class JobResponse(BaseModel):
    """Schema for job response."""

    id: UUID
    youtube_url: str
    video_title: Optional[str] = None
    video_duration: Optional[int] = None
    status: str
    progress: int
    transcript: Optional[str] = None
    frames_count: Optional[int] = None
    analysis: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # YouTube metadata fields
    youtube_metadata: Optional[Dict[str, Any]] = None
    channel_title: Optional[str] = None
    channel_id: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = None
    published_at: Optional[datetime] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    
    # English translations
    title_en: Optional[str] = None
    description_en: Optional[str] = None
    
    # Processing options
    disable_transcript: Optional[bool] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for job list response."""

    items: List[JobResponse]
    total: int
    limit: int
    offset: int


class JobProgressEvent(BaseModel):
    """Schema for job progress SSE event."""

    status: str
    progress: int
    message: str
