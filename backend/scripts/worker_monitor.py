#!/usr/bin/env python3
"""Worker health monitor with auto-restart.

This script monitors the Celery worker health by sending ping tasks periodically.
If the worker doesn't respond within the timeout, it automatically restarts the worker.

Usage (from project root):
    python backend/scripts/worker_monitor.py

The monitor runs continuously in the background and:
1. Sends a ping task to the worker every 60 seconds
2. Waits up to 10 seconds for a response
3. If no response, considers the worker hung and restarts it
4. Logs all actions to worker_monitor.log
"""

import os
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Get script directory and project root
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Add backend directory to path for imports
sys.path.insert(0, str(BACKEND_DIR))

from celery import Celery
from celery.exceptions import TimeoutError
from core.config import settings

# Setup logging
LOG_FILE = Path('/tmp/worker_monitor.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Celery app configuration
celery_app = Celery(
    'video_analysis',
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Configuration
CHECK_INTERVAL = 60  # seconds between health checks
RESPONSE_TIMEOUT = 10  # seconds to wait for ping response
MAX_RESTART_ATTEMPTS = 3  # max consecutive restart attempts
RESTART_COOLDOWN = 300  # seconds to wait after max restarts before trying again

# Worker command (run from backend directory)
WORKER_COMMAND = [
    str(BACKEND_DIR / 'venv' / 'bin' / 'celery'),
    '-A', 'celery_app',
    'worker',
    '--pool=solo',
    '--loglevel=info',
    '--time-limit=1800',
    '--soft-time-limit=1500'
]

# Worker log files
WORKER_LOG = Path('/tmp/worker.log')
WORKER_ERR_LOG = Path('/tmp/worker_error.log')


def find_worker_process():
    """Find the Celery worker process ID.
    
    Returns:
        Process ID if found, None otherwise.
    """
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'celery.*worker.*video_analysis'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            # Return the first PID (main worker process)
            return int(pids[0]) if pids else None
        return None
    except Exception as e:
        logger.error(f"Error finding worker process: {e}")
        return None


def kill_worker(pid):
    """Kill the worker process gracefully, then forcefully if needed.
    
    Args:
        pid: Process ID to kill.
    """
    try:
        logger.info(f"Sending SIGTERM to worker process {pid}")
        os.kill(pid, signal.SIGTERM)
        
        # Wait up to 10 seconds for graceful shutdown
        for _ in range(10):
            time.sleep(1)
            try:
                os.kill(pid, 0)  # Check if process still exists
            except OSError:
                logger.info(f"Worker process {pid} terminated gracefully")
                return
        
        # Force kill if still running
        logger.warning(f"Worker {pid} did not terminate, sending SIGKILL")
        os.kill(pid, signal.SIGKILL)
        time.sleep(2)
        logger.info(f"Worker process {pid} force killed")
        
    except ProcessLookupError:
        logger.info(f"Worker process {pid} already terminated")
    except Exception as e:
        logger.error(f"Error killing worker process {pid}: {e}")


def start_worker():
    """Start a new worker process.
    
    Returns:
        True if worker started successfully, False otherwise.
    """
    try:
        logger.info("Starting new worker process...")
        
        # Open log files
        log_file = open(WORKER_LOG, 'a')
        err_file = open(WORKER_ERR_LOG, 'a')
        
        # Start worker process (run from backend directory)
        process = subprocess.Popen(
            WORKER_COMMAND,
            cwd=str(BACKEND_DIR),
            stdout=log_file,
            stderr=err_file,
            start_new_session=True
        )
        
        # Wait a bit for worker to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info(f"Worker started successfully (PID: {process.pid})")
            return True
        else:
            logger.error(f"Worker failed to start (exit code: {process.returncode})")
            return False
            
    except Exception as e:
        logger.error(f"Error starting worker: {e}")
        return False


def check_worker_health():
    """Check if worker is responsive by sending a ping task.
    
    Returns:
        True if worker is healthy, False otherwise.
    """
    try:
        logger.debug("Sending health check ping to worker...")
        
        # Send ping task with timeout
        result = celery_app.send_task(
            'tasks.health_check.ping',
            expires=RESPONSE_TIMEOUT
        )
        
        # Wait for result
        response = result.get(timeout=RESPONSE_TIMEOUT)
        
        if response and response.get('status') == 'healthy':
            logger.debug("Worker health check: OK")
            return True
        else:
            logger.warning(f"Worker health check: Unexpected response: {response}")
            return False
            
    except TimeoutError:
        logger.error("Worker health check: TIMEOUT - Worker not responding")
        return False
    except Exception as e:
        logger.error(f"Worker health check: ERROR - {e}")
        return False


def restart_worker():
    """Restart the worker process.
    
    Returns:
        True if restart successful, False otherwise.
    """
    logger.warning("Attempting to restart worker...")
    
    # Find and kill existing worker
    pid = find_worker_process()
    if pid:
        kill_worker(pid)
    else:
        logger.warning("No worker process found to kill")
    
    # Wait a bit before starting new worker
    time.sleep(3)
    
    # Start new worker
    return start_worker()


def monitor_loop():
    """Main monitoring loop."""
    logger.info("Worker health monitor started")
    logger.info(f"Check interval: {CHECK_INTERVAL}s, Response timeout: {RESPONSE_TIMEOUT}s")
    
    consecutive_failures = 0
    last_restart_time = 0
    
    while True:
        try:
            # Check if worker is healthy
            is_healthy = check_worker_health()
            
            if is_healthy:
                # Reset failure counter on success
                if consecutive_failures > 0:
                    logger.info("Worker recovered")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                logger.warning(f"Worker health check failed ({consecutive_failures}/{MAX_RESTART_ATTEMPTS})")
                
                # Check if we should restart
                current_time = time.time()
                time_since_restart = current_time - last_restart_time
                
                if consecutive_failures >= MAX_RESTART_ATTEMPTS:
                    if time_since_restart < RESTART_COOLDOWN:
                        wait_time = RESTART_COOLDOWN - time_since_restart
                        logger.warning(
                            f"Max restart attempts reached. "
                            f"Waiting {wait_time:.0f}s before next restart attempt..."
                        )
                        time.sleep(wait_time)
                        consecutive_failures = 0
                        continue
                    
                    # Attempt restart
                    if restart_worker():
                        logger.info("Worker restarted successfully")
                        last_restart_time = current_time
                        consecutive_failures = 0
                        # Give worker time to stabilize
                        time.sleep(10)
                    else:
                        logger.error("Failed to restart worker")
                        # Continue checking, might recover
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    try:
        monitor_loop()
    except Exception as e:
        logger.error(f"Fatal error in monitor: {e}")
        sys.exit(1)
