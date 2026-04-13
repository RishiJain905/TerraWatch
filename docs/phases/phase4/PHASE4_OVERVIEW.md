# Phase 4 — World Events & Conflict Visualization

## Goal

Add two new data layers to TerraWatch:
1. **GDELT** — real-time world events from global news (fires, protests, diplomacy, etc.)
2. **GDELT Conflicts** — conflict heatmap derived from GDELT violent event categories

These complete the "intelligence layer" for V2 — transforming TerraWatch from a pure tracker into a GEOINT platform.

---

## Context Files (Read First)

Before any implementation, read:
- `docs/ARCHITECTURE.md` — current system architecture, data models
- `docs/DATA_SOURCES.md` — GDELT API details, response formats
- `docs/phases/phase4/PHASE4_OVERVIEW.md` — this file

---

## What This Phase Is

- A new **events layer** on the globe showing GDELT world events as colored points
- A new **conflict heatmap layer** powered by GDELT's violent event categories
- Backend services for GDELT data
- New WebSocket message types for event and conflict updates
- Filter controls to toggle events and conflicts on/off
- Click-to-inspect event/conflict details

---

## What This Phase Is NOT

- Zone alerting (Phase 6)
- Performance optimization (Phase 5)
- Historical event playback
- Real-time news streaming (GDELT is 15-min delayed)

---

## Data Source

### GDELT Project — World Events & Conflicts

|| Attribute | Detail ||
|-----------|---------|
| **What** | Global events from news — fires, protests, diplomacy, disease, etc. |
| **Coverage** | Global, every country |
| **Auth** | None — completely free |
| **Refresh** | ~15 minutes (hourly export files) |
| **Format** | CSV/JSON from their hourly export files |
| **Key endpoint** | `http://data.gdeltproject.org/gdeltv2/lastupdate.txt` (gets latest file URL) |

**Key fields:**
- `latitude`, `longitude` — event location
- `event_text` — human-readable description
- `tone` — tone of reporting (-10 very negative to +10 very positive)
- `category` — event category (protest, war, diplomacy, etc.)
- `source_url` — original news source

**Violent categories used for the conflicts heatmap:**
| Category | GDELT Event Code | Description |
|----------|-----------------|-------------|
| assault | 08 | Physical assault |
| fight | 09 | Exchange of physical violence |
| rioting | 18 | Rioting or mob violence |
| unconventional_mass_gvc | 10 | Unconventional mass violence |
| conventional_mass_gvc | 12 | Conventional mass violence |
| force_range | 13 | Use of force, military operations |

**Note:** The conflicts heatmap is powered entirely by GDELT. The conflicts table no longer exists — violent events are filtered from the `events` table at query time.

---

## Backend Implementation

### New Services

```
backend/app/services/
├── gdelt_service.py      NEW — fetch GDELT events, parse, normalize to WorldEvent
```

### Database Schema

