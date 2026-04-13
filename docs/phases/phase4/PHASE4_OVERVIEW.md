# Phase 4 — World Events & Conflict Visualization

## Goal

Add two new data layers to TerraWatch:
1. **GDELT** — real-time world events from global news (fires, protests, diplomacy, etc.)
2. **ACLED** — conflict event heatmap showing intensity of political violence worldwide

These complete the "intelligence layer" for V2 — transforming TerraWatch from a pure tracker into a GEOINT platform.

---

## Context Files (Read First)

Before any implementation, read:
- `docs/ARCHITECTURE.md` — current system architecture, data models
- `docs/DATA_SOURCES.md` — GDELT and ACLED API details, response formats
- `docs/phases/phase4/PHASE4_OVERVIEW.md` — this file

---

## What This Phase Is

- A new **events layer** on the globe showing GDELT world events as colored points
- A new **conflict heatmap layer** showing ACLED conflict intensity as a heat overlay
- Backend services for both data sources
- New WebSocket message types for event and conflict updates
- Filter controls to toggle events and conflicts on/off
- Click-to-inspect event/conflict details

---

## What This Phase Is NOT

- Zone alerting (Phase 6)
- Performance optimization (Phase 5)
- Historical event playback
- Real-time news streaming (GDELT is 15-min delayed, ACLED is daily)

---

## Data Sources

### GDELT Project — World Events

| Attribute | Detail |
|-----------|--------|
| **What** | Global events from news — fires, protests, diplomacy, disease, etc. |
| **Coverage** | Global, every country |
| **Auth** | None — completely free |
| **Refresh** | ~15 minutes (hourly export files) |
| **Format** | CSV/JSON from their gelevt API |
| **Key endpoint** | `http://data.gdeltproject.org/gdeltv2/lastupdate.txt` (gets latest file URL) |

**Key fields:**
- `latitude`, `longitude` — event location
- `event_text` — human-readable description
- `tone` — tone of reporting (-10 very negative to +10 very positive)
- `category` — event category (protest, war, diplomacy, etc.)
- `source_url` — original news source

### ACLED — Conflict Data

| Attribute | Detail |
|-----------|--------|
| **What** | Armed conflict and political violence events |
| **Coverage** | Global, 1997–present |
| **Auth** | Free registration required at acleddna.com |
| **Refresh** | Daily CSV download |
| **Format** | CSV download |
| **Key page** | https://www.acleddna.com/acleddatanew/access-all-data/ |

**Key fields:**
- `latitude`, `longitude` — event location
- `event_type` — battles, explosions, riots, protests, etc.
- `fatalities` — death count
- `date` — event date
- `country`, `region`

**ACLED registration:** User must register at acleddna.com for a free API key or direct CSV download access. Document the registration process in `.env.example`.

---

## Backend Implementation

### New Services

```
backend/app/services/
├── gdelt_service.py      NEW — fetch GDELT events, parse, normalize
└── acled_service.py      NEW — fetch ACLED conflicts, parse, normalize
```

### New Database Tables

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    date TEXT NOT NULL,
    event_text TEXT,
    tone REAL DEFAULT 0,
    category TEXT,
    source_url TEXT,
    timestamp TEXT
);

CREATE TABLE conflicts (
    id TEXT PRIMARY KEY,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    date TEXT NOT NULL,
    event_type TEXT,
    fatalities INTEGER DEFAULT 0,
    country TEXT,
    region TEXT,
    timestamp TEXT
);
```

### New REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/events` | All active events (configurable time window) |
| `GET` | `/api/events/count` | Event count |
| `GET` | `/api/events/{id}` | Single event details |
| `GET` | `/api/conflicts` | All active conflicts |
| `GET` | `/api/conflicts/count` | Conflict count |

### New WebSocket Messages

```json
{
  "type": "event_batch",
  "action": "upsert",
  "data": [{
    "id": "gdelt_123",
    "lat": 51.5,
    "lon": -0.1,
    "date": "2026-04-13",
    "event_text": "Protest in London",
    "tone": -2.5,
    "category": "protest",
    "source_url": "https://example.com"
  }],
  "timestamp": "2026-04-13T12:00:00Z"
}
```

```json
{
  "type": "conflict_batch",
  "action": "upsert",
  "data": [{
    "id": "acled_456",
    "lat": 34.0,
    "lon": 36.0,
    "date": "2026-04-12",
    "event_type": "battles",
    "fatalities": 15,
    "country": "Syria",
    "region": "Middle East"
  }],
  "timestamp": "2026-04-13T00:00:00Z"
}
```

### New Schedulers

| Service | Refresh Rate | Method |
|---------|-------------|--------|
| GDELT | Every 15 minutes | Download latest export, diff against DB |
| ACLED | Once per day | Download CSV, replace/upsert |

### Environment Variables

```
# .env.example additions
ACLED_API_KEY=        # Free registration at acleddna.com
```

---

## Frontend Implementation

### New Components

