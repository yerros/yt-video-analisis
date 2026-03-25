# Service Management Scripts

This directory contains robust service management scripts for the Video Analysis application.

## Available Scripts

### `start.sh` - Start All Services

Starts all services with comprehensive verification:

```bash
./scripts/start.sh
```

**Features:**
- ✅ Checks prerequisites (PostgreSQL, Redis, Python venv, node_modules)
- ✅ Gracefully stops existing services before starting
- ✅ Starts services in correct order: Backend API → Celery Worker → Worker Monitor → Frontend
- ✅ Verifies each service is listening on correct port
- ✅ Performs HTTP health checks on API and Frontend
- ✅ Verifies Celery worker responsiveness with health check task
- ✅ Creates PID files for all services
- ✅ Comprehensive status report with URLs, logs, and management commands

**What it starts:**
1. **Backend API** (FastAPI) - Port 8000
2. **Celery Worker** - Background job processing (pool=solo)
3. **Worker Monitor** - Health monitoring daemon
4. **Frontend** (Next.js) - Port 3000

---

### `stop.sh` - Stop All Services

Stops all services gracefully with force kill fallback:

```bash
./scripts/stop.sh
```

**Features:**
- ✅ Stops services in reverse order: Frontend → Worker Monitor → Celery Worker → Backend API
- ✅ Graceful shutdown with SIGTERM (10s timeout)
- ✅ Force kill with SIGKILL if graceful fails
- ✅ Multiple detection methods: PID file, process pattern, port listening
- ✅ Stops by port for Frontend/Backend
- ✅ Stops by pattern for Worker/Monitor
- ✅ Deep verification after each stop
- ✅ Cleans up PID files
- ✅ Final verification report

**Stop strategies:**
- **Graceful**: SIGTERM with 10-second timeout
- **Force**: SIGKILL if process doesn't respond
- **By Port**: Finds processes listening on specific ports
- **By Pattern**: Finds processes matching command patterns

---

### `restart.sh` - Restart All Services

Stops all services then starts them with full verification:

```bash
./scripts/restart.sh
```

**Features:**
- ✅ Runs `stop.sh` to gracefully/forcefully stop all services
- ✅ 2-second cooldown for clean shutdown
- ✅ Runs `start.sh` to start all services with verification
- ✅ Comprehensive error handling

**Use cases:**
- Apply configuration changes
- Recover from hung services
- Update code changes
- Clean restart after issues

---

### `status.sh` - Check Service Status

Displays comprehensive status of all services without starting or stopping them:

```bash
./scripts/status.sh
```

**Features:**
- ✅ Color-coded status indicators (🟢 Green = Running, 🟡 Yellow = Warning, 🔴 Red = Stopped)
- ✅ Checks prerequisites (PostgreSQL, Redis, venv, node_modules)
- ✅ Verifies process existence via PID files
- ✅ Verifies port listening for Backend/Frontend
- ✅ HTTP health checks for API and Frontend
- ✅ Log file sizes and locations
- ✅ Overall system health summary

**Status indicators:**
- **✓ Running** - Service is running normally with PID file
- **⚠ Running without PID file** - Service is running but missing PID file
- **⚠ Different process on port** - Different process than expected
- **⚠ Running but not responding** - Process exists but HTTP health check fails
- **✗ Not running** - Service is stopped
- **✗ Not running (stale PID file)** - PID file exists but process is dead

---

## Usage Examples

### Normal Workflow

```bash
# Start all services
./scripts/start.sh

# Check status
./scripts/status.sh

# Restart all services
./scripts/restart.sh

# Stop all services
./scripts/stop.sh
```

### Development Workflow

```bash
# Start services
./scripts/start.sh

# Make code changes...

# Restart to apply changes
./scripts/restart.sh

# Check if everything is running
./scripts/status.sh
```

### Troubleshooting

```bash
# Check what's running
./scripts/status.sh

# Force restart if services are hung
./scripts/restart.sh

# Stop everything and investigate
./scripts/stop.sh

# Check logs
tail -f backend/api.log
tail -f backend/worker.log
tail -f backend/worker_monitor.log
tail -f frontend/frontend.log
```

---

## Service Details

### Backend API (Port 8000)
- **Process**: Uvicorn FastAPI server
- **Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
- **PID File**: `backend/api.pid`
- **Log File**: `backend/api.log`
- **Health Check**: `GET http://localhost:8000/health`

### Celery Worker
- **Process**: Celery worker with solo pool
- **Command**: `celery -A celery_app worker --pool=solo --time-limit=1800 --soft-time-limit=1500 --loglevel=info`
- **PID File**: `backend/worker.pid`
- **Log File**: `backend/worker.log`
- **Health Check**: Sends `tasks.health_check.ping` task

