"""Custom exceptions for the application."""


class VideoAnalysisError(Exception):
    """Base exception for video analysis errors."""

    pass


class InvalidYouTubeUrlError(VideoAnalysisError):
    """Raised when the YouTube URL is invalid."""

    pass


class VideoTooLongError(VideoAnalysisError):
    """Raised when the video duration exceeds the maximum allowed."""

    pass


class DownloadFailedError(VideoAnalysisError):
    """Raised when video download fails."""

    pass


class TranscriptionFailedError(VideoAnalysisError):
    """Raised when audio transcription fails."""

    pass


class FrameExtractionFailedError(VideoAnalysisError):
    """Raised when frame extraction fails."""

    pass


class AnalysisFailedError(VideoAnalysisError):
    """Raised when AI analysis fails."""

    pass


class ChatError(VideoAnalysisError):
    """Raised when chat operation fails."""

    pass
