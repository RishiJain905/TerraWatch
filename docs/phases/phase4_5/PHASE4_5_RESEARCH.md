# Phase 4.5 — Data Model Research

**Agent:** MiniMax
**Date:** 2026-04-14
**Status:** Complete

---

## Overview

This document catalogs all filterable fields available in TerraWatch's data models for planes, ships, events, and conflicts. It is the authoritative reference for implementing Phase 4.5 filter controls.

Source files inspected:
- `backend/app/core/models.py` — Pydantic models
- `backend/app/services/gdelt_service.py` — GDELT event parsing and category mapping
- `backend/app/api/routes/events.py` — Events API route
- `backend/app/api/routes/conflicts.py` — Conflicts API route
- `backend/app/api/websocket.py` — WebSocket broadcast contracts
- `frontend/src/hooks/usePlanes.js` — Frontend plane state hook
- `frontend/src/hooks/useShips.js` — Frontend ship state hook
- `frontend/src/utils/planeIcons.js` — Plane icon/color mapping by altitude
- `frontend/src/utils/shipIcons.js` — Ship icon/color mapping by type
- `frontend/src/components/Globe/Globe.jsx` — deck.gl layer configuration

---

## Planes

### Backend Model (`backend/app/core/models.py → Plane`)

| Field | Type | Units | Default | Source | Notes |
|-------|------|-------|---------|--------|-------|
| `id` | str | — | — | OpenSky `states[0]` | Hex ICAO24 address, e.g. `"a1b2c3"` |
| `lat` | float | decimal degrees | — | OpenSky `states[6]` | Latitude |
| `lon` | float | decimal degrees | — | OpenSky `states[5]` | Longitude |
| `alt` | int | **feet** | `0` | OpenSky `states[7]` (meters) × 3.28084 | Nullable on ground aircraft |
| `heading` | float | degrees | `0` | OpenSky `states[10]` | True track, 0=North, 90=East |
| `callsign` | str | — | `""` | OpenSky `states[1]` | 8-char flight code, right-padded spaces |
| `squawk` | str | — | `""` | OpenSky `states[14]` | 4-digit transponder code |
| `speed` | float | **knots** | `0` | OpenSky `states[9]` (m/s) × 1.94384 | Ground speed |
| `timestamp` | str | ISO-8601 | `None` | OpenSky `states[4]` (unix epoch) | Optional |

### Frontend Contract

All fields above arrive via:
- REST: `GET /api/planes` → `Plane[]`
- WebSocket: `{ type: "plane_batch", data: Plane[] }` → `usePlanes.addPlanes()`
- WebSocket: `{ type: "plane", data: Plane }` → `usePlanes.addPlane()`

### Altitude Bands (planeIcons.js)

The globe uses three color-coded altitude bands:

| Band | Range | Color | Icon Constant |
|------|-------|-------|---------------|
| Low | < 10,000 ft | `0, 255, 100` (green) | `LOW_ICON` |
| Medium | 10,000 – 30,000 ft | `255, 255, 0` (yellow) | `MED_ICON` |
| High | > 30,000 ft | `255, 100, 100` (red) | `HIGH_ICON` |

Bands are used by `Globe.jsx` via `getPlaneIcon(d.alt)`. Band logic is **not** stored as a field — computed at render time.

### Globe.jsx Layer Field Usage (Planes)

| deck.gl Property | Field | Notes |
|-----------------|-------|-------|
| `getIcon: d => getPlaneIcon(d.alt)` | `alt` | Drives color band |
| `getPosition: d => [d.lon, d.lat]` | `lon`, `lat` | Required |
| `getSize: 48` | — | Fixed size |
| `getAngle: d => -(d.heading \|\| 0)` | `heading` | Rotation, defaults 0 |

### Filter Implementation Notes

- `alt` is **nullable in OpenSky** (`baro_altitude` can be `null` for on-ground aircraft). Backend defaults to `0` in Pydantic model. Frontend should treat `alt ?? 0`.
- `callsign` in OpenSky is right-padded with spaces (e.g., `"BAW123   "`). Partial match should `.trim()` first.
- `speed` is in knots at the frontend — no further conversion needed.
- `heading` can be `null` in OpenSky data. Globe.jsx already guards with `d.heading || 0`.

---

## Ships

### Backend Model (`backend/app/core/models.py → Ship`)

