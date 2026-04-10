# Task 6 — Plane Info Panel (Click to Inspect)
**Agent:** GLM 5.1 (Frontend)
**Dependencies:** Task 5 (globe layer)

## Goal

When a user clicks a plane on the globe, show a detailed info panel with callsign, altitude, speed, heading, and squawk.

## Context

- Read `frontend/src/components/Sidebar/Sidebar.jsx` — existing sidebar
- Read `frontend/src/components/Globe/Globe.jsx` — onEntityClick prop
- Read `frontend/src/App.jsx` — app-level state management

## Steps

### 1. Review Current Sidebar

```bash
cat frontend/src/components/Sidebar/Sidebar.jsx
cat frontend/src/components/Sidebar/Sidebar.css
```

### 2. Add Selected Plane State to App

In `App.jsx`, add state for selected plane:

```javascript
const [selectedPlane, setSelectedPlane] = useState(null)
```

Pass `setSelectedPlane` as the `onEntityClick` handler:

```jsx
<Globe layers={layers} onEntityClick={(type, entity) => {
  if (type === 'plane') setSelectedPlane(entity)
}} />
```

### 3. Create PlaneInfoPanel Component

Create `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx`:

```jsx
import './PlaneInfoPanel.css'

export default function PlaneInfoPanel({ plane, onClose }) {
  if (!plane) return null

  const formatAlt = (alt) => {
    if (!alt && alt !== 0) return '—'
    return `${alt.toLocaleString()} ft`
  }

  const formatSpeed = (speed) => {
    if (!speed && speed !== 0) return '—'
    return `${speed.toFixed(0)} kt`
  }

  const formatHeading = (h) => {
    if (!h && h !== 0) return '—'
    const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    const idx = Math.round(h / 45) % 8
    return `${h.toFixed(0)}° ${dirs[idx]}`
  }

  return (
    <div className="plane-info-panel">
      <div className="plane-info-header">
        <h3>{plane.callsign || plane.icao24}</h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      <div className="plane-info-grid">
        <div className="info-row">
          <span className="info-label">ICAO24</span>
          <span className="info-value mono">{plane.icao24}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Callsign</span>
          <span className="info-value">{plane.callsign || '—'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Altitude</span>
          <span className="info-value">{formatAlt(plane.alt)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Speed</span>
          <span className="info-value">{formatSpeed(plane.speed)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Heading</span>
          <span className="info-value">{formatHeading(plane.heading)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Squawk</span>
          <span className="info-value mono">{plane.squawk || '—'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Position</span>
          <span className="info-value mono">
            {plane.lat?.toFixed(4)}°, {plane.lon?.toFixed(4)}°
          </span>
        </div>
      </div>
    </div>
  )
}
```

### 4. Create PlaneInfoPanel.css

```css
.plane-info-panel {
  position: absolute;
  top: 80px;
  right: 20px;
  width: 280px;
  background: rgba(10, 15, 25, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  z-index: 1000;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.plane-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.plane-info-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  font-family: monospace;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.plane-info-grid {
  padding: 12px 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: #6b7280;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  color: #e5e7eb;
  font-size: 14px;
}

.info-value.mono {
  font-family: 'Courier New', monospace;
  color: #10b981;
}
```

### 5. Wire Into App.jsx

```jsx
import PlaneInfoPanel from './components/PlaneInfoPanel/PlaneInfoPanel'

// In App JSX:
<Globe ... onEntityClick={...} />
{selectedPlane && (
  <PlaneInfoPanel 
    plane={selectedPlane} 
    onClose={() => setSelectedPlane(null)} 
  />
)}
```

### 6. Animate Panel Entrance

Add CSS transition:

```css
.plane-info-panel {
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

### 7. Test

- [ ] Click a plane — panel appears with correct data
- [ ] Data is formatted properly (altitude with comma, speed in knots, heading with direction)
- [ ] Close button works
- [ ] Clicking globe background closes panel
- [ ] Panel stays within viewport

## Output

- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx`
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.css`
- Updated `frontend/src/App.jsx` with selectedPlane state

## Handoff

Message M2.7 (coordinator) when done. Task 7 (integration) can begin once Tasks 3, 5, and 6 are complete.
