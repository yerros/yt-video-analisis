# Server Deployment Instructions

## ✅ Quick Update & Build (Recommended)

Gunakan script otomatis yang sudah dibuat:

```bash
cd ~/yt-video-analisis
git pull origin main
bash update-and-build.sh
```

Script akan otomatis:
- ✓ Pull latest changes dari git
- ✓ Verify semua file yang dibutuhkan ada
- ✓ Clean Docker cache
- ✓ Build backend image
- ✓ Build frontend image

---

## 📋 Manual Steps (Alternative)

Jika ingin manual step-by-step:

### 1. Pull Latest Changes

```bash
cd ~/yt-video-analisis
git pull origin main
```

### 2. Verify Files

Pastikan file-file ini ada:

```bash
ls -la backend/.dockerignore        # Harus ada!
ls -la frontend/.dockerignore       # Harus ada!
ls -la frontend/lib/api.ts          # Harus ada!
ls -la frontend/lib/types.ts        # Harus ada!
cat backend/requirements.txt | grep pydantic  # Harus: pydantic==2.11.7
```

### 3. Clean Docker Cache

```bash
docker-compose down
docker system prune -f
```

### 4. Build Images

```bash
# Build backend (akan lebih cepat dengan .dockerignore)
docker-compose build --no-cache backend

# Build frontend (akan lebih cepat dengan .dockerignore)
docker-compose build --no-cache frontend
```

### 5. Verify Images

```bash
docker images | grep video-analysis
```

Should show:
- `yt-video-analisis_backend` (~831MB)
- `yt-video-analisis_frontend` (~70MB)

### 6. Start Services

```bash
docker-compose up -d
```

---

## 🔧 Files Updated in Latest Push

### New Files:
1. **backend/.dockerignore** - Reduces build context from 1.8GB → 349MB (81% reduction!)
2. **frontend/.dockerignore** - Reduces build context to 6.2MB
3. **update-and-build.sh** - Automated deployment script

### Modified Files (Already in Previous Commits):
1. **backend/requirements.txt** - Updated `pydantic==2.10.5` → `pydantic==2.11.7`
2. **frontend/app/worker/page.tsx** - Fixed ESLint error (apostrophe escape)

---

## ⚠️ Known Issues & Solutions

### Issue: "Module not found: Can't resolve '@/lib/api'"

**Cause:** File `frontend/lib/api.ts` tidak ada di server

**Solution:**
```bash
# After git pull, verify:
ls -la frontend/lib/
# Should show: api.ts and types.ts

# If missing, the git pull might have failed
# Check git status:
git status
git log --oneline -3
```

### Issue: "pydantic version conflict"

**Cause:** Old requirements.txt with `pydantic==2.10.5`

**Solution:**
```bash
# After git pull, verify:
cat backend/requirements.txt | grep pydantic
# Should show: pydantic==2.11.7

# If still 2.10.5, manual update:
sed -i 's/pydantic==2.10.5/pydantic==2.11.7/' backend/requirements.txt
```

### Issue: Build context too large (1.8GB)

**Cause:** Missing `.dockerignore` files

**Solution:**
```bash
# Verify .dockerignore exists:
ls -la backend/.dockerignore
ls -la frontend/.dockerignore

# If missing after git pull, they might be in .gitignore
# Check if git tracked them:
git ls-files | grep dockerignore
```

---

## 📊 Build Performance

### Before Optimization:
- Backend build context: **1.878GB** ❌
- Frontend build context: **~500MB** ❌
- Build time: **15+ minutes** ❌

### After Optimization:
- Backend build context: **349MB** ✅ (81% reduction!)
- Frontend build context: **6.2MB** ✅ (99% reduction!)
- Build time: **5-8 minutes** ✅

---

## 🚀 Deploy After Build

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Check status
docker-compose ps

# Test health
curl http://localhost:8000/health
curl http://localhost:3000/api/health
```

---

## 📝 Troubleshooting

If build still fails, try these debug steps:

```bash
# 1. Check git commit
git log --oneline -1
# Should show: "feat: Add automated update and build script for server deployment" or newer

# 2. Check if all files pulled
git status
# Should show: "Your branch is up to date with 'origin/main'"

# 3. Force clean git state
git reset --hard origin/main
git clean -fd

# 4. Rebuild from scratch
docker system prune -a --volumes -f
docker-compose build --no-cache --pull

# 5. Check Docker logs
docker-compose logs backend
docker-compose logs frontend
```

---

## ✅ Success Indicators

Build sukses jika:

1. ✓ No error messages during build
2. ✓ Backend image size ~831MB
3. ✓ Frontend image size ~70MB
4. ✓ Both images appear in `docker images`
5. ✓ Services start with `docker-compose up -d`
6. ✓ Health checks pass

---

**Last Updated:** March 26, 2026
**Git Commit:** 75f6cd1
