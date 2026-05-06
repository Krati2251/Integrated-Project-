# 🐳 Docker Deployment Guide

## Prerequisites

✅ **Required:**
- Docker Desktop installed: https://www.docker.com/products/docker-desktop
- All three project folders present:
  - `backend/`
  - `frontend/`
  - `quiz/Finance-Quiz-Bot/`
- `.env` file with credentials (already exists)

✅ **Verify Docker is installed:**
```powershell
docker --version
docker-compose --version
```

---

## 🚀 Quick Start (3 Commands)

### Step 1: Navigate to project
```powershell
cd "d:\Triage Agent Final\finance-support-triage-agent-final-streamlit-1"
```

### Step 2: First time deployment (builds images)
```powershell
.\deploy-docker.ps1 -Action start -Rebuild
```

### Step 3: Access services
Open in browser:
- **Frontend Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Quiz Service**: http://localhost:8502
- **API Documentation**: http://localhost:8000/docs

---

## 📋 Deployment Script Commands

```powershell
# Start services (uses cached images)
.\deploy-docker.ps1 -Action start

# Start and rebuild all images (slower, fresh build)
.\deploy-docker.ps1 -Action start -Rebuild

# Stop all services
.\deploy-docker.ps1 -Action stop

# Restart services
.\deploy-docker.ps1 -Action restart

# View live logs (all services)
.\deploy-docker.ps1 -Action logs

# Check service status
.\deploy-docker.ps1 -Action status

# Rebuild images only (don't start)
.\deploy-docker.ps1 -Action build

# Clean up containers and networks
.\deploy-docker.ps1 -Action clean
```

---

## 🔧 Manual Docker Commands (Alternative)

If you prefer manual control without the script:

### Build images
```powershell
cd "d:\Triage Agent Final\finance-support-triage-agent-final-streamlit-1"
docker-compose build
```

### Start services in background
```powershell
docker-compose up -d
```

### View logs (real-time)
```powershell
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f quiz
```

### Check running containers
```powershell
docker-compose ps
```

### Stop services
```powershell
docker-compose down
```

### Health check
```powershell
curl http://localhost:8000/
curl http://localhost:8501/
curl http://localhost:8502/
```

---

## 📍 Service Details

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Backend** | 8000 | http://localhost:8000 | FastAPI + Uvicorn |
| **Frontend** | 8501 | http://localhost:8501 | Streamlit Dashboard |
| **Quiz** | 8502 | http://localhost:8502 | Finance Quiz Service |

### Backend Endpoints
- `GET /` — Health check
- `GET /docs` — Interactive API documentation (Swagger)
- `POST /analyze_urgency` — Classify ticket urgency
- `GET /dashboard_metrics` — Get analytics data
- `/quiz/*` — Quiz endpoints

---

## 🐛 Troubleshooting

### Port already in use
**Error:** `Address already in use`

**Solution:**
```powershell
# Find which process is using the port
netstat -ano | findstr :8000
netstat -ano | findstr :8501
netstat -ano | findstr :8502

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or restart Docker Desktop
```

### Container won't start
**Check logs:**
```powershell
.\deploy-docker.ps1 -Action logs

# Or specific service
docker-compose logs backend
```

### Rebuild from scratch
**Complete reset:**
```powershell
# Stop and remove everything
.\deploy-docker.ps1 -Action clean

# Rebuild with fresh images
.\deploy-docker.ps1 -Action start -Rebuild
```

### Database connection issues
**Check .env file:**
```powershell
cat .env
```

Verify:
- `DATABASE_URL` is correct
- `GROQ_API_KEY` is set
- `EMAIL_USER` and `EMAIL_PASSWORD` are valid

### Frontend can't connect to backend
**Problem:** Frontend container can't reach backend

**Solution:**
- Services are on same network (`finance-net`)
- Frontend uses `http://backend:8000` (Docker DNS)
- Only works inside Docker containers
- From host, use `http://localhost:8000`

---

## 💡 For Live Presentation

### Before presentation:
1. Test deployment locally
2. Verify all services start without errors
3. Open browser tabs and bookmark URLs
4. Check internet (for API calls)

### During presentation (Recommended approach):

**Terminal 1 - Deployment:**
```powershell
cd "d:\Triage Agent Final\finance-support-triage-agent-final-streamlit-1"
.\deploy-docker.ps1 -Action start
```

**Terminal 2 - Watch logs (optional):**
```powershell
cd "d:\Triage Agent Final\finance-support-triage-agent-final-streamlit-1"
.\deploy-docker.ps1 -Action logs
```

**Browser:** Open http://localhost:8501

### Stop after presentation:
```powershell
.\deploy-docker.ps1 -Action stop
```

---

## 📊 What Gets Deployed

```
docker network: finance-net
├── finance-backend (port 8000)
│   ├── Python 3.11
│   ├── FastAPI + Uvicorn
│   └── Database: PostgreSQL (via .env)
├── finance-frontend (port 8501)
│   ├── Python 3.11
│   ├── Streamlit
│   └── Connects to: backend
└── finance-quiz (port 8502)
    ├── Python 3.11
    ├── Streamlit
    ├── Chroma DB (local volume)
    └── Connects to: backend
```

---

## ✅ Health Check Commands

After starting services, verify everything works:

```powershell
# Check all services are running
docker-compose ps

# Test backend
curl http://localhost:8000/

# Test frontend
curl http://localhost:8501/

# Test quiz
curl http://localhost:8502/

# View metrics
curl http://localhost:8000/dashboard_metrics | ConvertFrom-Json
```

---

## 🔄 Development Workflow

### Make code changes:
1. Edit files in `backend/`, `frontend/`, or `quiz/`
2. Restart service:
   ```powershell
   .\deploy-docker.ps1 -Action restart
   ```

### Push to Docker Hub (optional):
```powershell
docker tag finance-backend:latest yourusername/finance-backend:v1
docker push yourusername/finance-backend:v1
```

---

## 📝 Notes

- **Health checks enabled:** Services wait for dependencies before starting
- **Auto-restart:** Services restart on crash (`restart: unless-stopped`)
- **Volumes:** Quiz data persists in `quiz_data` volume
- **Network isolation:** Services communicate via `finance-net` bridge
- **Environment variables:** All loaded from `.env` file

---

## 🎯 For Your Presentation Tomorrow

**Simplest approach:**
```powershell
# One command to start everything
.\deploy-docker.ps1 -Action start -Rebuild

# One command to stop
.\deploy-docker.ps1 -Action stop
```

**Show URLs to audience:**
- Dashboard: http://localhost:8501
- Backend API: http://localhost:8000/docs

**If something breaks:**
```powershell
# Reset and restart
.\deploy-docker.ps1 -Action clean
.\deploy-docker.ps1 -Action start -Rebuild
```

---

**Good luck with your presentation! 🚀**
