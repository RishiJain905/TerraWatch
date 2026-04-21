# Phase 6 — Task 5: Entry/Exit Alert Rule Engine

## Context

Read first:
- `backend/app/services/zone_membership_service.py`
- `backend/app/core/models.py`
- `backend/app/core/database.py`

## Goal

Transform membership transitions into persisted, user-facing alerts with severity and cooldown logic.

## Implementation

Create `backend/app/services/alert_service.py`.

Responsibilities:
- map transition -> alert payload
- assign severity by entity type / alert type
- generate deterministic `dedup_key`
- apply cooldown windows to prevent jitter floods
- persist alert rows

### Suggested cooldown defaults
- same `dedup_key` suppressed for 60–120 seconds
- configurable via env vars in `config.py`

### Severity defaults
- `zone_entry` => `warning`
- `zone_exit` => `info`

(Allow per-zone override in future; keep simple in Phase 6.)

## Files

- Create: `backend/app/services/alert_service.py`
- Update: `backend/app/config.py` (cooldown settings)
- Create: `backend/tests/test_alert_service.py`

## Verification

- [ ] entry transition creates one alert
- [ ] duplicate transition within cooldown suppressed
- [ ] dedup key stable across repeated evaluations
- [ ] alert row persisted with expected schema
- [ ] tests pass
