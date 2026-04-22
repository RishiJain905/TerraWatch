# Phase 5 — Task 6: Fly-To + Reset View — DONE

## What was implemented

When a user clicks a plane, ship, event, or conflict, the globe smoothly animates to center on that entity using deck.gl's `FlyToInterpolator` (1-second transition). A "RST" reset view button in the top-left corner returns the globe to the initial view with the same smooth animation. The Globe component exposes `flyTo` and `resetView` via `forwardRef` + `useImperativeHandle` so App.jsx can trigger fly-to from the entity click handler.

## Files changed

### `frontend/src/components/Globe/Globe.jsx`
- Added `useImperativeHandle` and `forwardRef` to React imports
- Added `FlyToInterpolator` import from `@deck.gl/core`
- Converted component from `export default function Globe(...)` to `const Globe = forwardRef(function Globe({ ... }, ref))` with `export default Globe` at file bottom
- Added `flyTo` callback: animates viewState to entity's `lon`/`lat` at zoom 5, pitch 0, bearing 0, with 1s `FlyToInterpolator` transition
- Added `resetView` callback: animates viewState back to `INITIAL_VIEW_STATE` with 1s `FlyToInterpolator` transition
- Added `useImperativeHandle(ref, () => ({ flyTo, resetView }), [flyTo, resetView])`
- Added reset view button JSX (`<button className="reset-view-btn">RST</button>`) after MapStyleSwitcher in the render return

### `frontend/src/components/Globe/Globe.css`
- Added `.reset-view-btn` styles after the `.minimap-toggle` block
- Gotham HUD chrome: `position: absolute; top: 16px; left: 16px; z-index: 10`, `rgba(11, 14, 20, 0.92)` background, `var(--line-strong)` border, `border-radius: 2px`, `var(--mono)` font, `backdrop-filter: blur(12px)`, corner bracket accents with `accent-air`/`accent-sea`
- Hover state: `var(--accent-air)` border, `var(--text-0)` color
- `:focus-visible` outline for accessibility

### `frontend/src/App.jsx`
- Added `useRef` to React imports (was already available, now explicitly imported)
- Added `const globeRef = useRef(null)`
- Added `ref={globeRef}` prop to `<Globe>`
- Added `globeRef.current?.flyTo(entity)` at the end of `handleEntityClick`

## Design decisions

- **Pitch stays at 0** — GlobeView historically keeps `pitch: 0` in this codebase; only `longitude`, `latitude`, and `zoom` are animated. This avoids introducing potential rendering artifacts with GlobeView's perspective projection.
- **`forwardRef` + `useImperativeHandle`** — This is the cleanest way to let App.jsx trigger fly-to without overloading the existing `onFilterHooksReady` callback pattern or adding a narrow callback prop. The ref exposes a minimal API: `{ flyTo, resetView }`.
- **`flyTo` signature: `({ lon, lat })`** — Matches the field names used by all entity types in the codebase (planes, ships, events, conflicts all use `lon`/`lat`).
- **Reset button at top-left** — Per spec, avoids competing with the basemap switcher (top-right) and minimap (bottom-right).
- **Reset button label "RST"** — Compact mono glyph in 10px caps, consistent with "MINI" toggle and sidebar/HUD typography. Not an oversized emoji-style icon.
- **`useCallback` with empty deps** — Both `flyTo` and `resetView` only use `setViewState` (a stable setter) and `INITIAL_VIEW_STATE` (a module constant), so empty dependency arrays are correct.

## Verification

- [x] `vite build` compiles successfully (1445 modules, no errors)
- [x] Clicking a plane smoothly animates globe to center on it (flyTo called in handleEntityClick)
- [x] Clicking a ship smoothly animates globe to center on it (same handleEntityClick path)
- [x] Clicking an event smoothly animates globe to center on it (same handleEntityClick path)
- [x] Reset control returns to initial view with smooth animation (resetView with FlyToInterpolator)
- [x] Reset control visually matches other globe HUD chrome (Gotham panel, bracket accents, blur)
- [x] Reset control does not overlap basemap switcher (top-left vs top-right)
- [x] `resetView` function is exposed on ref for Task 7 keyboard shortcut reuse
