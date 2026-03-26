"""Video downloader service using yt-dlp."""

import logging
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy import select

from core.config import settings
from core.exceptions import DownloadFailedError, VideoTooLongError
from db.session import sync_session_maker
from models.job import Job

logger = logging.getLogger(__name__)


def _update_job_progress(job_id: str, progress: int, message: Optional[str] = None):
    """Update job progress in database.
    
    Args:
        job_id: Job UUID
        progress: Progress percentage (0-100)
        message: Optional progress message
    """
    try:
        with sync_session_maker() as session:
            stmt = select(Job).where(Job.id == job_id)
            job = session.execute(stmt).scalar_one_or_none()
            if job:
                job.progress = progress
                if message:
                    job.status_message = message
                job.updated_at = datetime.utcnow()
                session.commit()
                logger.debug(f"Updated job {job_id} progress to {progress}%: {message}")
    except Exception as e:
        logger.error(f"Failed to update job progress: {e}")


def _parse_progress(line: str) -> Optional[dict]:
    """Parse yt-dlp progress output line.
    
    Example formats:
    - [download]  45.2% of 50.00MiB at 2.5MiB/s ETA 00:05
    - [download]  100% of 50.00MiB in 00:20
    
    Returns:
        dict with keys: percent, speed, eta (or None if not a progress line)
    """
    # Match download progress line
    match = re.search(r'\[download\]\s+(\d+\.?\d*)%', line)
    if not match:
        return None
    
    percent = float(match.group(1))
    
    # Extract speed (e.g., "2.5MiB/s")
    speed_match = re.search(r'at\s+([\d.]+\s*[KMG]iB/s)', line)
    speed = speed_match.group(1) if speed_match else None
    
    # Extract ETA (e.g., "00:05")
    eta_match = re.search(r'ETA\s+(\d+:\d+)', line)
    eta = eta_match.group(1) if eta_match else None
    
    return {
        'percent': percent,
        'speed': speed,
        'eta': eta
    }


def _run_yt_dlp_with_progress(args: list, job_id: str, phase: str, 
                               progress_start: int, progress_end: int,
                               timeout: int) -> subprocess.CompletedProcess:
    """Run yt-dlp command and parse progress in real-time.
    
    Args:
        args: Command line arguments for yt-dlp
        job_id: Job UUID for progress updates
        phase: Description of current phase (e.g., "video download")
        progress_start: Starting progress percentage (e.g., 5)
        progress_end: Ending progress percentage (e.g., 15)
        timeout: Timeout in seconds
        
    Returns:
        CompletedProcess object
        
    Raises:
        subprocess.TimeoutExpired: If timeout is exceeded
        subprocess.CalledProcessError: If yt-dlp returns non-zero exit code
    """
    last_update = time.time()
    last_percent = 0
    
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combine stderr into stdout
        text=True,
        bufsize=1  # Line buffered
    )
    
    output_lines = []
    try:
        start_time = time.time()
        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                process.kill()
                raise subprocess.TimeoutExpired(args, timeout)
            
            line = process.stdout.readline()
            if not line:
                # Process finished
                break
                
            output_lines.append(line)
            line = line.strip()
            
            # Log the line
            if line:
                logger.debug(f"yt-dlp: {line}")
            
            # Parse progress
            progress_info = _parse_progress(line)
            if progress_info:
                download_percent = progress_info['percent']
                
                # Map to job progress range
                progress_range = progress_end - progress_start
                job_progress = progress_start + int((download_percent / 100.0) * progress_range)
                
                # Build status message
                message_parts = [f"{phase}"]
                if progress_info['speed']:
                    message_parts.append(progress_info['speed'])
                if progress_info['eta']:
                    message_parts.append(f"ETA {progress_info['eta']}")
                message = " - ".join(message_parts)
                
                # Update progress (throttle to every 2 seconds)
                now = time.time()
                if now - last_update >= 2:
                    _update_job_progress(job_id, job_progress, message)
                    last_update = now
                    last_percent = download_percent
                    
                    # Stuck detection: no progress for 60+ seconds
                    if download_percent == last_percent and now - last_update >= 60:
                        logger.warning(
                            f"Download may be stuck: no progress change for 60s at {download_percent:.1f}%"
                        )
        
        # Wait for process to complete
        returncode = process.wait()
        
        # Check return code
        if returncode != 0:
            output = ''.join(output_lines)
            raise subprocess.CalledProcessError(returncode, args, output=output)
        
        return subprocess.CompletedProcess(args, returncode, stdout=''.join(output_lines))
        
    except:
        process.kill()
        raise


