# Phase 5 — Task 7: Keyboard Shortcuts

## Context

Read `frontend/src/App.jsx` and `frontend/src/components/Globe/Globe.jsx` first.

## Goal

Add keyboard navigation shortcuts to the globe:

- `Escape` — close any open info panel
- `R` — reset view to initial position
- `Arrow keys` — rotate globe in that direction
- `+` / `-` — zoom in/out
- `1` — toggle planes layer
- `2` — toggle ships layer
- `3` — toggle events layer
- `4` — toggle conflicts layer

## Implementation

Add a `useEffect` in `App.jsx` that listens for keydown events:

```javascript
useEffect(() => {
  const handleKeyDown = (e) => {
    // Ignore if user is typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

    switch (e.key) {
      case 'Escape':
        setSelectedPlane(null)
        setSelectedShip(null)
        setSelectedEvent(null)
        setSelectedConflict(null)
        break
      case 'r':
      case 'R':
        // Reset view — pass through via a callback prop
        onResetView?.()
        break
      case 'ArrowLeft':
        rotateGlobe(-15, 0)
        break
      case 'ArrowRight':
        rotateGlobe(15, 0)
        break
      case 'ArrowUp':
        rotateGlobe(0, 5)
        break
      case 'ArrowDown':
        rotateGlobe(0, -5)
        break
      case '+':
      case '=':
        zoomGlobe(1)
        break
      case '-':
        zoomGlobe(-1)
        break
      case '1':
        toggleLayer('planes')
        break
      case '2':
        toggleLayer('ships')
        break
      case '3':
        toggleLayer('events')
        break
      case '4':
        toggleLayer('conflicts')
        break
    }
  }

  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [])
```

### Globe Rotation

Expose `rotateGlobe` and `zoomGlobe` from `Globe.jsx` via a ref or callback prop. These modify the `viewState`:

```javascript
const rotateGlobe = (dBearing, dPitch) => {
  setViewState(prev => ({
    ...prev,
    bearing: prev.bearing + dBearing,
    pitch: Math.max(0, Math.min(60, prev.pitch + dPitch)),
  }))
}

const zoomGlobe = (dZoom) => {
  setViewState(prev => ({
    ...prev,
    zoom: Math.max(0.5, Math.min(10, prev.zoom + dZoom)),
  }))
}
```

## Files to Update

- `frontend/src/App.jsx` — add keyboard event listener
- `frontend/src/components/Globe/Globe.jsx` — expose rotate/zoom functions

## Verification

- [ ] Escape closes open info panels
- [ ] R resets the view
- [ ] Arrow keys rotate the globe smoothly
- [ ] +/- zooms in/out
- [ ] Number keys 1-4 toggle respective layers
- [ ] Shortcuts don't fire when typing in an input field
