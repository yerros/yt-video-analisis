"""YouTube metadata service using YouTube Data API v3."""

import os
import re
import json
import redis
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import settings


class YouTubeMetadataService:
    """Service for fetching YouTube video metadata using YouTube Data API v3."""

    def __init__(self, api_key: Optional[str] = None, enable_cache: bool = True):
        """Initialize YouTube metadata service.
        
        Args:
            api_key: YouTube Data API v3 key. If not provided, will read from settings.
            enable_cache: Whether to enable Redis caching (default: True)
        """
        self.api_key = api_key or settings.youtube_api_key
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is required")
        
        self.youtube = build("youtube", "v3", developerKey=self.api_key)
        self.enable_cache = enable_cache
        
        # Initialize Redis client for caching
        if self.enable_cache:
            try:
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis cache disabled due to connection error: {e}")
                self.enable_cache = False
                self.redis_client = None
        else:
            self.redis_client = None
    
    def _get_cache_key(self, video_id: str) -> str:
        """Generate Redis cache key for video metadata."""
        return f"youtube:metadata:{video_id}"
    
    def _get_from_cache(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata from cache if available."""
        if not self.enable_cache or not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(video_id)
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                print(f"Cache HIT for video {video_id}")
                return json.loads(cached_data)
            print(f"Cache MISS for video {video_id}")
        except Exception as e:
            print(f"Cache read error: {e}")
        
        return None
    
    def _save_to_cache(self, video_id: str, metadata: Dict[str, Any], ttl: int = 86400 * 7):
        """Save metadata to cache.
        
        Args:
            video_id: YouTube video ID
            metadata: Metadata dictionary to cache
            ttl: Time to live in seconds (default: 7 days)
        """
        if not self.enable_cache or not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(video_id)
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(metadata, default=str)  # default=str for datetime serialization
            )
            print(f"Cached metadata for video {video_id} (TTL: {ttl}s)")
        except Exception as e:
            print(f"Cache write error: {e}")

    @staticmethod
    def extract_channel_id(url: str) -> Optional[str]:
        """Extract channel ID from YouTube channel URL.
        
        Supports formats:
        - https://www.youtube.com/channel/CHANNEL_ID
        - https://www.youtube.com/@username
        - https://www.youtube.com/c/channelname
        - https://www.youtube.com/user/username
        
        Args:
            url: YouTube channel URL
            
        Returns:
            Channel ID or username/handle or None if not found
        """
        # Pattern for channel ID
        pattern1 = r'(?:youtube\.com\/channel\/)([\w-]+)'
        match = re.search(pattern1, url)
        if match:
            return match.group(1)
        
        # Pattern for @username (handle)
        pattern2 = r'(?:youtube\.com\/@)([\w-]+)'
        match = re.search(pattern2, url)
        if match:
            return f"@{match.group(1)}"
        
        # Pattern for /c/channelname
        pattern3 = r'(?:youtube\.com\/c\/)([\w-]+)'
        match = re.search(pattern3, url)
        if match:
            return match.group(1)
        
        # Pattern for /user/username
        pattern4 = r'(?:youtube\.com\/user\/)([\w-]+)'
        match = re.search(pattern4, url)
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL.
        
        Supports formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID or None if not found
        """
        # Pattern 1: youtube.com/watch?v=VIDEO_ID
        pattern1 = r'(?:youtube\.com\/watch\?v=)([\w-]+)'
        # Pattern 2: youtu.be/VIDEO_ID
        pattern2 = r'(?:youtu\.be\/)([\w-]+)'
        # Pattern 3: youtube.com/embed/VIDEO_ID
        pattern3 = r'(?:youtube\.com\/embed\/)([\w-]+)'
        # Pattern 4: youtube.com/v/VIDEO_ID
        pattern4 = r'(?:youtube\.com\/v\/)([\w-]+)'
        
        for pattern in [pattern1, pattern2, pattern3, pattern4]:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Alternative method using urlparse
        try:
            parsed_url = urlparse(url)
            if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
                if parsed_url.path == '/watch':
                    return parse_qs(parsed_url.query).get('v', [None])[0]
                elif parsed_url.path.startswith('/embed/'):
                    return parsed_url.path.split('/')[2]
                elif parsed_url.path.startswith('/v/'):
                    return parsed_url.path.split('/')[2]
            elif parsed_url.hostname == 'youtu.be':
                return parsed_url.path[1:]
        except Exception:
            pass
        
        return None

    def get_video_metadata(self, video_url: str) -> Dict[str, Any]:
        """Fetch comprehensive metadata for a YouTube video.
        
        Uses Redis cache to avoid redundant API calls. Cache TTL is 7 days.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Dictionary containing video metadata
            
        Raises:
            ValueError: If video ID cannot be extracted
            HttpError: If API request fails
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {video_url}")
        
        # Check cache first
        cached_metadata = self._get_from_cache(video_id)
        if cached_metadata:
            return cached_metadata
        
        try:
            # Request video details with all relevant parts
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics,status,topicDetails,recordingDetails",
                id=video_id
            )
            response = request.execute()
            
            if not response.get("items"):
                raise ValueError(f"Video not found: {video_id}")
            
            video_data = response["items"][0]
            
            # Parse the response into a structured format
            metadata = self._parse_video_data(video_data)
            metadata["video_id"] = video_id
            metadata["video_url"] = video_url
            
            # Save to cache
            self._save_to_cache(video_id, metadata)
            
            return metadata
            
        except HttpError as e:
            raise Exception(f"YouTube API error: {e}")

    def _parse_video_data(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse YouTube API response into structured metadata.
        
        Args:
            video_data: Raw video data from YouTube API
            
        Returns:
            Parsed and structured metadata
        """
        snippet = video_data.get("snippet", {})
        content_details = video_data.get("contentDetails", {})
        statistics = video_data.get("statistics", {})
        status = video_data.get("status", {})
        topic_details = video_data.get("topicDetails", {})
        recording_details = video_data.get("recordingDetails", {})
        
        # Parse duration from ISO 8601 format (PT1H2M10S)
        duration_seconds = self._parse_duration(content_details.get("duration", "PT0S"))
        
        # Parse published date
        published_at_str = snippet.get("publishedAt")
        published_at = None
        if published_at_str:
            try:
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            except Exception:
                pass
        
        # Get thumbnail URLs (prefer maxres, then high, then default)
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = None
        for quality in ["maxres", "high", "standard", "medium", "default"]:
            if quality in thumbnails:
                thumbnail_url = thumbnails[quality].get("url")
                break
        
        metadata = {
            # Basic Info
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "published_at": published_at,
            "duration_seconds": duration_seconds,
            
            # Channel Info
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"),
            
            # Categorization
            "category_id": snippet.get("categoryId"),
            "tags": snippet.get("tags", []),
            "default_language": snippet.get("defaultLanguage"),
            "default_audio_language": snippet.get("defaultAudioLanguage"),
            
            # Statistics
            "view_count": int(statistics.get("viewCount", 0)),
            "like_count": int(statistics.get("likeCount", 0)),
            "comment_count": int(statistics.get("commentCount", 0)),
            "favorite_count": int(statistics.get("favoriteCount", 0)),
            
            # Content Details
            "definition": content_details.get("definition"),  # hd or sd
            "caption": content_details.get("caption") == "true",
            "licensed_content": content_details.get("licensedContent", False),
            "projection": content_details.get("projection"),  # rectangular or 360
            
            # Status
            "upload_status": status.get("uploadStatus"),
            "privacy_status": status.get("privacyStatus"),
            "license": status.get("license"),
            "embeddable": status.get("embeddable", False),
            "public_stats_viewable": status.get("publicStatsViewable", False),
            "made_for_kids": status.get("madeForKids", False),
            
            # Topics (Wikipedia topics)
            "topic_categories": topic_details.get("topicCategories", []),
            "relevant_topic_ids": topic_details.get("relevantTopicIds", []),
            
            # Recording Details
            "recording_date": recording_details.get("recordingDate"),
            "location": recording_details.get("location"),
            
            # Thumbnail
            "thumbnail_url": thumbnail_url,
            "all_thumbnails": thumbnails,
            
            # Complete raw data for reference
            "raw_data": video_data
        }
        
        return metadata

    @staticmethod
    def _parse_duration(duration: str) -> int:
        """Parse ISO 8601 duration to seconds.
        
        Args:
            duration: Duration in ISO 8601 format (e.g., PT1H2M10S)
            
        Returns:
            Duration in seconds
        """
        # Remove 'PT' prefix
        duration = duration.replace('PT', '')
        
        hours = 0
        minutes = 0
        seconds = 0
        
        # Parse hours
        if 'H' in duration:
            parts = duration.split('H')
            hours = int(parts[0])
            duration = parts[1]
        
        # Parse minutes
        if 'M' in duration:
            parts = duration.split('M')
            minutes = int(parts[0])
            duration = parts[1]
        
        # Parse seconds
        if 'S' in duration:
            seconds = int(duration.replace('S', ''))
        
        return hours * 3600 + minutes * 60 + seconds

    def get_channel_metadata(self, channel_id: str) -> Dict[str, Any]:
        """Fetch metadata for a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Dictionary containing channel metadata
        """
        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics,brandingSettings",
                id=channel_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return {}
            
            channel_data = response["items"][0]
            snippet = channel_data.get("snippet", {})
            statistics = channel_data.get("statistics", {})
            branding = channel_data.get("brandingSettings", {}).get("channel", {})
            
            return {
                "channel_id": channel_id,
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "custom_url": snippet.get("customUrl"),
                "published_at": snippet.get("publishedAt"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url"),
                "subscriber_count": int(statistics.get("subscriberCount", 0)),
                "video_count": int(statistics.get("videoCount", 0)),
                "view_count": int(statistics.get("viewCount", 0)),
                "keywords": branding.get("keywords"),
                "country": snippet.get("country"),
            }
        except HttpError as e:
            print(f"Error fetching channel metadata: {e}")
            return {}

    def get_video_comments(
        self, 
        video_id: str, 
        max_results: int = 20,
        order: str = "relevance"
    ) -> list[Dict[str, Any]]:
        """Fetch top comments for a video.
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments to fetch (default: 20)
            order: Sort order - "relevance" or "time" (default: relevance)
            
        Returns:
            List of comment dictionaries
        """
        try:
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results,
                order=order,
                textFormat="plainText"
            )
            response = request.execute()
            
            comments = []
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": snippet.get("authorDisplayName"),
                    "text": snippet.get("textDisplay"),
                    "like_count": snippet.get("likeCount", 0),
                    "published_at": snippet.get("publishedAt"),
                })
            
            return comments
            
        except HttpError as e:
            # Comments might be disabled
            print(f"Could not fetch comments: {e}")
            return []

    def get_related_videos(
        self, 
        video_id: str, 
        max_results: int = 10
    ) -> list[Dict[str, Any]]:
        """Fetch related videos.
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum number of related videos to fetch
            
        Returns:
            List of related video dictionaries
        """
        try:
            request = self.youtube.search().list(
                part="snippet",
                relatedToVideoId=video_id,
                type="video",
                maxResults=max_results
            )
            response = request.execute()
            
            related = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                related.append({
                    "video_id": item["id"].get("videoId"),
                    "title": snippet.get("title"),
                    "channel_title": snippet.get("channelTitle"),
                    "published_at": snippet.get("publishedAt"),
                    "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url"),
                })
            
            return related
            
        except HttpError as e:
            print(f"Could not fetch related videos: {e}")
            return []
    
    def get_channel_id_from_handle(self, handle: str) -> Optional[str]:
        """Get channel ID from username/handle.
        
        Args:
            handle: Channel handle (e.g., '@username' or 'username')
            
        Returns:
            Channel ID or None if not found
        """
        try:
            # Remove @ if present
            search_term = handle.lstrip('@')
            
            request = self.youtube.search().list(
                part="snippet",
                q=search_term,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            
            items = response.get("items", [])
            if items:
                return items[0]["snippet"]["channelId"]
            
            return None
            
        except HttpError as e:
            print(f"Could not find channel ID for handle {handle}: {e}")
            return None
    
    def get_channel_videos(
        self, 
        channel_url: str,
        max_results: Optional[int] = None,
        order: str = "date"
    ) -> Dict[str, Any]:
        """Fetch videos from a YouTube channel.
        
        Args:
            channel_url: YouTube channel URL
            max_results: Maximum number of videos to fetch (None = all videos)
            order: Order of results (date, rating, relevance, title, videoCount, viewCount)
            
        Returns:
            Dictionary containing:
            - channel_id: Channel ID
            - channel_title: Channel title
            - videos: List of video dictionaries with video_id, title, published_at, etc.
            - total_videos: Total number of videos fetched
        """
        try:
            # Extract channel identifier from URL
            channel_identifier = self.extract_channel_id(channel_url)
            if not channel_identifier:
                raise ValueError(f"Could not extract channel ID from URL: {channel_url}")
            
            # If it's a handle or username, get the actual channel ID
            if channel_identifier.startswith('@') or '/' in channel_url and '/c/' in channel_url or '/user/' in channel_url:
                actual_channel_id = self.get_channel_id_from_handle(channel_identifier)
                if not actual_channel_id:
                    raise ValueError(f"Could not find channel for: {channel_identifier}")
                channel_id = actual_channel_id
            else:
                channel_id = channel_identifier
            
            # Get channel info first
            channel_request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                id=channel_id
            )
            channel_response = channel_request.execute()
            
            if not channel_response.get("items"):
                raise ValueError(f"Channel not found: {channel_id}")
            
            channel_info = channel_response["items"][0]
            channel_title = channel_info["snippet"]["title"]
            channel_description = channel_info["snippet"].get("description", "")
            uploads_playlist_id = channel_info["contentDetails"]["relatedPlaylists"]["uploads"]
            total_channel_videos = int(channel_info["statistics"].get("videoCount", 0))
            
            # Fetch videos from uploads playlist
            videos = []
            page_token = None
            
            # Determine how many videos to fetch
            if max_results is None:
                # Fetch all videos (up to API limits)
                fetch_limit = total_channel_videos
            else:
                fetch_limit = min(max_results, total_channel_videos)
            
            while len(videos) < fetch_limit:
                # Calculate how many to request in this batch (max 50 per request)
                batch_size = min(50, fetch_limit - len(videos))
                
                playlist_request = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=batch_size,
                    pageToken=page_token
                )
                playlist_response = playlist_request.execute()
                
                for item in playlist_response.get("items", []):
                    snippet = item["snippet"]
                    video_id = item["contentDetails"]["videoId"]
                    
                    videos.append({
                        "video_id": video_id,
                        "video_url": f"https://www.youtube.com/watch?v={video_id}",
                        "title": snippet.get("title"),
                        "description": snippet.get("description"),
                        "published_at": snippet.get("publishedAt"),
                        "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url"),
                        "channel_title": channel_title,
                        "channel_id": channel_id,
                    })
                
                page_token = playlist_response.get("nextPageToken")
                
                # Break if no more pages
                if not page_token:
                    break
            
            return {
                "channel_id": channel_id,
                "channel_title": channel_title,
                "channel_description": channel_description,
                "total_channel_videos": total_channel_videos,
                "videos": videos,
                "total_fetched": len(videos),
            }
            
        except HttpError as e:
            raise ValueError(f"Failed to fetch channel videos: {e}")
        except Exception as e:
            raise ValueError(f"Error processing channel: {e}")
