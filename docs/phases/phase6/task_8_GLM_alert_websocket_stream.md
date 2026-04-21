# Phase 6 — Task 8: Alert WebSocket Stream

## Context

Read first:
- `backend/app/api/websocket.py`
- `frontend/src/hooks/useWebSocket.js`
- `frontend/src/App.jsx`

## Goal

Stream alert updates to connected clients in real time.

## Implementation

Update backend websocket contract:
- `type: "alert"`, `action: "upsert"|"ack"`
- `type: "alert_batch"`, `action: "upsert"`

Add backend broadcast helpers mirroring existing plane/ship patterns.

Frontend handling:
- update `useWebSocket` to route alert message types
- initial alert sync via REST + incremental updates via WebSocket

### Reconnect behavior

On reconnect:
- perform REST re-sync to avoid missed messages
- dedup client state by alert id

## Files

- Update: `backend/app/api/websocket.py`
- Update: `backend/app/services/alert_service.py`
- Update: `frontend/src/hooks/useWebSocket.js`
- Create/Update: `frontend/src/hooks/useAlerts.js`

## Verification

- [ ] new alert appears in UI without page refresh
- [ ] ack event updates existing alert row state
- [ ] reconnect does not duplicate alerts
- [ ] no regressions in existing WS message handling
