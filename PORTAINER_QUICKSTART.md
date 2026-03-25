# 🚀 Quick Start - Portainer Deployment

Panduan singkat untuk deploy Video Analysis menggunakan Portainer Stack.

## ⚡ 5 Menit Setup

### Step 1: Akses Portainer

Buka browser dan akses Portainer Anda:
```
http://your-server-ip:9000
```

### Step 2: Create Stack

1. Login ke Portainer
2. Pilih Environment → **local**
3. Sidebar → **Stacks**
4. Click **+ Add stack**

### Step 3: Konfigurasi Stack

**Name:** `video-analysis`

**Build method:** Pilih **Repository**

**Repository Configuration:**
- **Repository URL:** `https://github.com/yourusername/video-analysis`
- **Repository reference:** `refs/heads/main`
- **Compose path:** `docker-compose.yml`
- **Automatic updates:** Enable (optional)

### Step 4: Environment Variables

Scroll ke **Environment variables**, tambahkan:

```env
# REQUIRED - OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key-here

# REQUIRED - YouTube API Key
YOUTUBE_API_KEY=your-youtube-api-key-here

# REQUIRED - Database Password
POSTGRES_PASSWORD=your-secure-password-here

# REQUIRED - API URL (ganti dengan IP server Anda)
NEXT_PUBLIC_API_URL=http://your-server-ip:8000

# Database Configuration (default values OK)
POSTGRES_USER=postgres
POSTGRES_DB=video_analysis

# Redis Configuration (default values OK)
REDIS_URL=redis://redis:6379/0

# Optional - YouTube Cookies for avoiding bot detection
YOUTUBE_COOKIES_BROWSER=chrome

# Optional - Worker Monitor Settings
WORKER_HEALTH_CHECK_INTERVAL=60
WORKER_HEALTH_CHECK_TIMEOUT=10
WORKER_MAX_RESTART_ATTEMPTS=3
WORKER_RESTART_COOLDOWN=300
```

### Step 5: Deploy

1. Click **Deploy the stack**
2. Wait 5-10 minutes untuk:
   - Download images
   - Build containers
   - Run database migrations
   - Start all services

### Step 6: Verifikasi

**Check Container Status:**
```
Portainer → Containers → Filter: "video-analysis"
```

Pastikan semua container **Running** (hijau):
- ✅ video-analysis-postgres
- ✅ video-analysis-redis  
- ✅ video-analysis-backend
- ✅ video-analysis-celery-worker
- ✅ video-analysis-worker-monitor
- ✅ video-analysis-frontend

**Access Application:**
- Frontend: `http://your-server-ip:3000`
- Backend API: `http://your-server-ip:8000`
- API Docs: `http://your-server-ip:8000/docs`

---

## 🎯 Alternative: Web Editor Method

Jika repository Anda private atau ingin custom:

### Step 1-2: Same as above

### Step 3: Pilih Web Editor

**Build method:** Pilih **Web editor**

### Step 4: Copy-Paste Docker Compose

Copy seluruh content dari `docker-compose.yml` ke editor.

**IMPORTANT:** Ganti image references jika Anda build sendiri:

```yaml
# Ganti dari:
build:
  context: ./backend

# Menjadi:
image: ghcr.io/yourusername/video-analysis-backend:latest
```

### Step 5-6: Same as above

---

## 🔧 Build Custom Images

Jika menggunakan **Web Editor method**, build dan push images dulu:

### GitHub Container Registry (GHCR)

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build & Push Backend
docker build -t ghcr.io/USERNAME/video-analysis-backend:latest ./backend
docker push ghcr.io/USERNAME/video-analysis-backend:latest

# Build & Push Frontend
docker build -t ghcr.io/USERNAME/video-analysis-frontend:latest ./frontend
docker push ghcr.io/USERNAME/video-analysis-frontend:latest
```

### Docker Hub

```bash
# Login
docker login

# Build & Push Backend
docker build -t USERNAME/video-analysis-backend:latest ./backend
docker push USERNAME/video-analysis-backend:latest

