# Phase 4.5 — Filtering & Layer Controls

## Goal

Add granular filter controls to each data layer so users can reduce visual clutter. With 10k+ planes, thousands of ships, and thousands of events/conflicts on screen, users need the ability to filter by meaningful attributes — altitude, type, speed, category, tone, and date range.

---

## Motivation

Currently every layer shows all data all the time. This is overwhelming:
- **Planes**: 10k+ aircraft at all altitudes — low-flying clutter the view near airports
- **Ships**: Thousands of vessels — cargo, tankers, fishing boats all mixed together
- **Events**: GDELT returns thousands of events — diplomacy, protests, statements all as dots
- **Conflicts**: Heatmap shows all violent events equally — no way to focus on severe incidents

Giving users filter controls transforms the experience from "noise" to "signal."

---

## Scope

### What is in scope

1. **Altitude range filter for planes** — slider to show only aircraft within a min/max altitude band
2. **Callsign search for planes** — text input to find specific flights by callsign
3. **Ground speed threshold for planes** — filter out slow/parked aircraft
4. **Ship type toggles for ships** — show only cargo, only tankers, only passenger, etc.
5. **Speed threshold for ships** — filter stationary ships at port
6. **Category filter for events** — show only specific GDELT event categories
7. **Tone slider for events** — show only highly negative (dark news) or positive events
8. **Date range filter for events** — last 24h, 48h, 7 days, or all time
9. **Intensity threshold for conflicts** — minimum tone/casualties to display on heatmap
10. **Filter UI in Sidebar** — collapsible panels per layer with all controls

### What is out of scope

- Changing data sources or backend contracts
- Historical playback or time-series controls
- Zone-based geographic filters (Phase 6)
- Performance optimization (Phase 5)
- Adding new WebSocket message types

---

## Filter Specifications

### Planes

| Filter | Type | Default | Description |
|--------|------|---------|-------------|
| `altitudeMin` | range slider | 0 ft | Minimum altitude in feet |
| `altitudeMax` | range slider | 50,000 ft | Maximum altitude in feet |
| `callsign` | text search | "" | Filter by callsign (partial match, case-insensitive) |
| `speedMin` | slider | 0 kt | Minimum ground speed in knots |

**Altitude bands (reference):**
- Low: < 10,000 ft
- Medium: 10,000 – 30,000 ft
- High: > 30,000 ft

**Data fields available:** `alt` (feet), `callsign`, `gs` or `speed` (knots), `lat`, `lon`, `heading`

### Ships

| Filter | Type | Default | Description |
|--------|------|---------|-------------|
| `types` | checkbox toggles | all enabled | Ship type: cargo, tanker, passenger, fishing, other |
| `speedMin` | slider | 0 kt | Minimum speed in knots |

**Ship types:** `cargo`, `tanker`, `passenger`, `fishing`, `other`

**Data fields available:** `ship_type`, `sog` (speed over ground, knots), `lat`, `lon`, `heading`, `name`, `mmsi`

### Events (GDELT)

| Filter | Type | Default | Description |
|--------|------|---------|-------------|
| `categories` | checkbox toggles | all enabled | GDELT category: diplomacy, protest, war, etc. |
| `toneMin` | slider | -10 | Minimum tone value (-10 to +10) |
| `toneMax` | slider | +10 | Maximum tone value (-10 to +10) |
| `dateRange` | dropdown | all | 24h, 48h, 7 days, all |

**GDELT event categories (from `EVENT_CODE_CATEGORY_MAP`):**
- `diplomacy` — code 01-06
- `statement` — code 07
- `assault` — code 08
- `fight` — code 09
- `mass_gvc` — code 10, 12
- `force` — code 13
- `rioting` — code 18
- `protest` — code 14-16

**Data fields available:** `category`, `tone`, `lat`, `lon`, `date`, `event_text`

### Conflicts (GDELT violent events)

| Filter | Type | Default | Description |
|--------|------|---------|-------------|
| `intensityMin` | slider | 0 | Minimum intensity (tone magnitude + 1) |
| `dateRange` | dropdown | all | 24h, 48h, 7 days, all |

**Data fields available:** `tone`, `lat`, `lon`, `date`, `fatalities`

---

## Architecture

### Filter State Location

Filters are **frontend-only** — no backend changes needed. All data comes through existing endpoints/WebSocket channels; filtering happens in the hooks before data reaches the Globe.

```
usePlanes() ──────► filterPlanes() ──► Globe (IconLayer)
useShips() ───────► filterShips() ────► Globe (IconLayer)
useEvents() ──────► filterEvents() ───► Globe (ScatterplotLayer)
useConflicts() ───► filterConflicts() ─► Globe (HeatmapLayer)
```

### Filter State Management

Each hook manages its own filter state. Filter state lives in the hook, not in a global store.

```javascript
// Pattern (in each hook)
const [filters, setFilters] = useState({
  altitudeMin: 0,
  altitudeMax: 50000,
  callsign: '',
  speedMin: 0,
  // ... etc
})

const filteredData = useMemo(() => {
  return rawData.filter(item => applyFilters(item, filters))
}, [rawData, filters])
```

### Filter Controls Location

Sidebar gets collapsible filter panels, one per layer. Each panel contains the relevant controls for that layer.

---

## Task Breakdown

| # | Agent | Task |
|---|-------|------|
| 1 | MiniMax | Research existing data models — document available filter fields per entity |
| 2 | GLM | Add filter state and filtered data to `usePlanes`, `useShips`, `useEvents`, `useConflicts` hooks |
| 3 | GLM | Add filter UI panels to Sidebar — one collapsible panel per layer |
| 4 | GLM | Wire filter state from hooks into Globe.jsx layers |
| 5 | MiniMax | Update `docs/ARCHITECTURE.md` and `docs/DATA_SOURCES.md` with filter architecture |

---

## File Structure

```
frontend/src/
├── hooks/
│   ├── usePlanes.js          UPDATE — add filter state + filteredPlanes
│   ├── useShips.js           UPDATE — add filter state + filteredShips
│   ├── useEvents.js          UPDATE — add filter state + filteredEvents
│   └── useConflicts.js       UPDATE — add filter state + filteredConflicts
├── components/
│   ├── Sidebar/
│   │   ├── Sidebar.jsx       UPDATE — add filter panels
│   │   └── Sidebar.css       UPDATE — filter panel styles
│   └── Globe/
│       └── Globe.jsx         UPDATE — use filtered data from hooks
```

---

## Verification Checklist

- [ ] Planes can be filtered by altitude range (slider)
- [ ] Planes can be searched by callsign (text input)
- [ ] Planes can be filtered by minimum speed
- [ ] Ships can be toggled by type (checkboxes)
- [ ] Ships can be filtered by minimum speed
- [ ] Events can be filtered by category (checkboxes)
- [ ] Events can be filtered by tone range (dual slider)
- [ ] Events can be filtered by date range (dropdown)
- [ ] Conflicts show intensity threshold control
- [ ] All filters are applied in real-time (no apply button)
- [ ] Layer toggle still works independently of filters
- [ ] Sidebar remains usable on mobile
- [ ] No regression in existing layer rendering
- [ ] All filters persist across WebSocket reconnects
- [ ] Docs updated (ARCHITECTURE.md, DATA_SOURCES.md)
