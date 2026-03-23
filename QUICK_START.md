# Quick Start Guide - Video Analysis AI

## TL;DR - Cara Tercepat untuk Start/Stop Services

### ⚡ Quick Commands

```bash
# RESTART ALL SERVICES (Recommended - Paling Reliable)
make restart
# atau
./restart.sh

# STOP ALL SERVICES
make stop
# atau
./stop.sh

# VIEW HELP
make help
```

---

## 🚀 First Time Setup

```bash
# 1. Install dependencies
make setup

# 2. Setup environment variables
cp .env.example .env
nano .env  # Edit dengan API keys Anda

# 3. Setup database
createdb video_analysis
make migrate

# 4. Start all services
make restart
```

---

## 🔄 Daily Development Workflow

### Start Services

```bash
make restart
```

Output yang diharapkan:
```
================================================
  Video Analysis AI - Restart Script
================================================

[STEP] Stopping all development processes...
[SUCCESS] All development processes stopped!

[STEP] Checking prerequisites...
[SUCCESS] Prerequisites check passed!

[INFO] Starting all services...

[SUCCESS] Redis is already running
[SUCCESS] Backend started successfully (PID: 12345) on http://localhost:8000
[SUCCESS] Celery worker started successfully (PID: 12346)
[SUCCESS] Frontend started successfully (PID: 12347) on http://localhost:3000

================================================
  🚀 All Services Started Successfully!
================================================

[STEP] Verifying all services...

  ✓ Backend:  http://localhost:8000 (Running)
  ✓ Frontend: http://localhost:3000 (Running)
  ✓ Celery Worker (Running)
  ✓ Redis (Running)
  ✓ PostgreSQL (Running)

[SUCCESS] All services are running correctly!

================================================
  Service URLs:
================================================
  Frontend:   http://localhost:3000
  Backend:    http://localhost:8000
  API Docs:   http://localhost:8000/docs
================================================
```

### Stop Services

```bash
make stop
```

### Check Logs

```bash
# View logs in real-time
tail -f backend.log
tail -f worker.log
tail -f frontend.log

# View last 50 lines
tail -50 backend.log
```

---

## 🐛 Troubleshooting

### Problem: "Port already in use"

**Solution:**
```bash
make restart  # Script akan otomatis kill proses yang menggunakan port
```

### Problem: "Backend not starting"

**Solution:**
```bash
# Check backend logs
tail -50 backend.log

# Manual restart
make restart
```

### Problem: "Frontend error: EADDRINUSE"

**Solution:**
```bash
# Kill all Node processes
pkill -9 node

# Restart
make restart
```

### Problem: "Celery worker not processing jobs"

**Solution:**
```bash
# Check worker logs
tail -50 worker.log

# Check Redis
redis-cli ping  # Should return PONG

# Restart all
make restart
```

### Problem: "Database connection error"

**Solution:**
```bash
# Check PostgreSQL status
pg_isready

# Start PostgreSQL if not running
brew services start postgresql@16

# Restart services
make restart
```

### Nuclear Option: Kill Everything

```bash
# Stop all services
make stop

# Kill all processes manually
pkill -9 -f "uvicorn"
pkill -9 -f "celery"
pkill -9 -f "next dev"
pkill -9 node

# Verify ports are free
lsof -i :8000
lsof -i :3000

# Restart
make restart
```

---

## 📊 Monitoring Services

### Check Service Status

```bash
# Check what's running on ports
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Check processes
ps aux | grep uvicorn    # Backend
ps aux | grep celery     # Worker
ps aux | grep "next dev" # Frontend

# Check Redis
redis-cli ping

# Check PostgreSQL
pg_isready
```

### Test API Endpoints

```bash
# Test backend health
curl http://localhost:8000/docs

# Test API endpoint
curl http://localhost:8000/api/statistics/usage
```

---

## 🎯 Common Tasks

### Run Database Migration

```bash
make migrate
```

### Create New Migration

```bash
make migrate-create
# Enter migration message when prompted
```

### Clean Temporary Files

```bash
make clean
```

### Format Code

```bash
make format
```

### Lint Code

```bash
make lint
```

---

## 📝 Available Make Commands

```bash
make help              # Show all available commands
make setup             # Initial setup (venv + dependencies)
make install           # Install all dependencies
make restart           # Kill all & restart (RECOMMENDED)
make stop              # Stop all services
make dev-all           # Run all services at once
make dev-backend       # Run backend only
make dev-frontend      # Run frontend only
make dev-worker        # Run worker only
make dev-redis         # Run Redis only
make migrate           # Run database migrations
make migrate-create    # Create new migration
make clean             # Clean temporary files
make format            # Format code
make lint              # Lint code
```

---

## 🔗 Service URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **API OpenAPI JSON:** http://localhost:8000/openapi.json

---

## 📂 Log File Locations

- **Backend:** `backend.log` (project root)
- **Worker:** `worker.log` (project root)
- **Frontend:** `frontend.log` (project root)
- **Dev.sh logs:** `/tmp/video-analysis-*.log`

---

## 💡 Tips

1. **Always use `make restart`** untuk memulai development - ini akan memastikan tidak ada port conflict
2. **Check logs** jika ada masalah: `tail -f backend.log`
3. **Use `make stop`** sebelum shutdown komputer untuk clean exit
4. **Restart services** setelah update dependencies atau .env file
5. **Check prerequisites** dengan restart script jika ada error saat startup

---

## 🆘 Need Help?

Jika masih ada masalah:

1. Check logs: `tail -50 backend.log worker.log frontend.log`
2. Run restart script: `make restart`
3. Check prerequisites di README.md
4. Pastikan .env sudah di-setup dengan benar
