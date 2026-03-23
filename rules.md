# Copilot Rules — Video Analysis AI

Dokumen ini adalah aturan wajib yang harus diikuti Copilot saat mengerjakan project ini. Baca seluruh file ini sebelum menulis satu baris kode pun.

---

## 1. Prinsip Umum

- Selalu baca `project.md` terlebih dahulu untuk memahami arsitektur dan konteks project
- Jangan menambah library baru tanpa alasan yang jelas — gunakan yang sudah ada di stack
- Jangan over-engineer: pilih solusi paling sederhana yang memenuhi kebutuhan
- Setiap file baru harus mengikuti struktur direktori yang sudah didefinisikan di `project.md`
- Jangan pernah hardcode secret, API key, atau credential — selalu ambil dari environment variable

---

## 2. Aturan Python (Backend)

### Versi & Environment
- Gunakan **Python 3.11+**
- Semua dependency ada di `backend/requirements.txt`
- Jalankan di virtual environment — jangan install global

### Style & Formatting
- Formatter: **Black** (line length 88)
- Linter: **Ruff**
- Gunakan **type hints** di semua fungsi, parameter, dan return value
- Gunakan **docstring** untuk setiap class dan fungsi publik (format Google style)

```python
# BENAR
def extract_frames(video_path: str, max_frames: int = 30) -> list[str]:
    """Extract key frames dari video menggunakan PySceneDetect.

    Args:
        video_path: Path absolut ke file video.
        max_frames: Jumlah maksimum frames yang diekstrak.

    Returns:
        List path absolut ke file frame yang tersimpan.
    """
    ...

# SALAH — tidak ada type hints, tidak ada docstring
def extract_frames(video_path, max_frames):
    ...
```

### FastAPI
- Selalu gunakan **Pydantic v2** untuk request/response schema
- Gunakan `APIRouter` untuk setiap grup endpoint — jangan taruh semua di `main.py`
- Gunakan `async def` untuk semua endpoint
- Selalu kembalikan response dengan status code yang tepat
- Gunakan `HTTPException` untuk error handling, bukan raise generic Exception

```python
# BENAR
@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(body: JobCreate, db: AsyncSession = Depends(get_db)):
    ...

# SALAH
@app.post("/jobs")
def create_job(body: dict):
    ...
```

### Celery Tasks
- Setiap step pipeline harus update progress ke Redis setelah selesai
- Gunakan `try/except` di setiap task — jika error, update status job ke `failed` dan simpan `error_message`
- Jangan simpan object besar di task result — simpan ke DB dan return hanya ID

```python
# BENAR
@celery_app.task(bind=True)
def run_pipeline(self, job_id: str) -> None:
    try:
        update_job_status(job_id, "downloading", progress=10)
        ...
    except Exception as e:
        update_job_status(job_id, "failed", error_message=str(e))
        raise
```

### Database
- Selalu gunakan **async session** SQLAlchemy
- Setiap perubahan schema harus disertai **Alembic migration** — jangan edit tabel manual
- Gunakan `select()` bukan `query()` (SQLAlchemy 2.0 style)

### File Temp
- Semua file temp (video, audio, frames) disimpan di `TEMP_DIR/{job_id}/`
- Selalu hapus folder temp setelah job selesai atau gagal — jangan biarkan menumpuk
- Gunakan `pathlib.Path` bukan `os.path`

---

## 3. Aturan TypeScript (Frontend)

### Versi & Environment
- **TypeScript strict mode** wajib aktif di `tsconfig.json`
- Package manager: **pnpm**
- Node versi: 20+

### Style & Formatting
- Formatter: **Prettier** (single quote, no semicolon, tab width 2)
- Linter: **ESLint** dengan config Next.js
- Hindari `any` — gunakan tipe yang benar atau `unknown` jika perlu

```typescript
// BENAR
interface Job {
  id: string
  status: JobStatus
  progress: number
  analysis: AnalysisResult | null
}

// SALAH
const job: any = ...
```

### Next.js App Router
- Gunakan **Server Components** sebagai default — gunakan `'use client'` hanya jika benar-benar perlu interaktivitas
- Data fetching dilakukan di Server Component, bukan di `useEffect`
- Gunakan `loading.tsx` dan `error.tsx` untuk setiap route segment

