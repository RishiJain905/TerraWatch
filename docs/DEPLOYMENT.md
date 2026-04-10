# TerraWatch — Deployment Guide

## Local Development

### Prerequisites
- Docker and Docker Compose installed
- Node.js 22+ (for local frontend development without Docker)
- Python 3.12+ (for local backend development without Docker)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to project
cd TerraWatch

# Start both services
docker compose up --build

# Stop services
docker compose down
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Production Deployment

### Environment Variables

Create `.env` based on `.env.example`:

```
PYTHON_ENV=production
VITE_API_URL=https://your-domain.com
```

### Docker Health Checks

Both services have health checks configured:
- Backend: `GET /health` — returns `{"status": "healthy"}`
- Frontend: No health check needed (serves static files)

### Nginx Reverse Proxy

For production, use nginx as a reverse proxy (see `docker/nginx.conf`).

---

## Troubleshooting

### Frontend can't reach backend
- Ensure backend health check passes: `curl http://localhost:8000/health`
- Check CORS configuration in `backend/app/main.py`
- Verify nginx proxy configuration

### WebSocket not connecting
- Check nginx WebSocket proxy configuration
- Ensure the backend service is healthy: `curl http://localhost:8000/health`

### Docker build fails
- Clear Docker cache: `docker compose build --no-cache`
- Ensure ports 5173 and 8000 are not in use

### Performance issues
- Enable GPU acceleration for Docker (WSL2 backend on Windows)
- Increase Docker resource limits
- Consider PostgreSQL + TimescaleDB migration for V2+