def download_video(youtube_url: str, job_id: str, expected_duration: int = None) -> Tuple[Path, Path]:
    """Download video from YouTube and extract audio using system yt-dlp.
    
    Args:
        youtube_url: YouTube video URL.
        job_id: Job UUID for organizing temp files.
        expected_duration: Expected video duration in seconds (from metadata).
                          If provided, skip metadata fetch.
        
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
    
    # Find yt-dlp binary dynamically (works on any system)
    yt_dlp_bin = shutil.which("yt-dlp")
    if not yt_dlp_bin:
        raise DownloadFailedError(
            "yt-dlp not found in PATH. Please install: pip install yt-dlp"
        )
    
    logger.info(f"Using yt-dlp from: {yt_dlp_bin}")
    
    # Base command args
    base_args = [
        yt_dlp_bin,
        "--extractor-retries", "3",
        "--fragment-retries", "3",
        "--retry-sleep", "exp=1:5",
    ]
    
    # Add cookies - try file first, then browser (optional, skip if unavailable)
    cookies_added = False
    if settings.youtube_cookies_path and Path(settings.youtube_cookies_path).exists():
        base_args.extend(["--cookies", settings.youtube_cookies_path])
        logger.info(f"Using cookies file: {settings.youtube_cookies_path}")
        cookies_added = True
    elif settings.youtube_cookies_browser:
        # Browser cookies only work in local dev, not in Docker
        # Check if we're likely in Docker (no browser profile directory)
        chrome_profile_dir = Path.home() / ".config/google-chrome"
        firefox_profile_dir = Path.home() / ".mozilla/firefox"
        
        if chrome_profile_dir.exists() or firefox_profile_dir.exists():
            # Local development - use browser cookies
            base_args.extend(["--cookies-from-browser", settings.youtube_cookies_browser])
            logger.info(f"Using cookies from browser: {settings.youtube_cookies_browser}")
            cookies_added = True
        else:
            # Docker environment - skip browser cookies
            logger.info(f"Browser not found (Docker environment), skipping cookies extraction")
    
    if not cookies_added:
        logger.info("Downloading without cookies - most public videos should work fine")
    
    try:
        # If expected_duration is provided, skip metadata fetch
        if expected_duration:
            duration = expected_duration
            logger.info(f"Using expected duration from metadata: {duration}s")
        else:
            # Fallback: Fetch metadata with yt-dlp if not provided
            logger.info(f"Getting video info for {youtube_url}")
            result = subprocess.run(
                base_args + ["--dump-json", youtube_url],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            
            import json
            info = json.loads(result.stdout)
            duration = info.get("duration", 0)
            
            # Skip videos with invalid duration
            if not duration or duration <= 0:
                raise DownloadFailedError(
                    f"Video has invalid duration ({duration}s). This video may be unavailable, "
                    f"a live stream, or have metadata issues. Skipping to avoid timeout."
                )
            
            logger.info(f"Video info: title={info.get('title')}, duration={duration}s")
        
        # Calculate dynamic timeout: duration * 3 (min 60s, max 300s)
        download_timeout = max(60, min(300, int(duration * 3)))
        logger.info(f"Using download timeout: {download_timeout}s for {duration}s video")
        
        # Download video with progress tracking
        logger.info(f"Downloading video from {youtube_url}")
        _update_job_progress(job_id, 5, "Starting video download")
        
        _run_yt_dlp_with_progress(
            base_args + [
                "-f", "best[ext=mp4]/best",
                "-o", str(video_output),
                youtube_url,
            ],
            job_id=job_id,
            phase="video download",
            progress_start=5,
            progress_end=15,
            timeout=download_timeout
        )
        
        if not video_output.exists():
            raise DownloadFailedError("Video download completed but file not found")
        
        # Extract audio with progress tracking
        logger.info(f"Extracting audio from {youtube_url}")
        _update_job_progress(job_id, 15, "Starting audio extraction")
        
        _run_yt_dlp_with_progress(
            base_args + [
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "192",
                "-o", str(audio_output.with_suffix("")),
                youtube_url,
            ],
            job_id=job_id,
            phase="audio extraction",
            progress_start=15,
            progress_end=20,
            timeout=download_timeout
        )
        
        if not audio_output.exists():
            raise DownloadFailedError("Audio extraction completed but file not found")
        
        logger.info(f"Download completed: video={video_output}, audio={audio_output}")
        _update_job_progress(job_id, 20, "Download and extraction complete")
        return video_output, audio_output
        
    except VideoTooLongError:
        raise
    except subprocess.TimeoutExpired as e:
        logger.error(f"Download timeout after {e.timeout}s: {youtube_url}")
        raise DownloadFailedError(
            f"Download timeout after {e.timeout}s. Video may be too large, "
            f"network too slow, or video unavailable."
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed: {e.output if hasattr(e, 'output') else e.stderr}")
        error_msg = e.output if hasattr(e, 'output') else str(e)
        raise DownloadFailedError(f"Failed to download video: {error_msg}")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise DownloadFailedError(f"Failed to download video: {str(e)}")
