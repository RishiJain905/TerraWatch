# Phase 5 — Task 3: Minimap / Navigator Inset

## Context

Read `frontend/src/components/Globe/Globe.jsx` and `frontend/src/components/Globe/Globe.css` first. Note **Phase 5 Task 2** already added `MapStyleSwitcher.jsx` (top-right basemap HUD) and dynamic `MAP_STYLES` tile URLs in `Globe.jsx` — the minimap must stay visually and technically consistent with that stack.

## UI / UX baseline (Gotham — read before implementing)

The app uses a **Gotham command-panel** aesthetic. Do not ship generic floating circles with soft gray borders from older sketches.

- **Design tokens:** `frontend/src/index.css` — `--bg-*`, `--line`, `--line-strong`, `--text-*`, `--accent-air`, `--accent-sea`, `--mono`, `--sans`, etc.
- **Globe HUD reference:** `frontend/src/components/Globe/Globe.css` — `.globe-info`, `.globe-legend`, `.map-style-switcher` (corner brackets, `backdrop-filter: blur(12px)`, `rgba(11, 14, 20, 0.92)` panels).
- **Layout:** Top-right is reserved for the basemap switcher. Place the minimap **bottom-right** with enough `bottom` offset to clear the centered `.globe-info` strip (see existing `bottom` / `right` values in `Globe.css`). Bottom-left is the legend — avoid overlapping it.
- **Interaction:** The minimap is read-only navigation context — set `pointer-events: none` on the minimap wrapper (or the inner canvas container) so it never steals pan/zoom from the main `DeckGL`.
- **Basemap sync:** The main globe’s basemap URL comes from `MAP_STYLES` / `mapStyle` state. The minimap should use the **same** active basemap URL (and the same night-lights overlay behavior if applicable), not a second hard-coded Carto URL, so the inset always matches what the user sees.
- **Motion:** Any optional pulse on the view indicator should honor `prefers-reduced-motion` (`index.css` already defines global reduced-motion rules).

## Goal

Add a small globe inset in the corner of the screen showing the user's current view position on the full Earth. This is a standard GEOINT navigation aid.

## Implementation

### Minimap Component

Create a second, smaller `DeckGL` instance with its own `GlobeView` positioned absolutely in the bottom-right corner:

```javascript
function Minimap({ viewState, basemapUrl, overlayUrl }) {
  return (
    <div className="minimap-container" aria-hidden="true">
      <DeckGL
        views={new GlobeView({ id: 'minimap-globe' })}
        viewState={{
          longitude: viewState.longitude,
          latitude: viewState.latitude,
          zoom: 1,
          pitch: 0,
          bearing: 0, // always north-up
        }}
        layers={[
          new TileLayer({
            data: basemapUrl,
            // ... same renderSubLayers → BitmapLayer pattern as main Globe tileLayer
          }),
          // Optional: second TileLayer when overlayUrl is set (night lights)
          // View indicator: small dot at current view center — use RGBA that
          // aligns with plane accent (e.g. 232,184,74 ≈ --accent-air) not neon red
          new ScatterplotLayer({
            id: 'minimap-indicator',
            data: [{ longitude: viewState.longitude, latitude: viewState.latitude }],
            getPosition: d => [d.longitude, d.latitude],
            getFillColor: [232, 184, 74, 255],
            getRadius: 50000,
          }),
        ]}
      />
    </div>
  )
}
```

### Styling (Gotham-aligned)

Replace generic white-border / perfect circle language with HUD chrome that matches `.globe-legend` / `.map-style-switcher`:

```css
.minimap-container {
  position: absolute;
  bottom: 72px; /* clear .globe-info — tune against actual strip height */
  right: 16px;
  width: 148px;
  height: 148px;
  border-radius: 2px; /* square geometry matches sidebar cards; optional subtle radius only */
  border: 1px solid var(--line-strong);
  background: rgba(11, 14, 20, 0.92);
  overflow: hidden;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.4),
    0 8px 32px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  pointer-events: none;
  z-index: 90; /* below .globe-legend (100) if overlap risk; above deck canvas */
}

/* Optional: same corner-bracket ::before / ::after pattern as .globe-info */
```

### Sync with Main Globe

The minimap always shows north-up orientation. It reflects the main globe's center position. When the main globe rotates, the indicator dot moves accordingly.

## Files to Update

- `frontend/src/components/Globe/Globe.jsx` — render `<Minimap viewState={viewState} basemapUrl={...} overlayUrl={...} />` (wire URLs from the same `MAP_STYLES` / `mapStyle` source as the main basemap)
- `frontend/src/components/Globe/Globe.css` — minimap positioning and Gotham-aligned styling
- `frontend/src/components/Globe/Minimap.jsx` — NEW component

## Verification

- [ ] Minimap visible in bottom-right corner, clears `.globe-info` and does not cover `.globe-legend`
- [ ] Shows full globe with **current** basemap style (including night-lights overlay when active)
- [ ] Indicator shows current view center; uses accent color consistent with HUD (not unrelated neon palette)
- [ ] Minimap is north-up regardless of main globe bearing
- [ ] Minimap does not intercept pointer events on the main globe
- [ ] Panel chrome (border, blur, shadow) matches other globe HUD elements
