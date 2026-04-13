# Phase 4.5 — Task 3: Filter UI in Sidebar

**Agent:** GLM 5.1 (frontend)
**Related overview:** `PHASE4_5_OVERVIEW.md`
**Prerequisites:** Task 2 (hooks) must be complete first

---

## Objective

Add collapsible filter panels to the Sidebar, one per data layer. Each panel contains all filter controls for that layer. Filters update the hook state in real-time (no apply button).

---

## Filter Panel Layout

The Sidebar currently has a list of layer toggles. Replace this with collapsible sections:

```
┌─────────────────────────┐
│ Data Layers         [−] │  ← always visible header
├─────────────────────────┤
│ ✈️ Aircraft       [−][+] │  ← collapsible, toggle + filter button
│   └─ Filters:          │
│      Altitude: ═══○═══  │
│      [====○====] 0-50k  │
│      Callsign: [____]   │
│      Speed: ═══○════    │
│      [===○======] 0kt   │
├─────────────────────────┤
│ 🚢 Maritime       [−][+] │
│   └─ Filters:          │
│      [■] Cargo          │
│      [■] Tanker         │
│      [■] Passenger      │
│      [ ] Fishing        │
│      Speed: ═══○═══     │
├─────────────────────────┤
│ 🌍 World Events   [−][+]│
│ ⚠️ Conflict Zones [−][+]│
└─────────────────────────┘
```

---

## Component Structure

### `Sidebar.jsx` Changes

```jsx
import { useState } from 'react'
import './Sidebar.css'

export default function Sidebar({ layers, onToggleLayer, filterHooks }) {
  // filterHooks = { planes, ships, events, conflicts }
  // Each has: filters, updateFilter
  const [expandedPanel, setExpandedPanel] = useState('planes') // which filter panel is open

  const layerConfig = [
    { key: 'planes',    label: 'Aircraft',       icon: '✈️', color: '#ff6464' },
    { key: 'ships',     label: 'Maritime',        icon: '🚢', color: '#64c8ff' },
    { key: 'events',    label: 'World Events',    icon: '🌍', color: '#ffc864' },
    { key: 'conflicts', label: 'Conflict Zones',  icon: '⚠️', color: '#ff3232' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Data Layers</h2>
      </div>
      <div className="layer-list">
        {layerConfig.map(layer => (
          <LayerItem
            key={layer.key}
            layer={layer}
            layers={layers}
            onToggleLayer={onToggleLayer}
            filterHook={filterHooks[layer.key]}
            isExpanded={expandedPanel === layer.key}
            onToggleExpand={() => setExpandedPanel(
              expandedPanel === layer.key ? null : layer.key
            )}
          />
        ))}
      </div>
    </aside>
  )
}
```

---

## Filter Controls Per Layer

### Planes Filter Panel

```jsx
function PlanesFilterPanel({ filters, updateFilter }) {
  return (
    <div className="filter-panel">
      {/* Altitude range dual slider */}
      <div className="filter-group">
        <label>Altitude (ft)</label>
        <div className="range-slider">
          <span>{filters.altitudeMin.toLocaleString()} ft</span>
          <input
            type="range"
            min={0} max={50000} step={1000}
            value={filters.altitudeMin}
            onChange={e => updateFilter('altitudeMin', Number(e.target.value))}
          />
          <input
            type="range"
            min={0} max={50000} step={1000}
            value={filters.altitudeMax}
            onChange={e => updateFilter('altitudeMax', Number(e.target.value))}
          />
          <span>{filters.altitudeMax.toLocaleString()} ft</span>
        </div>
      </div>

      {/* Callsign search */}
      <div className="filter-group">
        <label>Callsign</label>
        <input
          type="text"
          placeholder="e.g. UAL123"
          value={filters.callsign}
          onChange={e => updateFilter('callsign', e.target.value)}
        />
      </div>

      {/* Speed slider */}
      <div className="filter-group">
        <label>Min Speed (kt)</label>
        <input
          type="range"
          min={0} max={600} step={10}
          value={filters.speedMin}
          onChange={e => updateFilter('speedMin', Number(e.target.value))}
        />
        <span>{filters.speedMin} kt</span>
      </div>

      {/* Quick preset buttons */}
      <div className="filter-presets">
        <button onClick={() => {
          updateFilter('altitudeMin', 10000)
          updateFilter('altitudeMax', 50000)
        }}>High Alt Only</button>
        <button onClick={() => {
          updateFilter('altitudeMin', 0)
          updateFilter('altitudeMax', 10000)
        }}>Low Alt Only</button>
        <button onClick={() => {
          updateFilter('altitudeMin', 0)
          updateFilter('altitudeMax', 50000)
        }}>Reset</button>
      </div>
    </div>
  )
}
```

### Ships Filter Panel

```jsx
function ShipsFilterPanel({ filters, updateFilter }) {
  const shipTypes = ['cargo', 'tanker', 'passenger', 'fishing', 'other']

  const toggleType = (type) => {
    const current = filters.types
    if (current.includes(type)) {
      updateFilter('types', current.filter(t => t !== type))
    } else {
      updateFilter('types', [...current, type])
    }
  }

  return (
    <div className="filter-panel">
      {/* Type toggles */}
      <div className="filter-group">
        <label>Ship Types</label>
        <div className="checkbox-grid">
          {shipTypes.map(type => (
            <label key={type} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.types.includes(type)}
                onChange={() => toggleType(type)}
              />
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </label>
          ))}
        </div>
      </div>

      {/* Speed slider */}
      <div className="filter-group">
        <label>Min Speed (kt)</label>
        <input
          type="range"
          min={0} max={30} step={1}
          value={filters.speedMin}
          onChange={e => updateFilter('speedMin', Number(e.target.value))}
        />
        <span>{filters.speedMin} kt</span>
      </div>
    </div>
  )
}
```