The `events` table stores all GDELT world events. The conflicts heatmap queries this table, filtering by violent categories at runtime.

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
```

### New REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/events` | All events |
| `GET` | `/api/events/count` | Event count |
| `GET` | `/api/events/{id}` | Single event details (returns None if not found) |
| `GET` | `/api/conflicts` | All violent events (filtered from events table) |
| `GET` | `/api/conflicts/count` | Violent event count |

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
    "id": "gdelt_456",
    "lat": 34.0,
    "lon": 36.0,
    "date": "2026-04-12",
    "event_text": "Fighting in region",
    "tone": -8.5,
    "category": "fight",
    "source_url": "https://example.com"
  }],
  "timestamp": "2026-04-13T00:00:00Z"
}
```

### New Scheduler

| Service | Refresh Rate | Method |
|---------|-------------|--------|
| GDELT | Every 15 minutes (configurable via GDELT_REFRESH_SECONDS env var) | Download latest export, parse, upsert, broadcast |

### Environment Variables

```
# .env.example
GDELT_REFRESH_SECONDS=900   # Optional: override GDELT polling interval (default: 900s / 15min)
```

---

## Frontend Implementation

### New Components

```
frontend/src/components/
├── EventsLayer/          NEW — ScatterplotLayer for GDELT events
├── EventInfoPanel/       NEW — Slide-in panel for event details
└── ConflictInfoPanel/    NEW — Slide-in panel for conflict details (GDELT fields)
```

### Layer Design

**GDELT Events (ScatterplotLayer):**
- Points colored by `tone` — red (negative), yellow (neutral), green (positive)
- Click to show EventInfoPanel

**GDELT Conflicts (HeatmapLayer):**
- Heat intensity by `|tone| + 1` — more negative tone = more intense heat
- Color range: red → orange → yellow
- Click on cluster to show ConflictInfoPanel

### Filter Controls (Sidebar or Header)

- Toggle: Show/Hide GDELT events
- Toggle: Show/Hide GDELT conflicts

---

## File Structure Changes

```
backend/app/
├── services/
│   ├── adsb_service.py       (existing)
│   ├── ais_service.py        (existing)
│   ├── adsblol_service.py    (existing)
│   ├── aisstream_service.py  (existing)
│   └── gdelt_service.py      NEW
├── tasks/
│   └── schedulers.py         UPDATE — add GDELT scheduler
├── api/routes/
│   ├── events.py             NEW — /api/events, /api/events/count, /api/events/{id}
│   └── conflicts.py           NEW — /api/conflicts, /api/conflicts/count, /api/conflicts/{id}

frontend/src/
├── components/
│   ├── Globe/                 UPDATE — add events and conflicts layers
│   ├── EventInfoPanel/        NEW
│   └── ConflictInfoPanel/      NEW
└── App.jsx                    UPDATE — add event/conflict panel state
```

---

## Tasks Overview

|| # | Task | Description | Dependencies |
|---|------|-------------|-------------|
| 1 | Phase 4 docs + API research | Update docs with GDELT event/conflict models | None |
| 2 | GDELT backend service | gdelt_service.py — fetch, parse, normalize to WorldEvent | Task 1 |
| 3 | Event + Conflict REST endpoints | /api/events, /api/conflicts routes | Task 2 |
| 4 | Scheduler integration | Add GDELT (15min configurable) to schedulers | Task 2 |
| 5 | Events layer on globe | ScatterplotLayer for GDELT points, colored by tone | Task 1 |
| 6 | Conflicts heatmap layer | HeatmapLayer for GDELT violent events, intensity by tone | Task 1 |
| 7 | Event + Conflict info panels | Slide-in panels for event/conflict details | Task 5, 6 |
| 8 | WebSocket wiring | Verify event_batch and conflict_batch messages handled | Task 3, 5, 6 |
| 9 | Integration test | Verify events and conflicts appear on globe | Tasks 4, 5, 6, 8 |

---

## Verification Checklist

- [x] GDELT service fetches and parses correctly
- [x] /api/events returns GDELT events
- [x] /api/conflicts returns only violent GDELT events
- [x] Events appear as colored points on globe (tone-colored ScatterplotLayer)
- [x] Conflicts appear as heatmap overlay (ScatterplotLayer intensity by |tone|)
- [x] EventInfoPanel shows event_text, tone, category, date, source_url
- [x] ConflictInfoPanel shows event_text, tone, category, date, source_url
- [x] WebSocket broadcasts event_batch and conflict_batch
- [x] All existing plane and ship functionality unchanged
- [x] GDELT YYYYMM dates normalized to full ISO dates for SQLite compatibility

---

## Constraints

- **Free APIs only** — GDELT requires no API key
- **Don't remove existing features** — planes and ships remain primary
- **Existing payload contracts unchanged** — new message types are additive
- **No zone alerting** — that's Phase 6
- **No performance changes** — that's Phase 5
