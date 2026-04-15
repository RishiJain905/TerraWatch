# Phase 5 — Task 3: Minimap / Navigator Inset

## Context

Read `frontend/src/components/Globe/Globe.jsx` first.

## Goal

Add a small globe inset in the corner of the screen showing the user's current view position on the full Earth. This is a standard GEOINT navigation aid.

## Implementation

### Minimap Component

Create a second, smaller `DeckGL` instance with its own `GlobeView` positioned absolutely in the bottom-right corner:

```javascript
function Minimap({ viewState }) {
  return (
    <div className="minimap-container">
      <DeckGL
        views={new GlobeView({ id: 'minimap-globe' })}
        viewState={{
          longitude: viewState.longitude,
          latitude: viewState.latitude,
          zoom: 1,
          pitch: 0,
          bearing: 0, // always north-up
        }}
        layers={[
          new TileLayer({
            data: 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
            // ... same tiles
          }),
          // View indicator: small dot or rectangle showing current view center
          new ScatterplotLayer({
            id: 'minimap-indicator',
            data: [{
              longitude: viewState.longitude,
              latitude: viewState.latitude,
            }],
            getPosition: d => [d.longitude, d.latitude],
            getFillColor: [255, 100, 100, 255],
            getRadius: 50000,
          }),
        ]}
      />
    </div>
  )
}
```

### Styling

```css
.minimap-container {
  position: absolute;
  bottom: 80px;
  right: 20px;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}
```

### Sync with Main Globe

The minimap always shows north-up orientation. It reflects the main globe's center position. When the main globe rotates, the indicator dot moves accordingly.

## Files to Update

- `frontend/src/components/Globe/Globe.jsx` — render `<Minimap viewState={viewState} />`
- `frontend/src/components/Globe/Globe.css` — minimap positioning and styling
- `frontend/src/components/Globe/Minimap.jsx` — NEW component

## Verification

- [ ] Minimap visible in bottom-right corner
- [ ] Shows full globe with current tile style
- [ ] Indicator dot shows current view center
- [ ] Minimap is north-up regardless of main globe rotation
- [ ] Minimap does not interfere with globe interaction
- [ ] Minimap border and shadow look polished
