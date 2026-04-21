# Phase 6 — Task 4: Entity-Zone Membership Tracking

## Context

Read first:
- `backend/app/tasks/schedulers.py`
- `backend/app/services/adsb_service.py`
- `backend/app/services/aisstream_service.py`
- `backend/app/services/spatial_service.py`

## Goal

Track real-time zone membership for planes and ships and emit transition events (`entered`, `exited`) without duplication.

## Implementation

Create `backend/app/services/zone_membership_service.py`.

Core state:
- `entity_zone_state[(entity_type, entity_id)] = set(zone_ids)`

Processing function:
- input: active zones + entity snapshot
- output: transitions list
  - `{entity_type, entity_id, zone_id, transition: 'entered'|'exited', timestamp}`

### Transition rules

- first-time seen entity with zone membership => `entered`
- zone removed from current set => `exited`
- no state change => no transition
- inactive zones should be ignored

### Reset behavior

- state cleanup for stale entities
- state refresh on zone edits/deletes

## Files

- Create: `backend/app/services/zone_membership_service.py`
- Create: `backend/tests/test_zone_membership_service.py`
- Update: `backend/app/tasks/schedulers.py` (wire periodic membership checks)

## Verification

- [ ] entry transitions emitted once
- [ ] exit transitions emitted once
- [ ] no duplicate transitions on steady-state updates
- [ ] zone deactivation suppresses further transitions
- [ ] tests pass
