"""Audio transcription service using OpenAI Whisper API."""

import logging
from pathlib import Path
from typing import Dict, Any

from openai import OpenAI

from core.config import settings
from core.exceptions import TranscriptionFailedError

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: Path) -> Dict[str, Any]:
    """Transcribe audio file to text using OpenAI Whisper API.
    
    Args:
        audio_path: Path to audio file.
        
    Returns:
        Dictionary containing:
        - text: Transcribed text
        - duration_seconds: Audio duration
        - model: Whisper model used
        - estimated_cost_usd: Estimated cost
        
    Raises:
        TranscriptionFailedError: If transcription fails.
    """
    try:
        if not audio_path.exists():
            raise TranscriptionFailedError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Starting transcription of {audio_path}")
        
        # Get audio duration
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
            capture_output=True,
            text=True
        )
        duration_seconds = float(result.stdout.strip()) if result.stdout.strip() else 0
        
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Transcribe using OpenAI Whisper API
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        # OpenAI returns the text directly when using response_format="text"
        text = str(transcript).strip()
        
        if not text:
            raise TranscriptionFailedError("Transcription produced empty text")
        
        # Calculate cost (Whisper pricing: $0.006 per minute)
        duration_minutes = duration_seconds / 60
        estimated_cost = duration_minutes * 0.006
        
        logger.info(
            f"Transcription completed: {len(text)} characters, "
            f"{duration_seconds:.1f}s, cost: ${estimated_cost:.4f}"
        )
        
        return {
            "text": text,
            "duration_seconds": round(duration_seconds, 2),
            "model": "whisper-1",
            "estimated_cost_usd": round(estimated_cost, 4)
        }
        
    except TranscriptionFailedError:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise TranscriptionFailedError(f"Failed to transcribe audio: {str(e)}")
