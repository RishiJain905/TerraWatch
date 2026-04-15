# Phase 5 Task 1: Terminator Line + Starfield + Atmospheric Glow — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add three visual enhancements to the TerraWatch globe — a day/night terminator line, a starfield background, and an atmospheric rim glow — transforming the globe from "flat map on sphere" to "planet from space."

**Architecture:** All three effects are additive, always-on visual layers rendered in the deck.gl layer stack. The terminator uses a `SolidPolygonLayer` with a computed night-side polygon. The starfield uses a `ScatterplotLayer` with procedurally placed points at large radius. The atmosphere glow uses a CSS radial-gradient overlay keyed off the globe's projected circle. No new npm packages are needed.

**Tech Stack:** deck.gl v9 (`SolidPolygonLayer`, `ScatterplotLayer`), React 18, plain CSS, NOAA solar equations (implemented in-house — no suncalc dependency).

---

## Spec vs Live Repo Reconciliation

| Spec Reference | Live File | Notes |
|---|---|---|
| `Architecture.md` | `docs/ARCHITECTURE.md` | Case mismatch only |
| `Data_source.md` | `docs/DATA_SOURCES.md` | Case mismatch only |
| `Phase5_overview.md` | `docs/phases/phase5/PHASE5_OVERVIEW.md` | Case + path mismatch |
| `task_1_GLM_terminator_starfield_atmosphere.md` | `docs/phases/phase5/task_1_GLM_terminator_starfield_atmosphere.md` | Path mismatch |
| `execution.md` | `Workflows/execution.md` | Path mismatch |

**Key technical divergences from spec:**

1. **No `SphereLayer` in deck.gl v9.** The spec suggests `SphereLayer` for the starfield — this layer does not exist in the installed `@deck.gl/layers@9.0.35`. We will use `ScatterplotLayer` with points at very large radius instead (spec itself provides this as the "Better" alternative).

2. **Atmosphere glow via CSS overlay, not a PolygonLayer.** The spec suggests a `PolygonLayer` or custom globe padding for atmosphere. deck.gl's `GlobeView` does not expose a `padding` prop or custom shader hooks in v9. A CSS pseudo-element with a radial gradient positioned over the center of the globe container is simpler, more performant, and achieves the exact same visual effect (soft blue glow at globe edges).

3. **Terminator `PolygonLayer` → `SolidPolygonLayer`.** The spec says `PolygonLayer` but for a filled night-side fill without stroke, `SolidPolygonLayer` is the correct deck.gl v9 layer for filled polygons.

4. **Layer order in spec.** The spec shows: `[starfieldLayer, terminatorLayer, tileLayer, ..., atmosphereGlowLayer]`. Since the atmosphere glow is a CSS overlay (not a deck.gl layer), it renders on top by default, which matches the z-order intent. Starfield and terminator insert before `tileLayer` in the deck stack.

5. **Star visibility with default farZ.** deck.gl `GlobeView` computes `farZ` from altitude and scale. Stars at very large radius may be clipped. We use a modest radius multiplier (globe radius × 10 → ~2.5M meters) instead of the spec's ×50M to stay within the far clip plane, while still appearing "behind" the globe.

---

## Implementation Tasks

### Task 1: Create `terminator.js` utility — solar position + night-side polygon

**Objective:** Provide a pure function that returns the night-side polygon coordinates given a Date object.

**Files:**
- Create: `frontend/src/utils/terminator.js`

**Step 1: Write the terminator utility**

