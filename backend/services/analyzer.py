"""AI analysis service using OpenAI GPT-4o."""

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

from core.config import settings
from core.exceptions import AnalysisFailedError

logger = logging.getLogger(__name__)


def analyze_video(
    transcript: str, 
    frames_data: List[Dict[str, Any]], 
    job_id: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Analyze video content using GPT-4o multimodal API.
    
    Args:
        transcript: Full transcript of the video audio.
        frames_data: List of frame metadata dicts containing path, timestamp, etc.
        job_id: Job UUID for reconstructing frame paths.
        metadata: YouTube metadata containing video info (title, description, etc.)
        
    Returns:
        Analysis results as structured JSON containing:
        - summary: Brief summary of video content
        - topics: List of main topics
        - key_points: List of key points with timestamps
        - sentiment: Overall sentiment (positive/neutral/negative)
        - language: Detected language
        - content_type: Type of content (tutorial/vlog/news/etc)
        - insights: Detailed analysis
        - frames: List of analyzed frames with metadata
        - ai_metadata: Information about AI usage (model, tokens, cost)
        
    Raises:
        AnalysisFailedError: If analysis fails.
    """
    try:
        # Check if we have transcript (can be empty if transcription was disabled)
        has_transcript = transcript and transcript.strip()
        
        if not has_transcript:
            logger.warning("Transcript is empty - analysis will be visual-only")
        
        if not frames_data:
            raise AnalysisFailedError("No frames provided for analysis")
        
        transcript_info = f"{len(transcript)} characters of transcript" if has_transcript else "no transcript (visual-only)"
        logger.info(
            f"Starting GPT-4o analysis with {len(frames_data)} frames "
            f"and {transcript_info}"
        )
        
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Prepare image content for GPT-4o
        image_contents = []
        analyzed_frames = []
        
        for frame_meta in frames_data[:settings.max_frames]:  # Respect max frames limit
            # Reconstruct actual file path from storage
            frame_path = Path(settings.storage_dir) / "frames" / job_id / frame_meta["filename"]
            
            if not frame_path.exists():
                logger.warning(f"Frame not found: {frame_path}")
                continue
            
            # Encode image to base64
            with open(frame_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode("utf-8")
            
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_data}",
                    "detail": "low"  # Use low detail to reduce token usage
                }
            })
            
            # Keep track of analyzed frames with their metadata
            analyzed_frames.append(frame_meta)
        
        if not image_contents:
            raise AnalysisFailedError("No valid frames found for analysis")
        
        # Build metadata context if available
        metadata_context = ""
        if metadata:
            metadata_parts = []
            
            if metadata.get("title"):
                metadata_parts.append(f"Title: {metadata['title']}")
            
            if metadata.get("channel_title"):
                metadata_parts.append(f"Channel: {metadata['channel_title']}")
            
            if metadata.get("description"):
                # Truncate description if too long
                desc = metadata["description"][:500]
                if len(metadata["description"]) > 500:
                    desc += "..."
                metadata_parts.append(f"Description: {desc}")
            
            if metadata.get("tags"):
                tags_str = ", ".join(metadata["tags"][:10])  # Limit tags
                metadata_parts.append(f"Tags: {tags_str}")
            
            if metadata.get("view_count"):
                metadata_parts.append(f"Views: {metadata['view_count']:,}")
            
            if metadata.get("like_count"):
                metadata_parts.append(f"Likes: {metadata['like_count']:,}")
            
            if metadata.get("published_at"):
                pub_date = str(metadata["published_at"])[:10]  # Just the date
                metadata_parts.append(f"Published: {pub_date}")
            
            if metadata_parts:
                metadata_context = "\n\nYOUTUBE VIDEO METADATA:\n" + "\n".join(metadata_parts)
        
        # Prepare prompt with metadata context
        # Handle case where transcript is not available
        if has_transcript:
            transcript_section = f"""
TRANSCRIPT:
{transcript}
"""
            analysis_note = "Analyze this video based on the provided frames, transcript, and metadata."
        else:
            transcript_section = "\nNOTE: Audio transcription was not available for this video. Base your analysis on visual content and metadata only."
            analysis_note = "Analyze this video based on the provided frames and metadata (no audio transcript available)."
        
        prompt = f"""You are an expert video content analyst. {analysis_note}
{metadata_context}
{transcript_section}

Please provide a comprehensive analysis in JSON format with the following structure:
{{
    "summary": "A 2-3 sentence summary of the video content",
    "topics": ["topic1", "topic2", "topic3"],
    "key_points": [
        {{"point": "description", "timestamp": "approximate time or 'N/A'"}},
    ],
    "sentiment": "positive/neutral/negative",
    "language": "detected language",
    "content_type": "tutorial/vlog/news/entertainment/educational/etc",
    "insights": "Detailed analysis including visual elements, presentation style, target audience, and quality. Consider the video's metadata context for deeper insights."
}}

Be thorough and analytical. Consider visual content{"" if not has_transcript else ", audio content,"} and video metadata."""

        # Build messages with text and images
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_contents
                ]
            }
        ]
        
        # Call GPT-4o API
        logger.info("Calling GPT-4o API...")
        response = client.chat.completions.create(
            model=settings.gpt_model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        
        # Extract token usage
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0
        
        # Calculate cost (GPT-4o pricing as of 2024)
        # Input: $5 per 1M tokens, Output: $15 per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * 5.0
        output_cost = (completion_tokens / 1_000_000) * 15.0
        total_cost = input_cost + output_cost
        
        logger.info(
            f"Token usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, "
            f"Total: {total_tokens}, Estimated cost: ${total_cost:.4f}"
        )
        
        # Extract and parse response
        result_text = response.choices[0].message.content
        
        if not result_text:
            raise AnalysisFailedError("GPT-4o returned empty response")
        
        logger.info("GPT-4o analysis completed successfully")
        
        # Parse JSON response
        import json
        result = json.loads(result_text)
        
        # Validate required fields
        required_fields = ["summary", "topics", "key_points", "sentiment", "language", "content_type", "insights"]
        for field in required_fields:
            if field not in result:
                logger.warning(f"Missing field in analysis result: {field}")
                result[field] = "N/A" if isinstance(result.get(field), str) else []
        
        # Add analyzed frames to result
        result["frames"] = analyzed_frames
        
        # Add AI metadata
        result["ai_metadata"] = {
            "model": settings.gpt_model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(total_cost, 4)
        }
        
        return result
        
    except AnalysisFailedError:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise AnalysisFailedError(f"Failed to analyze video: {str(e)}")
