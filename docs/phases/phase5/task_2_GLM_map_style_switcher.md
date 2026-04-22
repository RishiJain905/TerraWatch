# Phase 5 — Task 2: Map Style Switcher

## Context

Read `frontend/src/components/Globe/Globe.jsx` first.

## Goal

Allow users to switch between multiple tile providers for different visual styles. Currently hardcoded to Carto dark. Add a dropdown to switch between:

1. **Dark Satellite** — Carto dark (`c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png`) — current
2. **Dark Vector** — Stadia Alidade Smooth Dark
3. **Light** — Stadia Alidade Smooth
4. **Night Lights** — Carto dark with city lights overlay

## Implementation

### Tile Provider Config

```javascript
const MAP_STYLES = {
  dark_satellite: {
    label: 'Dark Satellite',
    url: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
  },
  dark_vector: {
    label: 'Dark Vector',
    url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}.png',
  },
  light: {
    label: 'Light',
    url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}.png',
  },
  night_lights: {
    label: 'Night Lights',
    url: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    overlay: 'https://tiles.stadiamaps.com/tiles/nightlights/{z}/{x}/{y}.png',
  },
}
```

### UI Component

Add a small dropdown control in the top-right of the globe area (above the globe-info bar, or in the header). Show current style name and cycle through on click.

```javascript
function MapStyleSwitcher({ currentStyle, onChange }) {
  const styles = Object.keys(MAP_STYLES)
  const currentIndex = styles.indexOf(currentStyle)
  
  const cycle = () => {
    const next = styles[(currentIndex + 1) % styles.length]
    onChange(next)
  }
  
  return (
    <button className="map-style-switcher" onClick={cycle}>
      {MAP_STYLES[currentStyle].label}
    </button>
  )
}
```

For Night Lights, the overlay can be a second `BitmapLayer` with the overlay URL.

### State Management

Store selected style in `Globe.jsx` state. Persist to `localStorage` so it survives page reload.

## Files to Update

- `frontend/src/components/Globe/Globe.jsx` — add tile provider state and MapStyleSwitcher
- `frontend/src/components/Globe/Globe.css` — switcher button styling
- `frontend/src/components/Globe/MapStyleSwitcher.jsx` — NEW component (optional, can inline)

## Verification

- [ ] Dropdown shows all 4 map styles
- [ ] Switching styles updates tiles immediately
- [ ] Selected style persists across page reload
- [ ] Night Lights mode shows city lights overlay
- [ ] No tile loading errors in console
