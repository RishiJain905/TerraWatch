# Phase 4.5 — Task 1: Data Model Research

**Agent:** MiniMax
**Related overview:** `PHASE4_5_OVERVIEW.md`

---

## Objective

Inspect the existing data models for planes, ships, events, and conflicts to document all available filterable fields. This task is research only — no code changes.

---

## Instructions

Read the following files and document the exact field names and types available for filtering:

### Planes

Read:
- `backend/app/core/models.py` — Plane model fields
- `frontend/src/hooks/usePlanes.js` — what fields arrive from the API/WebSocket
- `frontend/src/utils/planeIcons.js` — what fields are used for altitude bands

Document:
- Exact field names for: altitude, callsign, speed, lat, lon, heading
- Units (feet vs meters, knots vs km/h)
- Whether fields are nullable/missing on some records

### Ships

Read:
- `backend/app/core/models.py` — Ship model fields
- `frontend/src/hooks/useShips.js` — what fields arrive from the API/WebSocket
- `frontend/src/utils/shipIcons.js` — what fields are used for type

Document:
- Exact field names for: ship_type, speed, lat, lon, heading, mmsi
- All ship type values that appear in the data
- Units for speed

### Events (GDELT)

Read:
- `backend/app/services/gdelt_service.py` — event parsing, category mapping
- `backend/app/core/models.py` — WorldEvent model
- `backend/app/api/routes/events.py` — what fields the API returns

Document:
- Exact field names for: category, tone, lat, lon, date
- GDELT event code to category mapping (full list)
- Date format returned by API

### Conflicts (GDELT violent events)

Read:
- Same files as Events — conflicts is a filtered subset of GDELT events

Document:
- Are there fatality count fields available?
- What fields exist for intensity weighting?

### Globe.jsx Layer Configuration

Read:
- `frontend/src/components/Globe/Globe.jsx` — how each layer is configured

Document:
- What fields does each layer use for position, size, color, weight?
- Are there any hardcoded assumptions about field names?

---

## Output Format

Create a file `phase4_5/PHASE4_5_RESEARCH.md` with a table per entity:

```
## Planes

| Field | Type | Units | Source | Notes |
|-------|------|-------|--------|-------|
| alt | int | feet | API/WS | nullable on ground aircraft |
| ... | | | | |

## Ships

...same pattern...

## Events

...same pattern...

## Conflicts

...same pattern...
```

---

## Acceptance Criteria

- [ ] Research doc created at `docs/phases/phase4_5/PHASE4_5_RESEARCH.md`
- [ ] All filterable fields documented with exact names, types, and units
- [ ] GDELT category mapping fully enumerated
- [ ] Globe.jsx field usage documented per layer
- [ ] Commit message: `Phase 4.5 Task 1: Research data models for filter implementation`