```
frontend/src/components/
├── EventsLayer/          NEW — ScatterplotLayer for GDELT events
├── ConflictsLayer/       NEW — HeatmapLayer for ACLED conflict intensity
├── EventInfoPanel/       NEW — Slide-in panel for event details
└── ConflictInfoPanel/    NEW — Slide-in panel for conflict details
```

```
frontend/src/hooks/
├── useEvents.js          NEW — event state + WS event_batch handling
└── useConflicts.js      NEW — conflict state + WS conflict_batch handling
```

### Layer Design

**GDELT Events (ScatterplotLayer):**
- Points colored by `tone` — red (negative), yellow (neutral), green (positive)
- Size by significance or left as fixed
- Click to show EventInfoPanel

**ACLED Conflicts (HeatmapLayer):**
- Heat intensity by `fatalities` count
- Red/orange heat colors for high-fatality areas
- Click on cluster or point to show ConflictInfoPanel

### Filter Controls (Sidebar or Header)

- Toggle: Show/Hide GDELT events
- Toggle: Show/Hide ACLED conflicts
- Time window selector for events (last 1h, 6h, 24h, 7d)
- Conflict type filter (battles, protests, explosions, all)

---

## File Structure Changes

```
backend/app/
├── services/
│   ├── adsb_service.py       (existing)
│   ├── ais_service.py        (existing)
│   ├── gdelt_service.py      NEW
│   └── acled_service.py      NEW
├── tasks/
│   └── schedulers.py         UPDATE — add GDELT and ACLED schedulers
├── api/routes/
│   ├── events.py             NEW — /api/events, /api/events/count, /api/events/{id}
│   └── conflicts.py          NEW — /api/conflicts, /api/conflicts/count
└── core/
    └── models.py             UPDATE — add Event, Conflict Pydantic models

backend/tests/
├── test_gdelt_service.py     NEW
└── test_acled_service.py     NEW

frontend/src/
├── components/
│   ├── Globe/                UPDATE — add EventsLayer and ConflictsLayer
│   ├── EventInfoPanel/       NEW
│   └── ConflictInfoPanel/     NEW
├── hooks/
│   ├── useEvents.js          NEW
│   └── useConflicts.js        NEW
└── App.jsx                   UPDATE — add event/conflict state

.env.example                   UPDATE — add ACLED_API_KEY

docs/
└── phases/phase4/
    └── PHASE4_OVERVIEW.md    (this file)
```

---

## Tasks Overview

| # | Agent | Task | Description | Dependencies |
|---|-------|------|-------------|-------------|
| 1 | GLM 5.1 | Phase 4 docs + API research | Update ARCHITECTURE.md with event/conflict models, verify GDELT/ACLED API details | None |
| 2 | GLM 5.1 | GDELT backend service | gdelt_service.py — fetch, parse, normalize to Event model | Task 1 |
| 3 | GLM 5.1 | ACLED backend service | acled_service.py — CSV fetch, parse, normalize to Conflict model | Task 1, ACLED_API_KEY |
| 4 | GLM 5.1 | Event + Conflict REST endpoints | /api/events, /api/conflicts routes | Task 2, 3 |
| 5 | GLM 5.1 | Scheduler integration | Add GDELT (15min) and ACLED (daily) to schedulers | Task 2, 3 |
| 6 | GLM 5.1 | Events layer on globe | ScatterplotLayer for GDELT points, colored by tone | Task 1 |
| 7 | GLM 5.1 | Conflicts heatmap layer | HeatmapLayer for ACLED, intensity by fatalities | Task 1 |
| 8 | GLM 5.1 | Event + Conflict info panels | Slide-in panels for event/conflict details | Task 6, 7 |
| 9 | GLM 5.1 | Filter controls | Toggle events/conflicts, time window, conflict type | Task 6, 7, 8 |
| 10 | GLM 5.1 | WebSocket wiring | Verify event_batch and conflict_batch messages handled | Task 4, 6, 7 |
| 11 | M2.7 | Integration test | Verify events and conflicts appear on globe | Tasks 4, 6, 7, 10 |

---

## Verification Checklist

- [ ] GDELT service fetches and parses correctly
- [ ] ACLED service fetches and parses correctly (with API key)
- [ ] /api/events returns GDELT events
- [ ] /api/conflicts returns ACLED conflicts
- [ ] Events appear as colored points on globe
- [ ] Conflicts appear as heatmap overlay
- [ ] EventInfoPanel shows event_text, tone, category, source_url
- [ ] ConflictInfoPanel shows event_type, fatalities, country, date
- [ ] Filter controls toggle layers correctly
- [ ] WebSocket broadcasts event_batch and conflict_batch
- [ ] Backend runs without ACLED_API_KEY (GDELT-only fallback)
- [ ] All existing plane and ship functionality unchanged

---

## Constraints

- **Free APIs only** — GDELT is free, ACLED requires free registration only
- **Don't remove existing features** — planes and ships remain primary
- **Existing payload contracts unchanged** — new message types are additive
- **No zone alerting** — that's Phase 6
- **No performance changes** — that's Phase 5