```javascript
/**
 * TerraWatch Terminator Utility
 * Calculates the solar terminator (day/night boundary) using NOAA solar equations.
 * Returns a polygon covering the night side of the Earth.
 */

/**
 * Get the day of year (1-366) for a given date.
 */
function getDayOfYear(date) {
  const start = new Date(date.getUTCFullYear(), 0, 0)
  const diff = date - start
  return Math.floor(diff / 86400000)
}

/**
 * Calculate the approximate solar declination in radians.
 * Uses the simple NOAA approximation: δ = -23.45° × cos(360/365 × (d + 10))
 */
function getSolarDeclination(date) {
  const dayOfYear = getDayOfYear(date)
  return (-23.45 * Math.PI / 180) * Math.cos((2 * Math.PI / 365) * (dayOfYear + 10))
}

/**
 * Calculate the subsolar longitude (where the sun is directly overhead) in degrees.
 * Based on UTC time: solar noon at Greenwich ≈ 12:00 UTC,
 * so the subsolar point moves ~15°/hour west from 0° at 12:00 UTC.
 */
function getSubsolarLongitude(date) {
  const hours = date.getUTCHours() + date.getUTCMinutes() / 60 + date.getUTCSeconds() / 3600
  // At 12:00 UTC, sun is at ~0° longitude (equation of time ignored for visual purposes)
  return (12 - hours) * 15
}

/**
 * Calculate whether a given [lon, lat] point is on the night side.
 * A point is in night if the solar elevation angle is negative.
 *
 * @param {number} lon - longitude in degrees
 * @param {number} lat - latitude in degrees
 * @param {number} decRad - solar declination in radians
 * @param {number} subSolarLon - subsolar longitude in degrees
 * @returns {boolean} true if the point is on the night side
 */
function isNight(lon, lat, decRad, subSolarLon) {
  const latRad = lat * Math.PI / 180
  const hourAngle = (lon - subSolarLon) * Math.PI / 180
  // Solar elevation = arcsin(sin(lat)*sin(dec) + cos(lat)*cos(dec)*cos(hourAngle))
  const sinElev = Math.sin(latRad) * Math.sin(decRad) +
                  Math.cos(latRad) * Math.cos(decRad) * Math.cos(hourAngle)
  return sinElev < 0
}

/**
 * Compute the terminator polygon: a polygon covering the entire night side.
 * Strategy: sample latitudes from -90 to 90, find the terminator longitude at each,
 * then build a polygon that covers the night hemisphere.
 *
 * Returns an array of [lon, lat] coordinates forming the night-side polygon.
 * The polygon is closed (first point repeated at end).
 *
 * @param {Date} [date] - date for calculation (defaults to now)
 * @returns {Array<[number, number]>} polygon coordinates
 */
export function getTerminatorPolygon(date = new Date()) {
  const decRad = getSolarDeclination(date)
  const subSolarLon = getSubsolarLongitude(date)

  const NUM_LAT_SAMPLES = 36 // sample every 5 degrees
  const points = []

  // Walk terminator from south pole to north pole (night-side boundary, eastern side)
  for (let i = 0; i <= NUM_LAT_SAMPLES; i++) {
    const lat = -90 + (180 * i / NUM_LAT_SAMPLES)
    // Find terminator longitude at this latitude
    const termLon = findTerminatorLongitude(lat, decRad, subSolarLon)
    points.push([termLon, lat])
  }

  // Walk back from north pole to south pole (night-side boundary, western side)
  // The night side is 180° away from the day side
  for (let i = NUM_LAT_SAMPLES; i >= 0; i--) {
    const lat = -90 + (180 * i / NUM_LAT_SAMPLES)
    const termLon = findTerminatorLongitude(lat, decRad, subSolarLon)
    // The opposite side of the terminator
    const nightLon = termLon + 180 > 180 ? termLon - 180 : termLon + 180
    points.push([nightLon, lat])
  }

  // Close the polygon
  points.push([...points[0]])

  return points
}

/**
 * Find the longitude where the terminator crosses a given latitude.
 * Uses bisection to find where the solar elevation angle = 0.
 *
 * @param {number} lat - latitude in degrees
 * @param {number} decRad - solar declination in radians
 * @param {number} subSolarLon - subsolar longitude in degrees
 * @returns {number} terminator longitude in degrees
 */
function findTerminatorLongitude(lat, decRad, subSolarLon) {
  // Handle polar cases
  const latRad = lat * Math.PI / 180
  if (Math.abs(lat) > 89) {
    // At the poles, terminator longitude matches subsolar longitude
    return subSolarLon
  }

  // Use bisection: find lon where solar elevation = 0
  let lo = subSolarLon - 180
  let hi = subSolarLon + 180

  for (let iter = 0; iter < 50; iter++) {
    const mid = (lo + hi) / 2
    const sinElev = Math.sin(latRad) * Math.sin(decRad) +
                    Math.cos(latRad) * Math.cos(decRad) *
                    Math.cos((mid - subSolarLon) * Math.PI / 180)
    if (sinElev > 0) {
      // Day side — terminator is further west
      lo = mid
    } else {
      hi = mid
    }
    if (hi - lo < 0.001) break
  }

  return (lo + hi) / 2
}

/**
 * Check if a point is on the night side (convenience wrapper).
 * @param {number} lon
 * @param {number} lat
 * @param {Date} [date]
 * @returns {boolean}
 */
export function isNightSide(lon, lat, date = new Date()) {
  const decRad = getSolarDeclination(date)
  const subSolarLon = getSubsolarLongitude(date)
  return isNight(lon, lat, decRad, subSolarLon)
}
```

