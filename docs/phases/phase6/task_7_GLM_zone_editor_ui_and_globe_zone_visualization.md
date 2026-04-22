# Phase 6 — Task 7: Zone Editor UI + Globe Zone Visualization

## Context

Read first:
- `frontend/src/components/Globe/Globe.jsx`
- `frontend/src/components/Globe/Globe.css`
- `frontend/src/components/Sidebar/Sidebar.jsx`
- `frontend/src/utils/constants.js`
- `frontend/src/index.css`

## Goal

Allow users to create/edit polygon zones directly in the UI and render operational zone overlays on the globe with clear interaction states.

## Implementation

### Zone editor workflow

Add an editor mode with workflow:
1. Enter zone draw mode
2. Click to add polygon vertices
3. Preview polygon + closing edge
4. Save/cancel
5. Edit existing zone geometry

UX requirements:
- minimum 3 points before save enabled
- explicit save/cancel controls
- ESC cancels draw mode
- visible validation errors for malformed polygons
- consistent Gotham panel styling

Data contract:
- use `/api/zones` endpoints from Task 1

### Globe zone overlays

Add zone layers to globe:
- polygon fill (low alpha)
- boundary stroke
- selected-zone highlight
- optional label anchor at centroid

Visual rules:
- active zone: stronger stroke
- inactive zone: muted stroke/fill
- selected zone: accent + thicker outline
- keep entity layers readable

Interaction:
- click zone to select
- hover tooltip (name + status)
- zone selection syncs with Sidebar/Alert Center context

## Files

- Create: `frontend/src/components/Globe/ZoneEditorOverlay.jsx`
- Update: `frontend/src/components/Globe/Globe.jsx`
- Update: `frontend/src/components/Globe/Globe.css`
- Create: `frontend/src/utils/zoneGeometry.js` (centroid helpers)
- Update: `frontend/src/App.jsx`

## Verification

- [ ] user can draw polygon and save zone
- [ ] cancel exits editor without side effects
- [ ] polygon preview renders correctly during draw
- [ ] zones visible at different zoom levels
- [ ] active/inactive/selected visual states are obvious
- [ ] zone interactions do not break plane/ship/event picking
