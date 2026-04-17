# Phase 5 — Task 13: Relative Timestamps + Panel Overflow

## Context

Read all four info panel components and `frontend/src/utils/formatters.js`. Read **`frontend/src/components/InfoPanel/infoPanel.css`** — shared panel chrome already defines positioning, blur, brackets, and `z-index: 1000`.

## UI / UX baseline (Gotham — read before implementing)

- **Timestamps:** Relative strings (`2h ago`) should render in the same value typography as other `.info-value` rows — typically **`var(--sans)`** at `12px` for body values, or **`var(--mono)`** with `tabular-nums` if you want clock-like alignment; do not use a lighter gray hex outside the token scale.
- **Panel bounds:** Before adding new `calc(100vh - …)` rules, **audit what `infoPanel.css` already sets**. Extend or override in one place where possible so plane/ship/event/conflict panels don’t drift.
- **Z-index:** Shared panels already sit at **`z-index: 1000`**. New globe HUD elements use ~10–100; minimap (Task 3) should stay **below** info panels. Do not arbitrarily raise panel z-index to `500` if that breaks stacking — prefer harmonizing with the existing `1000`.
- **Narrow viewports:** If full-width takeover is needed below `400px`, use **`min()`** / **`max()`** width with `var(--line)` borders — match app’s flat 2px radius language.

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

**Optional enhancement:** For “live” feeling, refresh relative labels on an interval **only while the panel is open**, and pause when `document.hidden` — keep CPU negligible.

### Panel Overflow Protection

The info panels use shared chrome in `infoPanel.css` (`position: absolute`, `top: 72px`, `right: 16px`, `width: 300px`, blur, brackets). Ensure content scrolls inside the card instead of spilling past the viewport:

```css
.plane-info-panel,
.ship-info-panel {
  max-height: calc(100vh - 88px);
  overflow-y: auto;
  overflow-x: hidden;
}
```

Event and conflict panels should receive **equivalent** rules in their CSS modules (or share a common class if refactored).

Also clamp horizontal position on narrow viewports if needed:

```css
@media (max-width: 400px) {
  .plane-info-panel,
  .ship-info-panel {
    right: 8px;
    left: 8px;
    width: auto;
    max-width: min(100vw - 16px, 360px);
  }
}
```

Tune `top` offset against the real header height in `App` / `Header` so the panel never sits under the top bar.

### Panel Z-Index

Prefer the **existing** `z-index: 1000` from `infoPanel.css` unless a documented stacking bug requires adjustment — if raised, document interaction with `Globe` HUD (`z-index` 5–100) and any future minimap.

## Files to Update

- `frontend/src/utils/formatters.js` — add `formatRelativeTime()`
- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx` — use relative time for `last_contact`
- `frontend/src/components/ShipInfoPanel/ShipInfoPanel.jsx` — use relative time
- `frontend/src/components/EventInfoPanel/EventInfoPanel.jsx` — use relative time for `date`
- `frontend/src/components/ConflictInfoPanel/ConflictInfoPanel.jsx` — use relative time for `date`
- `frontend/src/components/InfoPanel/infoPanel.css` — `max-height`, `overflow`, optional narrow-screen width clamp (shared plane/ship)
- `frontend/src/components/EventInfoPanel/EventInfoPanel.css` — parity overflow rules if panels don’t share the same root class
- `frontend/src/components/ConflictInfoPanel/ConflictInfoPanel.css` — parity overflow rules

## Verification

- [ ] Timestamps show "2h ago", "3d ago", "Just now" format (or full locale date after cutoff)
- [ ] Panel scrolls internally rather than overflowing viewport
- [ ] Panel is usable on narrow screens (no horizontal clip of close button)
- [ ] Relative time updates as time passes **or** documented as static until panel re-open (pick one behavior and test)
- [ ] "—" shown for invalid/missing timestamps
- [ ] Stacking order: panels remain above globe HUD and minimap; no accidental click-through
