# Task 2 — React + Vite Frontend Scaffold

**Agent:** GLM 5.1
**Phase:** 1
**Sequential Order:** 2 of 7
**Dependency:** Task 1 (directory structure must exist)

---

## Task Overview

Set up the complete frontend project scaffold so that `npm install && npm run dev` works and starts a Vite dev server on port 5173 with a basic React app loading.

---

## Steps

### 1. Verify Directory Structure

Before starting, verify these directories exist from Task 1:
- `frontend/src/`
- `frontend/src/components/`
- `frontend/src/components/Globe/`
- `frontend/src/components/Globe/layers/`
- `frontend/src/components/Sidebar/`
- `frontend/src/components/Header/`
- `frontend/src/components/common/`
- `frontend/src/hooks/`
- `frontend/src/services/`
- `frontend/src/utils/`

### 2. Create All Required Files

Create the following files with actual implementations:

**`frontend/src/App.jsx`** — Replace the placeholder with:
```jsx
import { useState, useEffect } from 'react'

function App() {
  const [status, setStatus] = useState('connecting')

  useEffect(() => {
    fetch('/api/metadata')
      .then(res => res.json())
      .then(data => setStatus(data.status || 'connected'))
      .catch(() => setStatus('error'))
  }, [])

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      fontFamily: 'system-ui, sans-serif',
      background: '#0a0a0f',
      color: '#ffffff'
    }}>
      <div style={{ padding: '20px' }}>
        <h1>TerraWatch</h1>
        <p>Backend Status: {status}</p>
      </div>
    </div>
  )
}

export default App
```

**`frontend/src/hooks/useWebSocket.js`** — WebSocket hook stub:
```javascript
import { useEffect, useRef, useState } from 'react'

const WS_URL = `ws://${window.location.hostname}:8000/ws`

export function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (event) => onMessage(JSON.parse(event.data))
    wsRef.current = ws

    return () => ws.close()
  }, [onMessage])

  return { connected }
}
```

**`frontend/src/services/api.js`** — REST API client:
```javascript
const API_BASE = '/api'

export async function fetchPlanes() {
  const res = await fetch(`${API_BASE}/planes`)
  return res.json()
}

export async function fetchShips() {
  const res = await fetch(`${API_BASE}/ships`)
  return res.json()
}

export async function fetchEvents() {
  const res = await fetch(`${API_BASE}/events`)
  return res.json()
}

export async function fetchMetadata() {
  const res = await fetch(`${API_BASE}/metadata`)
  return res.json()
}
```

**`frontend/src/utils/constants.js`** — Layer configuration:
```javascript
export const LAYER_COLORS = {
  plane: [255, 100, 100],
  ship: [100, 200, 255],
  event: [255, 200, 100],
  conflict: [255, 50, 50],
}

export const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
}

export const REFRESH_INTERVALS = {
  planes: 30000,    // 30 seconds
  ships: 60000,    // 60 seconds
  events: 3600000, // 1 hour
}
```

**`frontend/src/utils/formatters.js`** — Data formatters:
```javascript
export function formatAltitude(feet) {
  return `${Math.round(feet)} ft`
}

export function formatSpeed(knots) {
  return `${knots.toFixed(1)} kts`
}

export function formatCoord(lat, lon) {
  const latDir = lat >= 0 ? 'N' : 'S'
  const lonDir = lon >= 0 ? 'E' : 'W'
  return `${Math.abs(lat).toFixed(4)}°${latDir}, ${Math.abs(lon).toFixed(4)}°${lonDir}`
}

export function formatTimestamp(ts) {
  return new Date(ts).toLocaleTimeString()
}
```

### 3. Add CSS Reset

Create `frontend/src/index.css`:
```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: system-ui, -apple-system, sans-serif;
  background: #0a0a0f;
  color: #ffffff;
  overflow: hidden;
}

#root {
  width: 100vw;
  height: 100vh;
}
```

### 4. Update `frontend/src/main.jsx` to import CSS

Add after the React imports:
```jsx
import './index.css'
```

---

## Verification

After completing your task, verify by running:
```bash
cd frontend
npm install
npm run dev
```

Should start without errors and show the Vite dev server on port 5173.

---

## Acceptance Criteria

1. `npm install` completes without errors
2. `npm run dev` starts dev server on port 5173 without errors
3. Opening http://localhost:5173 shows a React app with "TerraWatch" heading and backend status
4. No console errors on page load
5. All placeholder hook and service files are created and importable

---

## Commit Message

```
Phase 1 Task 2: React + Vite frontend scaffold
```
