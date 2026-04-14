import { useState } from 'react'
import './Sidebar.css'

function PlanesFilterPanel({ filters, updateFilter }) {
  const fmt = (v) => Number(v).toLocaleString()

  return (
    <div className="filter-panel">
      <div className="filter-group">
        <label>Min Altitude</label>
        <div className="range-slider">
          <input
            type="range"
            min={0}
            max={50000}
            step={1000}
            value={filters.altitudeMin}
            onChange={(e) => updateFilter('altitudeMin', Number(e.target.value))}
          />
          <span>{fmt(filters.altitudeMin)} ft</span>
        </div>
      </div>
      <div className="filter-group">
        <label>Max Altitude</label>
        <div className="range-slider">
          <input
            type="range"
            min={0}
            max={50000}
            step={1000}
            value={filters.altitudeMax}
            onChange={(e) => updateFilter('altitudeMax', Number(e.target.value))}
          />
          <span>{fmt(filters.altitudeMax)} ft</span>
        </div>
      </div>
      <div className="filter-group">
        <label>Callsign</label>
        <input
          type="text"
          value={filters.callsign}
          placeholder="e.g. UAL123"
          onChange={(e) => updateFilter('callsign', e.target.value)}
        />
      </div>
      <div className="filter-group">
        <label>Min Speed</label>
        <div className="range-slider">
          <input
            type="range"
            min={0}
            max={600}
            step={10}
            value={filters.speedMin}
            onChange={(e) => updateFilter('speedMin', Number(e.target.value))}
          />
          <span>{filters.speedMin} kt</span>
        </div>
      </div>
      <div className="filter-presets">
        <button onClick={() => { updateFilter('altitudeMin', 10000); updateFilter('altitudeMax', 50000) }}>
          High Alt Only
        </button>
        <button onClick={() => { updateFilter('altitudeMin', 0); updateFilter('altitudeMax', 10000) }}>
          Low Alt Only
        </button>
        <button onClick={() => { updateFilter('altitudeMin', 0); updateFilter('altitudeMax', 50000) }}>
          Reset
        </button>
      </div>
    </div>
  )
}

