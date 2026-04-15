# Phase 5 — Task 6: Fly-To + Reset View

## Context

Read `frontend/src/components/Globe/Globe.jsx` first.

## Goal

When a user clicks a plane, ship, or event, the globe should smoothly animate to center on that entity rather than snapping instantly. Also add a "Reset View" button to return to the initial view.

## Implementation

### Fly-To on Entity Click

In `Globe.jsx`, when `onEntityClick` fires (i.e., when user clicks an entity), animate the `viewState`:

```javascript
const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
}

// Smooth transition to entity
const flyTo = (entity) => {
  const targetViewState = {
    longitude: entity.lon,
    latitude: entity.lat,
    zoom: 5, // zoom in closer
    pitch: 30,
    bearing: 0,
    transitionDuration: 1000, // 1 second
    transitionInterpolator: new FlyToInterpolator(),
  }
  setViewState(targetViewState)
}
```

Import `FlyToInterpolator` from `@deck.gl/core`:

```javascript
import { FlyToInterpolator } from '@deck.gl/core'
```

When `handleEntityClick` fires in App.jsx, also call `flyTo` in Globe.jsx. Pass the `flyTo` function as a prop or expose it via `onFilterHooksReady`-style ref pattern.

### Reset View Button

Add a small button in the globe area (top-left or near the minimap) that resets to `INITIAL_VIEW_STATE`:

```javascript
const resetView = () => {
  setViewState({
    ...INITIAL_VIEW_STATE,
    transitionDuration: 1000,
    transitionInterpolator: new FlyToInterpolator(),
  })
}
```

Button can be a simple icon: `⟲` or `⌂` in a rounded button.

```css
.reset-view-btn {
  position: absolute;
  top: 10px;
  left: 10px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
```

## Files to Update

- `frontend/src/components/Globe/Globe.jsx` — fly-to logic, reset button, FlyToInterpolator
- `frontend/src/components/Globe/Globe.css` — reset button styling
- `frontend/src/App.jsx` — wire fly-to into handleEntityClick

## Verification

- [ ] Clicking a plane smoothly animates globe to center on it
- [ ] Clicking a ship smoothly animates globe to center on it
- [ ] Clicking an event smoothly animates globe to center on it
- [ ] Reset button returns to initial view with smooth animation
- [ ] Animation is smooth (no jank)
- [ ] Keyboard shortcut R also resets view
