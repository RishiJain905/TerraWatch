# Phase 6 — Task 13: Notification Channels (Webhook-First)

## Context

Read first:
- `backend/app/config.py`
- `backend/app/services/alert_service.py`
- `backend/app/tasks/schedulers.py`

## Goal

Deliver alerts to external systems through a configurable webhook channel with retries and fail-safe behavior.

## Implementation

Create `backend/app/services/notification_service.py`.

### Phase 6 channel scope

- outbound webhook POST only
- payload includes full alert object + source metadata
- HMAC signature support (optional env var)

### Reliability requirements

- timeout + retry with exponential backoff
- bounded retry count
- failure logging without blocking alert creation pipeline
- idempotency key header from `alert.id`

### Configuration

Add env vars:
- `ALERT_WEBHOOK_URL`
- `ALERT_WEBHOOK_TIMEOUT_SECONDS`
- `ALERT_WEBHOOK_MAX_RETRIES`
- `ALERT_WEBHOOK_SECRET` (optional)

## Files

- Create: `backend/app/services/notification_service.py`
- Update: `backend/app/config.py`
- Update: `backend/app/services/alert_service.py`
- Create: `backend/tests/test_notification_service.py`
- Update: `docs/ENVIRONMENT.md`

## Verification

- [ ] successful webhook dispatch for new alert
- [ ] retry path triggers on transient failure
- [ ] failure path does not block alert persistence
- [ ] secret signing works when enabled
- [ ] tests pass
