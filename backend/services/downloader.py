"""Video downloader service using yt-dlp."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Tuple

from core.config import settings
from core.exceptions import DownloadFailedError, VideoTooLongError

logger = logging.getLogger(__name__)


def download_video(youtube_url: str, job_id: str) -> Tuple[Path, Path]:
    """Download video from YouTube and extract audio using system yt-dlp.
    
    Args:
        youtube_url: YouTube video URL.
        job_id: Job UUID for organizing temp files.
        
    Returns:
        Tuple of (video_path, audio_path).
        
    Raises:
        VideoTooLongError: If video duration exceeds max_video_duration.
        DownloadFailedError: If download fails.
    """
    temp_dir = Path(settings.temp_dir) / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    video_output = temp_dir / "video.mp4"
    audio_output = temp_dir / "audio.mp3"
    
    # Use system yt-dlp binary (works better with JS challenges)
    yt_dlp_bin = "/opt/homebrew/bin/yt-dlp"
    
    # Base command args - simple approach to avoid bot detection
    # Processing one video at a time with delays is more reliable than cookies
    base_args = [
        yt_dlp_bin,
        "--extractor-retries", "3",
        "--fragment-retries", "3",
        "--retry-sleep", "exp=1:5",  # Exponential backoff from 1 to 5 seconds
    ]
    
    try:
        # First, get video info to check duration (with retry)
        logger.info(f"Getting video info for {youtube_url}")
        max_retries = 3
        retry_delay = 2
        result = None
        
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    base_args + ["--dump-json", youtube_url],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
                break
            except subprocess.CalledProcessError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        
        if result is None:
            raise DownloadFailedError("Failed to get video info after retries")
        
        import json
        info = json.loads(result.stdout)
        duration = info.get("duration", 0)
        
        if duration and duration > settings.max_video_duration:
            raise VideoTooLongError(
                f"Video duration ({duration}s) exceeds maximum allowed "
                f"({settings.max_video_duration}s)"
            )
        
        logger.info(
            f"Video info: title={info.get('title')}, duration={duration}s"
        )
        
        # Download video
        logger.info(f"Downloading video from {youtube_url}")
        subprocess.run(
            base_args + [
                "-f", "best[ext=mp4]/best",
                "-o", str(video_output),
                youtube_url,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout
        )
        
        # Extract audio
        logger.info(f"Extracting audio from {youtube_url}")
        subprocess.run(
            base_args + [
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "192",
                "-o", str(audio_output.with_suffix("")),
                youtube_url,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
        
        if not video_output.exists() or not audio_output.exists():
            raise DownloadFailedError(
                f"Download completed but files not found: "
                f"video={video_output.exists()}, audio={audio_output.exists()}"
            )
        
        logger.info(f"Download completed: video={video_output}, audio={audio_output}")
        return video_output, audio_output
        
    except VideoTooLongError:
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed: {e.stderr}")
        raise DownloadFailedError(f"Failed to download video: {e.stderr}")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise DownloadFailedError(f"Failed to download video: {str(e)}")