| Field | Type | Units | Default | Source | Notes |
|-------|------|-------|---------|--------|-------|
| `id` | str | — | — | Digitraffic `mmsi` or AISStream `UserID` | MMSI number as string |
| `lat` | float | decimal degrees | — | Digitraffic GeoJSON `geometry.coordinates[1]` | Latitude |
| `lon` | float | decimal degrees | — | Digitraffic GeoJSON `geometry.coordinates[0]` | Longitude |
| `heading` | float | degrees | `0` | Digitraffic `cog` / AISStream `TrueHeading` | COG, 0=North |
| `speed` | float | **knots** | `0` | Digitraffic `sog` / AISStream `Sog` | Speed over ground |
| `name` | str | — | `""` | Digitraffic `name` | Vessel name |
| `destination` | str | — | `""` | Digitraffic `destination` | Destination port |
| `ship_type` | str | — | `""` | AIS type code → mapped string | See mapping below |
| `timestamp` | str | ISO-8601 | `None` | Various | Optional |

### Ship Type Mapping (shipIcons.js + ais_service.py)

| AIS Code | Frontend `ship_type` | Color | Icon |
|----------|---------------------|-------|------|
| 70 | `cargo` | `#4A90D9` (blue) | Container/bulk ship SVG |
| 80 | `tanker` | `#F5A623` (orange) | Wide vessel SVG |
| 60 | `passenger` | `#7ED321` (green) | Ferry/cruise SVG |
| 52 | `tug` | `#999999` (gray) | Falls through to OTHER |
| 31 | `tug` | `#999999` (gray) | Falls through to OTHER |
| 36 | `sailing` | `#999999` (gray) | Falls through to OTHER |
| 37 | `other` | `#999999` (gray) | — |
| 30 | `fishing` | `#9013FE` (purple) | Fishing boat SVG |
| 0 | `other` | `#999999` (gray) | — |
| (any other) | `other` | `#999999` (gray) | Generic boat SVG |

### Frontend Contract

All fields above arrive via:
- REST: `GET /api/ships` → `Ship[]`
- WebSocket: `{ type: "ship_batch", data: Ship[] }` → `useShips.addShips()`
- WebSocket: `{ type: "ship", data: Ship }` → `useShips.addShip()`

### Globe.jsx Layer Field Usage (Ships)

| deck.gl Property | Field | Notes |
|-----------------|-------|-------|
| `getIcon: d => getShipIcon(d.ship_type)` | `ship_type` | Drives icon shape/color |
| `getPosition: d => [d.lon, d.lat]` | `lon`, `lat` | Required |
| `getSize: 48` | — | Fixed size |
| `getAngle: d => -(d.heading \|\| 0)` | `heading` | Rotation, defaults 0 |

### Filter Implementation Notes

- `ship_type` is always a string (`""` if unmapped). Filtering by type should handle empty string as `other`.
- `speed` (SOG) is already in **knots** from Digitraffic — no conversion needed.
- `heading` can be null. Globe.jsx already guards with `d.heading || 0`.
- `id` is the MMSI as a string.
- No separate `mmsi` field — `id` IS the MMSI.

---

## Events (GDELT)

### Backend Model (`backend/app/core/models.py → WorldEvent`)

| Field | Type | Units | Default | Source | Notes |
|-------|------|-------|---------|--------|-------|
| `id` | str | — | — | GDELT `GLOBALEVENTID` | Prefixed `"gdelt_"` |
| `date` | str | ISO date | — | GDELT `SQLDATE` | Format: `"YYYY-MM-DD"` |
| `lat` | float | decimal degrees | — | GDELT `ActionGeo_Lat` | Latitude |
| `lon` | float | decimal degrees | — | GDELT `ActionGeo_Long` | Longitude |
| `event_text` | str | — | — | GDELT `EventCode` → `EVENT_CODE_DESCRIPTION` | Human-readable description |
| `tone` | float | score | `0` | GDELT `AvgTone` | Range approximately −10 to +10 |
| `category` | str | — | `""` | GDELT `EventCode` → `EVENT_CODE_CATEGORY_MAP` | See mapping below |
| `source_url` | str | — | `""` | GDELT CSV URL | Archive URL |

### GDELT Event Code → Category Mapping

Full enumeration from `backend/app/services/gdelt_service.py`:

