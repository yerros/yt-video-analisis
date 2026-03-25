"""Worker health check task.

This module provides a simple health check task that can be used to verify
the worker is responsive and processing tasks.
"""

import time
from celery_app import celery_app


@celery_app.task(name="tasks.health_check.ping")
def ping() -> dict:
    """Simple ping task to check if worker is responsive.
    
    Returns:
        Dictionary with status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "message": "Worker is responsive",
    }
