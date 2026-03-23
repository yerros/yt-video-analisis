"""Pydantic schemas for chat system."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""

    content: str = Field(..., min_length=1, description="Message content")
    session_id: Optional[UUID] = Field(None, description="Chat session ID, if continuing existing conversation")


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""

    id: UUID
    session_id: UUID
    role: str
    content: str
    referenced_jobs: Optional[list[UUID]] = None
    token_usage: Optional[dict[str, int]] = None
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""

    id: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []

    class Config:
        """Pydantic config."""
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """Schema for chat session list item."""

    id: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        """Pydantic config."""
        from_attributes = True


class StreamChatResponse(BaseModel):
    """Schema for streaming chat response."""

    session_id: UUID
    message_id: UUID
    content: str
    done: bool = False
    referenced_jobs: Optional[list[UUID]] = None
    token_usage: Optional[dict[str, int]] = None
