# Phase 5 — Task 10: Loading Skeletons

## Context

Read `frontend/src/components/Globe/Globe.jsx`, `frontend/src/App.jsx`, and `frontend/src/index.css`.

## Goal

Show loading skeletons during the initial data fetch (before first WebSocket data arrives), so users don't see a blank globe or an empty state before data loads.

## Implementation

### Globe Loading State

In `Globe.jsx`, track whether initial data has been received:

```javascript
const [initialDataLoaded, setInitialDataLoaded] = useState(false)

// In handleWSMessage, after first plane_batch or plane message:
if (!initialDataLoaded && (msg.type === 'plane_batch' || msg.type === 'plane')) {
  setInitialDataLoaded(true)
}
```

Or better — track per layer:

```javascript
const [loadedLayers, setLoadedLayers] = useState({ planes: false, ships: false, events: false, conflicts: false })

// When first data of each type arrives:
setLoadedLayers(prev => ({ ...prev, planes: true }))
```

### Skeleton Overlay

While not all layers are loaded, show a centered skeleton overlay:

```css
.globe-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 20, 0.7);
  z-index: 100;
}

.globe-loading-spinner {
  width: 60px;
  height: 60px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #64c8ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.globe-loading-text {
  margin-top: 16px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

Show layer-specific loading status:
- "Loading aircraft..." when planes not yet loaded
- "Loading maritime..." when ships not yet loaded

### Sidebar Skeleton

The sidebar can show skeleton lines in the layer count area while data is loading:
- A pulsing gray bar instead of the layer count numbers
- Same pulsing animation as the globe skeleton

```css
.skeleton-line {
  height: 14px;
  background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%);
  background-size: 200% 100%;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
  border-radius: 4px;
}
```

## Files to Update

- `frontend/src/components/Globe/Globe.jsx` — add loading state tracking and skeleton overlay
- `frontend/src/components/Globe/Globe.css` — skeleton and spinner styles
- `frontend/src/components/Sidebar/Sidebar.css` — sidebar skeleton styles

## Verification

- [ ] Skeleton overlay appears while initial data loads
- [ ] Layer-specific loading text shown
- [ ] Skeleton disappears once all layers have data
- [ ] Globe and sidebar skeletons use consistent animation
- [ ] No flash of empty content during initial load
