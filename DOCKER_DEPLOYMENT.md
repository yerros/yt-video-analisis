# 🐳 Docker Deployment Guide

Panduan lengkap untuk men-deploy Video Analysis menggunakan Docker dan Portainer.

## 📋 Daftar Isi

- [Prasyarat](#prasyarat)
- [Deployment dengan Docker Compose](#deployment-dengan-docker-compose)
- [Deployment dengan Portainer](#deployment-dengan-portainer)
- [Konfigurasi Environment](#konfigurasi-environment)
- [Service Architecture](#service-architecture)
- [Monitoring dan Troubleshooting](#monitoring-dan-troubleshooting)
- [Production Best Practices](#production-best-practices)

---

## 🔧 Prasyarat

### System Requirements

- **Docker**: Version 20.10 atau lebih baru
- **Docker Compose**: Version 2.0 atau lebih baru
- **Portainer** (opsional): Version 2.19 atau lebih baru
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 20GB free space
- **CPU**: 2 cores minimum, 4+ cores recommended

### Install Docker

#### Ubuntu/Debian
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### macOS
```bash
brew install --cask docker
```

#### Windows
Download dari [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Verifikasi Installation
```bash
docker --version
docker compose version
```

---

## 🚀 Deployment dengan Docker Compose

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/video-analysis.git
cd video-analysis
```

### 2. Setup Environment Variables

```bash
# Copy template environment file
cp .env.example .env

# Edit dengan text editor pilihan Anda
nano .env  # atau vim, code, etc.
```

**Minimal configuration required:**

```env
# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-your-openai-api-key-here

# YouTube API (REQUIRED)
YOUTUBE_API_KEY=your-youtube-api-key-here

# Database (Docker akan auto-setup)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_DB=video_analysis
POSTGRES_PORT=5432

# Redis (Docker akan auto-setup)
REDIS_PORT=6379

# Application
TEMP_DIR=/tmp/video-analysis
MAX_VIDEO_DURATION=1800
MAX_FRAMES=30

# YouTube Cookies (OPTIONAL tapi recommended)
YOUTUBE_COOKIES_PATH=/app/cookies.txt
YOUTUBE_COOKIES_BROWSER=chrome

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### 3. Setup YouTube Cookies (Recommended)

YouTube cookies diperlukan untuk menghindari bot detection:

```bash
# Menggunakan browser extension "Get cookies.txt LOCALLY"
# 1. Install extension di Chrome/Firefox
# 2. Buka youtube.com dan login
# 3. Click extension icon > Export cookies
# 4. Save sebagai www.youtube.com_cookies.txt
# 5. Copy ke project root

cp ~/Downloads/www.youtube.com_cookies.txt ./www.youtube.com_cookies.txt
```

**Update .env:**
```env
YOUTUBE_COOKIES_PATH=/app/www.youtube.com_cookies.txt
```

**Update docker-compose.yml untuk mount cookies:**
```yaml
volumes:
  - ./www.youtube.com_cookies.txt:/app/www.youtube.com_cookies.txt:ro
```

### 4. Build dan Start Services

```bash
# Build images
docker compose build

# Start semua services
docker compose up -d

# Check logs
docker compose logs -f
```

### 5. Verifikasi Deployment

```bash
# Check semua services running
docker compose ps

# Health check
curl http://localhost:8000/health
curl http://localhost:3000

# Check worker status
curl http://localhost:8000/api/worker/status
```

### 6. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Worker Monitor**: http://localhost:3000/worker

---

## 🎯 Deployment dengan Portainer

### Step 1: Install Portainer

#### Portainer Community Edition (Free)

```bash
# Create volume untuk Portainer data
docker volume create portainer_data

# Deploy Portainer
docker run -d \
  -p 9000:9000 \
  -p 9443:9443 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

#### Access Portainer

Buka browser: `http://your-server-ip:9000` atau `https://your-server-ip:9443`

**First time setup:**
1. Create admin user
2. Choose "Get Started" untuk local environment
3. Connect ke Docker environment

---

### Step 2: Deploy Stack via Portainer

#### A. Via Git Repository (Recommended)

1. **Login ke Portainer** → `http://your-server-ip:9000`

2. **Navigate**: 
   - Pilih environment (local)
   - Sidebar → **Stacks**
   - Click **+ Add stack**

3. **Stack Configuration**:
   - **Name**: `video-analysis`
   - **Build method**: Select **Repository**
   - **Repository URL**: `https://github.com/yourusername/video-analysis`
   - **Repository reference**: `refs/heads/main` (atau branch lain)
   - **Compose path**: `docker-compose.yml`

4. **Environment Variables**:
   
   Scroll ke bawah ke section **Environment variables**, lalu tambahkan:

   ```env
   OPENAI_API_KEY=sk-your-api-key
   YOUTUBE_API_KEY=your-youtube-key
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=secure-password-here
   POSTGRES_DB=video_analysis
   REDIS_URL=redis://redis:6379/0
   NEXT_PUBLIC_API_URL=http://your-server-ip:8000
   ```

5. **Deploy Stack**:
   - Click **Deploy the stack**
   - Wait untuk build process (5-10 minutes)
   - Monitor logs di **Stack logs** tab

---

#### B. Via Web Editor

1. **Login ke Portainer** → `http://your-server-ip:9000`

2. **Navigate**:
   - Stacks → **+ Add stack**
   - **Name**: `video-analysis`
   - **Build method**: Select **Web editor**

3. **Paste Docker Compose**:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: video-analysis-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: video_analysis
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - video-analysis-network

  redis:
    image: redis:7-alpine
    container_name: video-analysis-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - video-analysis-network

  backend:
    image: ghcr.io/yourusername/video-analysis-backend:latest  # Ganti dengan image registry Anda
    container_name: video-analysis-backend
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/video_analysis
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      YOUTUBE_API_KEY: ${YOUTUBE_API_KEY}
      YOUTUBE_COOKIES_BROWSER: chrome
      TEMP_DIR: /tmp/video-analysis
      MAX_VIDEO_DURATION: 1800
      MAX_FRAMES: 30

    volumes:
      - video_temp:/tmp/video-analysis
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - video-analysis-network

  celery-worker:
    image: ghcr.io/yourusername/video-analysis-backend:latest  # Same image as backend
    container_name: video-analysis-celery-worker
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/video_analysis
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      YOUTUBE_API_KEY: ${YOUTUBE_API_KEY}
      YOUTUBE_COOKIES_BROWSER: chrome
      TEMP_DIR: /tmp/video-analysis
      MAX_VIDEO_DURATION: 1800
      MAX_FRAMES: 30

    volumes:
      - video_temp:/tmp/video-analysis
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - video-analysis-network
    command: celery -A celery_app worker --loglevel=info --pool=solo --time-limit=1800 --soft-time-limit=1500
    healthcheck:
      test: ["CMD-SHELL", "celery -A celery_app inspect ping -d celery@$HOSTNAME"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s

  worker-monitor:
    image: ghcr.io/yourusername/video-analysis-backend:latest  # Same image as backend
    container_name: video-analysis-worker-monitor
    environment:
      REDIS_URL: redis://redis:6379/0
      WORKER_HEALTH_CHECK_INTERVAL: 60
      WORKER_HEALTH_CHECK_TIMEOUT: 10
      WORKER_MAX_RESTART_ATTEMPTS: 3
      WORKER_RESTART_COOLDOWN: 300
    depends_on:
      redis:
        condition: service_healthy
      celery-worker:
        condition: service_started
    restart: unless-stopped
    networks:
      - video-analysis-network
    command: python scripts/worker_monitor.py

  frontend:
    image: ghcr.io/yourusername/video-analysis-frontend:latest  # Ganti dengan image registry Anda
    container_name: video-analysis-frontend
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - video-analysis-network

volumes:
  postgres_data:
  redis_data:
  video_temp:

networks:
  video-analysis-network:
    driver: bridge
```

4. **Environment Variables**:

Scroll ke **Environment variables** section, tambahkan:

| Name | Value |
|------|-------|
| POSTGRES_PASSWORD | your-secure-password |
| OPENAI_API_KEY | sk-your-openai-key |
| YOUTUBE_API_KEY | your-youtube-key |
| NEXT_PUBLIC_API_URL | http://your-server-ip:8000 |

5. **Deploy**:
   - Click **Deploy the stack**
   - Wait untuk images pull dan startup

---

#### C. Via File Upload

1. **Prepare files locally**:
   - `docker-compose.yml`
   - `.env` file

2. **Login ke Portainer**

3. **Navigate**: Stacks → **+ Add stack**

4. **Configuration**:
   - **Name**: `video-analysis`
   - **Build method**: Select **Upload**
   - **Upload**: Select `docker-compose.yml`

5. **Load environment**: 
   - Enable **Load variables from .env file**
   - Upload `.env` file

6. **Deploy the stack**

---

### Step 3: Build Images untuk Portainer

Jika menggunakan method **Web Editor**, Anda perlu build dan push images terlebih dahulu:

#### Option A: GitHub Container Registry (Recommended)

```bash
# Login ke GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build backend image
docker build -t ghcr.io/yourusername/video-analysis-backend:latest ./backend
docker push ghcr.io/yourusername/video-analysis-backend:latest

# Build frontend image
docker build -t ghcr.io/yourusername/video-analysis-frontend:latest ./frontend
docker push ghcr.io/yourusername/video-analysis-frontend:latest
```

#### Option B: Docker Hub

```bash
# Login ke Docker Hub
docker login

# Build and push
docker build -t yourusername/video-analysis-backend:latest ./backend
docker push yourusername/video-analysis-backend:latest

docker build -t yourusername/video-analysis-frontend:latest ./frontend
docker push yourusername/video-analysis-frontend:latest
```

#### Option C: Private Registry

```bash
# Login ke private registry
docker login your-registry.com

# Build and push
docker build -t your-registry.com/video-analysis-backend:latest ./backend
docker push your-registry.com/video-analysis-backend:latest

docker build -t your-registry.com/video-analysis-frontend:latest ./frontend
docker push your-registry.com/video-analysis-frontend:latest
```

---

### Step 4: Monitoring di Portainer

#### Stack Status

1. **Navigate**: Stacks → `video-analysis`
2. View:
   - Services status
   - Container logs
   - Resource usage

#### Container Management

1. **Navigate**: Containers
2. Filter by stack: `video-analysis`
3. Actions available:
   - Start/Stop/Restart
   - View logs
   - Exec console
   - Inspect
   - Stats

#### View Logs

```
Portainer → Containers → [Select container] → Logs
```

**Real-time logs:**
- Enable "Auto-refresh"
- Set refresh interval: 5s
- Filter by keyword

#### Execute Commands

```
Portainer → Containers → [Select container] → Console
```

**Common commands:**
```bash
# Check database migrations
alembic current

# Check Celery worker
celery -A celery_app inspect active

# Check Redis connection
redis-cli -h redis ping

# Test API
curl http://localhost:8000/health
```

---

## 🔐 Konfigurasi Environment

### Environment Variables Reference

#### Database (PostgreSQL + pgvector)

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=video_analysis
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/video_analysis
```

#### Redis

```env
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
```

#### OpenAI

```env
OPENAI_API_KEY=sk-your-api-key-here
```

#### YouTube

```env
YOUTUBE_API_KEY=your-youtube-api-key
YOUTUBE_COOKIES_PATH=/app/cookies.txt  # Optional
YOUTUBE_COOKIES_BROWSER=chrome         # Optional fallback
```

#### Application Settings

```env
TEMP_DIR=/tmp/video-analysis
MAX_VIDEO_DURATION=1800        # 30 minutes
MAX_FRAMES=30                  # Frame extraction limit
```

#### Worker Monitor

```env
WORKER_HEALTH_CHECK_INTERVAL=60      # Check every 60 seconds
WORKER_HEALTH_CHECK_TIMEOUT=10       # Timeout after 10 seconds
WORKER_MAX_RESTART_ATTEMPTS=3        # Max 3 restart attempts
WORKER_RESTART_COOLDOWN=300          # 5 minute cooldown
```

#### Frontend

```env
NEXT_PUBLIC_API_URL=http://localhost:8000  # Public API URL
FRONTEND_PORT=3000
BACKEND_PORT=8000
```

#### Storage (Optional - Supabase)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET=video-frames
```

#### Storage (Optional - AWS S3)

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=video-analysis-frames
```

---

## 🏗️ Service Architecture

### Services Overview

```
┌─────────────────────────────────────────────────────┐
│                    Docker Network                    │
│              (video-analysis-network)                │
│                                                      │
│  ┌──────────────┐      ┌──────────────┐            │
│  │  PostgreSQL  │      │    Redis     │            │
│  │  (pgvector)  │      │   (Broker)   │            │
│  │  Port: 5432  │      │  Port: 6379  │            │
│  └──────┬───────┘      └──────┬───────┘            │
│         │                     │                     │
│         │                     │                     │
│  ┌──────▼──────────────────────▼──────┐            │
│  │        Backend API (FastAPI)       │            │
│  │         Port: 8000                 │            │
│  │  - REST API endpoints              │            │
│  │  - Database migrations             │            │
│  │  - Job management                  │            │
│  └──────┬─────────────────────────────┘            │
│         │                     │                     │
│         │                     │                     │
│  ┌──────▼───────┐    ┌───────▼────────┐           │
│  │   Celery     │    │     Worker     │           │
│  │   Worker     │◄───┤    Monitor     │           │
│  │ (pool=solo)  │    │  (Auto-restart)│           │
│  │              │    │                │           │
│  │ - Video DL   │    │ - Health check │           │
│  │ - Transcribe │    │ - Auto-restart │           │
│  │ - Analysis   │    │ - Logging      │           │
│  └──────────────┘    └────────────────┘           │
│                                                     │
│  ┌──────────────────────────────────┐             │
│  │    Frontend (Next.js)            │             │
│  │    Port: 3000                    │             │
│  │  - React UI                      │             │
│  │  - Worker status page            │             │
│  │  - Job monitoring                │             │
│  └──────────────────────────────────┘             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Container Details

| Service | Image | CPU | RAM | Storage | Description |
|---------|-------|-----|-----|---------|-------------|
| **postgres** | pgvector/pgvector:pg16 | 1 core | 512MB | 10GB | Database dengan vector search |
| **redis** | redis:7-alpine | 0.5 core | 256MB | 1GB | Message broker untuk Celery |
| **backend** | custom | 2 cores | 2GB | 1GB | FastAPI REST API |
| **celery-worker** | custom | 2 cores | 4GB | 5GB | Background job processing |
| **worker-monitor** | custom | 0.25 core | 128MB | 100MB | Worker health monitoring |
| **frontend** | custom | 1 core | 512MB | 500MB | Next.js web interface |

### Port Mapping

| Service | Internal Port | External Port | Protocol |
|---------|--------------|---------------|----------|
| PostgreSQL | 5432 | 5432 | TCP |
| Redis | 6379 | 6379 | TCP |
| Backend API | 8000 | 8000 | HTTP |
| Frontend | 3000 | 3000 | HTTP |

### Volume Mounts

| Volume | Mount Point | Purpose | Size Estimate |
|--------|-------------|---------|---------------|
| `postgres_data` | `/var/lib/postgresql/data` | Database storage | 5-50GB |
| `redis_data` | `/data` | Redis persistence | 100MB-1GB |
| `video_temp` | `/tmp/video-analysis` | Temporary video files | 10-100GB |

---

## 📊 Monitoring dan Troubleshooting

### Health Checks

#### Check All Services

```bash
# Via Docker Compose
docker compose ps

# Via Docker CLI
docker ps --filter "name=video-analysis"

# Via Portainer
# Navigate: Containers → Filter by "video-analysis"
```

#### Individual Service Health

```bash
# Backend API
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Worker Status
curl http://localhost:8000/api/worker/status

# PostgreSQL
docker exec video-analysis-postgres pg_isready

# Redis
docker exec video-analysis-redis redis-cli ping
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f worker-monitor

# Last 100 lines
docker compose logs --tail=100 backend

# Since timestamp
docker compose logs --since 2024-03-26T10:00:00 celery-worker
```

### Common Issues

#### 1. Database Connection Failed

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
docker exec video-analysis-backend psql $DATABASE_URL -c "SELECT 1"
```

#### 2. Redis Connection Failed

**Symptoms:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**
```bash
# Check Redis is running
docker compose ps redis

# Test Redis connection
docker exec video-analysis-redis redis-cli ping

# Check REDIS_URL
echo $REDIS_URL
```

#### 3. Worker Not Processing Jobs

**Symptoms:**
- Jobs stuck in "pending" status
- Worker logs show no activity

**Solutions:**
```bash
# Check worker health
curl http://localhost:8000/api/worker/status

# Check worker logs
docker compose logs -f celery-worker

# Check worker monitor
docker compose logs -f worker-monitor

# Restart worker
docker compose restart celery-worker

# Or via Portainer: Containers → celery-worker → Restart
```

#### 4. YouTube Download Failed

**Symptoms:**
```
ERROR: Sign in to confirm you're not a bot
ERROR: Video unavailable
```

**Solutions:**
```bash
# Setup cookies (see YouTube Cookies section)
# Update .env:
YOUTUBE_COOKIES_PATH=/app/cookies.txt

# Or use browser extraction:
YOUTUBE_COOKIES_BROWSER=chrome

# Restart worker
docker compose restart celery-worker
```

#### 5. Out of Memory (OOM)

**Symptoms:**
- Container keeps restarting
- Logs show "Killed"

**Solutions:**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory

# Or limit specific service in docker-compose.yml:
services:
  celery-worker:
    deploy:
      resources:
        limits:
          memory: 4G
```

#### 6. Port Already in Use

**Symptoms:**
```
Error: bind: address already in use
```

**Solutions:**
```bash
# Find process using port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill process
kill -9 <PID>

# Or change port in .env:
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

### Performance Optimization

#### Monitor Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats video-analysis-backend

# Export metrics
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

#### Optimize Worker Performance

**docker-compose.yml:**
```yaml
celery-worker:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

#### Database Optimization

```bash
# Create indexes
docker exec -it video-analysis-backend alembic revision --autogenerate -m "add indexes"

# Vacuum database
docker exec video-analysis-postgres psql -U postgres -d video_analysis -c "VACUUM ANALYZE;"
```

---

## 🔒 Production Best Practices

### Security

#### 1. Use Strong Passwords

```env
# Generate secure password
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

#### 2. Environment Variables Security

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use Docker secrets (Portainer)
# Portainer → Secrets → Add secret
# Then reference in stack:
secrets:
  postgres_password:
    external: true

services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

#### 3. Network Isolation

```yaml
# Only expose necessary ports
services:
  postgres:
    # ports:
    #   - "5432:5432"  # Comment out, only internal access
    expose:
      - "5432"  # Internal only
```

#### 4. Use HTTPS (Nginx Reverse Proxy)

```bash
# Enable nginx profile
docker compose --profile production up -d
```

Create `nginx/nginx.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Backup Strategy

#### 1. Database Backup

**Automated backup script:**
```bash
#!/bin/bash
# backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

docker exec video-analysis-postgres pg_dump \
  -U postgres \
  -d video_analysis \
  -F c \
  -f /tmp/backup_$DATE.dump

docker cp video-analysis-postgres:/tmp/backup_$DATE.dump \
  $BACKUP_DIR/backup_$DATE.dump

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.dump" -mtime +7 -delete
```

**Setup cron job:**
```bash
# Run backup daily at 2 AM
0 2 * * * /path/to/backup-db.sh
```

#### 2. Volume Backup

```bash
# Backup all volumes
docker run --rm \
  -v video-analysis_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_data.tar.gz /data
```

#### 3. Configuration Backup

```bash
# Backup compose and env files
tar czf config-backup-$(date +%Y%m%d).tar.gz \
  docker-compose.yml \
  .env \
  nginx/
```

### Update Strategy

#### 1. Update Images

```bash
# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d

# Clean old images
docker image prune -a
```

#### 2. Database Migration

```bash
# Run migrations
docker exec video-analysis-backend alembic upgrade head

# Rollback if needed
docker exec video-analysis-backend alembic downgrade -1
```

#### 3. Zero-Downtime Update (Blue-Green)

```bash
# Scale up new version
docker compose up -d --scale backend=2

# Wait for health check
sleep 30

# Scale down old version
docker compose up -d --scale backend=1
```

### Monitoring Production

#### 1. Setup Prometheus + Grafana

Create `docker-compose.monitoring.yml`:
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - video-analysis-network

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    networks:
      - video-analysis-network

volumes:
  prometheus_data:
  grafana_data:

networks:
  video-analysis-network:
    external: true
```

#### 2. Setup Alerts

**prometheus.yml:**
```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - 'alerts.yml'
```

**alerts.yml:**
```yaml
groups:
  - name: video-analysis
    rules:
      - alert: WorkerDown
        expr: up{job="celery-worker"} == 0
        for: 5m
        annotations:
          summary: "Celery worker is down"
```

### Resource Limits

**Production docker-compose.yml:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  celery-worker:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Logging

#### 1. Centralized Logging

**docker-compose.yml:**
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### 2. Log Aggregation (ELK Stack)

```bash
# Add to docker-compose.monitoring.yml
elasticsearch:
  image: elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data

logstash:
  image: logstash:8.11.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

kibana:
  image: kibana:8.11.0
  ports:
    - "5601:5601"
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

---

## 📚 Additional Resources

### Documentation

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Portainer Documentation](https://docs.portainer.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Next.js Documentation](https://nextjs.org/docs)

### Support

- **GitHub Issues**: https://github.com/yourusername/video-analysis/issues
- **Docker Community**: https://forums.docker.com/
- **Portainer Community**: https://community.portainer.io/

### Quick Commands Reference

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart services
docker compose restart

# View logs
docker compose logs -f [service]

# Check status
docker compose ps

# Execute command
docker compose exec [service] [command]

# Scale service
docker compose up -d --scale celery-worker=3

# Update images
docker compose pull && docker compose up -d

# Clean up
docker compose down -v  # Remove volumes
docker system prune -a  # Clean everything
```

---

## 🎉 Selesai!

Deployment Anda sekarang sudah running! 

**Access your application:**
- Frontend: http://your-server:3000
- Backend API: http://your-server:8000
- API Docs: http://your-server:8000/docs
- Portainer: http://your-server:9000

**Next steps:**
1. ✅ Setup SSL certificate (Let's Encrypt)
2. ✅ Configure domain name
3. ✅ Setup monitoring alerts
4. ✅ Schedule database backups
5. ✅ Review security settings

Happy deploying! 🚀
