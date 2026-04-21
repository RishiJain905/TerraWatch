# Phase 6 — Task 6: Event/Conflict Zone Correlation

## Context

Read first:
- `backend/app/services/gdelt_service.py`
- `backend/app/api/routes/events.py`
- `backend/app/api/routes/conflicts.py`
- `backend/app/services/spatial_service.py`

## Goal

Generate correlation alerts when events/conflicts occur inside active zones.

## Implementation

Extend alerting pipeline to process event/conflict records:
- event point inside active zone => `event_in_zone`
- conflict point inside active zone => `conflict_in_zone`

### Correlation policy

- correlate on newly ingested events/conflicts only (avoid full historical rescans each cycle)
- dedup by `(zone_id, entity_type, entity_id)`
- severity defaults:
  - `event_in_zone` => `info`
  - `conflict_in_zone` => `critical`

### Message template examples

- `Event in Zone Alpha: protest near 48.85, 2.35`
- `Conflict in Zone Alpha: assault category detected`

## Files

- Update: `backend/app/tasks/schedulers.py`
- Update: `backend/app/services/alert_service.py`
- Create: `backend/tests/test_event_conflict_zone_correlation.py`

## Verification

- [ ] event in zone creates correlation alert
- [ ] conflict in zone creates critical alert
- [ ] out-of-zone events do not alert
- [ ] dedup prevents repetitive alerts for same item
- [ ] tests pass
