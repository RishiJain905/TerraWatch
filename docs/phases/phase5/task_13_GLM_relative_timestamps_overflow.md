# Phase 5 — Task 13: Relative Timestamps + Panel Overflow

## Context

Read all four info panel components and `frontend/src/utils/formatters.js`.

## Goal

1. Replace raw ISO timestamps in info panels with human-readable relative time ("2 hours ago")
2. Ensure info panels don't overflow the viewport when opened near edges

## Implementation

### Relative Timestamps

Add a `formatRelativeTime` utility in `formatters.js`:

```javascript
export function formatRelativeTime(isoTimestamp) {
  if (!isoTimestamp) return '—'
  
  const date = new Date(isoTimestamp)
  if (isNaN(date.getTime())) return '—'
  
  const now = Date.now()
  const diffMs = now - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  
  if (diffSec < 60) return 'Just now'
  if (diffMin < 60) return `${diffMin}m ago`
  if (diffHour < 24) return `${diffHour}h ago`
  if (diffDay < 7) return `${diffDay}d ago`
  
  return date.toLocaleDateString()
}
```

Apply to all timestamp fields:
- `PlaneInfoPanel`: `last_contact`
- `ShipInfoPanel`: `last_updated` (or similar timestamp field)
- `EventInfoPanel`: `date`
- `ConflictInfoPanel`: `date`

### Panel Overflow Protection

The info panels are positioned fixed/absolute. They slide in from the right. Ensure they don't overflow the viewport.

Current behavior: `right: 0` or fixed width. When viewport is narrow (mobile), the panel may extend offscreen.

Fix: Use `max-height: calc(100vh - 80px)` and `overflow-y: auto` so the panel scrolls internally rather than extending beyond viewport:

```css
.info-panel {
  position: fixed;
  top: 60px;
  right: 0;
  width: 320px;
  height: calc(100vh - 80px);
  max-height: calc(100vh - 80px);
  overflow-y: auto;
  /* ... existing styles */
}
```

Also clamp the panel to not go below `right: 0` on narrow screens. On very narrow screens (< 400px), the panel could take full width.

### Panel Z-Index

Make sure info panels are always above the globe, minimap, and sidebar:

```css
.info-panel {
  z-index: 500;
}
```

## Files to Update

- `frontend/src/utils/formatters.js` — add `formatRelativeTime()`
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx` — use relative time for `last_contact`
- `frontend/src/components/ShipInfoPanel/ShipInfoPanel.jsx` — use relative time
- `frontend/src/components/EventInfoPanel/EventInfoPanel.jsx` — use relative time for `date`
- `frontend/src/components/ConflictInfoPanel/ConflictInfoPanel.jsx` — use relative time for `date`
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.css` — add max-height and overflow
- `frontend/src/components/ShipInfoPanel/ShipInfoPanel.css` — add max-height and overflow
- `frontend/src/components/EventInfoPanel/EventInfoPanel.css` — add max-height and overflow
- `frontend/src/components/ConflictInfoPanel/ConflictInfoPanel.css` — add max-height and overflow

## Verification

- [ ] Timestamps show "2h ago", "3d ago", "Just now" format
- [ ] Panel scrolls internally rather than overflowing viewport
- [ ] Panel is usable on mobile (narrow screen)
- [ ] Relative time updates as time passes (or shows static value)
- [ ] "—" shown for invalid/missing timestamps
