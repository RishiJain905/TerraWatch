# Phase 6 — Task 9: Zone Editor UI (Draw/Edit Polygons)

## Context

Read first:
- `frontend/src/components/Globe/Globe.jsx`
- `frontend/src/components/Globe/Globe.css`
- `frontend/src/components/Sidebar/Sidebar.jsx`
- `frontend/src/index.css`

## Goal

Allow users to create and edit polygon zones directly from the TerraWatch UI.

## Implementation

Add an editor mode with workflow:
1. Enter zone draw mode
2. Click to add polygon vertices
3. Preview polygon + closing edge
4. Save/cancel
5. Edit existing zone geometry

### UX requirements

- minimum 3 points before save enabled
- explicit save/cancel controls
- ESC cancels draw mode
- visible validation errors for malformed polygons
- consistent Gotham panel styling

### Data contract

Use `/api/zones` endpoints from Task 2.

## Files

- Create: `frontend/src/components/Globe/ZoneEditorOverlay.jsx`
- Update: `frontend/src/components/Globe/Globe.jsx`
- Update: `frontend/src/components/Globe/Globe.css`
- Update: `frontend/src/App.jsx`

## Verification

- [ ] user can draw polygon and save zone
- [ ] cancel exits editor without side effects
- [ ] polygon preview renders correctly during draw
- [ ] invalid shape cannot be submitted
- [ ] editor mode does not break existing globe interactions
