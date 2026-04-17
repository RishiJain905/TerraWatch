# Phase 5 — Task 12: External Links + Copy Buttons

## Context

Read all four info panel components: `PlaneInfoPanel.jsx`, `ShipInfoPanel.jsx`, `EventInfoPanel.jsx`, `ConflictInfoPanel.jsx`, plus shared `frontend/src/components/InfoPanel/infoPanel.css`.

## UI / UX baseline (Gotham — read before implementing)

Controls inside info panels must look like **`close-btn`** / **`info-row`** siblings — square corners, `1px` borders, `var(--mono)` where appropriate.

- **Links:** Style external anchors with **`--accent-evt`** or **`--panel-accent`** (for conflict) and underline on hover only; keep `target="_blank"` + `rel="noopener noreferrer"`. External indicator can be a small mono suffix (e.g. `↗`) **or** a CSS `::after` on a class like `.info-external-link` — ensure screen readers get text (`aria-label` includes “opens in new tab”).
- **Copy buttons:** Not raw unicode at 50% opacity alone — use a **`copy-btn`** class: `22px` min hit target (match `.close-btn` height family), `border: 1px solid var(--line)`, hover `border-color: var(--panel-accent)`, icon/text in `var(--text-2)` → `var(--text-0)` on hover. Optional “Copied!” state uses **`--accent-ok`** micro-label for 1.5s.
- **Clipboard:** `navigator.clipboard.writeText` may require HTTPS; fail silently with optional toast using same mono micro-style.

## Goal

- `source_url` links in EventInfoPanel and ConflictInfoPanel should open in a new tab (not replace the TerraWatch page)
- IDs (icao24, MMSI, event IDs) should have a copy-to-clipboard control
- All external links should indicate they open externally (suffix or icon + accessible name)

## Implementation

### External Links

In `EventInfoPanel.jsx` and `ConflictInfoPanel.jsx`:

```javascript
// Before:
<a href={event.source_url}>{event.source_url}</a>

// After:
<a
  href={event.source_url}
  target="_blank"
  rel="noopener noreferrer"
  className="info-external-link"
  aria-label="View source (opens in new tab)"
>
  View source <span aria-hidden="true">↗</span>
</a>
```

### Copy Buttons

Add a small copy control next to IDs. Use the Clipboard API:

```javascript
const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    // Optional: brief "Copied!" tooltip — mono, --accent-ok, matches HUD microcopy
  })
}
```

For each ID field:

```javascript
<div className="info-row">
  <span className="info-label">MMSI</span>
  <span className="info-value mono">
    {ship.mmsi}
    <button
      type="button"
      className="copy-btn"
      onClick={() => copyToClipboard(ship.mmsi)}
      aria-label="Copy MMSI"
      title="Copy to clipboard"
    >
      COPY
    </button>
  </span>
</div>
```

Styling (Gotham — align with `close-btn` proportions):

```css
.copy-btn {
  margin-left: 8px;
  padding: 2px 8px;
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--text-2);
  background: transparent;
  border: 1px solid var(--line);
  border-radius: 2px;
  cursor: pointer;
  transition: border-color 140ms ease, color 140ms ease, background 140ms ease;
  vertical-align: middle;
}

.copy-btn:hover {
  border-color: var(--panel-accent);
  color: var(--text-0);
  background: var(--bg-2);
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
- `frontend/src/utils/formatters.js` — add `copyToClipboard` helper (shared)
- `frontend/src/components/InfoPanel/infoPanel.css` — shared `.copy-btn` / `.info-external-link` rules (prefer centralizing vs duplicating across four panel CSS files)

## Verification

- [ ] `source_url` opens in new tab (not same window)
- [ ] Copy control appears next to icao24, mmsi, event id
- [ ] Clicking copy puts ID in clipboard
- [ ] External links expose “opens in new tab” to assistive tech
- [ ] Copy / link controls match bracket-card HUD styling and hover/focus behavior