### Events Filter Panel

```jsx
function EventsFilterPanel({ filters, updateFilter }) {
  const categories = [
    'diplomacy', 'statement', 'assault', 'fight',
    'mass_gvc', 'force', 'rioting', 'protest'
  ]

  const toggleCategory = (cat) => {
    const current = filters.categories
    if (current.includes(cat)) {
      updateFilter('categories', current.filter(c => c !== cat))
    } else {
      updateFilter('categories', [...current, cat])
    }
  }

  return (
    <div className="filter-panel">
      {/* Category toggles */}
      <div className="filter-group">
        <label>Categories</label>
        <div className="checkbox-grid">
          {categories.map(cat => (
            <label key={cat} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.categories.includes(cat)}
                onChange={() => toggleCategory(cat)}
              />
              {cat.replace('_', ' ')}
            </label>
          ))}
        </div>
      </div>

      {/* Tone range dual slider */}
      <div className="filter-group">
        <label>Tone Range</label>
        <div className="range-slider">
          <span>{filters.toneMin}</span>
          <input
            type="range"
            min={-10} max={10} step={1}
            value={filters.toneMin}
            onChange={e => updateFilter('toneMin', Number(e.target.value))}
          />
          <input
            type="range"
            min={-10} max={10} step={1}
            value={filters.toneMax}
            onChange={e => updateFilter('toneMax', Number(e.target.value))}
          />
          <span>{filters.toneMax}</span>
        </div>
      </div>

      {/* Date range dropdown */}
      <div className="filter-group">
        <label>Date Range</label>
        <select
          value={filters.dateRange}
          onChange={e => updateFilter('dateRange', e.target.value)}
        >
          <option value="all">All Time</option>
          <option value="24h">Last 24 Hours</option>
          <option value="48h">Last 48 Hours</option>
          <option value="7d">Last 7 Days</option>
        </select>
      </div>
    </div>
  )
}
```

### Conflicts Filter Panel

```jsx
function ConflictsFilterPanel({ filters, updateFilter }) {
  return (
    <div className="filter-panel">
      {/* Intensity slider */}
      <div className="filter-group">
        <label>Min Intensity</label>
        <input
          type="range"
          min={0} max={11} step={1}
          value={filters.intensityMin}
          onChange={e => updateFilter('intensityMin', Number(e.target.value))}
        />
        <span>{filters.intensityMin}</span>
      </div>

      {/* Date range dropdown */}
      <div className="filter-group">
        <label>Date Range</label>
        <select
          value={filters.dateRange}
          onChange={e => updateFilter('dateRange', e.target.value)}
        >
          <option value="all">All Time</option>
          <option value="24h">Last 24 Hours</option>
          <option value="48h">Last 48 Hours</parameter>
          <option value="7d">Last 7 Days</option>
        </select>
      </div>
    </div>
  )
}
```

---

## CSS Additions (`Sidebar.css`)

Add these styles:

```css
/* Collapsible panel */
.layer-item {
  /* existing styles... */
  flex-direction: column;
  align-items: stretch;
}

.layer-item.active {
  /* existing... */
}

.layer-item-header {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.expand-btn {
  margin-left: auto;
  font-size: 12px;
  opacity: 0.6;
}

/* Filter panel */
.filter-panel {
  padding: 12px 16px;
  background: rgba(0,0,0,0.2);
  border-radius: 0 0 8px 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-group label {
  font-size: 11px;
  text-transform: uppercase;
  opacity: 0.7;
}

.filter-group input[type="text"],
.filter-group select {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 4px;
  color: white;
  padding: 6px 8px;
  font-size: 13px;
}

.range-slider {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-slider input[type="range"] {
  flex: 1;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  cursor: pointer;
}

.filter-presets {
  display: flex;
  gap: 4px;
}

.filter-presets button {
  flex: 1;
  padding: 4px;
  font-size: 10px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 4px;
  color: white;
  cursor: pointer;
}
```

---

## App.jsx Changes

The Sidebar needs access to all filter hooks. Update `App.jsx` to pass filter hooks down:

```jsx
// In App.jsx
import { usePlanes, useShips, useEvents, useConflicts } from './hooks'

function App() {
  // ... existing state ...
  const planesHook = usePlanes()
  const shipsHook = useShips()
  const eventsHook = useEvents()
  const conflictsHook = useConflicts()

  const filterHooks = {
    planes: { filters: planesHook.filters, updateFilter: planesHook.updateFilter },
    ships: { filters: shipsHook.filters, updateFilter: shipsHook.updateFilter },
    events: { filters: eventsHook.filters, updateFilter: eventsHook.updateFilter },
    conflicts: { filters: conflictsHook.filters, updateFilter: conflictsHook.updateFilter },
  }

  return (
    <Sidebar
      layers={layers}
      onToggleLayer={toggleLayer}
      filterHooks={filterHooks}
    />
    // ... Globe and panels ...
  )
}
```

---

## Acceptance Criteria

- [ ] Each layer has a collapsible filter panel in the Sidebar
- [ ] Expanding one panel does not close others (optional: allow multiple)
- [ ] All filter controls are functional (sliders, text input, checkboxes, dropdown)
- [ ] Filters update data in real-time (no apply button needed)
- [ ] Filter state persists across layer toggle on/off
- [ ] Sidebar remains scrollable when many filters are open
- [ ] Quick preset buttons work on Planes panel
- [ ] Checkbox labels match actual data values (check with Task 1 research doc)
- [ ] Commit message: `Phase 4.5 Task 3: Add filter UI panels to Sidebar`
