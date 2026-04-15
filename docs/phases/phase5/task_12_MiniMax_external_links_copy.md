# Phase 5 — Task 12: External Links + Copy Buttons

## Context

Read all four info panel components: `PlaneInfoPanel.jsx`, `ShipInfoPanel.jsx`, `EventInfoPanel.jsx`, `ConflictInfoPanel.jsx`.

## Goal

- `source_url` links in EventInfoPanel and ConflictInfoPanel should open in a new tab (not replace the TerraWatch page)
- IDs (icao24, MMSI, event IDs) should have a copy-to-clipboard button
- All external links should indicate they open externally (icon suffix)

## Implementation

### External Links

In `EventInfoPanel.jsx` and `ConflictInfoPanel.jsx`:

```javascript
// Before:
<a href={event.source_url}>{event.source_url}</a>

// After:
<a href={event.source_url} target="_blank" rel="noopener noreferrer">
  View Source ↗
</a>
```

### Copy Buttons

Add a small copy button next to IDs. Use the Clipboard API:

```javascript
const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    // Optional: brief "Copied!" tooltip
  })
}
```

For each ID field:

```javascript
<div className="info-row">
  <span className="info-label">MMSI</span>
  <span className="info-value">
    {ship.mmsi}
    <button
      className="copy-btn"
      onClick={() => copyToClipboard(ship.mmsi)}
      title="Copy to clipboard"
    >
      ⎘
    </button>
  </span>
</div>
```

Styling:

```css
.copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  font-size: 12px;
  opacity: 0.5;
  transition: opacity 0.2s;
}
.copy-btn:hover {
  opacity: 1;
}
```

### Affected Fields

- **PlaneInfoPanel**: `icao24`, `callsign`
- **ShipInfoPanel**: `mmsi`
- **EventInfoPanel**: `source_url` (external link), `id` (copy)
- **ConflictInfoPanel**: `source_url` (external link), `id` (copy)

## Files to Update

- `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx` — add copy buttons
- `frontend/src/components/ShipInfoPanel/ShipInfoPanel.jsx` — add copy buttons
- `frontend/src/components/EventInfoPanel/EventInfoPanel.jsx` — external link + copy button
- `frontend/src/components/ConflictInfoPanel/ConflictInfoPanel.jsx` — external link + copy button
- `frontend/src/utils/formatters.js` — add `copyToClipboard` helper

## Verification

- [ ] source_url opens in new tab (not same window)
- [ ] Copy button appears next to icao24, mmsi, event id
- [ ] Clicking copy button puts ID in clipboard
- [ ] All external links have "↗" indicator
- [ ] Copy button has hover effect
