# 🚀 Production Deployment Guide - Video Analysis System

Production-ready deployment menggunakan Docker dan Docker Compose untuk sistem analisis video YouTube dengan AI.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Deployment Methods](#deployment-methods)
- [Production Checklist](#production-checklist)
- [Monitoring & Logs](#monitoring--logs)
- [Scaling & Performance](#scaling--performance)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## 🎯 Prerequisites

### Required Software
- **Docker**: v24.0+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: v2.20+ (included with Docker Desktop)
- **Git**: untuk clone repository

### Required API Keys
- **OpenAI API Key**: [Get from OpenAI Platform](https://platform.openai.com/api-keys)
- **YouTube Data API v3 Key**: [Get from Google Cloud Console](https://console.cloud.google.com/apis/credentials)

### Optional (Recommended)
- **Supabase Account**: untuk storage frames ([Sign up](https://supabase.com))
- **YouTube Cookies**: untuk menghindari bot detection

### System Requirements

| Environment | CPU | RAM | Storage |
|-------------|-----|-----|---------|
| Development | 2 cores | 4 GB | 20 GB |
| Production | 4+ cores | 8+ GB | 50+ GB |

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/video-analysis.git
cd video-analysis
```

### 2. Setup Environment Variables

```bash
# Copy environment file template
cp .env.production .env

# Edit dengan API keys Anda
nano .env  # atau gunakan text editor favorit
```

**Minimal configuration required:**
```env
OPENAI_API_KEY=sk-your-key-here
YOUTUBE_API_KEY=your-youtube-key-here
POSTGRES_PASSWORD=your-secure-password
```

### 3. Build & Run

```bash
# Build semua containers
docker-compose build

# Start services (development mode)
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
open http://localhost:3000

# View logs
docker-compose logs -f
```

**Expected output:**
```json
{"status": "healthy"}
```

---

## ⚙️ Environment Configuration

### Database Configuration

```env
# PostgreSQL (with pgvector extension)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here  # Generate: openssl rand -base64 32
POSTGRES_DB=video_analysis
POSTGRES_PORT=5432
```

### API Keys

```env
# OpenAI (Required)
OPENAI_API_KEY=sk-proj-...

# YouTube Data API v3 (Required)
YOUTUBE_API_KEY=AIza...

# YouTube Download Configuration (mencegah bot detection)
# Option 1: Path to cookies.txt file (manual export)
YOUTUBE_COOKIES_PATH=./www.youtube.com_cookies.txt

# Option 2: Extract cookies from browser automatically (jika path tidak diset)
# Supported: chrome, firefox, edge, safari, opera, brave, chromium
YOUTUBE_COOKIES_BROWSER=chrome
```

### YouTube Cookies Setup

**Option 1: Cookies dari Browser Otomatis (Recommended)**

yt-dlp versi terbaru sudah support ekstrak cookies langsung dari browser tanpa perlu export manual:

```env
# Set browser yang Anda gunakan untuk login YouTube
YOUTUBE_COOKIES_BROWSER=chrome  # atau firefox, edge, safari, etc
```

**Supported browsers:**
- `chrome` - Google Chrome
- `firefox` - Mozilla Firefox
- `edge` - Microsoft Edge
- `safari` - Safari (macOS only)
- `brave` - Brave Browser
- `opera` - Opera
- `chromium` - Chromium

**Catatan:** Pastikan Anda sudah login ke YouTube di browser tersebut.

**Option 2: Export Manual Cookies.txt**

Jika cookies from browser tidak bekerja, export manual:

1. Install browser extension: [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
2. Login ke YouTube
3. Export cookies as `www.youtube.com_cookies.txt`
4. Letakkan file di project root
5. Set `YOUTUBE_COOKIES_PATH=./www.youtube.com_cookies.txt`

**Tips untuk Menghindari Bot Detection:**
- ✅ Gunakan cookies (from browser atau file)
- ✅ Sequential queue processing dengan delay 30s antar job
- ✅ Jangan download terlalu banyak video sekaligus (max 10-20/batch)
- ✅ Update yt-dlp ke versi terbaru secara rutin

### Storage Configuration

**Option 1: Supabase (Recommended)**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbG...
SUPABASE_BUCKET=video-frames
```

**Option 2: AWS S3**
```env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name
```

### Application Settings

```env
# Backend
BACKEND_PORT=8000
MAX_VIDEO_DURATION=1800  # 30 minutes
MAX_FRAMES=30

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000  # Change to your domain in production
```

---

## 🌐 Deployment Methods

### Method 1: Development Mode (Default)

Untuk testing dan development:

```bash
docker-compose up -d
```

**Services running:**
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### Method 2: Production with Nginx

Dengan reverse proxy dan rate limiting:

```bash
# Start dengan profile production
docker-compose --profile production up -d
```

**Services running:**
- Nginx: `http://localhost:80` (proxy to frontend + backend)
- Backend: internal
- Frontend: internal
- PostgreSQL: internal
- Redis: internal

**Access:**
- Frontend: `http://your-domain.com`
- API: `http://your-domain.com/api/`
- Health: `http://your-domain.com/health`

### Method 3: Production with SSL (HTTPS)

#### Step 1: Get SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com
```

#### Step 2: Update Nginx Config

Edit `nginx/conf.d/default.conf`:

```bash
# Uncomment HTTPS server block
# Update server_name to your domain
# Update SSL certificate paths
```

#### Step 3: Deploy

```bash
# Update environment
export NEXT_PUBLIC_API_URL=https://yourdomain.com

# Start services
docker-compose --profile production up -d

# Verify SSL
curl https://yourdomain.com/health
```

---

## ✅ Production Checklist

### Security

- [ ] Ganti semua default passwords
- [ ] Generate secure PostgreSQL password: `openssl rand -base64 32`
- [ ] Enable firewall (UFW/iptables)
- [ ] Setup SSL certificate (Let's Encrypt)
- [ ] Restrict database access ke localhost only
- [ ] Backup `.env` file ke secure location (NOT in git)
- [ ] Setup fail2ban untuk rate limiting

### Configuration

- [ ] Update `NEXT_PUBLIC_API_URL` ke production domain
- [ ] Configure storage (Supabase/S3)
- [ ] Setup YouTube cookies untuk production
- [ ] Configure max video duration sesuai needs
- [ ] Set proper `MAX_FRAMES` untuk balance speed/quality

### Infrastructure

- [ ] Setup automated backups (database)
- [ ] Configure log rotation
- [ ] Setup monitoring (health checks)
- [ ] Configure reverse proxy (nginx)
- [ ] Setup CDN untuk static assets (optional)

### Testing

- [ ] Test video upload & processing
- [ ] Verify SSE streaming works
- [ ] Check duplicate URL detection
- [ ] Test error handling
- [ ] Load testing (optional)

---

## 📊 Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Check all containers status
docker-compose ps

# Check resource usage
docker stats
```

### Logs Location (inside containers)

- Backend: `/app/backend.log`
- Nginx: `/var/log/nginx/`
- PostgreSQL: `/var/log/postgresql/`

### Database Monitoring

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d video_analysis

# Check job statistics
SELECT status, COUNT(*) FROM jobs GROUP BY status;

# Check disk usage
SELECT pg_size_pretty(pg_database_size('video_analysis'));
```

---

## 📈 Scaling & Performance

### Horizontal Scaling (Multiple Workers)

Edit `docker-compose.yml`:

```yaml
celery-worker:
  deploy:
    replicas: 3  # Add this
```

Or scale dynamically:

```bash
docker-compose up -d --scale celery-worker=3
```

### Backend Scaling

```yaml
backend:
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
  deploy:
    replicas: 2
```

### Database Performance

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d video_analysis

# Add indexes (already created by migrations)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_jobs_status ON jobs(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_jobs_youtube_url ON jobs(youtube_url);

# Analyze tables
ANALYZE jobs;
```

### Redis Optimization

```yaml
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

---

## 🔧 Troubleshooting

### Issue: Container tidak start

```bash
# Check logs
docker-compose logs <service-name>

# Rebuild container
docker-compose build --no-cache <service-name>
docker-compose up -d <service-name>
```

### Issue: Database connection refused

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Verify DATABASE_URL
echo $DATABASE_URL

# Restart database
docker-compose restart postgres
```

### Issue: Backend tidak bisa akses database

```bash
# Run migrations manually
docker-compose exec backend alembic upgrade head

# Check logs
docker-compose logs backend
```

### Issue: Celery worker not processing jobs

```bash
# Check worker logs
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Issue: Out of disk space

```bash
# Check disk usage
df -h

# Clean Docker resources
docker system prune -a --volumes

# Clean old images
docker image prune -a
```

### Issue: Memory issues

```bash
# Check memory usage
docker stats

# Limit memory per container
docker-compose.yml:
  celery-worker:
    mem_limit: 2g
```

---

## 🔒 Security Best Practices

### 1. Environment Variables

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use secrets management in production
# Example: Docker Swarm secrets, Kubernetes secrets, AWS Secrets Manager
```

### 2. Database Security

```yaml
# Only expose database port for development
# In production, remove ports section:
postgres:
  # ports:
  #   - "5432:5432"  # Comment this out
```

### 3. Network Security

```bash
# Setup firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# Restrict Docker network
docker network create --internal video-analysis-internal
```

### 4. SSL/TLS Configuration

```nginx
# Strong SSL configuration (nginx/conf.d/default.conf)
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

### 5. Rate Limiting

Already configured in `nginx/conf.d/default.conf`:
- API: 10 req/s with burst 20
- General: 30 req/s with burst 50

### 6. Regular Updates

```bash
# Update Docker images
docker-compose pull

# Rebuild services
docker-compose build --pull

# Update dependencies
docker-compose exec backend pip install --upgrade -r requirements.txt
```

---

## 🔄 Backup & Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres video_analysis > backup_$(date +%Y%m%d).sql

# Automated backup (add to crontab)
0 2 * * * /path/to/backup-script.sh
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U postgres video_analysis < backup.sql
```

### Backup Environment

```bash
# Backup environment file
cp .env .env.backup

# Store securely (encrypted)
gpg -c .env.backup
```

---

## 📞 Support & Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com
- Docker: https://docs.docker.com
- Next.js: https://nextjs.org/docs

### Troubleshooting Resources
- GitHub Issues: https://github.com/yourusername/video-analysis/issues
- Discord Community: [Your Discord Link]

### Performance Monitoring
- Setup Prometheus + Grafana (optional)
- Use Docker stats for basic monitoring
- Application logs untuk debugging

---

## 📝 License

[Your License Here]

## 👥 Contributors

[Your Team]

---

**Last Updated:** 2026-03-24  
**Version:** 1.0.0
