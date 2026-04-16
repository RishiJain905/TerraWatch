# Terminator Polygon Visual Tuning Guide

## Current State

The terminator utility (`frontend/src/utils/terminator.js`) correctly computes the night-side polygon:
- Crossing points are accurate (equator crossings match expected ~90° from subsolar point)
- `isNightSide()` returns correct results for all test locations
- Polygon winding is CCW per GeoJSON right-hand rule
- `wrapLongitude: true` is set on `SolidPolygonLayer` in `Globe.jsx`
- Polygon recalculates every 60 seconds via `useState` + `setInterval`

## Known Visual Issue

The rendered polygon does not visually match the expected day/night boundary. Despite the math being correct, the deck.gl `SolidPolygonLayer` render may still cover too much or too little area depending on how `wrapLongitude` splits the polygon at the antimeridian.

## What to Tune / Fix

### 1. Polygon Winding Direction

File: `frontend/src/utils/terminator.js`, lines 136-161

Current order (CCW): west edge N→S → south closure → east edge S→N → north closure.

If the visual is still inverted (day side shaded instead of night side), swap back to the original CW order:
- East edge N→S → south closure → west edge S→N → north closure

To test which winding works, toggle between the two builds and check visually.

### 2. wrapLongitude Behavior

File: `frontend/src/components/Globe/Globe.jsx`

Current: `wrapLongitude: true` on the `SolidPolygonLayer`.

What `wrapLongitude` does: splits polygons that cross the ±180° antimeridian into two separate polygons so deck.gl renders them correctly on a globe.

If the split is producing unexpected results, try:
- **Option A**: Keep `wrapLongitude: true` and verify the polygon vertices don't have large longitude jumps (the algorithm already uses `normalizeLon` to keep everything in [-180, 180]).
- **Option B**: Remove `wrapLongitude: true` and instead manually split the polygon into two sub-polygons in `getTerminatorPolygon()`:
  - Poly A: all vertices with lon >= 0 (or lon > some threshold)
  - Poly B: all vertices with lon < 0
  - Each sub-polygon closes independently

### 3. Polygon Opacity and Color

File: `frontend/src/components/Globe/Globe.jsx`, terminatorLayer definition

Current fills:
- `getFillColor: [0, 0, 30, 128]` — dark blue, 50% opacity
- `getLineColor: [50, 80, 160, 100]` — subtle blue terminator line

If the overlay is too heavy or too light, adjust the 4th value (alpha):
- `128` = ~50% opacity (current)
- `64` = ~25% opacity (lighter)
- `192` = ~75% opacity (darker)

### 4. Edge Tracing Debug

Run this in the browser console to inspect the polygon at runtime:

```javascript
(async () => {
  const mod = await import('/src/utils/terminator.js')
  const poly = mod.getTerminatorPolygon()
  
  // Winding check
  let area = 0
  for (let i = 0; i < poly.length - 1; i++)
    area += poly[i][0] * poly[i+1][1] - poly[i+1][0] * poly[i][1]
  console.log('Winding:', area > 0 ? 'CCW' : 'CW', '| Signed area:', (area/2).toFixed(0))
  
  // Equator crossings
  const eq = poly.filter(p => Math.abs(p[1]) < 3).map(p => `[${p[0].toFixed(1)}, ${p[1].toFixed(1)}]`)
  console.log('Equator points:', eq.join(' | '))
  
  // Point-in-polygon consistency
  const tests = [
    { name: 'New York', lon: -74, lat: 40 },
    { name: 'London', lon: 0, lat: 51 },
    { name: 'Tokyo', lon: 139, lat: 35 }
  ]
  tests.forEach(t => {
    const isNight = mod.isNightSide(t.lon, t.lat)
    console.log(`${t.name}: isNight=${isNight}`)
  })
})()
```

### 5. Manual Polygon Split (Nuclear Option)

If `wrapLongitude` does not work as expected, replace `getTerminatorPolygon` to return TWO polygons instead of one, avoiding the antimeridian entirely:

In `terminator.js`:
```javascript
export function getTerminatorPolygons(date = new Date()) {
  const poly = getTerminatorPolygon(date)
  if (poly.length < 4) return []
  
  // Split at antimeridian
  const eastHalf = []  // lon > 0
  const westHalf = []  // lon < 0
  // ... split logic, close each half independently ...
  
  return [eastHalf, westHalf].filter(p => p.length >= 4)
}
```

Then in `Globe.jsx`, change the terminator layer data:
```javascript
const terminatorPolygons = getTerminatorPolygons()
// ...
data: terminatorPolygons.map(polygon => ({ polygon })),
```

And remove `wrapLongitude: true`.

### 6. Quick Visual Test Matrix

| Change | File | Line/Key | Try |
|--------|------|----------|-----|
| Flip winding | terminator.js | lines 139-159 | Swap east/west edge order |
| Adjust opacity | Globe.jsx | getFillColor | `[0, 0, 30, 64]` or `[0, 0, 30, 192]` |
| Toggle wrapLongitude | Globe.jsx | wrapLongitude prop | `true` / `false` |
| Star radius | starfield.js | radius param | `10000000` (10Mm) if stars are clipped |
| Atmosphere size | Globe.css | width/height % | Adjust `52%` / `88%` |
| Terminator line visibility | Globe.jsx | getLineColor alpha | `100` → `200` for more visible |

## Rebuild + Verify

After any change:
```bash
cd ~/TerraWatch/docker && docker compose build frontend && docker compose up -d frontend
```

Then open http://localhost:5173 and verify:
- Night side is shaded, day side is clear
- Terminator boundary lines up with expected sunset/sunrise at known cities
- Stars visible behind the globe
- Atmosphere glow visible at edges
- No console errors