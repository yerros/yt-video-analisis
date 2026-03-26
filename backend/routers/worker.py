"""Worker status API router."""

import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from celery_app import celery_app
from core.config import settings

router = APIRouter()


class WorkerStatusResponse(BaseModel):
    """Worker status response schema."""
    
    status: str  # "running", "stopped", "unknown"
    is_healthy: bool
    pid: Optional[int]
    uptime_seconds: Optional[float]
    active_tasks: int
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    monitor_running: bool
    monitor_pid: Optional[int]
    last_health_check: Optional[str]
    redis_connected: bool
    timestamp: str


def find_worker_process() -> Optional[int]:
    """Find the Celery worker process ID.
    
    Returns:
        Process ID if found, None otherwise.
    """
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'celery.*worker'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            return int(pids[0]) if pids else None
        return None
    except Exception:
        return None


def find_monitor_process() -> Optional[int]:
    """Find the worker monitor process ID.
    
    Returns:
        Process ID if found, None otherwise.
    """
    try:
        # Check if monitor.pid file exists (relative to backend directory)
        backend_dir = Path(__file__).parent.parent
        pid_file = backend_dir / "monitor.pid"
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            # Verify process is still running
            try:
                os.kill(pid, 0)
                return pid
            except OSError:
                return None
        return None
    except Exception:
        return None


def get_worker_uptime(pid: int) -> Optional[float]:
    """Get worker process uptime in seconds.
    
    Args:
        pid: Process ID.
        
    Returns:
        Uptime in seconds, or None if error.
    """
    try:
        result = subprocess.run(
            ['ps', '-o', 'etime=', '-p', str(pid)],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            elapsed = result.stdout.strip()
            # Parse elapsed time (format: [[dd-]hh:]mm:ss)
            parts = elapsed.split('-')
            if len(parts) == 2:
                days = int(parts[0])
                time_part = parts[1]
            else:
                days = 0
                time_part = parts[0]
            
            time_parts = time_part.split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = map(int, time_parts)
            elif len(time_parts) == 2:
                hours = 0
                minutes, seconds = map(int, time_parts)
            else:
                return None
            
            total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
            return float(total_seconds)
        return None
    except Exception:
        return None


def check_redis_connection() -> bool:
    """Check if Redis is connected.
    
    Returns:
        True if connected, False otherwise.
    """
    try:
        result = subprocess.run(
            ['redis-cli', 'ping'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and result.stdout.strip() == 'PONG'
    except Exception:
        return False


def check_worker_health() -> bool:
    """Check if worker is responsive by sending a ping task.
    
    Returns:
        True if worker is healthy, False otherwise.
    """
    try:
        result = celery_app.send_task('tasks.health_check.ping', expires=5)
        response = result.get(timeout=5)
        return response and response.get('status') == 'healthy'
    except Exception:
        return False


def get_celery_stats() -> Dict[str, int]:
    """Get Celery task statistics.
    
    Returns:
        Dictionary with active, pending, completed, and failed task counts.
    """
    try:
        # Get active tasks
        inspect = celery_app.control.inspect()
        active = inspect.active()
        active_count = sum(len(tasks) for tasks in (active or {}).values())
        
        # Get reserved/pending tasks
        reserved = inspect.reserved()
        pending_count = sum(len(tasks) for tasks in (reserved or {}).values())
        
        # Get stats for completed/failed (from result backend)
        stats = inspect.stats()
        
        return {
            'active': active_count,
            'pending': pending_count,
            'completed': 0,  # Would need to query result backend
            'failed': 0,  # Would need to query result backend
        }
    except Exception:
        return {
            'active': 0,
            'pending': 0,
            'completed': 0,
            'failed': 0,
        }


def get_last_health_check() -> Optional[str]:
    """Get timestamp of last health check from monitor log.
    
    Returns:
        ISO timestamp string, or None if not found.
    """
    try:
        log_file = Path("/tmp/worker_monitor.log")
        if not log_file.exists():
            return None
        
        # Read last 50 lines
        lines = log_file.read_text().strip().split('\n')[-50:]
        
        # Find last health check line
        for line in reversed(lines):
            if 'Worker health check' in line or 'health check ping' in line:
                # Extract timestamp (format: 2026-03-25 14:15:25,375)
                parts = line.split(' - ')
                if parts:
                    timestamp_str = parts[0]
                    # Convert to ISO format
                    try:
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        return dt.isoformat()
                    except ValueError:
                        pass
        return None
    except Exception:
        return None


@router.get("/status", response_model=WorkerStatusResponse)
async def get_worker_status() -> WorkerStatusResponse:
    """Get current worker status and health information.
    
    Returns:
        Worker status details including health, tasks, and monitor status.
    """
    # Find worker process
    worker_pid = find_worker_process()
    
    # Determine worker status
    if worker_pid:
        status = "running"
        uptime = get_worker_uptime(worker_pid)
    else:
        status = "stopped"
        uptime = None
    
    # Check worker health (only if running)
    is_healthy = False
    if worker_pid:
        is_healthy = check_worker_health()
    
    # Get task statistics
    stats = get_celery_stats()
    
    # Check monitor status
    monitor_pid = find_monitor_process()
    monitor_running = monitor_pid is not None
    
    # Get last health check time
    last_health_check = get_last_health_check()
    
    # Check Redis connection
    redis_connected = check_redis_connection()
    
    return WorkerStatusResponse(
        status=status,
        is_healthy=is_healthy,
        pid=worker_pid,
        uptime_seconds=uptime,
        active_tasks=stats['active'],
        pending_tasks=stats['pending'],
        completed_tasks=stats['completed'],
        failed_tasks=stats['failed'],
        monitor_running=monitor_running,
        monitor_pid=monitor_pid,
        last_health_check=last_health_check,
        redis_connected=redis_connected,
        timestamp=datetime.now().isoformat(),
    )


@router.post("/restart")
async def restart_worker() -> Dict[str, Any]:
    """Restart the Celery worker.
    
    This endpoint stops the current worker and starts a new one.
    Use with caution as this will interrupt any running tasks.
    
    Returns:
        Status message about the restart operation.
    """
    try:
        # Find and kill existing worker
        worker_pid = find_worker_process()
        if worker_pid:
            os.kill(worker_pid, 15)  # SIGTERM
            time.sleep(2)
        
        # Start new worker
        backend_dir = Path(__file__).parent.parent
        worker_log = Path('/tmp/worker.log')
        worker_err = Path('/tmp/worker_error.log')
        
        log_file = open(worker_log, 'a')
        err_file = open(worker_err, 'a')
        
        subprocess.Popen(
            [
                str(backend_dir / 'venv' / 'bin' / 'celery'),
                '-A', 'celery_app',
                'worker',
                '--pool=solo',
                '--loglevel=info',
                '--time-limit=1800',
                '--soft-time-limit=1500'
            ],
            cwd=str(backend_dir),
            stdout=log_file,
            stderr=err_file,
            start_new_session=True
        )
        
        return {
            'status': 'success',
            'message': 'Worker restarted successfully',
            'timestamp': datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Failed to restart worker: {str(e)}'
        )
