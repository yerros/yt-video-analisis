"""Chat API routes."""

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionListResponse,
    ChatSessionResponse,
)
from services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    """Get chat service instance."""
    return ChatService()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_chat_session(
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Create a new chat session.
    
    Returns:
        New chat session
    """
    try:
        session = await chat_service.create_session(db)
        return session
    except Exception as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=list[ChatSessionListResponse])
async def list_chat_sessions(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """List all chat sessions.
    
    Args:
        limit: Maximum number of sessions to return
        
    Returns:
        List of chat sessions
    """
    try:
        sessions = await chat_service.list_sessions(db, limit=limit)
        return sessions
    except Exception as e:
        logger.error(f"Failed to list chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get chat session by ID with all messages.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Chat session with messages
    """
    try:
        session = await chat_service.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/stream")
async def chat_stream(
    request: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Stream chat response with video knowledge context.
    
    Args:
        request: Chat message request
        
    Returns:
        Server-sent events stream with chat response
    """
    async def event_generator():
        try:
            async for chunk in chat_service.chat_stream(
                db=db,
                message=request.content,
                session_id=request.session_id
            ):
                # Format as SSE with proper JSON encoding
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {str(e)}")
            error_data = {
                "error": str(e),
                "done": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_chat_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Delete a chat session and all its messages.
    
    Args:
        session_id: Session UUID
    """
    try:
        session = await chat_service.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        await db.delete(session)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