**Step 2: Verify the utility loads**

```bash
cd ~/TerraWatch/frontend
node -e "
  const m = require('./src/utils/terminator.js');  # won't work with ESM, just check syntax
"
# Instead, verify by starting the dev server and checking for import errors
```

We'll verify during integration in Task 4.

**Step 3: Commit**

```bash
cd ~/TerraWatch
git add frontend/src/utils/terminator.js
git commit -m "feat(globe): add terminator utility — solar position + night-side polygon"
```

---

### Task 2: Create starfield generator utility

**Objective:** Provide a pure function that generates a stable set of star positions (randomly distributed on a large-radius sphere) for the ScatterplotLayer. Use a seeded PRNG so positions are stable across re-renders.

**Files:**
- Create: `frontend/src/utils/starfield.js`

**Step 1: Write the starfield utility**

```javascript
/**
 * TerraWatch Starfield Utility
 * Generates stable, procedurally-placed star positions on a large-radius sphere
 * for rendering behind the globe.
 */

/**
 * Simple seeded PRNG (mulberry32) — ensures stars don't shift between frames.
 */
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * Generate star positions distributed uniformly on a sphere.
 *
 * @param {Object} options
 * @param {number} [options.count=800] - number of stars
 * @param {number} [options.radius=20000000] - sphere radius in meters (~globe radius × ~3)
 * @param {number} [options.seed=42] - PRNG seed for stable positions
 * @param {number} [options.minBrightness=0.3] - minimum alpha (0-1)
 * @param {number} [options.maxBrightness=1.0] - maximum alpha (0-1)
 * @returns {Array<{position: [number, number, number], color: [number, number, number, number], radius: number}>}
 */
export function generateStarfield({
  count = 800,
  radius = 20000000,
  seed = 42,
  minBrightness = 0.3,
  maxBrightness = 1.0,
} = {}) {
  const rand = mulberry32(seed)
  const stars = []

  for (let i = 0; i < count; i++) {
    // Uniform distribution on sphere surface
    // theta ∈ [0, 2π], phi = arccos(2u - 1) for uniform distribution
    const u = rand()
    const v = rand()
    const theta = 2 * Math.PI * u
    const phi = Math.acos(2 * v - 1)

    const lat = (Math.PI / 2 - phi) * (180 / Math.PI)
    const lon = (theta * 180 / Math.PI) % 360
    if (lon > 180) lon -= 360  // normalize to [-180, 180]

    // Vary brightness and size
    const brightness = minBrightness + rand() * (maxBrightness - minBrightness)
    const starRadius = 80000 + rand() * 200000  // 80-280 km visual radius

    // Slight color variation: most white, some blue-ish, some warm
    const colorVariant = rand()
    let r, g, b
    if (colorVariant < 0.7) {
      // White stars
      r = 255; g = 255; b = 255
    } else if (colorVariant < 0.85) {
      // Blue-white stars
      r = 180; g = 200; b = 255
    } else {
      // Warm stars
      r = 255; g = 220; b = 180
    }

    stars.push({
      position: [lon, lat, radius],
      color: [r, g, b, Math.round(brightness * 255)],
      radius: starRadius,
    })
  }

  return stars
}
```