# Build & Push Frontend
docker build -t USERNAME/video-analysis-frontend:latest ./frontend
docker push USERNAME/video-analysis-frontend:latest
```

---

## 📋 Environment Variables Quick Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key |
| `YOUTUBE_API_KEY` | ✅ Yes | - | YouTube Data API v3 key |
| `POSTGRES_PASSWORD` | ✅ Yes | - | Database password |
| `NEXT_PUBLIC_API_URL` | ✅ Yes | - | Public API URL |
| `POSTGRES_USER` | ❌ No | postgres | Database username |
| `POSTGRES_DB` | ❌ No | video_analysis | Database name |
| `REDIS_URL` | ❌ No | redis://redis:6379/0 | Redis connection URL |
| `YOUTUBE_COOKIES_BROWSER` | ❌ No | chrome | Browser for cookie extraction |
| `WORKER_HEALTH_CHECK_INTERVAL` | ❌ No | 60 | Health check interval (seconds) |

---

## 🩺 Health Check

### Via Browser

```
http://your-server-ip:8000/health
http://your-server-ip:3000
http://your-server-ip:8000/api/worker/status
```

### Via Portainer Console

1. **Navigate:** Containers → **video-analysis-backend** → **Console**
2. **Connect:** Click **Connect**
3. **Run:**
   ```bash
   curl http://localhost:8000/health
   ```

---

## 📊 Monitoring

### View Logs

**Portainer:** Containers → Select container → **Logs**

Enable:
- ✅ Auto-refresh
- ✅ Timestamps
- Set lines: 100

### Container Stats

**Portainer:** Containers → Select container → **Stats**

Monitor:
- CPU usage
- Memory usage
- Network I/O
- Block I/O

---

## 🔄 Common Operations

### Restart Service

```
Portainer → Containers → Select container → Restart
```

### View Container Logs

```
Portainer → Containers → Select container → Logs
```

### Execute Commands

```
Portainer → Containers → Select container → Console → Connect
```

### Update Stack

```
Portainer → Stacks → video-analysis → Editor → Update the stack
```

### Stop All Services

```
Portainer → Stacks → video-analysis → Stop this stack
```

### Remove Stack

```
Portainer → Stacks → video-analysis → Delete this stack
```
⚠️ **Warning:** This will remove all containers and volumes!

---

## 🆘 Troubleshooting

### Container Not Starting

**Check logs:**
```
Portainer → Containers → Select container → Logs
```

**Common issues:**
- Missing environment variables
- Port already in use
- Out of memory
- Database connection failed

### Database Connection Error

**Check PostgreSQL logs:**
```
Portainer → Containers → video-analysis-postgres → Logs
```

**Verify:**
- PostgreSQL is running (green status)
- `POSTGRES_PASSWORD` is set correctly
- `DATABASE_URL` format is correct

### Worker Not Processing Jobs

**Check worker status:**
```bash
# Via Portainer Console on backend container:
curl http://localhost:8000/api/worker/status
```

**Restart worker:**
```
Portainer → Containers → video-analysis-celery-worker → Restart
```

### Frontend Can't Connect to Backend

**Verify `NEXT_PUBLIC_API_URL`:**
```env
# Should be your server's IP, not localhost!
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000
```

**Restart frontend:**
```
Portainer → Containers → video-analysis-frontend → Restart
```

---

## 🎉 Done!

Your Video Analysis application is now running!

**URLs:**
- 🌐 Frontend: `http://your-server-ip:3000`
- 🔧 API Docs: `http://your-server-ip:8000/docs`
- 📊 Worker Status: `http://your-server-ip:3000/worker`

**Next Steps:**
1. Test video analysis dengan URL YouTube
2. Monitor worker status
3. Setup domain & SSL (optional)
4. Configure backups

**Need Help?**
- Full documentation: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- GitHub Issues: https://github.com/yourusername/video-analysis/issues

Happy analyzing! 🚀🎬
