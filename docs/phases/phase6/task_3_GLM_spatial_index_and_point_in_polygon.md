# Phase 6 — Task 3: Spatial Utils (Point-in-Polygon + Prefilter)

## Context

Read first:
- `backend/app/core/models.py`
- `backend/app/tasks/schedulers.py`
- `backend/tests/test_dedup.py`

## Goal

Add a deterministic geometry utility layer for zone membership checks that is fast enough for frequent refresh cycles.

## Implementation

Create `backend/app/services/spatial_service.py`.

Implement:
- polygon normalization (`[lon, lat]`)
- bbox derivation for polygons
- fast bbox point prefilter
- ray-casting point-in-polygon
- boundary handling policy (document inclusive/exclusive behavior)

### Performance pattern

For each zone:
1. compute bbox once
2. for each entity point, check bbox first
3. run ray-casting only if bbox hit

### Test design

Create unit tests covering:
- inside/outside points
- boundary points
- concave polygons
- invalid polygons
- antimeridian edge-case strategy (explicitly document if deferred)

## Files

- Create: `backend/app/services/spatial_service.py`
- Create: `backend/tests/test_spatial_service.py`

## Verification

- [ ] spatial tests pass
- [ ] function behavior is deterministic
- [ ] bbox prefilter path exercised in tests
- [ ] invalid input path returns safe failure (no crashes)
