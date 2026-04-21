# Phase 5 — Task 12: External Links + Copy Buttons — DONE

## What was shipped

All four info panels now have copy-to-clipboard controls next to their ID fields, and external source links in Event/Conflict panels use a consistent, accessible `.info-external-link` style.

## Files changed

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/utils/formatters.js` | UPDATE | Added `copyToClipboard(text)` helper wrapping `navigator.clipboard.writeText`; fails silently |
| `frontend/src/components/InfoPanel/infoPanel.css` | UPDATE | Added `.copy-btn` (22px hit target, mono, 1px border, hover → `var(--panel-accent)`), `.copy-btn.copied` (transient `--accent-ok` state), and `.info-external-link` (underlined on hover, `::after` ↗ suffix) |
| `frontend/src/components/EventInfoPanel/EventInfoPanel.css` | UPDATE | Removed obsolete `.source-link` and `.source-link:hover` rules (superseded by shared `.info-external-link`) |
| `frontend/src/components/PlaneInfoPanel/PlaneInfoPanel.jsx` | UPDATE | Added `copyToClipboard` import; `useState` for `copiedId`; copy buttons for **ICAO24** and **Callsign** inside `.info-value` |
| `frontend/src/components/ShipInfoPanel/ShipInfoPanel.jsx` | UPDATE | Added `copyToClipboard` import; `useState` for `copiedId`; copy button for **MMSI** inside `.info-value` |
| `frontend/src/components/EventInfoPanel/EventInfoPanel.jsx` | UPDATE | Added `copyToClipboard` import; `useState` for `copiedId`; new **ID** row with copy button (strips `gdelt_` prefix for display and clipboard); restyled `source_url` anchor to `.info-external-link` with `aria-label="View source (opens in new tab)"` |
| `frontend/src/components/ConflictInfoPanel/ConflictInfoPanel.jsx` | UPDATE | Added `copyToClipboard` import; `useState` for `copiedId`; new **ID** row with copy button (strips `gdelt_` prefix for display and clipboard); restyled `source_url` anchor to `.info-external-link` with `aria-label="View source (opens in new tab)"` |

## Implementation details

### Copy buttons

- Each panel uses local `copiedId` state (managed with `useState`) and a `handleCopy(id, text)` helper.
- Clicking a copy button: calls `copyToClipboard(text)`, sets `copiedId`, auto-clears after **1.5s** via `setTimeout`.
- While `copiedId` matches, the button text switches from **COPY** → **COPIED!** and the `.copied` class activates (`--accent-ok` border + color + subtle background).
- Buttons are conditionally rendered only when the field value is truthy (e.g., `{plane.id && <button … />}`).
- All buttons have `type="button"`, `aria-label`, and `title="Copy to clipboard"` for accessibility.
- Plane: buttons placed **inside** `.info-value` / `.info-value.mono` so they stay next to the text value.

### External links

- Replaced `.source-link` (bordered button-like style) with `.info-external-link` (text link, underline on hover, `::after` ↗ suffix).
- Links use per-panel CSS custom property `--panel-accent` (`var(--accent-evt)` for events, `var(--accent-cnf)` for conflicts) — no hardcoded colors.
- `target="_blank"` + `rel="noopener noreferrer"` already present; added `aria-label="View source (opens in new tab)"` and `aria-hidden="true"` on the visual ↗ glyph.
- When `source_url` is absent, the existing fallback (label + em dash) is preserved.

### CSS centralization

- `.copy-btn`, `.copy-btn.copied`, and `.info-external-link` live in the **shared** `InfoPanel/infoPanel.css` rather than duplicated across four panel CSS files.

## Verification

- [x] `npm run build` in `frontend/` passes with zero errors (1447 modules, 3.03s)
- [x] `source_url` in EventInfoPanel and ConflictInfoPanel opens in new tab (`target="_blank"`)
- [x] Copy buttons appear next to **ICAO24** (Plane), **Callsign** (Plane), **MMSI** (Ship), **ID** (Event), **ID** (Conflict)
- [x] Clicking copy puts the ID text in clipboard via `navigator.clipboard.writeText`
- [x] `.info-external-link` uses `--panel-accent` and underline on hover
- [x] All external links have `aria-label="...opens in new tab"`
- [x] Copy/link controls match Gotham bracket-card HUD styling (square corners, mono, 1px border, 140ms transitions)
- [x] `.copy-btn.copied` state uses `--accent-ok` for 1.5s visual feedback
- [x] No new CSS files created; all styling centralized in shared `infoPanel.css`
- [x] Old `.source-link` rules removed from `EventInfoPanel.css`
