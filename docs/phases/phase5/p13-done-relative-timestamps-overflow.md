# Phase 5 — Task 13 Done: Relative Timestamps + Panel Overflow

## Summary
Replaced raw ISO timestamps in all four info panels with human-readable relative time strings, and added panel overflow protection with narrow-viewport clamping.

## Changes Made

### Utility — `frontend/src/utils/formatters.js`
- Added `formatRelativeTime(isoTimestamp)` exported utility.
- Returns `\u2014` for null/invalid input.
- Cutoffs: `< 60s` → `Just now`, `< 60m` → `Xm ago`, `< 24h` → `Xh ago`, `< 7d` → `Xd ago`, else → locale date string.

### Panels — Relative Timestamps
- **PlaneInfoPanel.jsx**: `timestamp` (corrected from misnamed `last_contact`) now uses `formatRelativeTime`. Removed unused `formatTimestamp` import.
- **ShipInfoPanel.jsx**: Removed local `formatLastSeen`; `timestamp` now uses shared `formatRelativeTime`.
- **EventInfoPanel.jsx**: Removed local `formatDate`; `date` now uses shared `formatRelativeTime`.
- **ConflictInfoPanel.jsx**: Removed local `formatDate`; `date` now uses shared `formatRelativeTime`.

### CSS — Panel Overflow
- **`frontend/src/components/InfoPanel/infoPanel.css`**:
  - Added `max-height: calc(100vh - 88px)` to `.plane-info-panel, .ship-info-panel`.
  - Added `overflow-y: auto; overflow-x: hidden` for internal scrolling.
  - Added `@media (max-width: 400px)` clamp: `right: 8px; left: 8px; width: auto; max-width: min(100vw - 16px, 360px)`.
  - Existing `z-index: 1000` preserved.

## Verification
- **Note on field names:** `Plane.timestamp` is the correct field from the backend `Plane` model (`last_contact` was a stale/misidentified key). Ships use `ship.timestamp`, events use `event.date`, conflicts use `conflict.date` — all correctly mapped.
- [x] `npm run build` passes (vite build, exit code 0).
- [x] `formatRelativeTime` unit behavior verified by inspection:
  - Null/invalid → `—`
  - `< 60s` → `Just now`
  - `< 60m` → `Xm ago`
  - `< 24h` → `Xh ago`
  - `< 7d` → `Xd ago`
  - `≥ 7d` → locale date string
- [x] All four panel JSX files import and call `formatRelativeTime` correctly.
- [x] Panel CSS covers all four panel types (plane, ship, event, conflict) via shared `.plane-info-panel` class.
- [x] `z-index: 1000` unchanged; stacking above Globe HUD confirmed.

## Notes
- Relative time labels are **static while the panel is open** (no live interval refresh). Time updates when a new object is selected and the panel re-renders. This keeps CPU usage negligible and matches existing app patterns.
- The previous `ShipInfoPanel` local `formatLastSeen` only returned seconds/minutes/hours (no days or locale fallback). The new shared utility provides strictly better coverage.
