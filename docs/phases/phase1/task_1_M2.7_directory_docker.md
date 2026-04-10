# Task 1 — Directory Structure + Docker Base Files

**Agent:** M2.7 (MiniMax)
**Phase:** 1
**Sequential Order:** 1 of 7

---

## Task Overview

Create the entire directory structure for the TerraWatch monorepo and set up all Docker-related base files.

---

## Steps

### 1. Create Directory Structure

Create all directories:

```bash
mkdir -p backend/app/{api/routes,core,services,tasks}
mkdir -p frontend/src/{components/{Globe/layers,Sidebar,Header,common},hooks,services,utils}
mkdir -p docker
mkdir -p docs
mkdir -p phases/phase1
mkdir -p scripts
```

### 2. Create `backend/requirements.txt`

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
websockets==13.1
pydantic==2.9.2
httpx==0.27.2
asyncio-cache==0.0.6
python-dotenv==1.0.1
aiosqlite==0.20.0
```

### 3. Create `backend/app/__init__.py`

Empty file.

### 4. Create `backend/app/main.py`

Placeholder FastAPI app:
```python
from fastapi import FastAPI

app = FastAPI(title="TerraWatch API", version="0.1.0")

@app.get("/api/metadata")
async def metadata():
    return {"status": "ok", "phase": 1}
```

### 5. Create `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6. Create `frontend/package.json`

```json
{
  "name": "terrawatch-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "deck.gl": "^9.0.35",
    "@deck.gl/core": "^9.0.35",
    "@deck.gl/layers": "^9.0.35",
    "@deck.gl/react": "^9.0.35",
    "@luma.gl/core": "^9.0.35",
    "mapbox-gl": "^3.8.0",
    "@mapbox/mapbox-gl-style-spec": "^14.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^6.0.5"
  }
}
```

### 7. Create `frontend/vite.config.js`

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

### 8. Create `frontend/index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>TerraWatch</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

### 9. Create `frontend/src/main.jsx`

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

### 10. Create `frontend/src/App.jsx`

```jsx
function App() {
  return <div style={{ padding: '20px' }}>TerraWatch Loading...</div>
}

export default App
```

### 11. Create `frontend/Dockerfile`

```dockerfile
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

### 12. Create `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - PYTHONUNBUFFERED=1

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    depends_on:
      - backend
```

### 13. Create `.env.example`

```
# Backend
PYTHON_ENV=development

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 14. Create `.gitignore`

```
__pycache__/
*.pyc
.env
node_modules/
dist/
.venv/
*.egg-info/
.DS_Store
```

---

## Acceptance Criteria

1. All directories created match the architecture spec
2. Both Dockerfiles exist and are valid
3. docker-compose.yml is valid (run `docker compose config` to verify)
4. backend/requirements.txt has all listed packages
5. frontend/package.json has all listed dependencies
6. `docker compose build` completes without errors (will be tested in Task 8)

---

## Commit Message

```
Phase 1 Task 1: Directory structure + Docker base files
```
