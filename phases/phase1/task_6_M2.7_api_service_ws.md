# Task 6 — Frontend API Service + WebSocket Integration

**Agent:** M2.7 (MiniMax)
**Phase:** 1
**Sequential Order:** 6 of 7
**Dependencies:** Tasks 2, 3, 4, 5 (frontend scaffold working, backend running, globe shell rendering)

---

## Task Overview

Complete the frontend-backend connection pipeline:
1. Refine the WebSocket hook to properly handle real data
2. Create data hooks for planes, ships, events
3. Wire up the Globe component to receive and display data
4. Add layer rendering to deck.gl
5. Ensure the full flow works end-to-end

---

## Steps

### 1. Update `frontend/src/hooks/useWebSocket.js`

```javascript
import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = `ws://${window.location.hostname}:8000/ws`

export function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)
  const onMessageRef = useRef(onMessage)

  // Keep onMessage ref current
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL)
      
      ws.onopen = () => {
        setConnected(true)
        console.log('[WS] Connected to TerraWatch backend')
      }
      
      ws.onclose = () => {
        setConnected(false)
        console.log('[WS] Disconnected, reconnecting in 3s...')
        setTimeout(connect, 3000)
      }
      
      ws.onerror = (error) => {
        console.error('[WS] Error:', error)
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          if (onMessageRef.current) {
            onMessageRef.current(data)
          }
        } catch (e) {
          console.error('[WS] Failed to parse message:', e)
        }
      }
      
      wsRef.current = ws
    } catch (e) {
      console.error('[WS] Connection failed:', e)
      setTimeout(connect, 3000)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { connected, lastMessage }
}
```

### 2. Create `frontend/src/hooks/usePlanes.js`

```javascript
import { useState, useEffect, useCallback } from 'react'

const initialPlanes = []

