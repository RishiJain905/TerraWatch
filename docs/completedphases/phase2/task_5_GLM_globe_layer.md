# Task 5 — Globe Plane Layer with Directional Icons
**Agent:** GLM 5.1 (Frontend)
**Dependencies:** Task 1 (M2.7 docs)

## Goal

Update the deck.gl globe to display planes as directional icons that rotate based on heading. Color-code by altitude.

## Context

- Read `frontend/src/components/Globe/Globe.jsx`
- Read `frontend/src/components/Globe/Globe.css`
- Read `frontend/src/hooks/usePlanes.js`
- Read `frontend/src/services/api.js`

## Steps

### 1. Review Current Globe.jsx

The globe currently uses ScatterplotLayer for planes. We need to upgrade to IconLayer for directional aircraft icons.

### 2. Install Required deck.gl Layers

Check `frontend/package.json` — verify these packages are present:
- `@deck.gl/core`
- `@deck.gl/layers`
- `@deck.gl/geo-layers`
- `@deck.gl/react`

If IconLayer isn't available, it comes from `@deck.gl/layers`.

### 3. Upgrade Plane Layer to IconLayer

In `Globe.jsx`, replace the ScatterplotLayer for planes with IconLayer:

```javascript
import { IconLayer } from '@deck.gl/layers'
// IconLayer handles both static icons and rotated markers
```

Replace the planes ScatterplotLayer section with:

```javascript
// Plane layer — directional icons
if (layers && layers.planes) {
  deckLayers.push(
    new IconLayer({
      id: 'planes-layer',
      data: planes,
      pickable: true,
      // Use a simple marker — we'll create a data URL for the plane icon
      getIcon: d => ({
        url: createPlaneIcon(d.alt),  // color based on altitude
        width: 64,
        height: 64,
        anchorY: 32,
      }),
      getPosition: d => [d.lon, d.lat],
      getSize: 48,
      getAngle: d => -d.heading,  // deck.gl uses degrees, negate for rotation
      onClick: (info) => onEntityClick && onEntityClick('plane', info.object),
      billboard: false,  // Keep icons flat to globe surface
    })
  )
}
```

### 4. Create Plane Icon Function

Add this helper in `Globe.jsx` or a new `frontend/src/utils/planeIcons.js`:

```javascript
// Create a plane SVG icon as a data URL, colored by altitude
function createPlaneIcon(altitude) {
  // Color: low=green(0,255,0), medium=yellow(255,255,0), high=red(255,0,0)
  let color
  if (altitude < 10000) {
    color = [0, 255, 100]  // low — green
  } else if (altitude < 30000) {
    color = [255, 255, 0]  // medium — yellow
  } else {
    color = [255, 100, 100]  // high — red
  }
  
  // Return a data URL with inline SVG
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
    <polygon points="32,4 44,56 32,48 20,56" fill="rgb(${color.join(',')})" stroke="white" stroke-width="2"/>
  </svg>`
  
  return `data:image/svg+xml;base64,${btoa(svg)}`
}
```

### 5. Add Altitude Color Legend

In `Globe.css`, add:

```css
.globe-legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(0, 0, 0, 0.7);
  padding: 10px 15px;
  border-radius: 6px;
  font-size: 12px;
  color: #fff;
  z-index: 100;
}

.legend-item {
  display: flex;
  align-items: center;
  margin: 4px 0;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}

.legend-dot.low { background: rgb(0, 255, 100); }
.legend-dot.medium { background: rgb(255, 255, 0); }
.legend-dot.high { background: rgb(255, 100, 100); }
```

### 6. Update Globe.jsx to Render Legend

In the Globe return:

```jsx
<div className="globe-container">
  {/* existing globe code */}
  <div className="globe-legend">
    <div className="legend-item"><span className="legend-dot low"></span>Low (&lt;10k ft)</div>
    <div className="legend-item"><span className="legend-dot medium"></span>Medium (10-30k ft)</div>
    <div className="legend-item"><span className="legend-dot high"></span>High (&gt;30k ft)</div>
  </div>
</div>
```

### 7. Handle Missing Data Gracefully

In IconLayer, handle cases where heading might be null:

```javascript
getAngle: d => -(d.heading || 0),
```

### 8. Verify WebSocket Updates

The existing `useWebSocket` hook should already handle `type: 'plane'` messages and call `addPlane`. Verify this works with the new data structure from the scheduler.

### 9. Test in Browser

Run `npm run dev` and check:
- [ ] Globe renders
- [ ] Planes appear with directional icons
- [ ] Icons rotate based on heading
- [ ] Color coding works (low=green, medium=yellow, high=red)
- [ ] Altitude legend is visible
- [ ] Console has no errors

## Output

- Updated `frontend/src/components/Globe/Globe.jsx` with IconLayer
- Updated `frontend/src/components/Globe/Globe.css` with legend styles
- Icon helper function (inline or extracted to utils)

## Handoff

After completing, message M2.7 (coordinator) that Task 5 is done and Task 7 (integration) can begin once Tasks 3 and 6 are also complete.
