"""Chat service with video knowledge base."""

import json
import logging
import uuid
from typing import Any, AsyncGenerator, Optional

from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import settings
from core.exceptions import ChatError
from models.chat import ChatMessage, ChatSession, MessageRole
from models.job import Job, JobStatus
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat with video knowledge base."""

    def __init__(self):
        """Initialize chat service."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o"  # Using GPT-4o for multimodal understanding
        self.embedding_service = EmbeddingService()
        
    async def create_session(self, db: AsyncSession) -> ChatSession:
        """Create a new chat session.
        
        Args:
            db: Database session
            
        Returns:
            Created chat session
        """
        session = ChatSession()
        db.add(session)
        await db.commit()
        await db.refresh(session, ["messages"])  # Explicitly load messages relationship
        return session
    
    async def get_session(self, db: AsyncSession, session_id: uuid.UUID) -> Optional[ChatSession]:
        """Get chat session by ID.
        
        Args:
            db: Database session
            session_id: Session UUID
            
        Returns:
            Chat session or None
        """
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(selectinload(ChatSession.messages))
        )
        return result.scalar_one_or_none()
    
    async def list_sessions(self, db: AsyncSession, limit: int = 50) -> list[dict[str, Any]]:
        """List all chat sessions with message count.
        
        Args:
            db: Database session
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions with metadata
        """
        result = await db.execute(
            select(
                ChatSession,
                func.count(ChatMessage.id).label("message_count")
            )
            .outerjoin(ChatMessage, ChatSession.id == ChatMessage.session_id)
            .group_by(ChatSession.id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        
        sessions = []
        for session, message_count in result:
            sessions.append({
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "message_count": message_count or 0
            })
        
        return sessions
    
    async def get_relevant_videos(
        self, 
        db: AsyncSession, 
        query: str, 
        limit: int = 5
    ) -> list[Job]:
        """Get relevant videos from knowledge base based on query using semantic search.
        
        Uses vector embeddings for semantic similarity search to find the most
        relevant videos based on the meaning of the query, not just keywords.
        
        Args:
            db: Database session
            query: User query
            limit: Maximum number of videos to return
            
        Returns:
            List of relevant jobs ordered by similarity
        """
        # Use embedding service for semantic search
        jobs = await self.embedding_service.search_similar_jobs(
            db=db,
            query=query,
            limit=limit,
            similarity_threshold=0.5  # Lower threshold to get more results
        )
        
        # If no semantic matches found, fall back to recent videos
        if not jobs:
            logger.info("No semantic matches found, returning recent videos")
            result = await db.execute(
                select(Job)
                .where(Job.status == JobStatus.DONE.value)
                .where(Job.analysis.isnot(None))
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            jobs = list(result.scalars().all())
        
        return jobs
    
    def _build_knowledge_context(self, jobs: list[Job]) -> str:
        """Build context string from video knowledge base.
        
        Args:
            jobs: List of jobs to use as context
            
        Returns:
            Formatted context string
        """
        if not jobs:
            return ""
        
        context_parts = ["Here are the analyzed YouTube videos in my knowledge base:\n"]
        
        for idx, job in enumerate(jobs, 1):
            analysis = job.analysis.get("summary", {}) if job.analysis else {}
            
            context_parts.append(f"\n--- Video {idx} ---")
            context_parts.append(f"URL: {job.youtube_url}")
            context_parts.append(f"Title: {job.video_title or 'Unknown'}")
            
            # Add YouTube metadata for richer context
            if job.channel_title:
                context_parts.append(f"Channel: {job.channel_title}")
            
            if job.published_at:
                context_parts.append(f"Published: {job.published_at}")
            
            if job.view_count is not None:
                context_parts.append(f"Views: {job.view_count:,}")
            
            if job.like_count is not None:
                context_parts.append(f"Likes: {job.like_count:,}")
            
            if job.description:
                # Include first 200 chars of description
                description_snippet = job.description[:200]
                context_parts.append(f"Description: {description_snippet}...")
            
            if job.tags and len(job.tags) > 0:
                tags_str = ", ".join(job.tags[:5])  # First 5 tags
                context_parts.append(f"Tags: {tags_str}")
            
            if analysis:
                context_parts.append(f"Summary: {analysis.get('summary', 'N/A')}")
                context_parts.append(f"Topics: {', '.join(analysis.get('topics', []))}")
                context_parts.append(f"Content Type: {analysis.get('content_type', 'N/A')}")
                context_parts.append(f"Sentiment: {analysis.get('sentiment', 'N/A')}")
                
                # Add key points
                key_points = analysis.get('key_points', [])
                if key_points:
                    context_parts.append("Key Points:")
                    for kp in key_points[:5]:  # Limit to 5 key points
                        context_parts.append(f"  - {kp.get('point', '')}")
            
            # Add transcript excerpt
            if job.transcript:
                transcript_excerpt = job.transcript[:500]  # First 500 chars
                context_parts.append(f"Transcript Excerpt: {transcript_excerpt}...")
        
        return "\n".join(context_parts)
    
    def _get_system_prompt(self, knowledge_context: str) -> str:
        """Get system prompt for YouTube Analysis Expert chatbot.
        
        Args:
            knowledge_context: Context from video knowledge base
            
        Returns:
            System prompt
        """
        base_prompt = """You are a YouTube Analysis Expert AI assistant. You have access to a knowledge base of analyzed YouTube videos including their transcripts, summaries, topics, key points, and insights.

Your capabilities:
- Analyze video content and provide insights
- Answer questions about specific videos
- Compare multiple videos
- Identify trends and patterns across videos
- Provide recommendations based on video content
- Explain video topics in detail

Guidelines:
- Always cite specific videos when providing information
- Use video titles and URLs when referencing content
- Be accurate and base your responses on the actual video data
- If information is not in the knowledge base, clearly state that
- Provide timestamp references when available
- Give detailed, helpful responses focused on video analysis

"""
        
        if knowledge_context:
            return base_prompt + "\n" + knowledge_context
        else:
            return base_prompt + "\nNote: The knowledge base is currently empty. No videos have been analyzed yet."
    
    async def chat_stream(
        self,
        db: AsyncSession,
        message: str,
        session_id: Optional[uuid.UUID] = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chat response with video knowledge context.
        
        Args:
            db: Database session
            message: User message
            session_id: Optional session ID to continue conversation
            
        Yields:
            Chunks of chat response
        """
        try:
            # Get or create session
            if session_id:
                session = await self.get_session(db, session_id)
                if not session:
                    raise ChatError(f"Session {session_id} not found")
            else:
                session = await self.create_session(db)
            
            # Get relevant videos from knowledge base
            relevant_jobs = await self.get_relevant_videos(db, message)
            knowledge_context = self._build_knowledge_context(relevant_jobs)
            
            # Build message history
            messages = [
                {"role": "system", "content": self._get_system_prompt(knowledge_context)}
            ]
            
            # Add previous messages from session
            if session.messages:
                for msg in session.messages[-10:]:  # Last 10 messages for context
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # Save user message
            user_message = ChatMessage(
                session_id=session.id,
                role=MessageRole.USER.value,
                content=message
            )
            db.add(user_message)
            await db.commit()
            
            # Generate session title from first message
            if not session.title and len(session.messages) == 0:
                session.title = message[:100] + "..." if len(message) > 100 else message
                await db.commit()
            
            # Stream response from OpenAI
            response_content = ""
            message_id = uuid.uuid4()
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    response_content += content_chunk
                    
                    yield {
                        "session_id": str(session.id),
                        "message_id": str(message_id),
                        "content": content_chunk,
                        "done": False
                    }
            
            # Save assistant message
            assistant_message = ChatMessage(
                id=message_id,
                session_id=session.id,
                role=MessageRole.ASSISTANT.value,
                content=response_content,
                referenced_jobs=[str(job.id) for job in relevant_jobs] if relevant_jobs else None
            )
            db.add(assistant_message)
            await db.commit()
            
            # Send final chunk with metadata
            yield {
                "session_id": str(session.id),
                "message_id": str(message_id),
                "content": "",
                "done": True,
                "referenced_jobs": [str(job.id) for job in relevant_jobs] if relevant_jobs else None
            }
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise ChatError(f"Failed to generate response: {str(e)}")
