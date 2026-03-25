"""Core configuration settings."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI
    openai_api_key: str

    # YouTube Data API
    youtube_api_key: str

    # Supabase Storage
    supabase_url: str
    supabase_key: str

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Application
    temp_dir: str = "/tmp/video-analysis"
    storage_dir: str = str(Path(__file__).parent.parent / "storage")
    max_video_duration: int = 1800  # 30 minutes in seconds
    max_frames: int = 30
    
    # yt-dlp
    youtube_cookies_path: str = ""  # Optional: Path to cookies.txt file for YouTube authentication
    youtube_cookies_browser: str = "chrome"  # Browser to extract cookies from (chrome, firefox, edge, safari, etc.)

    # Whisper
    whisper_model: str = "mlx-community/whisper-large-v3-mlx"
    
    # GPT Model
    gpt_model: str = "gpt-4o"

    class Config:
        """Pydantic config."""

        # Look for .env in project root (parent of backend/)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields like NEXT_PUBLIC_API_URL


settings = Settings()
