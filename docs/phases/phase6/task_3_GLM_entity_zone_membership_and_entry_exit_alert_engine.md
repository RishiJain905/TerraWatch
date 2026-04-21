# Phase 6 — Task 3: Entity-Zone Membership Tracking + Entry/Exit Alert Engine

## Context

Read first:
- `backend/app/tasks/schedulers.py`
- `backend/app/services/adsb_service.py`
- `backend/app/services/aisstream_service.py`
- `backend/app/services/spatial_service.py`
- `backend/app/core/models.py`
- `backend/app/core/database.py`

## Goal

Track real-time zone membership for planes and ships, emit transition events (`entered`, `exited`) without duplication, and transform transitions into persisted alerts with cooldown logic.

## Implementation

### Membership tracking service

Create `backend/app/services/zone_membership_service.py`.

Core state:
- `entity_zone_state[(entity_type, entity_id)] = set(zone_ids)`

Processing function:
- input: active zones + entity snapshot
- output: transitions list
  - `{entity_type, entity_id, zone_id, transition: 'entered'|'exited', timestamp}`

Transition rules:
- first-time seen entity with zone membership => `entered`
- zone removed from current set => `exited`
- no state change => no transition
- inactive zones should be ignored

Reset behavior:
- state cleanup for stale entities
- state refresh on zone edits/deletes

### Alert rule engine

Create `backend/app/services/alert_service.py`.

Responsibilities:
- map transition -> alert payload
- assign severity by entity type / alert type
- generate deterministic `dedup_key`
- apply cooldown windows to prevent jitter floods
- persist alert rows

Suggested cooldown defaults:
- same `dedup_key` suppressed for 60–120 seconds
- configurable via env vars in `config.py`

Severity defaults:
- `zone_entry` => `warning`
- `zone_exit` => `info`

## Files

- Create: `backend/app/services/zone_membership_service.py`
- Create: `backend/app/services/alert_service.py`
- Update: `backend/app/config.py` (cooldown settings)
- Update: `backend/app/tasks/schedulers.py` (wire membership + alert checks)
- Create: `backend/tests/test_zone_membership_service.py`
- Create: `backend/tests/test_alert_service.py`

## Verification

- [ ] entry transitions emitted once
- [ ] exit transitions emitted once
- [ ] no duplicate transitions on steady-state updates
- [ ] entry transition creates one alert
- [ ] duplicate transition within cooldown suppressed
- [ ] dedup key stable across repeated evaluations
- [ ] tests pass
