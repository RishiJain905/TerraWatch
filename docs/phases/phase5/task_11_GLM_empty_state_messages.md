# Phase 5 — Task 11: Empty State Messages

## Context

Read `frontend/src/components/Sidebar/Sidebar.jsx` and `frontend/src/components/Globe/Globe.jsx`.

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
      <div className="filter-empty-state">
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

### Layer Toggle Empty States

When a layer is **off** and its count is 0, show a different message:
"Enable the [layer] layer to see data."

### Globe Info Bar

In the globe info bar, when `filteredPlanes.length === 0`, show a subtle indicator:
- If layer is on but filter returns 0: dim the count number or show it in orange

## Files to Update

- `frontend/src/components/Sidebar/Sidebar.jsx` — add empty state messages in LayerItem
- `frontend/src/components/Sidebar/Sidebar.css` — empty state styling

```css
.filter-empty-state {
  padding: 8px 12px;
  margin-top: 8px;
  background: rgba(255, 200, 100, 0.1);
  border: 1px solid rgba(255, 200, 100, 0.3);
  border-radius: 6px;
  font-size: 12px;
  color: rgba(255, 200, 100, 0.9);
}
```

## Verification

- [ ] Empty state message appears when filters return 0 results
- [ ] Each layer has its own contextual empty message
- [ ] Message disappears when filters are adjusted to return results
- [ ] Message does not appear when layer is toggled off
- [ ] Message is readable but not obtrusive
