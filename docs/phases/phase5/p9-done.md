# Phase 5 — Task 9: Null Field Graceful Handling — DONE

## Summary

All 4 info panels now render gracefully when fields are null, undefined, or missing. No more `"null"`, `"undefined"`, or blank values — all fallback to em dash `—` or contextual fallbacks.

## Changes Made

### `frontend/src/utils/formatters.js`
- Added `formatOptional(value, formatter, fallback = '—')` — core null-coalescing helper
- Updated `formatAltitude(ft)` — null guard, returns `'—'` when `ft == null`; uses `toLocaleString()` for comma-separated thousands (e.g., `"35,000 ft"`)
- Updated `formatSpeed(kt)` — null guard, returns `'—'` when `kt == null`; format `"X.X kt"`
- Updated `formatCoord(lat, lon)` — null guard for either param being null
- Updated `formatTimestamp(ts)` — null guard + Invalid Date detection
- Added `formatHeading(h)` — extracted from panels; `0` = North (valid), `null` = unknown → `'—'`
- Added `formatTone(tone)` — extracted from panels; `0` is valid (neutral), `null` → `'—'`

### `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx`
- Removed 3 inline formatters (`formatAlt`, `formatSpeed`, `formatHeading`)
- All fields now use shared formatters with null safety
- Added `last_contact` row using `formatTimestamp`
- Heading includes comment explaining 0 vs null distinction
- Header uses `??` (nullish coalescing) instead of `||`

### `frontend/src/components/ShipInfoPanel/ShipInfoPanel.jsx`
- Removed 3 inline formatters (`formatSpeed`, `formatHeading`, `formatPosition`)
- Kept local `formatLastSeen` with null guard added
- MMSI, Destination use `formatOptional()` for null safety
- Position uses shared `formatCoord`

### `frontend/src/components/EventInfoPanel/EventInfoPanel.jsx`
- Removed local `formatTone` (replaced by shared import)
- Kept local `formatDate` and `toneBadgeClass` (UI-specific)
- event_text, category use `formatOptional()` for null safety
- Position uses shared `formatCoord`
- Source URL shows `'—'` fallback when null (no broken links)

### `frontend/src/components/ConflictInfoPanel/ConflictInfoPanel.jsx`
- Removed local `formatTone` and `formatPosition` (replaced by shared imports)
- Kept local `formatDate` and `toneBadgeClass` (UI-specific)
- Header title uses nested `formatOptional()` for fallback chain
- Category uses `formatOptional()` for null safety
- Position uses shared `formatCoord`
- Source URL shows `'—'` fallback when null

## Verification

- [x] `vite build` passes with no errors
- [x] PlaneInfoPanel: all fields show `'—'` when null
- [x] ShipInfoPanel: all fields show `'—'` when null
- [x] EventInfoPanel: all fields show `'—'` when null
- [x] ConflictInfoPanel: all fields show `'—'` when null
- [x] Altitude shows comma-separated thousands (e.g., `"35,000 ft"`)
- [x] Typography unchanged — uses existing `.info-value` / `.info-value.mono` classes
- [x] No new CSS added
- [x] Em dash `'—'` used consistently as fallback glyph per Gotham design system
