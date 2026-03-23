"""Supabase Storage service for uploading frame images."""

import os
from pathlib import Path
from typing import Optional
from PIL import Image
from io import BytesIO
from supabase import create_client, Client
from core.config import settings


class StorageService:
    """Service for managing file uploads to Supabase Storage."""

    def __init__(self):
        """Initialize Supabase client."""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        self.bucket_name = "video-frames"

    def upload_frame(
        self, 
        file_path: str, 
        job_id: str, 
        frame_filename: str,
        compress: bool = True,
        quality: int = 85,
        max_width: int = 1920
    ) -> Optional[str]:
        """
        Upload a frame image to Supabase Storage with optional compression.
        
        Args:
            file_path: Local path to the frame image file
            job_id: Job ID for organizing files
            frame_filename: Name of the frame file (e.g., "frame_0001.jpg")
            compress: Whether to compress the image (default: True)
            quality: JPEG quality 1-100 (default: 85)
            max_width: Max width in pixels, maintains aspect ratio (default: 1920)
            
        Returns:
            Public URL of the uploaded file, or None if upload fails
        """
        try:
            # Create storage path: job_id/frame_filename
            storage_path = f"{job_id}/{frame_filename}"
            
            if compress:
                # Compress image before upload
                try:
                    with Image.open(file_path) as img:
                        # Convert RGBA to RGB if needed
                        if img.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                            img = background
                        
                        # Resize if needed
                        if img.width > max_width:
                            ratio = max_width / img.width
                            new_height = int(img.height * ratio)
                            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Save to BytesIO with compression
                        buffer = BytesIO()
                        img.save(buffer, format='JPEG', quality=quality, optimize=True)
                        file_data = buffer.getvalue()
                        
                        original_size = os.path.getsize(file_path)
                        compressed_size = len(file_data)
                        savings = ((original_size - compressed_size) / original_size) * 100
                        print(f"Compressed {frame_filename}: {original_size:,} → {compressed_size:,} bytes ({savings:.1f}% savings)")
                        
                except Exception as compress_error:
                    print(f"Compression failed for {frame_filename}: {compress_error}, uploading original")
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
            else:
                # Read file without compression
                with open(file_path, 'rb') as f:
                    file_data = f.read()
            
            # Upload to Supabase Storage
            result = self.supabase.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={
                    "content-type": "image/jpeg",
                    "upsert": "true"  # Overwrite if exists
                }
            )
            
            # Get public URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(storage_path)
            
            return public_url
            
        except Exception as e:
            print(f"Error uploading frame {frame_filename}: {str(e)}")
            return None

    def delete_job_frames(self, job_id: str) -> bool:
        """
        Delete all frames for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # List all files in the job folder
            files = self.supabase.storage.from_(self.bucket_name).list(job_id)
            
            if not files:
                return True
            
            # Delete all files
            file_paths = [f"{job_id}/{file['name']}" for file in files]
            self.supabase.storage.from_(self.bucket_name).remove(file_paths)
            
            return True
            
        except Exception as e:
            print(f"Error deleting frames for job {job_id}: {str(e)}")
            return False


# Create singleton instance
storage_service = StorageService()
