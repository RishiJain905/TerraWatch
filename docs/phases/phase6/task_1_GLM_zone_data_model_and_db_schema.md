# Phase 6 — Task 1: Zone Data Model + DB Schema

## Context

Read first:
- `backend/app/core/models.py`
- `backend/app/core/database.py`
- `backend/app/main.py`
- `docs/ARCHITECTURE.md`

## Goal

Add first-class backend support for zones and alerts:
- Pydantic models
- SQLite tables
- indexes
- migration-safe init path

## Implementation

### Models (`backend/app/core/models.py`)

Add:
- `Zone` model
- `ZoneCreate` / `ZoneUpdate` request models
- `Alert` model

Recommended `Zone` fields:
- `id: str`
- `name: str`
- `polygon: list[list[float]]` (`[lon, lat]` points)
- `active: bool`
- `alert_on_entry: bool`
- `alert_on_exit: bool`
- `created_at`, `updated_at`

Recommended `Alert` fields:
- `id`, `zone_id`, `zone_name`
- `entity_type`, `entity_id`
- `alert_type`, `severity`
- `title`, `message`, `timestamp`
- `acked`, `acked_at`
- `dedup_key`

### Database (`backend/app/core/database.py`)

Add table creation in `init_db()`:
- `zones`
- `alerts`

`zones` table:
- `id TEXT PRIMARY KEY`
- `name TEXT NOT NULL`
- `polygon TEXT NOT NULL` (JSON array)
- `active INTEGER NOT NULL DEFAULT 1`
- `alert_on_entry INTEGER NOT NULL DEFAULT 1`
- `alert_on_exit INTEGER NOT NULL DEFAULT 1`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

`alerts` table:
- `id TEXT PRIMARY KEY`
- `zone_id TEXT NOT NULL`
- `zone_name TEXT NOT NULL`
- `entity_type TEXT NOT NULL`
- `entity_id TEXT NOT NULL`
- `alert_type TEXT NOT NULL`
- `severity TEXT NOT NULL`
- `title TEXT NOT NULL`
- `message TEXT NOT NULL`
- `timestamp TEXT NOT NULL`
- `acked INTEGER NOT NULL DEFAULT 0`
- `acked_at TEXT`
- `dedup_key TEXT NOT NULL`

Indexes:
- `idx_zones_active`
- `idx_alerts_timestamp`
- `idx_alerts_zone`
- `idx_alerts_entity`
- `idx_alerts_ack_state`
- `idx_alerts_dedup_key`

### Helpers

Add DB helpers for:
- insert/update/list/get/delete zones
- insert/list/count/ack alerts

Keep function style aligned with existing plane/ship/event helper patterns.

## Files to Update

- `backend/app/core/models.py`
- `backend/app/core/database.py`
- `backend/tests/test_database_and_scheduler.py` (schema assertions)

## Verification

- [ ] `init_db()` creates `zones` and `alerts` tables
- [ ] required indexes exist
- [ ] zone row round-trip works
- [ ] alert row round-trip works
- [ ] `python -m pytest backend/tests/test_database_and_scheduler.py -v` passes