### Worker Monitor
- **Process**: Python monitoring daemon
- **Command**: `python backend/scripts/worker_monitor.py`
- **PID File**: `backend/monitor.pid`
- **Log File**: `backend/worker_monitor.log`
- **Function**: Monitors worker health and auto-restarts if unresponsive

### Frontend (Port 3000)
- **Process**: Next.js dev server
- **Command**: `npm run dev`
- **PID File**: `frontend/frontend.pid`
- **Log File**: `frontend/frontend.log`
- **Health Check**: `GET http://localhost:3000`

---

## Prerequisites

Before using these scripts, ensure the following are installed and running:

1. **PostgreSQL** - Database server
   ```bash
   # macOS with Homebrew
   brew services start postgresql
   
   # Linux with systemd
   sudo systemctl start postgresql
   ```

2. **Redis** - Message broker for Celery
   ```bash
   # macOS with Homebrew
   brew services start redis
   
   # Linux with systemd
   sudo systemctl start redis
   ```

3. **Python Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   pip install -r backend/requirements.txt
   ```

4. **Node.js Dependencies**
   ```bash
   cd frontend
   npm install
   ```

---

## Important Notes

### Worker Pool Configuration
- ⚠️ **CRITICAL**: Celery worker MUST use `--pool=solo`
- Multiprocessing pools cause SIGSEGV crashes with yt-dlp
- Solo pool is single-threaded but stable

### Health Check Timeouts
- Worker may appear "unhealthy" during heavy video processing
- This is NORMAL - video download/transcription blocks the worker
- Monitor waits for 3 consecutive failures before restarting
- Prevents restarting workers doing legitimate work

### PID Files
- Located in `backend/` and `frontend/` directories
- Used for tracking and managing service processes
- Scripts handle stale PID files automatically
- Cleaned up on graceful shutdown

### Process Detection
- Scripts use multiple detection methods for reliability:
  1. **PID File** - Check stored PID and verify process exists
  2. **Pattern Matching** - Find processes by command pattern (pgrep)
  3. **Port Listening** - Find processes listening on specific ports (lsof)

### Force Kill
- Used when graceful shutdown fails after 10-second timeout
- Sends SIGKILL to ensure process termination
- Necessary for hung/unresponsive processes
- Safe to use - scripts verify process state

---

## Troubleshooting

### "Port already in use" error
```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Stop all services to free ports
./scripts/stop.sh
```

### Services won't stop gracefully
```bash
# stop.sh automatically force kills after timeout
# Or manually force kill:
pkill -9 -f "uvicorn main:app"
pkill -9 -f "celery.*worker"
pkill -9 -f "worker_monitor.py"
pkill -9 -f "next dev"
```

### Stale PID files
```bash
# Scripts handle automatically, or manually remove:
rm -f backend/api.pid backend/worker.pid backend/monitor.pid frontend/frontend.pid
```

### Worker not processing jobs
```bash
# Check worker status
./scripts/status.sh

# Check worker logs
tail -f backend/worker.log

# Restart worker
./scripts/restart.sh
```

### Prerequisites not running
```bash
# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql # Linux

# Start Redis
brew services start redis       # macOS
sudo systemctl start redis      # Linux
```

---

## Exit Codes

All scripts return appropriate exit codes:

- **0** - Success
- **1** - Error (service failed to start/stop, verification failed, etc.)

Use exit codes in automation:
```bash
if ./scripts/start.sh; then
    echo "Services started successfully"
else
    echo "Failed to start services"
    exit 1
fi
```

---

## Log Files

All services log to separate files for easy debugging:

```bash
# View logs in real-time
tail -f backend/api.log
tail -f backend/worker.log
tail -f backend/worker_monitor.log
tail -f frontend/frontend.log

# View last 100 lines
tail -n 100 backend/api.log

# Search logs
grep "ERROR" backend/api.log
grep "Task failed" backend/worker.log
```

---

## Security Notes

- Scripts use `set -e` to exit on errors
- PID files are verified before use to prevent race conditions
- Force kill is only used as last resort after graceful timeout
- Logs contain sensitive information - keep them secure
- Scripts should only be run by authorized users

---

## Contributing

When modifying these scripts:

1. ✅ Test thoroughly in development environment
2. ✅ Maintain error handling and verification steps
3. ✅ Update this README if behavior changes
4. ✅ Preserve color-coded output for readability
5. ✅ Keep exit codes consistent

---

## Related Documentation

- [Worker Health Monitoring](../backend/WORKER_MONITOR.md) - Details on worker monitoring system
- [Environment Configuration](../.env.example) - Environment variables setup
- [Backend API Documentation](http://localhost:8000/docs) - API endpoints (when running)
- [Worker Status Page](http://localhost:3000/worker) - Real-time monitoring UI (when running)