**Step 2: Commit**

```bash
cd ~/TerraWatch
git add frontend/src/utils/starfield.js
git commit -m "feat(globe): add starfield generator — seeded PRNG stable star positions"
```

---

### Task 3: Add atmosphere glow CSS overlay to Globe.css

**Objective:** Add a CSS pseudo-element that creates a soft blue radial glow around the projected globe circle, simulating atmospheric rim light.

**Files:**
- Modify: `frontend/src/components/Globe/Globe.css`

**Step 1: Add atmosphere glow styles**

Append the following to `Globe.css`:

```css
/* Atmosphere glow — soft blue rim light at globe edges */
.globe-container::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 52%;   /* slightly larger than the projected globe circle */
  height: 88%;  /* match the vertical extent */
  border-radius: 50%;
  background: radial-gradient(
    circle,
    transparent 42%,
    rgba(100, 150, 255, 0.03) 48%,
    rgba(100, 180, 255, 0.06) 52%,
    rgba(100, 150, 255, 0.03) 56%,
    transparent 62%
  );
  pointer-events: none;
  z-index: 5;
}
```

**Design notes:**
- The gradient is extremely subtle (3-6% alpha) — it should look like a faint atmospheric haze, not a colored ring.
- `pointer-events: none` ensures it doesn't block deck.gl interactions.
- `z-index: 5` places it above the deck.gl canvas (z-index 1) but below the info bar (z-index 10) and legend (z-index 100).
- The width/height percentages are tuned for a landscape viewport where the globe projects as an ellipse slightly wider than tall. We'll refine in visual verification (Task 5).

**Step 2: Commit**

```bash
cd ~/TerraWatch
git add frontend/src/components/Globe/Globe.css
git commit -m "feat(globe): add atmosphere glow CSS overlay — soft blue radial gradient"
```

---

### Task 4: Integrate terminator, starfield, and atmosphere into Globe.jsx

**Objective:** Wire the new utilities and CSS into the main globe component, adding all three visual layers to the deck.gl layer stack.

**Files:**
- Modify: `frontend/src/components/Globe/Globe.jsx`

**Step 1: Add imports**

Add these imports after the existing imports (line 14):

```javascript
import { getTerminatorPolygon } from '../../utils/terminator'
import { generateStarfield } from '../../utils/starfield'
```

Add `SolidPolygonLayer` to the deck.gl layers import (line 5):

```javascript
import { IconLayer, BitmapLayer, ScatterplotLayer, SolidPolygonLayer } from '@deck.gl/layers'
```

**Step 2: Generate starfield data (memoized)**

After the `INITIAL_VIEW_STATE` definition (after line 22), add:

```javascript
// Generate starfield once — stable across re-renders (seeded PRNG)
const STARFIELD_DATA = generateStarfield({ count: 800, radius: 20000000, seed: 42 })
```

**Step 3: Add terminator recalculation timer**

Inside the `Globe` component function, after the `useFilterHooksReady` effect (after line 56), add:

```javascript
  // Terminator polygon — recalculated every 60 seconds (terminator moves ~15°/hour)
  const [terminatorPolygon, setTerminatorPolygon] = useState(() => getTerminatorPolygon())

  useEffect(() => {
    const interval = setInterval(() => {
      setTerminatorPolygon(getTerminatorPolygon())
    }, 60000) // every minute
    return () => clearInterval(interval)
  }, [])
```

**Step 4: Build the three new layers**

After the `tileLayer` definition (after line 105) and BEFORE the `deckLayers` assembly (before line 108), add:

```javascript
  // Starfield layer — scatter points on a large-radius sphere behind the globe
  const starfieldLayer = new ScatterplotLayer({
    id: 'starfield-layer',
    data: STARFIELD_DATA,
    pickable: false,
    getPosition: d => d.position,
    getFillColor: d => d.color,
    getRadius: d => d.radius,
    radiusUnits: 'meters',
    opacity: 0.9,
    stroked: false,
  })

  // Terminator layer — semi-transparent dark fill on the night side
  const terminatorLayer = new SolidPolygonLayer({
    id: 'terminator-layer',
    data: [{ polygon: terminatorPolygon }],
    getPolygon: d => d.polygon,
    getFillColor: [0, 0, 30, 128],   // dark blue, 50% transparent
    getLineColor: [50, 80, 160, 100], // subtle blue terminator line
    lineWidthMinPixels: 1,
    stroked: true,
    pickable: false,
  })
```

**Step 5: Assemble layer stack in the correct order**

Replace the existing layer assembly (line 108):

```javascript
  // Build deck.gl layers — order matters for overlapping rendering
  // starfield → terminator → tiles → data layers → (atmosphere via CSS)
  const deckLayers = [starfieldLayer, terminatorLayer, tileLayer]
```

The rest of the `if` blocks for planes/ships/events/conflicts remain unchanged — they continue to `.push()` onto `deckLayers` after the tile layer.

**Step 6: Verify the file compiles**

```bash
cd ~/TerraWatch/frontend
npx vite build --logLevel error 2>&1 | tail -5
# Expected: no errors about missing imports or invalid layer props
```

**Step 7: Commit**

```bash
cd ~/TerraWatch
git add frontend/src/components/Globe/Globe.jsx
git commit -m "feat(globe): integrate terminator, starfield layers into deck.gl stack

- Terminator: SolidPolygonLayer with night-side fill, recalculated every 60s
- Starfield: 800 ScatterplotLayer points on radius-20Mm sphere
- Atmosphere: CSS ::after overlay with radial gradient (added in prior commit)
- Layer order: starfield → terminator → tiles → data layers"
```

---

### Task 5: Visual verification + performance check

**Objective:** Start the dev server, visually verify all three enhancements, and confirm no performance regression.

**Step 1: Start the app**

```bash
cd ~/TerraWatch
docker compose up --build  # or: cd frontend && npx vite --host
```

**Verification checklist (from spec):**
- [ ] Terminator line is visible and accurate (dark on night side)
- [ ] Stars visible behind the globe in space
- [ ] Atmospheric glow visible at globe edges
- [ ] Globe rotation still smooth (no jank)
- [ ] No performance degradation (10k+ planes still smooth)

**Step 2: Adjust if needed**

If the atmosphere glow size is off, tweak the width/height percentages in `Globe.css` `::after` pseudo-element.

If stars are clipped by the far plane, reduce `radius` in the `generateStarfield` call (try 10000000 → 10Mm).

If the terminator polygon looks wrong, check that `SolidPolygonLayer` handles the antimeridian correctly. If the polygon crosses the antimeridian (±180°), split it into two polygons: one from terminator lon to +180°, and one from -180° to terminator lon + 180°.

**Step 3: Take a screenshot for evidence**

**Step 4: Final commit (if any adjustments made)**

```bash
cd ~/TerraWatch
git add -A
git commit -m "fix(globe): visual tuning for terminator, starfield, atmosphere glow"
```

---

## Execution Order Summary

| Task | What | Files Changed | Can Parallel? |
|------|------|---------------|---------------|
| 1 | Create `terminator.js` | `frontend/src/utils/terminator.js` (NEW) | Yes (1-3 parallel) |
| 2 | Create `starfield.js` | `frontend/src/utils/starfield.js` (NEW) | Yes |
| 3 | Add atmosphere CSS | `frontend/src/components/Globe/Globe.css` (UPDATE) | Yes |
| 4 | Integrate into Globe.jsx | `frontend/src/components/Globe/Globe.jsx` (UPDATE) | No (depends on 1-3) |
| 5 | Visual verification + tuning | Possibly all above | No (depends on 4) |

**Parallel plan:** Tasks 1, 2, and 3 can be delegated simultaneously to subagents. Task 4 must wait for all three. Task 5 must wait for 4.

## Summary File

Upon successful completion, create `docs/phases/phase5/P5-task1-done.md` per TerraWatch convention.