function ShipsFilterPanel({ filters, updateFilter }) {
  const shipTypes = ['cargo', 'tanker', 'passenger', 'fishing', 'other']

  const toggleType = (type) => {
    const current = filters.types
    if (current.includes(type)) {
      updateFilter('types', current.filter((t) => t !== type))
    } else {
      updateFilter('types', [...current, type])
    }
  }

  return (
    <div className="filter-panel">
      <div className="filter-group">
        <label>Ship Type</label>
        <div className="checkbox-grid">
          {shipTypes.map((type) => (
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
      <div className="filter-group">
        <label>Min Speed</label>
        <div className="range-slider">
          <input
            type="range"
            min={0}
            max={30}
            step={1}
            value={filters.speedMin}
            onChange={(e) => updateFilter('speedMin', Number(e.target.value))}
          />
          <span>{filters.speedMin} kt</span>
        </div>
      </div>
    </div>
  )
}

const EVENT_CATEGORIES = [
  'diplomacy', 'material_help', 'train', 'yield', 'demonstrate',
  'assault', 'fight', 'unconventional_mass_gvc', 'conventional_mass_gvc',
  'force_range', 'protest', 'government_debate', 'rioting', 'disaster',
  'health', 'weather'
]

function formatCategory(cat) {
  return cat.charAt(0).toUpperCase() + cat.slice(1).replace(/_/g, ' ')
}

function EventsFilterPanel({ filters, updateFilter }) {
  const toggleCategory = (cat) => {
    const current = filters.categories
    if (current.includes(cat)) {
      updateFilter('categories', current.filter((c) => c !== cat))
    } else {
      updateFilter('categories', [...current, cat])
    }
  }

  return (
    <div className="filter-panel">
      <div className="filter-group">
        <label>Categories</label>
        <div className="checkbox-grid">
          {EVENT_CATEGORIES.map((cat) => (
            <label key={cat} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.categories.includes(cat)}
                onChange={() => toggleCategory(cat)}
              />
              {formatCategory(cat)}
            </label>
          ))}
        </div>
      </div>
      <div className="filter-group">
        <label>Min Tone</label>
        <div className="range-slider">
          <input
            type="range"
            min={-10}
            max={10}
            step={1}
            value={filters.toneMin}
            onChange={(e) => updateFilter('toneMin', Number(e.target.value))}
          />
          <span>{filters.toneMin}</span>
        </div>
      </div>
      <div className="filter-group">
        <label>Max Tone</label>
        <div className="range-slider">
          <input
            type="range"
            min={-10}
            max={10}
            step={1}
            value={filters.toneMax}
            onChange={(e) => updateFilter('toneMax', Number(e.target.value))}
          />
          <span>{filters.toneMax}</span>
        </div>
      </div>
      <div className="filter-group">
        <label>Date Range</label>
        <select
          value={filters.dateRange}
          onChange={(e) => updateFilter('dateRange', e.target.value)}
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

function ConflictsFilterPanel({ filters, updateFilter }) {
  return (
    <div className="filter-panel">
      <div className="filter-group">
        <label>Min Intensity</label>
        <div className="range-slider">
          <input
            type="range"
            min={0}
            max={11}
            step={1}
            value={filters.intensityMin}
            onChange={(e) => updateFilter('intensityMin', Number(e.target.value))}
          />
          <span>{filters.intensityMin}</span>
        </div>
      </div>
      <div className="filter-group">
        <label>Date Range</label>
        <select
          value={filters.dateRange}
          onChange={(e) => updateFilter('dateRange', e.target.value)}
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

const FILTER_PANELS = {
  planes: PlanesFilterPanel,
  ships: ShipsFilterPanel,
  events: EventsFilterPanel,
  conflicts: ConflictsFilterPanel,
}

function LayerItem({ layer, isActive, onToggleLayer, isExpanded, onToggleExpand, filterHook }) {
  const FilterPanel = FILTER_PANELS[layer.key]

  return (
    <div className={`layer-item ${isActive ? 'active' : ''}`}>
      <div className="layer-item-header">
        <span className="layer-icon">{layer.icon}</span>
        <span className="layer-label">
          {layer.label}
          {filterHook?.rawCount != null && (
            <span className="layer-count">
              {filterHook.filteredCount === filterHook.rawCount
                ? filterHook.rawCount.toLocaleString()
                : `${filterHook.filteredCount.toLocaleString()} / ${filterHook.rawCount.toLocaleString()}`}
            </span>
          )}
        </span>
        <div
          className="layer-toggle"
          style={{ '--toggle-color': layer.color }}
          onClick={(e) => { e.stopPropagation(); onToggleLayer(layer.key) }}
        >
          <div className="toggle-knob" />
        </div>
        <button
          className="expand-btn"
          onClick={(e) => { e.stopPropagation(); onToggleExpand(layer.key) }}
        >
          {isExpanded ? '▾' : '▸'}
        </button>
      </div>
      {isExpanded && filterHook && FilterPanel && (
        <FilterPanel filters={filterHook.filters} updateFilter={filterHook.updateFilter} />
      )}
    </div>
  )
}

export default function Sidebar({ layers, onToggleLayer, filterHooks }) {
  const [expandedPanels, setExpandedPanels] = useState({
    planes: false,
    ships: false,
    events: false,
    conflicts: false,
  })

  const layerConfig = [
    { key: 'planes', label: 'Aircraft', icon: '✈️', color: '#ff6464' },
    { key: 'ships', label: 'Maritime', icon: '🚢', color: '#64c8ff' },
    { key: 'events', label: 'World Events', icon: '🌍', color: '#ffc864' },
    { key: 'conflicts', label: 'Conflict Zones', icon: '⚠️', color: '#ff3232' },
  ]

  const toggleExpand = (key) => {
    setExpandedPanels((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Data Layers</h2>
      </div>
      <div className="layer-list">
        {layerConfig.map((layer) => (
          <LayerItem
            key={layer.key}
            layer={layer}
            isActive={layers[layer.key]}
            onToggleLayer={onToggleLayer}
            isExpanded={expandedPanels[layer.key]}
            onToggleExpand={toggleExpand}
            filterHook={filterHooks?.[layer.key] ?? null}
          />
        ))}
      </div>
      <div className="sidebar-footer">
        <p className="phase-label">Phase 4 of 7</p>
      </div>
    </aside>
  )
}
