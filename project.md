# Video Analysis AI — Project Specification

## Overview

Aplikasi web untuk menganalisa konten video YouTube secara otomatis menggunakan AI multimodal (GPT-4o). User memasukkan URL YouTube, sistem mendownload video, mengekstrak audio dan key frames, lalu mengirimkan semua data ke GPT-4o untuk analisa mendalam.

---

## Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **State management**: Zustand
- **HTTP client**: Axios / native fetch
- **Live progress**: Server-Sent Events (SSE)

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Task queue**: Celery
- **Message broker**: Redis
- **ORM**: SQLAlchemy + Alembic (migrations)
- **Validation**: Pydantic v2

### Processing
- **Video download**: yt-dlp
- **Audio transcription**: mlx-whisper (native Apple Silicon)
- **Frame extraction**: OpenCV + PySceneDetect
- **AI analysis**: OpenAI GPT-4o API (multimodal)

### Storage
- **Database**: PostgreSQL 16
- **Cache / broker**: Redis
- **Temp files**: Local filesystem (`/tmp/video-analysis/`)

### Dev Tools
- **Python env**: pyenv + virtualenv
- **Package manager (frontend)**: pnpm
- **Process runner**: Makefile
- **Linter**: Ruff (Python), ESLint (TypeScript)
- **Formatter**: Black (Python), Prettier (TypeScript)

---

## Project Structure

```
video-analysis/
├── frontend/                  # Next.js app
│   ├── app/
│   │   ├── page.tsx           # Home — input URL form
│   │   ├── jobs/
│   │   │   └── [id]/
│   │   │       └── page.tsx   # Detail hasil analisa
│   │   └── history/
│   │       └── page.tsx       # Riwayat semua job
│   ├── components/
│   │   ├── UrlForm.tsx
│   │   ├── ProgressStream.tsx
│   │   ├── AnalysisResult.tsx
│   │   └── JobHistory.tsx
│   ├── lib/
│   │   └── api.ts
│   └── package.json
│
├── backend/                   # FastAPI app
│   ├── main.py                # Entry point
│   ├── routers/
│   │   ├── jobs.py            # POST /jobs, GET /jobs, GET /jobs/{id}
│   │   └── stream.py          # GET /jobs/{id}/stream (SSE)
│   ├── services/
│   │   ├── downloader.py      # yt-dlp wrapper
│   │   ├── transcriber.py     # mlx-whisper wrapper
│   │   ├── extractor.py       # OpenCV + PySceneDetect
│   │   └── analyzer.py        # GPT-4o API call
│   ├── tasks/
│   │   └── pipeline.py        # Celery task — orchestrate semua step
│   ├── models/
│   │   └── job.py             # SQLAlchemy models
│   ├── schemas/
│   │   └── job.py             # Pydantic schemas
│   ├── db/
│   │   └── session.py         # DB session
│   ├── core/
│   │   └── config.py          # Settings dari .env
│   ├── celery_app.py
│   └── requirements.txt
│
├── .env.example
├── Makefile
└── README.md
```

---

## Database Schema

### Table: `jobs`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `youtube_url` | TEXT | Input dari user |
| `video_title` | TEXT | Dari metadata yt-dlp |
| `video_duration` | INTEGER | Durasi dalam detik |
| `status` | ENUM | `pending`, `downloading`, `transcribing`, `extracting`, `analyzing`, `done`, `failed` |
| `progress` | INTEGER | 0–100 |
| `transcript` | TEXT | Hasil Whisper |
| `frames_count` | INTEGER | Jumlah key frames yang diekstrak |
| `analysis` | JSONB | Hasil analisa dari GPT-4o |
| `error_message` | TEXT | Isi error jika gagal |
| `created_at` | TIMESTAMP | Auto |
| `updated_at` | TIMESTAMP | Auto |

---

## API Endpoints

### `POST /api/jobs`
Terima YouTube URL, buat job baru, jalankan Celery task.

**Request body:**
```json
{ "youtube_url": "https://www.youtube.com/watch?v=..." }
```

**Response:**
```json
{ "job_id": "uuid", "status": "pending" }
```

### `GET /api/jobs`
Ambil semua jobs (riwayat). Support query param `?limit=20&offset=0`.

### `GET /api/jobs/{id}`
Ambil detail satu job beserta hasil analisa.

### `GET /api/jobs/{id}/stream`
SSE endpoint untuk live progress. Stream event berupa:
```
data: {"status": "transcribing", "progress": 40, "message": "Mentranskrip audio..."}
```

### `DELETE /api/jobs/{id}`
Hapus job dan file temp terkait.

---

## Processing Pipeline

Setiap job menjalankan langkah berikut secara berurutan di Celery worker:

1. **Download** — `yt-dlp` download video + extract audio (MP3). Update status → `downloading` (progress 10%)
2. **Transcribe** — `mlx-whisper` transkripsi audio ke teks. Update status → `transcribing` (progress 30%)
3. **Extract frames** — `PySceneDetect` detect scene changes, `OpenCV` capture frame di setiap scene. Update status → `extracting` (progress 60%)
4. **Analyze** — Susun prompt dari transkripsi + key frames (sebagai base64 image), kirim ke GPT-4o. Update status → `analyzing` (progress 85%)
5. **Save** — Simpan hasil ke PostgreSQL, hapus file temp. Update status → `done` (progress 100%)

Setiap update status dipush ke Redis channel `job:{id}:progress` dan di-stream ke frontend via SSE.

---

## Analysis Output Format

GPT-4o diminta mengembalikan JSON terstruktur:

```json
{
  "summary": "Ringkasan singkat isi video (2-3 kalimat)",
  "topics": ["topik 1", "topik 2"],
  "key_points": [
    { "timestamp": "00:01:23", "point": "Poin penting dari video" }
  ],
  "sentiment": "positive | neutral | negative",
  "language": "id | en | ...",
  "content_type": "tutorial | vlog | news | review | other",
  "insights": "Analisa mendalam tentang isi dan pesan video"
}
```

---

## Environment Variables

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/video_analysis

# Redis
REDIS_URL=redis://localhost:6379/0

# App
TEMP_DIR=/tmp/video-analysis
MAX_VIDEO_DURATION=1800   # detik, default 30 menit
MAX_FRAMES=30             # maksimum key frames yang dikirim ke GPT-4o
WHISPER_MODEL=mlx-community/whisper-large-v3-mlx
```

---

## Makefile Commands

```makefile
dev-frontend:   # cd frontend && pnpm dev
dev-backend:    # uvicorn backend.main:app --reload --port 8000
dev-worker:     # celery -A backend.celery_app worker --loglevel=info
dev-redis:      # redis-server
dev:            # jalankan semua sekaligus
migrate:        # alembic upgrade head
install:        # install semua dependency frontend + backend
```

---

## Platform Notes (macOS M1)

- Gunakan Python native ARM via `pyenv` — hindari Rosetta
- `mlx-whisper` memanfaatkan Neural Engine M1, jauh lebih cepat dari CPU
- PostgreSQL dan Redis install via `brew install postgresql@16 redis`
- Hindari Docker untuk development — install semua native agar performa optimal
- `opencv-python` gunakan versi headless: `pip install opencv-python-headless`