```typescript
// BENAR — Server Component
export default async function JobPage({ params }: { params: { id: string } }) {
  const job = await fetchJob(params.id)
  return <AnalysisResult job={job} />
}

// SALAH — mengambil data di client
'use client'
export default function JobPage() {
  const [job, setJob] = useState(null)
  useEffect(() => { fetch(...).then(...) }, [])
}
```

### SSE / Live Progress
- Implementasi SSE di `ProgressStream.tsx` menggunakan `EventSource` API
- Tutup koneksi SSE saat komponen unmount (`useEffect` cleanup)
- Tampilkan progress bar yang smooth — update state hanya jika nilai progress berubah

```typescript
// BENAR
useEffect(() => {
  const es = new EventSource(`/api/jobs/${jobId}/stream`)
  es.onmessage = (e) => {
    const data = JSON.parse(e.data)
    setProgress(data.progress)
    setStatus(data.status)
    if (data.status === 'done' || data.status === 'failed') es.close()
  }
  return () => es.close()  // cleanup wajib
}, [jobId])
```

### Komponen
- Satu file = satu komponen utama
- Props selalu didefinisikan dengan `interface`, bukan `type` untuk object shape
- Gunakan named export, bukan default export untuk komponen (kecuali page.tsx)

---

## 4. Aturan API Contract

- URL selalu menggunakan **kebab-case**: `/api/jobs`, `/api/jobs/{id}/stream`
- Request body dan response selalu **JSON**
- Semua response error mengikuti format:
```json
{ "detail": "Pesan error yang jelas" }
```
- Semua response sukses untuk list mengikuti format:
```json
{ "data": [...], "total": 100, "limit": 20, "offset": 0 }
```
- Jangan expose detail internal error (stack trace, path file) ke client

---

## 5. Aturan Environment & Konfigurasi

- Semua config dibaca dari `.env` via `python-dotenv` (backend) dan `next.config.js` (frontend)
- File `.env` tidak boleh di-commit — hanya `.env.example` yang boleh
- Backend config terpusat di `backend/core/config.py` menggunakan Pydantic `BaseSettings`

```python
# backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str
    redis_url: str
    temp_dir: str = "/tmp/video-analysis"
    max_video_duration: int = 1800
    max_frames: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 6. Aturan Error Handling

- Backend: setiap service function harus raise exception spesifik, bukan generic `Exception`
- Buat custom exception di `backend/core/exceptions.py`:
  - `VideoTooLongError`
  - `InvalidYouTubeUrlError`
  - `DownloadFailedError`
  - `TranscriptionFailedError`
  - `AnalysisFailedError`
- Frontend: semua error dari API ditampilkan ke user dengan pesan yang ramah — jangan tampilkan raw error message

---

## 7. Aturan Git & Commit

- Branch naming: `feature/nama-fitur`, `fix/nama-bug`, `chore/nama-task`
- Commit message format (Conventional Commits):
  - `feat: tambah endpoint POST /jobs`
  - `fix: perbaiki SSE disconnect saat job done`
  - `chore: update requirements.txt`
  - `refactor: pisahkan logic download ke service terpisah`
- Satu commit = satu perubahan logis — jangan campur banyak hal dalam satu commit

---

## 8. Urutan Pengerjaan yang Disarankan

Kerjakan dalam urutan ini agar bisa test end-to-end secepatnya:

1. Setup project structure (folder, virtual env, pnpm init)
2. Setup database + Alembic migration untuk tabel `jobs`
3. Buat Celery app + Redis connection
4. Implementasi processing pipeline (downloader → transcriber → extractor → analyzer)
5. Buat FastAPI endpoints (`POST /jobs`, `GET /jobs/{id}`)
6. Implementasi SSE stream (`GET /jobs/{id}/stream`)
7. Buat frontend: form input URL + panggil `POST /jobs`
8. Buat komponen `ProgressStream` dengan SSE
9. Buat halaman hasil analisa
10. Buat halaman riwayat (`GET /jobs`)
11. Polish UI + error states + loading states

---

## 9. Hal yang Dilarang

- Jangan gunakan `print()` untuk logging — gunakan `logging` module atau `loguru`
- Jangan gunakan `time.sleep()` di dalam async function — gunakan `asyncio.sleep()`
- Jangan commit file video, audio, atau frame ke repository
- Jangan gunakan `SELECT *` di query database — selalu sebut kolom secara eksplisit
- Jangan proses video lebih dari `MAX_VIDEO_DURATION` detik — validasi di awal sebelum download
- Jangan kirim lebih dari `MAX_FRAMES` gambar ke GPT-4o dalam satu request
