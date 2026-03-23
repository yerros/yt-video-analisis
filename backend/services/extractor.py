"""Frame extraction service using OpenCV and PySceneDetect."""

import logging
from pathlib import Path
from typing import Dict, List, Any

import cv2
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

from core.config import settings
from core.exceptions import FrameExtractionFailedError
from services.storage_service import storage_service

logger = logging.getLogger(__name__)


def extract_frames(video_path: Path, job_id: str) -> Dict[str, Any]:
    """Extract key frames from video using scene detection.
    
    Args:
        video_path: Path to video file.
        job_id: Job UUID for organizing output files.
        
    Returns:
        Dict containing:
            - frames: List of dicts with frame metadata (path, timestamp, frame_number)
            - count: Number of frames extracted
        
    Raises:
        FrameExtractionFailedError: If frame extraction fails.
    """
    try:
        if not video_path.exists():
            raise FrameExtractionFailedError(f"Video file not found: {video_path}")
        
        # Use permanent storage instead of temp
        frames_dir = Path(settings.storage_dir) / "frames" / job_id
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Detecting scenes in {video_path}")
        
        # Initialize video manager and scene manager
        video_manager = VideoManager([str(video_path)])
        scene_manager = SceneManager()
        
        # Add content detector with threshold (lower = more scenes)
        scene_manager.add_detector(ContentDetector(threshold=30.0))
        
        # Start video manager and perform scene detection
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        
        # Get list of detected scenes
        scene_list = scene_manager.get_scene_list()
        
        logger.info(f"Detected {len(scene_list)} scenes")
        
        if not scene_list:
            # If no scenes detected, extract frames at regular intervals
            return _extract_uniform_frames(video_path, frames_dir, job_id)
        
        # Extract one frame from each scene
        frames_data = []
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        try:
            for idx, (start_time, end_time) in enumerate(scene_list):
                # Limit to max frames
                if idx >= settings.max_frames:
                    logger.info(f"Reached max frames limit ({settings.max_frames})")
                    break
                
                # Get frame at the middle of the scene
                start_frame = start_time.get_frames()
                end_frame = end_time.get_frames()
                mid_frame = int((start_frame + end_frame) / 2)
                
                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
                ret, frame = cap.read()
                
                if ret:
                    frame_filename = f"frame_{idx:04d}.jpg"
                    frame_path = frames_dir / frame_filename
                    cv2.imwrite(str(frame_path), frame)
                    
                    # Calculate timestamp in seconds
                    timestamp = mid_frame / fps if fps > 0 else 0
                    
                    # Upload to Supabase Storage
                    public_url = storage_service.upload_frame(
                        str(frame_path),
                        job_id,
                        frame_filename
                    )
                    
                    # Use public URL if upload successful, otherwise fallback to local path
                    frame_url = public_url if public_url else f"/api/frames/{job_id}/{frame_filename}"
                    
                    frames_data.append({
                        "filename": frame_filename,
                        "path": frame_url,
                        "timestamp": round(timestamp, 2),
                        "frame_number": mid_frame
                    })
                    logger.debug(f"Extracted and uploaded frame {idx} at frame number {mid_frame}")

        finally:
            cap.release()
            video_manager.release()
        
        if not frames_data:
            raise FrameExtractionFailedError("No frames extracted from video")
        
        logger.info(f"Extracted {len(frames_data)} frames")
        return {
            "frames": frames_data,
            "count": len(frames_data)
        }
        
    except FrameExtractionFailedError:
        raise
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
        raise FrameExtractionFailedError(f"Failed to extract frames: {str(e)}")


def _extract_uniform_frames(video_path: Path, frames_dir: Path, job_id: str) -> Dict[str, Any]:
    """Extract frames at uniform intervals when scene detection fails.
    
    Args:
        video_path: Path to video file.
        frames_dir: Directory to save frames.
        job_id: Job UUID for organizing URLs.
        
    Returns:
        Dict containing frames metadata and count.
    """
    logger.info("Extracting frames at uniform intervals")
    
    frames_data = []
    cap = cv2.VideoCapture(str(video_path))
    
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if total_frames == 0 or fps == 0:
            raise FrameExtractionFailedError("Could not get video properties")
        
        # Extract one frame every N seconds, up to max_frames
        interval_seconds = 10  # Extract one frame every 10 seconds
        frame_interval = int(fps * interval_seconds)
        
        idx = 0
        frame_num = 0
        
        while frame_num < total_frames and idx < settings.max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if ret:
                frame_filename = f"frame_{idx:04d}.jpg"
                frame_path = frames_dir / frame_filename
                cv2.imwrite(str(frame_path), frame)
                
                timestamp = frame_num / fps if fps > 0 else 0
                
                # Upload to Supabase Storage
                public_url = storage_service.upload_frame(
                    str(frame_path),
                    job_id,
                    frame_filename
                )
                
                # Use public URL if upload successful, otherwise fallback to local path
                frame_url = public_url if public_url else f"/api/frames/{job_id}/{frame_filename}"
                
                frames_data.append({
                    "filename": frame_filename,
                    "path": frame_url,
                    "timestamp": round(timestamp, 2),
                    "frame_number": frame_num
                })
                logger.debug(f"Extracted and uploaded uniform frame {idx} at frame {frame_num}")
                idx += 1
            
            frame_num += frame_interval
        
        return {
            "frames": frames_data,
            "count": len(frames_data)
        }
        
    finally:
        cap.release()
