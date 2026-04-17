# Phase 5 — Task 11: Empty State Messages

## Context

Read `frontend/src/components/Sidebar/Sidebar.jsx` and `frontend/src/components/Sidebar/Sidebar.css`, plus `frontend/src/components/Globe/Globe.jsx` / `Globe.css` for the bottom HUD strip.

## UI / UX baseline (Gotham — read before implementing)

Empty states belong **inside the sidebar filter surface** (the expanded `.filter-panel` region), not as random toast banners.

- **Panel chrome:** Reuse `.filter-panel` language — left accent bar via `.filter-panel::before`, borders `var(--line)`, text `var(--text-1)` / `var(--text-2)`, optional warning emphasis via **`--accent-warn`** (not one-off orange RGBA blocks).
- **Radius:** Use **`border-radius: 2px`** (sidebar cards) — avoid large `6px` “pill alert” corners unless matching an existing alert pattern (none today).
- **Globe info bar:** The bottom `.globe-info` strip already uses per-stat accent squares. If counts go to zero, prefer **muted `var(--text-3)` numerals** or subtle **`--accent-warn`** on the numeric span only — do not introduce a second competing HUD panel.

## Goal

When a filter returns zero results, show a helpful message in the Sidebar panel explaining why — not just silence.

## Implementation

### Sidebar Filter Empty States

In the `LayerItem` component within `Sidebar.jsx`, when `filterHook.filteredCount === 0` and the layer is active, show an empty state message below the filter panel:

```javascript
{isExpanded && filterHook && FilterPanel && (
  <>
    <FilterPanel filters={filterHook.filters} updateFilter={filterHook.updateFilter} />
    {filterHook.filteredCount === 0 && filterHook.rawCount > 0 && (
      <div className="filter-empty-state" role="status">
        <span>No results — try widening your filters</span>
      </div>
    )}
  </>
)}
```

### Empty State Messages Per Layer

**Planes**: "No aircraft match your filters. Try lowering altitude range or expanding speed."
**Ships**: "No vessels match your filters. Try enabling more ship types or lowering speed."
**Events**: "No events match your filters. Try selecting more categories or widening the date range."
**Conflicts**: "No conflict zones match your filters. Try lowering the intensity threshold."

Keep copy in **`var(--mono)`** or **`var(--sans)`** per sidebar body conventions; title-case vs ALL CAPS should match neighboring filter labels.

### Layer Toggle Empty States

When a layer is **off** and its count is 0, show a different message:
"Enable the [layer] layer to see data."

### Globe Info Bar

In the globe info bar, when `filteredPlanes.length === 0` (and similarly for other layers if surfaced there):
- If layer is on but filter returns 0: dim the count with `var(--text-3)` or apply **`--accent-warn`** only to the value span — subtle, not a full-width banner

## Files to Update

- `frontend/src/components/Sidebar/Sidebar.jsx` — add empty state messages in LayerItem
- `frontend/src/components/Sidebar/Sidebar.css` — empty state styling (token-driven)

```css
.filter-empty-state {
  margin-top: 10px;
  padding: 10px 12px 10px 16px;
  position: relative;
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: 2px;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.4px;
  line-height: 1.45;
  color: var(--text-1);
}

.filter-empty-state::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--accent-warn);
  opacity: 0.5;
  pointer-events: none;
}
```

## Verification

- [ ] Empty state message appears when filters return 0 results but raw data exists
- [ ] Each layer has its own contextual empty message
- [ ] Message disappears when filters are adjusted to return results
- [ ] Message does not appear when layer is toggled off (show layer-off copy instead)
- [ ] Message is readable, uses Gotham tokens, and does not blow out `.layer-item` height excessively
- [ ] Globe stat strip (if adjusted) stays visually consistent with existing HUD styling
