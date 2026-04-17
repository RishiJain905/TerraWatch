# Phase 5 — Task 10: Loading Skeletons

## Context

Read `frontend/src/components/Globe/Globe.jsx`, `frontend/src/App.jsx`, `frontend/src/index.css`, and `frontend/src/components/Sidebar/Sidebar.css`.

## UI / UX baseline (Gotham — read before implementing)

Replace neon spinners and light-theme skeleton gradients from the old sketch with **token-driven** loading surfaces.

- **Colors:** Overlays use `var(--bg-0)` / `var(--bg-1)` with alpha, bordered by `var(--line)` / `var(--line-strong)` — not raw `rgba(10,10,20)` / `#64c8ff` unless mapped to a token (`--accent-sea` can drive a spinner stroke if a spinner is kept).
- **Skeleton shimmer:** Animate between `var(--line-soft)` and `var(--line-strong)` (or a subtle horizontal gradient using those stops) instead of bright white bands on dark gray.
- **Typography:** Loading copy uses `var(--mono)` or `var(--sans)` in the same micro-caps / letter-spacing regime as `.sidebar-header-meta` (`10px`, uppercase, `var(--text-2)`).
- **Motion:** Reuse global `prefers-reduced-motion` behavior — if skeletons animate, provide a static fallback when reduced motion is requested.

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
  background: color-mix(in srgb, var(--bg-0) 75%, transparent);
  z-index: 100;
}

.globe-loading-spinner {
  width: 40px;
  height: 40px;
  border: 2px solid var(--line);
  border-top-color: var(--accent-sea);
  border-radius: 50%;
  animation: globeSpin 0.9s linear infinite;
}

.globe-loading-text {
  margin-top: 14px;
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--text-2);
}

@keyframes globeSpin {
  to { transform: rotate(360deg); }
}
```

If `color-mix` is undesirable for browser support targets, use `rgba(11, 14, 20, 0.85)` which matches the HUD panels.

Show layer-specific loading status:
- "Loading aircraft..." when planes not yet loaded
- "Loading maritime..." when ships not yet loaded

### Sidebar Skeleton

The sidebar can show skeleton lines in the layer count area while data is loading:
- A pulsing bar using **`var(--line-soft)` → `var(--line-strong)`** instead of high-contrast white shimmer
- Same vertical rhythm as `.layer-count` / `.count-filtered`

```css
.skeleton-line {
  height: 12px;
  background: linear-gradient(
    90deg,
    var(--line-soft) 25%,
    var(--line-strong) 50%,
    var(--line-soft) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
  border-radius: 2px;
}
```

## Files to Update

- `frontend/src/components/Globe/Globe.jsx` — add loading state tracking and skeleton overlay
- `frontend/src/components/Globe/Globe.css` — skeleton and overlay styles (token-driven)
- `frontend/src/components/Sidebar/Sidebar.css` — sidebar skeleton styles (token-driven)
- `frontend/src/components/Sidebar/Sidebar.jsx` — wire skeleton visibility to the same loaded signals

## Verification

- [ ] Skeleton overlay appears while initial data loads
- [ ] Layer-specific loading text shown (Gotham typography)
- [ ] Skeleton disappears once all layers have data (per chosen loaded heuristic)
- [ ] Globe and sidebar skeletons use consistent animation and **design tokens**
- [ ] No flash of empty content during initial load
- [ ] Reduced-motion: animation degrades gracefully per global CSS rules
