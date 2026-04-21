# Phase 6 — Task 10: Zone Management Sidebar

## Context

Read first:
- `frontend/src/components/Sidebar/Sidebar.jsx`
- `frontend/src/components/Sidebar/Sidebar.css`
- `frontend/src/hooks/usePlanes.js`
- `frontend/src/hooks/useShips.js`

## Goal

Add a dedicated Zone Manager section in Sidebar for operational control.

## Implementation

Zone Manager capabilities:
- list zones with status (active/inactive)
- quick toggle active state
- open edit mode
- delete confirmation
- zone health indicators (recent alert count)

### Suggested row structure

- zone name
- active toggle
- entry/exit badges
- actions: edit/delete

### Hook/state

Add `useZones` hook:
- fetch list
- create/update/delete helpers
- optimistic update policy with rollback on failure

## Files

- Update: `frontend/src/components/Sidebar/Sidebar.jsx`
- Update: `frontend/src/components/Sidebar/Sidebar.css`
- Create: `frontend/src/hooks/useZones.js`
- Update: `frontend/src/App.jsx`

## Verification

- [ ] sidebar shows zones list from backend
- [ ] active toggle persists
- [ ] delete removes zone after confirmation
- [ ] edit action opens zone editor with existing geometry
- [ ] network failures show non-blocking error UI