| Event Code | Category | Description | Tone Polarity |
|------------|----------|-------------|---------------|
| `01` | `diplomacy` | Made a statement | Neutral |
| `02` | `material_help` | Appealed for material assistance | Neutral |
| `03` | `train` | Expressed intent to cooperate | Positive |
| `04` | `yield` | Yielded | Negative |
| `05` | `demonstrate` | Demonstrated or rallied | Neutral |
| `08` | `assault` | Assaulted | Negative |
| `09` | `fight` | Fought | Negative |
| `10` | `unconventional_mass_gvc` | Used unconventional mass violence | Very Negative |
| `12` | `conventional_mass_gvc` | Used conventional mass violence | Very Negative |
| `13` | `force_range` | Used force | Negative |
| `14` | `protest` | Protested | Neutral |
| `17` | `government_debate` | Engaged in government debate | Neutral |
| `18` | `rioting` | Rioted | Negative |
| `20` | `disaster` | Responded to disaster | Negative |
| `21` | `health` | Addressed health issue | Neutral |
| `22` | `weather` | Responded to weather event | Negative |

> **Note:** The Phase 4.5 overview mentions `mass_gvc` but the actual implementation uses `unconventional_mass_gvc` and `conventional_mass_gvc` as two separate categories (codes 10 and 12). The `EVENT_CODE_CATEGORY_MAP` uses 2-digit root code keys. Events with codes 06, 07, 11, 15, 16, 19 have no mapping and get category `""`.

### Date Format

GDELT dates are normalized to `YYYY-MM-DD` format in `gdelt_service.py`:
- `YYYYMMDD` (SQLDATE) → `YYYY-MM-DD`
- `YYYYMMDDHHMMSS` (DATEADDED) → `YYYY-MM-DD`
- `YYYYMM` (edge case) → `YYYY-MM-01` (normalized to first of month)

### Frontend Contract

- REST: `GET /api/events` → `WorldEvent[]`
- WebSocket: `{ type: "event_batch", data: WorldEvent[] }` → `Globe.jsx` state
- No dedicated `useEvents` hook — events/conflicts managed in `Globe.jsx` via `useState`

### Globe.jsx Layer Field Usage (Events)

| deck.gl Property | Field | Notes |
|-----------------|-------|-------|
| `getPosition: d => [d.lon, d.lat]` | `lon`, `lat` | Required |
| `getFillColor: d => ...` | `tone` | Red for negative, yellow for neutral, green for positive |
| `getRadius: 150000` | — | Fixed radius, in meters |
| `radiusUnits: 'meters'` | — | Fixed |

Tone-to-color mapping in Globe.jsx:
```
t = clamp(tone, -10, 10)
r = clamp(128 - t * 25.5, 0, 255)
g = clamp(128 + t * 25.5, 0, 255)
→ tone=-10: [255, 0, 0, 200]   (pure red)
→ tone=0:   [128, 128, 0, 200] (yellow-green)
→ tone=+10: [0, 255, 0, 200]   (pure green)
```

### Filter Implementation Notes

- `date` is a string in `YYYY-MM-DD` format — can be parsed for date-range filtering.
- `category` is a string — can be used for exact-match filtering against the category list.
- `tone` is a float approximately in range −10 to +10 — filterable by range.
- Events with empty `category` (codes with no mapping) should be handled — they will not match any known category filter when categories are toggled.

---

## Conflicts (GDELT Violent Events)

Conflicts are a **filtered subset** of WorldEvents — specifically those with violent/aggressive categories. The filtering is done server-side in `conflicts.py`.

### Source

- Backend: `backend/app/api/routes/conflicts.py` — filters by `category IN ("assault", "fight", "unconventional_mass_gvc", "conventional_mass_gvc", "force_range", "rioting")`
- No separate model — conflicts use the `WorldEvent` model.

### Conflicts Fields (same as WorldEvent)

| Field | Type | Units | Notes |
|-------|------|-------|-------|
| `id` | str | — | Prefixed `"gdelt_"` |
| `date` | str | `YYYY-MM-DD` | From GDELT SQLDATE |
| `lat` | float | decimal degrees | ActionGeo_Lat |
| `lon` | float | decimal degrees | ActionGeo_Long |
| `event_text` | str | — | From EVENT_CODE_DESCRIPTION |
| `tone` | float | score | From GDELT AvgTone |
| `category` | str | — | One of: `assault`, `fight`, `unconventional_mass_gvc`, `conventional_mass_gvc`, `force_range`, `rioting` |
| `source_url` | str | — | GDELT CSV URL |