export function usePlanes() {
  const [planes, setPlanes] = useState(initialPlanes)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchPlanes = useCallback(async () => {
    try {
      const res = await fetch('/api/planes')
      if (!res.ok) throw new Error('Failed to fetch planes')
      const data = await res.json()
      setPlanes(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const addPlane = useCallback((plane) => {
    setPlanes(prev => {
      const existing = prev.findIndex(p => p.id === plane.id)
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = plane
        return updated
      }
      return [...prev, plane]
    })
  }, [])

  const removePlane = useCallback((planeId) => {
    setPlanes(prev => prev.filter(p => p.id !== planeId))
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchPlanes()
  }, [fetchPlanes])

  return { planes, loading, error, fetchPlanes, addPlane, removePlane }
}
```

### 3. Create `frontend/src/hooks/useShips.js`

```javascript
import { useState, useEffect, useCallback } from 'react'

const initialShips = []

export function useShips() {
  const [ships, setShips] = useState(initialShips)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchShips = useCallback(async () => {
    try {
      const res = await fetch('/api/ships')
      if (!res.ok) throw new Error('Failed to fetch ships')
      const data = await res.json()
      setShips(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const addShip = useCallback((ship) => {
    setShips(prev => {
      const existing = prev.findIndex(s => s.id === ship.id)
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = ship
        return updated
      }
      return [...prev, ship]
    })
  }, [])

  const removeShip = useCallback((shipId) => {
    setShips(prev => prev.filter(s => s.id !== shipId))
  }, [])

  useEffect(() => {
    fetchShips()
  }, [fetchShips])

  return { ships, loading, error, fetchShips, addShip, removeShip }
}
```

### 4. Create `frontend/src/hooks/useEvents.js`

```javascript
import { useState, useEffect, useCallback } from 'react'

const initialEvents = []

export function useEvents() {
  const [events, setEvents] = useState(initialEvents)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch('/api/events')
      if (!res.ok) throw new Error('Failed to fetch events')
      const data = await res.json()
      setEvents(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  return { events, loading, error, fetchEvents }
}
```

### 5. Update Globe Component — Add Layer Rendering

Update `frontend/src/components/Globe/Globe.jsx` to accept and render data layers:

```jsx
import { useState, useEffect, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { GlobeView } from '@deck.gl/core'
import { ScatterplotLayer, ArcLayer, IconLayer } from '@deck.gl/layers'
import { useWebSocket } from '../../hooks/useWebSocket'
import { usePlanes } from '../../hooks/usePlanes'
import { useShips } from '../../hooks/useShips'

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.8,
  pitch: 0,
  bearing: 0,
}

const COLORS = {
  plane: [255, 100, 100],
  ship: [100, 200, 255],
}

export default function Globe({ layers, onEntityClick }) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const { planes, addPlane } = usePlanes()
  const { ships, addShip } = useShips()

  // Handle WebSocket messages
  const handleWSMessage = useCallback((msg) => {
    if (msg.type === 'plane') {
      addPlane(msg.data)
    } else if (msg.type === 'ship') {
      addShip(msg.data)
    }
  }, [addPlane, addShip])

  const { connected } = useWebSocket(handleWSMessage)

  // Build deck.gl layers
  const deckLayers = []

  // Plane layer
  if (layers.planes) {
    deckLayers.push(
      new ScatterplotLayer({
        id: 'planes-layer',
        data: planes,
        pickable: true,
        opacity: 0.9,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 4,
        radiusMaxPixels: 20,
        lineWidthMinPixels: 1,
        getPosition: d => [d.lon, d.lat],
        getRadius: d => 100,
        getFillColor: COLORS.plane,
        getLineColor: [255, 255, 255],
        onClick: (info) => onEntityClick && onEntityClick('plane', info.object),
      })
    )
  }

  // Ship layer
  if (layers.ships) {
    deckLayers.push(
      new ScatterplotLayer({
        id: 'ships-layer',
        data: ships,
        pickable: true,
        opacity: 0.9,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 4,
        radiusMaxPixels: 15,
        lineWidthMinPixels: 1,
        getPosition: d => [d.lon, d.lat],
        getRadius: d => 80,
        getFillColor: COLORS.ship,
        getLineColor: [255, 255, 255],
        onClick: (info) => onEntityClick && onEntityClick('ship', info.object),
      })
    )
  }

  return (
    <div className="globe-container">
      <DeckGL
        views={new GlobeView({ id: 'globe' })}
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) => setViewState(vs)}
        controller={true}
        layers={deckLayers}
        style={{ position: 'absolute', width: '100%', height: '100%' }}
      />
      <div className="globe-info">
        <span>Planes: {planes.length}</span>
        <span>Ships: {ships.length}</span>
        <span className={`ws-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Live' : '○ Reconnecting'}
        </span>
      </div>
    </div>
  )
}
```

### 6. Add CSS for Globe Info Overlay

Update `frontend/src/components/Globe/Globe.css`:

```css
.globe-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #0a0a0f;
}

.globe-info {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 24px;
  padding: 10px 20px;
  background: rgba(10, 10, 15, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  z-index: 10;
}

.globe-info span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ws-status.connected {
  color: #22c55e;
}

.ws-status.disconnected {
  color: #eab308;
}

.globe-info span::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
```

### 7. Update App.jsx to Wire Everything Together

```jsx
import { useState, useCallback } from 'react'
import Globe from './components/Globe/Globe'
import Header from './components/Header/Header'
import Sidebar from './components/Sidebar/Sidebar'
import './index.css'

function App() {
  const [layers, setLayers] = useState({
    planes: true,
    ships: true,
    events: false,
    conflicts: false,
  })

  const [selectedEntity, setSelectedEntity] = useState(null)

  const toggleLayer = useCallback((layer) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }))
  }, [])

  const handleEntityClick = useCallback((type, entity) => {
    setSelectedEntity({ type, entity })
    console.log(`Selected ${type}:`, entity)
  }, [])

  return (
    <div className="app">
      <Header />
      <div className="main-content">
        <Sidebar layers={layers} onToggleLayer={toggleLayer} />
        <div className="globe-wrapper">
          <Globe layers={layers} onEntityClick={handleEntityClick} />
        </div>
      </div>
    </div>
  )
}

export default App
```

### 8. Verify Dockerfile Exposes Ports Correctly

Ensure `frontend/Dockerfile` exposes port 5173:

```dockerfile
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

---

## Verification

1. Backend running on port 8000
2. Frontend running on port 5173
3. Open http://localhost:5173
4. Verify:
   - Globe renders
   - Header shows "TerraWatch"
   - WS status indicator shows "connected" (green dot)
   - Globe info overlay shows "Planes: 0" and "Ships: 0" (since no real data in Phase 1)
   - Layer toggles work
5. No console errors

---

## Acceptance Criteria

1. WebSocket connects to backend and shows connected status
2. Globe renders without errors
3. Layer toggles affect which data is visible on globe
4. Console shows no JavaScript errors
5. Globe info overlay shows entity counts
6. Selected entity click handler fires (logs to console)

---

## Commit Message

```
Phase 1 Task 6: Frontend API service + WebSocket integration
```
