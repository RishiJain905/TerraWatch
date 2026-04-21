# Phase 6 — Task 9: Alert Center Panel

## Context

Read first:
- `frontend/src/App.jsx`
- `frontend/src/hooks/useWebSocket.js`
- `frontend/src/components/InfoPanel/infoPanel.css`
- `frontend/src/utils/formatters.js`

## Goal

Provide a first-class in-app Alert Center for real-time operational awareness.

## Implementation

Create Alert Center panel with:
- reverse-chronological alert feed
- severity badges (`info`, `warning`, `critical`)
- filters (zone, type, severity, acked state)
- ack action per alert
- optional bulk actions (`ack all visible`)

### Behavior

- live updates via websocket
- graceful empty state
- virtualized or capped list for performance
- retain filter state while new alerts arrive

### Formatting

- relative timestamps
- short, scan-friendly titles
- expandable details row

## Files

- Create: `frontend/src/components/AlertCenter/AlertCenter.jsx`
- Create: `frontend/src/components/AlertCenter/AlertCenter.css`
- Create/Update: `frontend/src/hooks/useAlerts.js`
- Update: `frontend/src/App.jsx`

## Verification

- [ ] alerts render with correct severity styles
- [ ] filters work client-side and/or server-side as designed
- [ ] ack action updates row immediately
- [ ] empty/error/loading states render correctly
- [ ] panel remains usable under burst alert traffic
