# Phase 6 — Zone Alerting & Event Correlation

## Goal

Turn TerraWatch from a passive situational display into an active decision-support system by introducing **user-defined zones**, **entry/exit alerts**, and **event/conflict correlation inside zones**.

This phase builds on existing live streams (planes, ships, events, conflicts) and adds alerting logic without breaking current Phase 1–5 contracts.

---

## Context Files (Read First)

Before implementation, read:
- `docs/ARCHITECTURE.md`
- `docs/DATA_SOURCES.md`
- `docs/API.md`
- `backend/app/main.py`
- `backend/app/core/database.py`
- `backend/app/core/models.py`
- `backend/app/api/websocket.py`
- `backend/app/tasks/schedulers.py`
- `frontend/src/App.jsx`
- `frontend/src/components/Globe/Globe.jsx`
- `frontend/src/components/Sidebar/Sidebar.jsx`
- `frontend/src/components/Sidebar/Sidebar.css`
- `frontend/src/utils/constants.js`
- `docs/phases/phase5/PHASE5_OVERVIEW.md`

---

## UI / UX Baseline (Gotham Command Panel)

All new controls must match the shipped Gotham styling language from Phase 5:
- layered dark panels (`--bg-*` tokens)
- subtle border hierarchy (`--line`, `--line-strong`)
- mono labels and compact command-panel controls
- semantic color use (air/sea/event/conflict) without random one-off hues

Zone and alert controls should live in Sidebar + dedicated panels, not scattered floating modals.

---

## What This Phase Is

- User-defined polygon zones (create/edit/delete/enable/disable)
- Zone membership tracking for planes and ships
- Alert generation on entry/exit transitions
- Correlation of events/conflicts to zones
- Alert stream via REST + WebSocket + in-app alert center
- Optional outbound notifications (webhook-first, extensible)

---

## What This Phase Is NOT

- Full incident-management workflow (assignment/escalation/runbooks)
- Historical replay/time-travel UI
- Complex GIS stack migration (PostGIS/GeoServer)
- Paid push notification vendor lock-in
- Deployment hardening work (Phase 7)

---

## Task Breakdown (Rationalized to 11 Tasks)

### Backend Foundation

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 1 | Zone model/schema + CRUD API | Add Zone/Alert models + SQLite tables/indexes and ship `/api/zones` CRUD with validation | GLM |
| 2 | Spatial utils | Polygon normalization, bbox prefilter, point-in-polygon with tests | GLM |
| 3 | Membership tracking + entry/exit alert engine | Track plane/ship zone transitions and convert them into cooldown-aware alerts | GLM |

### Alerting & Correlation Engine

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 4 | Event/conflict zone correlation | Correlate incoming events/conflicts to active zones | GLM |
| 5 | Alert persistence + dedup | Store alerts, dedup bursts, add ack/suppress metadata | MiniMax |
| 6 | Alert WebSocket stream | Broadcast `alert` / `alert_batch` messages to frontend clients | GLM |

### Frontend Zone & Alert UX

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 7 | Zone editor + globe overlays | Draw/edit polygons and render zone overlays/selection states on globe | GLM |
| 8 | Zone manager in Sidebar | Zone list, toggle active, edit/delete, quick status indicators | GLM |
| 9 | Alert center panel | Real-time alert feed, filters, ack/clear controls, severity badges | MiniMax |

### Notifications, QA, Docs

| # | Task | Description | Agent |
|---|------|-------------|-------|
| 10 | Notification channels | Webhook delivery + retry queue + env-configured providers | MiniMax |
| 11 | End-to-end verification + docs | Full scenario tests, failure-mode tests, docs + runbooks | MiniMax |

---

## File Structure (Planned)

