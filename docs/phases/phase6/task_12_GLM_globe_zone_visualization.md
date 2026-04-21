# Phase 6 — Task 12: Globe Zone Visualization

## Context

Read first:
- `frontend/src/components/Globe/Globe.jsx`
- `frontend/src/components/Globe/Globe.css`
- `frontend/src/utils/constants.js`

## Goal

Render operational zones clearly on the globe with low clutter and strong selection affordances.

## Implementation

Add zone layers to globe:
- polygon fill (low alpha)
- boundary stroke
- selected-zone highlight
- optional label anchor at centroid

### Visual rules

- active zone: stronger stroke
- inactive zone: muted stroke/fill
- selected zone: accent + thicker outline
- keep icon picking and core entity layers readable

### Interaction

- click zone to select
- hover tooltip (name + status)
- zone selection syncs with Sidebar/Alert Center context

## Files

- Update: `frontend/src/components/Globe/Globe.jsx`
- Update: `frontend/src/components/Globe/Globe.css`
- Create: `frontend/src/utils/zoneGeometry.js` (centroid helpers)

## Verification

- [ ] zones visible at different zoom levels
- [ ] selection/highlight states are obvious
- [ ] active/inactive visual difference is clear
- [ ] zone interactions do not break plane/ship/event picking
