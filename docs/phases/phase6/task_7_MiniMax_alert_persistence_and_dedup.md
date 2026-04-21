# Phase 6 — Task 7: Alert Persistence, Dedup, and Acknowledgement

## Context

Read first:
- `backend/app/core/database.py`
- `backend/app/services/alert_service.py`
- `backend/app/api/routes/metadata.py`

## Goal

Add alert query/ack APIs and robust dedup persistence semantics.

## Implementation

Create `backend/app/api/routes/alerts.py`.

Endpoints:
- `GET /api/alerts` (filters: zone, type, severity, acked, since, limit)
- `GET /api/alerts/count`
- `POST /api/alerts/{alert_id}/ack`

### Database behavior

- alert inserts should preserve full history by default
- dedup should suppress insert if same `dedup_key` within cooldown window
- ack operation updates `acked=1`, `acked_at=timestamp`

### Pagination

- support `limit` + `offset`
- default sort: newest first

## Files

- Create: `backend/app/api/routes/alerts.py`
- Update: `backend/app/main.py`
- Update: `backend/app/core/database.py`
- Create: `backend/tests/test_alert_routes.py`

## Verification

- [ ] list endpoint returns alerts in descending timestamp order
- [ ] count endpoint reflects filters
- [ ] ack endpoint updates state and idempotently handles re-acks
- [ ] dedup window logic verified
- [ ] tests pass
