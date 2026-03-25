# Video Analysis AI

Aplikasi web untuk menganalisa konten video YouTube secara otomatis menggunakan AI multimodal (GPT-4o).

## 🚀 Quick Start

**Production Deployment:**
- 🐳 [Docker Deployment Guide](./DOCKER_DEPLOYMENT.md) - Lengkap dengan monitoring, backup, security
- ⚡ [Portainer Quick Start](./PORTAINER_QUICKSTART.md) - 5 menit setup via Portainer Stack
- 🛠️ [Service Management Scripts](./scripts/README.md) - Automated start/stop/restart/status

**Development Setup:** Lihat [Local Development](#setup) section di bawah

## Features

- 🎥 Download video YouTube otomatis
- 🎤 Transkripsi audio menggunakan mlx-whisper (optimized for Apple Silicon)
- 🖼️ Ekstraksi key frames dengan scene detection
- 🤖 Analisa mendalam menggunakan GPT-4o multimodal
- 📊 Real-time progress tracking dengan SSE
- 📝 Hasil analisa terstruktur (summary, topics, key points, sentiment)

## Tech Stack

### Frontend
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- Zustand (state management)

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL 16
- Redis
- Celery (task queue)
- SQLAlchemy + Alembic

### Processing
- yt-dlp (video download)
- mlx-whisper (audio transcription)
- OpenCV + PySceneDetect (frame extraction)
- OpenAI GPT-4o (AI analysis)

## Prerequisites

- Python 3.11+ (installed via pyenv, native ARM for M1)
- Node.js 20+
- pnpm
- PostgreSQL 16
- Redis

### macOS Installation

```bash
# Install Homebrew dependencies
brew install postgresql@16 redis pyenv

# Install Python 3.11
pyenv install 3.11.9
pyenv local 3.11.9

# Install pnpm (if not already installed)
npm install -g pnpm
```

## Setup

### 1. Initial Setup

```bash
# Run initial setup (creates virtual environment + installs all dependencies)
make setup
```

Or if you want to install manually:

```bash
# Create Python virtual environment
python3 -m venv backend/venv

# Install frontend dependencies
cd frontend && pnpm install

# Install backend dependencies
source backend/venv/bin/activate
cd backend && pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string (use `postgresql+asyncpg://` for async)
- `REDIS_URL` - Redis connection string

### 3. Setup Database

```bash
# Start PostgreSQL
brew services start postgresql@16

# Create database
createdb video_analysis

# Run migrations
make migrate
```

### 4. Start Development Servers

**Option 1: Restart All Services (RECOMMENDED - Paling Reliable)**

Script ini akan kill semua proses yang berjalan dan start ulang dengan verifikasi lengkap:

```bash
# Using restart script (recommended)
./restart.sh

# Or using make
make restart
```

Features restart script:
- ✅ Kill semua proses development (backend, frontend, worker) secara otomatis
- ✅ Verifikasi port 8000 dan 3000 sudah bebas
- ✅ Check prerequisites (venv, Redis, PostgreSQL, pnpm)
- ✅ Start Redis jika belum running
- ✅ Start semua services dengan proper error handling
- ✅ Verifikasi semua services berjalan dengan baik
- ✅ Colorful output untuk mudah dibaca

**Stop All Services:**
```bash
# Using stop script (recommended)
./stop.sh

# Or using make
make stop
```

**Option 2: Run all services at once**

```bash
# Using the shell script
./dev.sh

# Or using make
make dev-all
```

This will start all services (Redis, Backend, Worker, Frontend) and display their logs. Press Ctrl+C to stop all services.

**Option 3: Run each service in separate terminals**

You need to run these in **separate terminals**:

```bash
# Terminal 1: Redis
make dev-redis

# Terminal 2: Backend API
make dev-backend

# Terminal 3: Celery Worker
make dev-worker

# Terminal 4: Frontend
make dev-frontend
```

**Logs Location:**
- Backend: `backend.log` (project root)
- Worker: `worker.log` (project root)
- Frontend: `frontend.log` (project root)
- Dev.sh logs: `/tmp/video-analysis-*.log`

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
video-analysis/
├── frontend/              # Next.js 15 application
│   ├── app/              # App Router pages
│   ├── components/       # React components
│   └── lib/              # Utilities and API client
├── backend/              # FastAPI application
│   ├── main.py           # App entry point
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── tasks/            # Celery tasks
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── db/               # Database configuration
│   └── core/             # Core settings and exceptions
├── .env.example          # Environment variables template
├── Makefile              # Development commands
└── README.md
```

## API Endpoints

### Jobs
- `POST /api/jobs` - Create new analysis job
- `GET /api/jobs` - List all jobs (with pagination)
- `GET /api/jobs/{id}` - Get job details
- `DELETE /api/jobs/{id}` - Delete job
- `GET /api/jobs/{id}/stream` - SSE stream for real-time progress

## Development Commands

```bash
make help              # Show all available commands
make setup             # Initial setup (create venv + install dependencies)
make install           # Install all dependencies (if venv exists)

# Running services
./dev.sh               # Run all services at once (Recommended)
make dev-all           # Alternative: Run all services using make
make dev-redis         # Run Redis only
make dev-backend       # Run Backend only
make dev-worker        # Run Celery worker only
make dev-frontend      # Run Frontend only
make stop              # Stop all running services

# Database
make migrate           # Run database migrations
make migrate-create    # Create new migration

# Code quality
make clean             # Clean temporary files (including venv)
make format            # Format code (black + prettier)
make lint              # Lint code (ruff + eslint)
```

## Processing Pipeline

1. **Download** (10%) - Download video and extract audio using yt-dlp
2. **Transcribe** (30%) - Transcribe audio to text using mlx-whisper
3. **Extract Frames** (60%) - Detect scenes and capture key frames
4. **Analyze** (85%) - Send transcript + frames to GPT-4o for analysis
5. **Done** (100%) - Save results to database

## Configuration

Key settings in `.env`:

```env
# Maximum video duration (seconds)
MAX_VIDEO_DURATION=1800

# Maximum frames to extract
MAX_FRAMES=30

# Whisper model
WHISPER_MODEL=mlx-community/whisper-large-v3-mlx

# Temporary directory for processing
TEMP_DIR=/tmp/video-analysis

# YouTube Cookies (Optional - untuk menghindari bot detection)
# Export cookies dari browser: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp
YOUTUBE_COOKIES_PATH=/path/to/cookies.txt
```

### YouTube Cookies Setup (RECOMMENDED untuk Bulk Analysis)

**yt-dlp versi terbaru (2026.3.17)** sudah support ekstrak cookies langsung dari browser tanpa perlu export manual!

**Option 1: Cookies dari Browser Otomatis (RECOMMENDED)**

```bash
# Edit .env file
YOUTUBE_COOKIES_BROWSER=chrome  # atau firefox, edge, safari
```

**Supported browsers:**
- `chrome` - Google Chrome
- `firefox` - Mozilla Firefox  
- `edge` - Microsoft Edge
- `safari` - Safari (macOS)
- `brave` - Brave Browser
- `opera` - Opera
- `chromium` - Chromium

**Pastikan:** Anda sudah login ke YouTube di browser tersebut.

**Option 2: Export Manual Cookies.txt (Fallback)**

Jika cookies from browser tidak bekerja:

1. **Install Browser Extension:**
   - Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Export Cookies:**
   - Login ke YouTube di browser
   - Klik extension dan pilih "Export" untuk youtube.com
   - Save sebagai `www.youtube.com_cookies.txt` di root project

3. **Configure:**
   ```bash
   # Di file .env, set path:
   YOUTUBE_COOKIES_PATH=/path/to/www.youtube.com_cookies.txt
   ```

4. **Restart Celery Worker:**
   ```bash
   make restart
   # atau
   ./restart.sh
   ```

**Catatan:** Cookies akan expired setelah beberapa waktu, jadi perlu di-export ulang jika mulai gagal lagi.


## Platform Notes (macOS M1/M2)

- Uses Python native ARM (not Rosetta) for optimal performance
- mlx-whisper leverages Apple Neural Engine for fast transcription
- All dependencies installed natively (no Docker)
- opencv-python-headless used to avoid GUI dependencies

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
brew services list

# Restart if needed
brew services restart postgresql@16
```

### Redis Connection Error
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

### Celery Worker Not Processing
```bash
# Check Redis connection
redis-cli ping

# Restart worker
make dev-worker
```

### YouTube Bot Detection Error

Jika muncul error **"Sign in to confirm you're not a bot"** saat bulk analysis:

1. Export cookies dari browser (lihat bagian **YouTube Cookies Setup** di atas)
2. Set `YOUTUBE_COOKIES_PATH` di file `.env`
3. Restart Celery worker: `make restart` atau `./restart.sh`

Solusi lain yang sudah diimplementasikan:
- ✅ Sequential queue processing dengan delay 30 detik antar job
- ✅ Automatic retry dengan exponential backoff (3x retry)
- ✅ User-agent yang lebih natural (Chrome)
- ✅ Referer header (youtube.com)
- ✅ Fragment retries untuk download yang terputus

Jika masih gagal setelah menggunakan cookies:
- Cookies sudah expired (export ulang dari browser)
- IP Anda di-rate limit YouTube (tunggu beberapa jam atau gunakan VPN)
- Video memang private/restricted

Jika masih gagal setelah menggunakan cookies, kemungkinan:
- Cookies sudah expired (export ulang)
- IP Anda di-rate limit YouTube (tunggu beberapa jam)
- Video memang private/restricted

## License

MIT

## Contributing

Contributions are welcome! Please read the rules.md file for coding standards.
