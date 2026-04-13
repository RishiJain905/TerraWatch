# Phase 4.5 — Task 5: Update Architecture Docs

**Agent:** MiniMax
**Related overview:** `PHASE4_5_OVERVIEW.md`
**Prerequisites:** Tasks 2, 3, and 4 must be complete first

---

## Objective

Update the project documentation to reflect the new filter architecture introduced in Phase 4.5. Update `docs/ARCHITECTURE.md` and `docs/DATA_SOURCES.md`.

---

## Files to Update

### 1. `docs/ARCHITECTURE.md`

Add a new section called **"Filtering Architecture"** after the existing layer/data architecture sections:

```markdown
## Filtering Architecture

Filters are **frontend-only** — all data comes through existing endpoints and WebSocket channels, with filtering applied in the React hooks before data reaches the Globe.

### Filter Pattern

Each data hook (`usePlanes`, `useShips`, `useEvents`, `useConflicts`) maintains:
- **Raw data** — all records received from the backend, never mutated
- **Filter state** — user-configured filter values (altitude range, categories, etc.)
- **Filtered data** — derived via `useMemo`, raw data with filters applied
- **Update function** — `updateFilter(key, value)` to update a single filter

```
usePlanes() ──► filterPlanes() ──► Globe (IconLayer)
useShips() ───► filterShips() ───► Globe (IconLayer)
useEvents() ──► filterEvents() ───► Globe (ScatterplotLayer)
useConflicts() ─► filterConflicts() ──► Globe (HeatmapLayer)
```

### Filtered Data Exposure

Globe.jsx uses filtered data for rendering. Raw data counts are shown in the globe info bar so users can see how many items are hidden by filters.

### Filter UI

Filter controls live in collapsible panels in the Sidebar, one per layer. Filters update in real-time — no "Apply" button. State persists across WebSocket reconnects.
```

Also update any diagram or section that references data flow to note that filtering happens at the hook level.

---

### 2. `docs/DATA_SOURCES.md`

Update the filter section to document what filters are available per data source:

After the existing data source entries, add a **"Filterable Fields"** section:

```markdown
## Filterable Fields

### Planes (ADSB / OpenSky)
| Field | Type | Filter Control |
|-------|------|----------------|
| alt | int | Altitude range slider (0–50,000 ft) |
| callsign | string | Text search (partial, case-insensitive) |
| gs / speed | int | Min speed slider (0–600 kt) |

### Ships (Digitraffic / aisstream.io)
| Field | Type | Filter Control |
|-------|------|----------------|
| ship_type | string | Type checkboxes (cargo, tanker, passenger, fishing, other) |
| sog / speed | int | Min speed slider (0–30 kt) |

### Events (GDELT)
| Field | Type | Filter Control |
|-------|------|----------------|
| category | string | Category checkboxes (8 categories) |
| tone | float | Tone range dual slider (-10 to +10) |
| date | string | Date range dropdown (24h, 48h, 7d, all) |

### Conflicts (GDELT violent subset)
| Field | Type | Filter Control |
|-------|------|----------------|
| intensity | computed | Min intensity slider (0–11) |
| date | string | Date range dropdown (24h, 48h, 7d, all) |

Note: Conflicts is a filtered subset of GDELT events showing only violent/aggressive events (assault, fight, rioting, mass_gvc, force categories).
```

---

## Acceptance Criteria

- [ ] `docs/ARCHITECTURE.md` has new "Filtering Architecture" section
- [ ] Data flow diagram/narrative updated to show hook-level filtering
- [ ] `docs/DATA_SOURCES.md` has new "Filterable Fields" section
- [ ] Filter controls documented per data source
- [ ] Both files render correctly as markdown
- [ ] Commit message: `Phase 4.5 Task 5: Update ARCHITECTURE.md and DATA_SOURCES.md with filter documentation`
