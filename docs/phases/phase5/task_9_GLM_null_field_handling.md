# Phase 5 — Task 9: Null Field Graceful Handling

## Context

Read `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx`, `ShipInfoPanel.jsx`, `EventInfoPanel.jsx`, and `ConflictInfoPanel.jsx`.

## Goal

Ensure info panels render gracefully even when fields are null, undefined, or missing. Currently may crash or show "null", "undefined", or blank spaces where data should be.

## Fields to Check

Each info panel has different fields. The pattern is consistent:

```javascript
// Bad — shows "null" or "undefined"
<span>{plane.callsign}</span>

// Good — shows "N/A" or "Unknown" or icon
<span>{plane.callsign ?? '—'}</span>
```

## Per-Panel Requirements

### PlaneInfoPanel

Fields: `callsign`, `icao24`, `alt` (feet), `gs` (speed), `heading`, `lat`, `lon`, `last_contact`
- `alt` — format as "35,000 ft" or "—"
- `gs` — format as "450 kt" or "—"
- `heading` — show "N/A" if null (0 heading = north, so need to distinguish unknown vs 0)
- `callsign` — show "Unknown" if empty/null

### ShipInfoPanel

Fields: `name`, `mmsi`, `ship_type`, `lat`, `lon`, `heading`, `sog` (speed), `destination`
- `name` — show "Unknown vessel" if null/empty
- `heading` — same as planes
- `sog` — format as "12.5 kt" or "—"
- `destination` — show "—" if null/empty

### EventInfoPanel

Fields: `event_text`, `category`, `tone`, `date`, `source_url`
- `event_text` — show "No description available" if null
- `tone` — show "—" if null (tone can be 0, so check undefined specifically)
- `source_url` — show "—" if null (don't show broken link)

### ConflictInfoPanel

Fields: same as EventInfoPanel (uses GDELT fields)
- Same handling as EventInfoPanel

## Formatting Utility

Add helper to `formatters.js`:

```javascript
export function formatOptional(value, formatter, fallback = '—') {
  if (value == null || value === '') return fallback
  return formatter ? formatter(value) : value
}

export function formatSpeed(kt) {
  if (kt == null) return '—'
  return `${Number(kt).toFixed(1)} kt`
}

export function formatAltitude(ft) {
  if (ft == null) return '—'
  return `${Number(ft).toLocaleString()} ft`
}
```

## Files to Update

- `frontend/src/utils/formatters.js` — add formatOptional, formatSpeed, formatAltitude helpers
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx` — apply null handling to all fields
- `frontend/src/components/ShipInfoPanel/ShipInfoPanel.jsx` — apply null handling to all fields
- `frontend/src/components/EventInfoPanel/EventInfoPanel.jsx` — apply null handling to all fields
- `frontend/src/components/ConflictInfoPanel/ConflictInfoPanel.jsx` — apply null handling to all fields

## Verification

- [ ] PlaneInfoPanel renders with all fields showing "—" when null
- [ ] ShipInfoPanel renders with all fields showing "—" when null
- [ ] EventInfoPanel renders with all fields showing "—" when null
- [ ] ConflictInfoPanel renders with all fields showing "—" when null
- [ ] No console errors when panel data has null fields
- [ ] Altitude shows comma-separated thousands (e.g., "35,000 ft")
