"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from core.config import settings

# Create Celery app
celery_app = Celery(
    "video_analysis",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.pipeline_sync", "tasks.embedding", "tasks.job_monitor", "tasks.queue_processor", "tasks.health_check"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'process-pending-jobs-every-30s': {
        'task': 'tasks.job_monitor.process_pending_jobs',
        'schedule': 30.0,  # Run every 30 seconds
    },
}
