# Worker Health Monitor

Script untuk monitoring kesehatan Celery worker dan auto-restart jika worker hang/tidak responsif.

## Fitur

- **Health Check Berkala**: Mengirim ping task setiap 60 detik untuk mengecek responsif worker
- **Auto-Restart**: Otomatis restart worker jika tidak responsif setelah 3 kali gagal check
- **Restart Cooldown**: Menunggu 5 menit sebelum mencoba restart lagi setelah max attempts
- **Logging**: Semua aktivitas dicatat di `backend/worker_monitor.log`

## Cara Penggunaan

### 1. Jalankan Monitor (Foreground)

Dari root directory project:

```bash
backend/venv/bin/python backend/scripts/worker_monitor.py
```

### 2. Jalankan Monitor (Background)

```bash
backend/venv/bin/python backend/scripts/worker_monitor.py > backend/worker_monitor.log 2>&1 &
```

Simpan PID untuk stop nanti:
```bash
echo $! > backend/monitor.pid
```

### 3. Stop Monitor

```bash
# Jika ada PID file
kill $(cat backend/monitor.pid)

# Atau cari manual
pkill -f worker_monitor.py
```

### 4. Lihat Log

```bash
tail -f backend/worker_monitor.log
```

## Konfigurasi

Edit `backend/scripts/worker_monitor.py` untuk mengubah:

```python
CHECK_INTERVAL = 60          # Detik antara health checks
RESPONSE_TIMEOUT = 10        # Detik menunggu response
MAX_RESTART_ATTEMPTS = 3     # Max restart attempts berturut-turut
RESTART_COOLDOWN = 300       # Detik cooldown setelah max restarts
```

## Log Output

Monitor akan log aktivitas seperti:

```
2026-03-25 14:00:00 - INFO - Worker health monitor started
2026-03-25 14:00:00 - INFO - Check interval: 60s, Response timeout: 10s
2026-03-25 14:01:00 - DEBUG - Worker health check: OK
2026-03-25 14:02:00 - ERROR - Worker health check: TIMEOUT - Worker not responding
2026-03-25 14:02:00 - WARNING - Worker health check failed (1/3)
2026-03-25 14:03:00 - ERROR - Worker health check: TIMEOUT - Worker not responding
2026-03-25 14:03:00 - WARNING - Worker health check failed (2/3)
2026-03-25 14:04:00 - ERROR - Worker health check: TIMEOUT - Worker not responding
2026-03-25 14:04:00 - WARNING - Worker health check failed (3/3)
2026-03-25 14:04:00 - WARNING - Attempting to restart worker...
2026-03-25 14:04:00 - INFO - Sending SIGTERM to worker process 12345
2026-03-25 14:04:02 - INFO - Worker process 12345 terminated gracefully
2026-03-25 14:04:05 - INFO - Starting new worker process...
2026-03-25 14:04:10 - INFO - Worker started successfully (PID: 12346)
2026-03-25 14:04:10 - INFO - Worker restarted successfully
2026-03-25 14:05:00 - DEBUG - Worker health check: OK
2026-03-25 14:05:00 - INFO - Worker recovered
```

## Troubleshooting

### Monitor tidak bisa start worker

Pastikan path ke celery binary benar di `WORKER_COMMAND`. Default:
```python
WORKER_COMMAND = [
    str(BACKEND_DIR / 'venv' / 'bin' / 'celery'),
    '-A', 'celery_app',
    'worker',
    '--pool=solo',
    '--loglevel=info',
    '--time-limit=1800',
    '--soft-time-limit=1500'
]
```

### Health check selalu timeout

1. Cek worker sedang sibuk processing video panjang (normal)
2. Cek Redis connection: `redis-cli ping`
3. Cek worker log: `tail -f backend/worker.log`

### Monitor restart terus-menerus

- Kemungkinan worker crash saat start
- Cek `backend/worker_error.log` untuk error
- Cek dependencies: `cd backend && venv/bin/pip list`

## Integration dengan Systemd (Production)

Untuk production, buat systemd service:

```ini
# /etc/systemd/system/video-analysis-monitor.service
[Unit]
Description=Video Analysis Worker Monitor
After=redis.service postgresql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/video-analysis
ExecStart=/path/to/video-analysis/backend/venv/bin/python backend/scripts/worker_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable dan start:
```bash
sudo systemctl enable video-analysis-monitor
sudo systemctl start video-analysis-monitor
sudo systemctl status video-analysis-monitor
```