### Fatalities Field — NOT Available

**Important:** GDELT events do NOT carry explicit fatality counts in the standard event export files. The conflict heatmap intensity is weighted by `|tone| + 1`, not fatalities.

The Phase 4.5 overview mentions a `fatalities` field for conflicts — this does not exist in the actual data. The heatmap weight formula is:
```
getWeight: d => Math.abs(d.tone || 0) + 1
```
This means:
- More negative tone = higher weight
- Neutral tone (0) = weight of 1 (minimum visible)
- A conflict with tone −10 has weight 11; tone −5 has weight 6

### Frontend Contract

- REST: `GET /api/conflicts` → `WorldEvent[]` (filtered subset)
- WebSocket: `{ type: "conflict_batch", data: WorldEvent[] }` → `Globe.jsx` state
- No dedicated `useConflicts` hook — managed in `Globe.jsx` via `useState`

### Globe.jsx Layer Field Usage (Conflicts)

| deck.gl Property | Field | Notes |
|-----------------|-------|-------|
| `getPosition: d => [d.lon, d.lat]` | `lon`, `lat` | Required |
| `getWeight: d => Math.abs(d.tone \|\| 0) + 1` | `tone` | Intensity weight |
| `intensity: 1` | — | Fixed |
| `threshold: 0.05` | — | Minimum density threshold |
| `colorRange` | — | `[[255,0,0], [255,80,0], [255,160,0], [255,255,0]]` — red to yellow |

### Filter Implementation Notes

- No `fatalities` field exists — intensity is purely tone-driven.
- `date` is in `YYYY-MM-DD` format — filterable for date range.
- `category` is one of 6 violent categories — could be used for sub-filtering but the backend already pre-filters.
- `tone` range: approximately −10 to +10. Since conflicts are violent events (negative tone), the practical range for filtering is likely −10 to 0.

---

## Summary of Filterable Fields

### Planes

| Field | Filter Type | Units | Notes |
|-------|------------|-------|-------|
| `alt` | Range slider | feet | Altitude bands: <10k, 10-30k, >30k ft |
| `callsign` | Text search | — | Partial match, case-insensitive, trim spaces |
| `speed` | Range slider | knots | Ground speed |
| `lat`/`lon` | — | decimal deg | Not filterable in Phase 4.5 (Phase 6) |

### Ships

| Field | Filter Type | Units | Notes |
|-------|------------|-------|-------|
| `ship_type` | Checkbox toggles | — | cargo, tanker, passenger, fishing, other |
| `speed` | Range slider | knots | SOG |

### Events

| Field | Filter Type | Units | Notes |
|-------|------------|-------|-------|
| `category` | Checkbox toggles | — | diplomacy, material_help, train, yield, demonstrate, assault, fight, unconventional_mass_gvc, conventional_mass_gvc, force_range, protest, government_debate, rioting, disaster, health, weather |
| `tone` | Range slider | score | −10 to +10 approximately |
| `date` | Dropdown | YYYY-MM-DD | 24h, 48h, 7 days, all |

### Conflicts

| Field | Filter Type | Units | Notes |
|-------|------------|-------|-------|
| `tone` (as intensity) | Range slider | score | Min intensity = \|tone\|+1 weight |
| `date` | Dropdown | YYYY-MM-DD | 24h, 48h, 7 days, all |

---

## Key Discrepancies with Phase 4.5 Overview

1. **`fatalities` field does not exist** — conflicts use `tone` for intensity weighting. The overview spec mentions `fatalities` but the actual GDELT data does not provide it.

2. **`mass_gvc` is two categories** — `unconventional_mass_gvc` (code 10) and `conventional_mass_gvc` (code 12) are separate, not one `mass_gvc`.

3. **No `useEvents` or `useConflicts` hooks** — events and conflicts are managed directly in `Globe.jsx` with `useState`. The filter implementation will need to either extend `Globe.jsx` state or create new hooks.

4. **`speed` field name** — The overview says `gs` (ground speed) for planes but the actual Pydantic model uses `speed`. Frontend uses `speed` as well.

5. **`EVENT_CODE_CATEGORY_MAP` has 2-digit keys** — codes like `"08"` are stored with the leading zero. When mapping, `root_code[:2]` extracts the 2-digit root from the full 3-digit code.
