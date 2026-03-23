# 🚀 Video Analysis System - Production Ready

Sistem analisis video YouTube dengan AI menggunakan FastAPI, Next.js, dan Docker.

## ⚡ Quick Start (5 menit)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd video-analysis

# 2. Setup environment
cp .env.production .env
nano .env  # Edit API keys

# 3. Run!
./quick-start.sh
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📦 Apa yang Included?

### Docker Services
- **Backend API** (FastAPI + Uvicorn)
- **Frontend** (Next.js)
- **PostgreSQL** (dengan pgvector)
- **Redis** (message broker)
- **Celery Worker** (background jobs)
- **Celery Beat** (scheduler)
- **Nginx** (reverse proxy - production only)

### Production Features
✅ Multi-stage Docker builds (optimized size)  
✅ Health checks untuk semua services  
✅ Auto-restart containers  
✅ Database migrations otomatis  
✅ Nginx dengan rate limiting  
✅ SSL/HTTPS ready  
✅ Monitoring & logging scripts  
✅ Automated backups  
✅ Non-root user (security)  
✅ Environment variables management  
✅ Horizontal scaling ready  

## 📋 Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- OpenAI API Key
- YouTube Data API v3 Key

## 🔧 Deployment Methods

### Development
```bash
docker-compose up -d
```

### Production (with Nginx)
```bash
docker-compose --profile production up -d
```

### Production (with SSL)
```bash
# Setup SSL certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx config dengan SSL
nano nginx/conf.d/default.conf

# Deploy
docker-compose --profile production up -d
```

## 📊 Management Commands

```bash
# View logs
docker-compose logs -f

# Health check
./scripts/health-check.sh

# Database backup
./scripts/backup-database.sh

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Scale workers
docker-compose up -d --scale celery-worker=3
```

## 🔒 Security

✅ Environment variables tidak di-commit  
✅ Database password harus di-generate secure  
✅ SSL/TLS support  
✅ Rate limiting on API  
✅ Non-root containers  
✅ Firewall recommendations included  

## 📚 Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide (Bahasa Indonesia)
- **[API Documentation](http://localhost:8000/docs)** - OpenAPI/Swagger docs
- **[Project README](./README.md)** - Development guide

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python 3.12)
- PostgreSQL + pgvector
- Redis
- Celery
- OpenAI GPT-4
- yt-dlp

**Frontend:**
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS

**Infrastructure:**
- Docker & Docker Compose
- Nginx
- Let's Encrypt (SSL)

## 🌍 Production Deployment Scenarios

### 1. Single Server (VPS/Cloud)
```bash
# AWS EC2, DigitalOcean Droplet, etc.
ssh user@your-server
git clone <repo>
cd video-analysis
./quick-start.sh
```

### 2. Docker Swarm (Multi-node)
```bash
docker swarm init
docker stack deploy -c docker-compose.yml video-analysis
```

### 3. Kubernetes
```bash
# Generate k8s manifests
kompose convert -f docker-compose.yml
kubectl apply -f .
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale workers
docker-compose up -d --scale celery-worker=5

# Scale backend API
docker-compose up -d --scale backend=3
```

### Vertical Scaling
Edit `docker-compose.yml`:
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

## 🔍 Monitoring

Built-in health checks:
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000`
- Database: `pg_isready`
- Redis: `redis-cli ping`
- Celery: `celery inspect`

## 🆘 Troubleshooting

### Container tidak start
```bash
docker-compose logs <service-name>
docker-compose restart <service-name>
```

### Database issues
```bash
docker-compose exec backend alembic upgrade head
```

### Out of disk space
```bash
docker system prune -a --volumes
```

### Performance issues
```bash
docker stats  # Monitor resource usage
```

## 🤝 Support

- GitHub Issues: [Create Issue](https://github.com/yourusername/video-analysis/issues)
- Documentation: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Email: support@example.com

## 📄 License

MIT License - see LICENSE file

## 🎯 Next Steps

1. ✅ Setup environment variables
2. ✅ Run `./quick-start.sh`
3. ✅ Test with sample YouTube URL
4. ✅ Setup SSL for production
5. ✅ Configure backups
6. ✅ Setup monitoring/alerts

---

**Made with ❤️ for production deployment**

Last updated: 2026-03-24
