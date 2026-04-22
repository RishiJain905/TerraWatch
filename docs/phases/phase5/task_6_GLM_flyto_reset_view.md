# Phase 5 — Task 6: Fly-To + Reset View

## Context

Read `frontend/src/components/Globe/Globe.jsx` and `frontend/src/App.jsx` first.

## UI / UX baseline (Gotham — read before implementing)

Do **not** use the old generic circular “dark glass” floating button from pre-revamp sketches.

- **Globe HUD controls:** Match the language of `.map-style-switcher` / `.mss-cell` and `.close-btn` in `Globe.css` + `infoPanel.css` — `border-radius: 2px`, `1px solid var(--line-strong)`, `rgba(11, 14, 20, 0.92)` backgrounds, `backdrop-filter: blur(12px)`, mono icon or label, **`--accent-air`** hover/focus emphasis where appropriate.
- **Placement:** **Top-left** for reset is preferred so it does not compete with **Phase 5 Task 2** basemap control (**top-right**). Task 3 minimap will sit **bottom-right** — keep reset away from that corner too.
- **Icons:** Prefer a minimal mono glyph (e.g. `HOME` text label in 9px caps, or a simple geometric icon) consistent with sidebar / HUD typography rather than oversized emoji-style symbols at 18px in a circle.
- **Accessibility:** `type="button"`, `aria-label` on icon-only controls, visible `:focus-visible` outline (global rule in `index.css`).

## Goal

When a user clicks a plane, ship, or event, the globe should smoothly animate to center on that entity rather than snapping instantly. Also add a "Reset View" control to return to the initial view.

## Implementation

### Fly-To on Entity Click

In `Globe.jsx`, when `onEntityClick` fires (i.e., when user clicks an entity), animate the `viewState`:

```javascript
const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
}

// Smooth transition to entity
const flyTo = (entity) => {
  const targetViewState = {
    longitude: entity.lon,
    latitude: entity.lat,
    zoom: 5, // zoom in closer
    pitch: 30,
    bearing: 0,
    transitionDuration: 1000, // 1 second
    transitionInterpolator: new FlyToInterpolator(),
  }
  setViewState(targetViewState)
}
```

Import `FlyToInterpolator` from `@deck.gl/core`:

```javascript
import { FlyToInterpolator } from '@deck.gl/core'
```

When entity click is handled in `App.jsx`, also invoke `flyTo` in `Globe.jsx`. Pass the `flyTo` function as a prop, **or** expose it via `useImperativeHandle` on a ref forwarded from `Globe`, **or** a narrow callback prop — avoid overloading `onFilterHooksReady` unless that pattern is already the established integration surface.

**Note:** `GlobeView` in this codebase historically keeps `pitch: 0`; confirm whether introducing non-zero pitch matches product intent. If pitch must stay 0, animate `longitude` / `latitude` / `zoom` only.

### Reset View Control

Add a compact HUD control (not a 36px circle) that resets to `INITIAL_VIEW_STATE`:

```javascript
const resetView = () => {
  setViewState({
    ...INITIAL_VIEW_STATE,
    transitionDuration: 1000,
    transitionInterpolator: new FlyToInterpolator(),
  })
}
```

Example **Gotham-aligned** markup (label or icon inside a square HUD button):

```jsx
<button
  type="button"
  className="reset-view-btn"
  onClick={resetView}
  aria-label="Reset globe view"
  title="Reset view"
>
  RST
</button>
```

```css
.reset-view-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  padding: 6px 10px;
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-2);
  background: rgba(11, 14, 20, 0.92);
  border: 1px solid var(--line-strong);
  border-radius: 2px;
  cursor: pointer;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.4),
    0 8px 32px rgba(0, 0, 0, 0.5);
  transition: background 140ms ease, color 140ms ease, border-color 140ms ease;
}

.reset-view-btn:hover {
  border-color: var(--accent-air);
  color: var(--text-0);
  background: var(--bg-2);
}
```

Optional: corner-bracket `::before` / `::after` accents matching `.globe-info` for visual continuity.

## Files to Update

- `frontend/src/components/Globe/Globe.jsx` — fly-to logic, reset control, `FlyToInterpolator`
- `frontend/src/components/Globe/Globe.css` — reset control styling (Gotham HUD)
- `frontend/src/App.jsx` — wire fly-to into entity click path (if not handled entirely inside `Globe`)

## Verification

- [ ] Clicking a plane smoothly animates globe to center on it
- [ ] Clicking a ship smoothly animates globe to center on it
- [ ] Clicking an event smoothly animates globe to center on it
- [ ] Reset control returns to initial view with smooth animation
- [ ] Animation is smooth (no jank)
- [ ] Keyboard shortcut R also resets view (Task 7) — keep behavior in sync
- [ ] Reset control visually matches other globe HUD chrome; does not overlap basemap switcher (top-right)