```text
backend/app/
├── api/
│   ├── routes/
│   │   ├── zones.py                 NEW
│   │   └── alerts.py                NEW
│   └── websocket.py                 UPDATE (alert message types + broadcast helpers)
├── core/
│   ├── models.py                    UPDATE (Zone, Alert, correlation models)
│   └── database.py                  UPDATE (zones + alerts tables, indexes, helpers)
├── services/
│   ├── spatial_service.py           NEW (point-in-polygon, bbox checks)
│   ├── zone_membership_service.py   NEW (entity-zone transition tracking)
│   ├── alert_service.py             NEW (alert creation, dedup, persistence)
│   └── notification_service.py      NEW (webhook dispatch + retries)
└── tasks/
    └── schedulers.py                UPDATE (wire correlation/alert checks)

backend/tests/
├── test_zone_routes.py              NEW
├── test_alert_routes.py             NEW
├── test_spatial_service.py          NEW
├── test_zone_membership_service.py  NEW
├── test_alert_service.py            NEW
└── test_notification_service.py     NEW

frontend/src/
├── components/
│   ├── Globe/
│   │   ├── Globe.jsx                UPDATE (zone layers + interaction)
│   │   ├── Globe.css                UPDATE (zone overlay styling)
│   │   └── ZoneEditorOverlay.jsx    NEW
│   ├── Sidebar/
│   │   ├── Sidebar.jsx              UPDATE (zone manager)
│   │   └── Sidebar.css              UPDATE
│   ├── AlertCenter/
│   │   ├── AlertCenter.jsx          NEW
│   │   └── AlertCenter.css          NEW
│   └── ZonePanel/
│       ├── ZonePanel.jsx            NEW
│       └── ZonePanel.css            NEW
├── hooks/
│   ├── useZones.js                  NEW
│   ├── useAlerts.js                 NEW
│   └── useWebSocket.js              UPDATE (alert message handling)
└── utils/
    ├── zoneGeometry.js              NEW
    └── alertFormatters.js           NEW

docs/
├── API.md                           UPDATE
├── ARCHITECTURE.md                  UPDATE
├── ENVIRONMENT.md                   UPDATE
└── phases/phase6/
    ├── PHASE6_OVERVIEW.md           NEW
    └── task_*.md                    NEW
```

---

## API Contract Additions (Planned)

### REST
- `GET /api/zones`
- `POST /api/zones`
- `GET /api/zones/{zone_id}`
- `PATCH /api/zones/{zone_id}`
- `DELETE /api/zones/{zone_id}`
- `GET /api/alerts`
- `GET /api/alerts/count`
- `POST /api/alerts/{alert_id}/ack`

### WebSocket
- `alert` — single alert upsert/update
- `alert_batch` — bulk initial sync or burst updates

---

## Alert Model (Draft)

Minimum fields:
- `id`, `zone_id`, `zone_name`
- `entity_type` (`plane|ship|event|conflict`)
- `entity_id`
- `alert_type` (`zone_entry|zone_exit|event_in_zone|conflict_in_zone`)
- `severity` (`info|warning|critical`)
- `title`, `message`
- `timestamp`
- `acked` (bool), `acked_at` (nullable)
- `dedup_key`

---

## Key Technical Decisions

1. **Frontend + backend split:** drawing/editing on frontend, validation + persistence on backend.
2. **Spatial engine in Python utility layer:** bbox prefilter + ray-casting point-in-polygon (no heavy GIS dependency in Phase 6).
3. **Transition-based alerts:** generate on state change, not every tick.
4. **Dedup/cooldown required:** avoid alert storms for jittering entities near boundaries.
5. **Webhook-first notifications:** generic outbound channel that can be expanded in Phase 7.

---

## Verification Checklist

- [ ] Zone CRUD works via REST and UI
- [ ] Polygon validation rejects malformed or self-intersecting inputs
- [ ] Plane entry into zone generates one alert (not per refresh loop)
- [ ] Plane exit from zone generates one alert
- [ ] Ship entry/exit parity with planes
- [ ] Event/conflict correlation alerts generated for active zones
- [ ] Alert dedup/cooldown prevents floods
- [ ] Alerts visible in Alert Center in near real-time
- [ ] Alert ack action persists and reflects in UI
- [ ] WebSocket reconnect restores alert state without duplication
- [ ] Existing planes/ships/events/conflicts flows show no regression
- [ ] Backend tests pass
- [ ] Frontend build passes

---

## Constraints

- Keep existing Phase 1–5 API behavior backward-compatible
- No new paid infrastructure dependencies required for core functionality
- Keep per-refresh alert logic performant at 10k+ planes
- Zone checks should use prefiltering to avoid O(N×M) blowups in common case
- All new behavior must degrade gracefully when no zones are configured
