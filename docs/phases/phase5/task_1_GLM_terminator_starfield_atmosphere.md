# Phase 5 — Task 1: Terminator Line + Starfield + Atmospheric Glow

## Context

Read `docs/ARCHITECTURE.md` and `frontend/src/components/Globe/Globe.jsx` first.

## Goal

Add three visual enhancements to the globe that transform it from "flat map on sphere" to "planet from space":

1. **Terminator line** — day/night boundary great circle (dark fill on night side)
2. **Starfield** — sphere of stars visible behind the globe
3. **Atmospheric glow** — soft rim light at globe edges

## Implementation

### Terminator Line

Calculate the solar terminator using NOAA solar equations:

```javascript
// Day of year (1-365)
const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 86400000)

// Solar declination (radians)
const declination = -23.45 * Math.PI / 180 * Math.cos(2 * Math.PI / 365 * (dayOfYear + 10))

// Approximate sunrise/sunset longitude at each latitude
// For each lat from -90 to 90, compute the terminator lon
function getTerminatorPoints(date) {
  // Returns array of [lon, lat] points forming the terminator polygon
}
```

Render as a `PolygonLayer`:
- Night side: filled with `rgba(0, 0, 30, 0.5)` (dark blue, semi-transparent)
- Day side: no fill (transparent)

The terminator moves slowly (~15° per hour) so it can be recalculated every minute.

### Starfield

Create a large sphere (radius = globe radius * 3) behind the globe:

```javascript
new SphereLayer({
  id: 'starfield',
  data: [{ position: [0, 0, 0] }],
  getSphereRadius: 50000000, // >> globe radius
  getFillColor: [10, 10, 20, 255],
  // Use a star texture or procedural dots
})
```

Better: use a `ScatterplotLayer` with hundreds of randomly placed points at large radius, colored white with low alpha.

### Atmospheric Glow

A slightly larger sphere with a radial gradient:

```javascript
new PolygonLayer({
  id: 'atmosphere',
  data: [{ polygon: /* large circle around globe */ }],
  getFillColor: [100, 150, 255, 30], // blue glow, very transparent
  stroked: true,
  getLineColor: [100, 180, 255, 100],
  lineWidthMinPixels: 2,
})
```

Or use deck.gl's `GlobeView` with custom globe padding to create the glow effect.

## Architecture

All three layers are rendered behind the base tile layer. They are always visible and do not toggle with the layer panel.

```javascript
// Order in deckLayers array:
[starfieldLayer, terminatorLayer, tileLayer, planesLayer, shipsLayer, eventsLayer, conflictsLayer, atmosphereGlowLayer]
```

## Files to Update

- `frontend/src/components/Globe/Globe.jsx` — add terminator calculation, starfield, atmosphere layers
- `frontend/src/components/Globe/Globe.css` — any glow-related styles

## Verification

- [ ] Terminator line is visible and accurate (dark on night side)
- [ ] Stars visible behind the globe in space
- [ ] Atmospheric glow visible at globe edges
- [ ] Globe rotation still smooth
- [ ] No performance degradation
