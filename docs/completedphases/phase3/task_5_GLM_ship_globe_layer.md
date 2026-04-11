# Phase 3 — Task 5: GLM 5.1 — Ship IconLayer on Globe

## Context

Ships are flowing through the backend. This task replaces the placeholder ScatterplotLayer for ships with directional IconLayer icons, color-coded by ship type — mirroring how planes are rendered.

## Instructions

You are GLM 5.1 (frontend specialist). Read these files first:
- `docs/ARCHITECTURE.md`
- `docs/docs/completedphases/phase3/PHASE3_OVERVIEW.md`
- `docs/docs/completedphases/phase3/P3-task1-done.md`
- `frontend/src/components/Globe/Globe.jsx` (existing plane IconLayer — use as reference)
- `frontend/src/utils/planeIcons.js` (existing plane icon generation — use as pattern)
- `frontend/src/hooks/useShips.js` (existing — verify it handles ship_batch WS messages)
- `frontend/src/components/Globe/Globe.css` (existing styles)

## Your Task

### 1. Create `frontend/src/utils/shipIcons.js`

Generate directional ship/boat SVG icons (parallel to `planeIcons.js`):

```javascript
// Generate directional SVG ship icon rotated by heading
export function getShipIcon(type, heading = 0) {
  // Return an icon atlas entry { url, width, height, anchorY }
  // Use different icon shapes per ship type:
  // - cargo: large container ship silhouette
  // - tanker: wide vessel silhouette
  // - passenger: ferry/boat shape
  // - fishing: small boat
  // - other: generic boat
}
```

Requirements:
- Directional icons rotated by `heading` field
- At least 3 icon variants based on ship type
- Pre-cached at module load (same pattern as planeIcons.js)
- Returns a proper icon atlas for deck.gl IconLayer

### 2. Update `frontend/src/hooks/useShips.js`

Ensure it handles WebSocket messages correctly:
- `type: "ship"` — single ship upsert
- `type: "ship_batch"` — batch upsert (preferred)
- `action: "remove"` — remove ship by id

```javascript
// Expected WebSocket message formats:
// { type: "ship", action: "upsert", data: {...ship} }
// { type: "ship_batch", action: "upsert", data: [...ships] }
// { type: "ship", action: "remove", data: { id: "..." } }
```

### 3. Update `frontend/src/components/Globe/Globe.jsx`

Replace the placeholder ScatterplotLayer with IconLayer for ships:

```javascript
// Replace ScatterplotLayer with IconLayer
new IconLayer({
  id: 'ships-layer',
  data: ships,
  pickable: true,
  getIcon: d => getShipIcon(d.ship_type),
  getPosition: d => [d.lon, d.lat],
  getSize: 48,
  getAngle: d => -(d.heading || 0),
  onClick: (info) => onEntityClick && onEntityClick('ship', info.object),
  billboard: false,
})
```

Color coding by ship type (fallback colors if icons aren't ready):
- Cargo = [74, 144, 217] (blue)
- Tanker = [245, 166, 35] (orange)
- Passenger = [126, 211, 33] (green)
- Fishing = [144, 19, 254] (purple)
- Other = [153, 153, 153] (gray)

### 4. Update `frontend/src/components/Globe/Globe.css`

Update the legend to show ship types alongside plane altitude:

```css
.legend-item .ship-icon.cargo { background: #4A90D9; }
.legend-item .ship-icon.tanker { background: #F5A623; }
/* etc. */
```

### 5. Update `Globe.jsx` info bar

The info bar currently shows:
```javascript
<span>Ships: {ships.length}</span>
```

Keep it, but also ensure the WebSocket status indicator correctly reflects ship data being received.

## Key Constraints

- Ships layer must work alongside the existing planes layer (no regression)
- IconLayer must have proper icon atlas (SVG-based, no external assets)
- Color coding by type
- Ships rotate based on heading field
- Globe must NOT crash if ships array is empty

## Output Files

- `frontend/src/utils/shipIcons.js` — create (new file)
- `frontend/src/hooks/useShips.js` — update to handle ship_batch
- `frontend/src/components/Globe/Globe.jsx` — replace ScatterplotLayer with IconLayer
- `frontend/src/components/Globe/Globe.css` — add ship legend styles

## Verification

- Ships appear as directional icons on globe
- Icons are color-coded by type
- No console errors
- Ships layer toggle in sidebar works
- Globe renders correctly with both planes AND ships simultaneously
