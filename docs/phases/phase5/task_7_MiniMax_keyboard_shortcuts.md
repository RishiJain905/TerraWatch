# Phase 5 — Task 7: Keyboard Shortcuts

## Context

Read `frontend/src/App.jsx` and `frontend/src/components/Globe/Globe.jsx` first.

## UI / UX baseline (Gotham — read before implementing)

Shortcuts are **behavioral** — they rarely need new chrome — but any **on-screen hint** (future help popover) must use the same tokens and typography as the sidebar (`--mono` micro-caps, `--text-2` labels, `--line` borders).

- **Focus safety:** Ignore shortcuts when the user is typing in **`INPUT`**, **`TEXTAREA`**, **`SELECT`**, or **`[contenteditable="true"]`**. Also ignore when the target is inside `[role="combobox"]` / ARIA listbox patterns if the app adds them later.
- **Globe integration:** `rotateGlobe` / `zoomGlobe` / `resetView` should live with `viewState` ownership (typically `Globe.jsx`). `App.jsx` should call into Globe via a **stable ref** (`useImperativeHandle`) or a small set of callback props — avoid duplicating `INITIAL_VIEW_STATE` in two files unless one re-exports the other.
- **Layer toggles:** Number-key toggles must stay consistent with the Sidebar’s layer ON/OFF state and the `layers` prop passed into `Globe` (no desync between keyboard and visible toggles).

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
    const t = e.target
    if (
      t.tagName === 'INPUT' ||
      t.tagName === 'TEXTAREA' ||
      t.tagName === 'SELECT' ||
      t.isContentEditable
    ) {
      return
    }

    switch (e.key) {
      case 'Escape':
        setSelectedPlane(null)
        setSelectedShip(null)
        setSelectedEvent(null)
        setSelectedConflict(null)
        break
      case 'r':
      case 'R':
        // Reset view — call into Globe via ref or callback
        globeApiRef.current?.resetView?.()
        break
      case 'ArrowLeft':
        globeApiRef.current?.rotateGlobe?.(-15, 0)
        break
      case 'ArrowRight':
        globeApiRef.current?.rotateGlobe?.(15, 0)
        break
      case 'ArrowUp':
        globeApiRef.current?.rotateGlobe?.(0, 5)
        break
      case 'ArrowDown':
        globeApiRef.current?.rotateGlobe?.(0, -5)
        break
      case '+':
      case '=':
        globeApiRef.current?.zoomGlobe?.(1)
        break
      case '-':
        globeApiRef.current?.zoomGlobe?.(-1)
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

Expose `rotateGlobe` and `zoomGlobe` from `Globe.jsx` via ref (`forwardRef` + `useImperativeHandle`) or callback props. These modify the `viewState`:

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

**GlobeView note:** If the production globe keeps `pitch` pinned to `0`, arrow up/down may only affect latitude via a deliberate pan model — align implementation with however `GlobeView` + controller interpret `pitch` today.

## Files to Update

- `frontend/src/App.jsx` — add keyboard event listener; robust target filtering
- `frontend/src/components/Globe/Globe.jsx` — expose rotate/zoom/reset APIs consumed by `App`

## Verification

- [ ] Escape closes open info panels
- [ ] R resets the view (same path as Task 6 reset control)
- [ ] Arrow keys adjust globe view as designed
- [ ] +/- zooms in/out
- [ ] Number keys 1–4 toggle respective layers and stay in sync with Sidebar
- [ ] Shortcuts don't fire when typing in an input field, textarea, select, or contenteditable
