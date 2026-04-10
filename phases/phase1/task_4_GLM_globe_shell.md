# Task 4 — Basic Globe Shell (deck.gl)

**Agent:** GLM 5.1
**Phase:** 1
**Sequential Order:** 4 of 7
**Dependency:** Tasks 2 and 3 (frontend scaffold must be working, backend must respond to /api/metadata)

---

## Task Overview

Replace the basic App.jsx with a real deck.gl globe that renders on the page. The globe should:
- Display a 3D globe using deck.gl's GlobeView
- Have a dark base map style
- Accept initial view state (longitude, latitude, zoom)
- NOT load any data layers yet — just render the globe shell
- Connect to the backend API and show the backend status

---

## Steps

### 1. Install deck.gl explicitly

The package.json already has deck.gl dependencies, but ensure they're properly installed:

```bash
cd frontend
npm install
```

If there are issues, explicitly install:
```bash
npm install deck.gl@^9.0.35 @deck.gl/core@^9.0.35 @deck.gl/layers@^9.0.35 @deck.gl/react@^9.0.35 @luma.gl/core@^9.0.35
```

### 2. Create the GlobeView Component

Create `frontend/src/components/Globe/Globe.jsx`:

```jsx
import { useState, useEffect } from 'react'
import DeckGL from '@deck.gl/react'
import { GlobeView } from '@deck.gl/core'
import { BitmapLayer } from '@deck.gl/layers'

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
}

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

export default function Globe() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const [mapLoaded, setMapLoaded] = useState(false)

  // Create a simple tile layer for the base map
  const tileLayer = new BitmapLayer({
    id: 'base-tile-layer',
    data: getTileData,
    pickable: false,
  })

  function getTileData({ x, y, z }) {
    const subdomain = 'abc'[Math.abs(x + y) % 3]
    const url = `https://${subdomain}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png`
    return { url }
  }

  const layers = [tileLayer]

  return (
    <DeckGL
      views={new GlobeView({ id: 'globe' })}
      viewState={viewState}
      onViewStateChange={({ viewState }) => setViewState(viewState)}
      controller={true}
      layers={layers}
      style={{ position: 'absolute', width: '100%', height: '100%' }}
    >
      {/* Globe renders here */}
    </DeckGL>
  )
}
```

### 3. Create `frontend/src/components/Globe/Globe.css`

```css
.globe-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #0a0a0f;
}
```

### 4. Update `frontend/src/App.jsx`

Replace the current App.jsx with:

```jsx
import { useState, useEffect } from 'react'
import Globe from './components/Globe/Globe'
import Header from './components/Header/Header'
import Sidebar from './components/Sidebar/Sidebar'
import './index.css'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [layers, setLayers] = useState({
    planes: true,
    ships: true,
    events: false,
    conflicts: false,
  })

  useEffect(() => {
    // Check backend connectivity
    fetch('/api/metadata')
      .then(res => {
        if (res.ok) return res.json()
        throw new Error('Backend not reachable')
      })
      .then(data => setBackendStatus(data.status || 'connected'))
      .catch(() => setBackendStatus('error'))
  }, [])

  const toggleLayer = (layer) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }))
  }

  return (
    <div className="app">
      <Header backendStatus={backendStatus} />
      <div className="main-content">
        <Sidebar layers={layers} onToggleLayer={toggleLayer} />
        <div className="globe-wrapper">
          <Globe />
          <div className="status-bar">
            Phase 1 — Globe Shell
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
```

### 5. Create Header Component

Create `frontend/src/components/Header/Header.jsx`:

```jsx
export default function Header({ backendStatus }) {
  return (
    <header className="header">
      <div className="header-left">
        <h1 className="logo">TerraWatch</h1>
        <span className="subtitle">Live GEOINT Platform</span>
      </div>
      <div className="header-right">
        <div className={`status-indicator ${backendStatus}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {backendStatus === 'checking' ? 'Connecting...' :
             backendStatus === 'ok' ? 'Backend Connected' :
             backendStatus === 'error' ? 'Backend Error' : backendStatus}
          </span>
        </div>
      </div>
    </header>
  )
}
```

Create `frontend/src/components/Header/Header.css`:

```css
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
  padding: 0 20px;
  background: rgba(10, 10, 15, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
}

.status-indicator.ok .status-dot { background: #22c55e; }
.status-indicator.error .status-dot { background: #ef4444; }
.status-indicator.checking .status-dot { background: #eab308; animation: pulse 1s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
```

### 6. Create Sidebar Component

Create `frontend/src/components/Sidebar/Sidebar.jsx`:

```jsx
export default function Sidebar({ layers, onToggleLayer }) {
  const layerConfig = [
    { key: 'planes', label: 'Aircraft', icon: '✈️', color: '#ff6464' },
    { key: 'ships', label: 'Maritime', icon: '🚢', color: '#64c8ff' },
    { key: 'events', label: 'World Events', icon: '🌍', color: '#ffc864' },
    { key: 'conflicts', label: 'Conflict Zones', icon: '⚠️', color: '#ff3232' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Data Layers</h2>
      </div>
      <div className="layer-list">
        {layerConfig.map(layer => (
          <div
            key={layer.key}
            className={`layer-item ${layers[layer.key] ? 'active' : ''}`}
            onClick={() => onToggleLayer(layer.key)}
          >
            <span className="layer-icon">{layer.icon}</span>
            <span className="layer-label">{layer.label}</span>
            <div 
              className="layer-toggle"
              style={{ '--toggle-color': layer.color }}
            >
              <div className="toggle-knob" />
            </div>
          </div>
        ))}
      </div>
      <div className="sidebar-footer">
        <p className="phase-label">Phase 1 of 7</p>
      </div>
    </aside>
  )
}
```

Create `frontend/src/components/Sidebar/Sidebar.css`:

```css
.sidebar {
  width: 240px;
  background: rgba(10, 10, 15, 0.95);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 50;
}

.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.5);
}

.layer-list {
  flex: 1;
  padding: 12px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.layer-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.layer-item.active {
  background: rgba(255, 255, 255, 0.08);
}

.layer-icon {
  font-size: 18px;
}

.layer-label {
  flex: 1;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.layer-item.active .layer-label {
  color: #ffffff;
}

.layer-toggle {
  width: 36px;
  height: 20px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
  position: relative;
  transition: background 0.2s;
}

.layer-item.active .layer-toggle {
  background: var(--toggle-color);
}

.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  transition: transform 0.2s;
}

.layer-item.active .toggle-knob {
  transform: translateX(16px);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.phase-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  letter-spacing: 1px;
}
```

### 7. Update `frontend/src/index.css`

Replace with:

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

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.globe-wrapper {
  flex: 1;
  position: relative;
}

.status-bar {
  position: absolute;
  bottom: 16px;
  right: 16px;
  padding: 8px 16px;
  background: rgba(10, 10, 15, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}
```

---

## Verification

After completing your task:
```bash
cd frontend
npm run dev
```

Open http://localhost:5173 and verify:
1. The page loads without errors
2. A dark globe is visible on screen (rendered by deck.gl)
3. Header shows "TerraWatch" and backend connection status
4. Sidebar shows 4 layer toggles
5. No console errors

---

## Acceptance Criteria

1. Globe renders as a 3D sphere with dark map styling
2. Header shows backend connection status (should show "ok" if backend is running)
3. Sidebar renders with all 4 layer toggles
4. Layer toggles are interactive (clicking changes state)
5. Page is responsive to window resize
6. No JavaScript console errors on load

---

## Commit Message

```
Phase 1 Task 4: Basic deck.gl globe shell
```
