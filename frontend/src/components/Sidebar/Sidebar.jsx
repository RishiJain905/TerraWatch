import { useState, useEffect } from 'react'
import './Sidebar.css'

function PlaneIcon() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinecap="square" strokeLinejoin="miter" aria-hidden="true">
      <path d="M8 1.5 L9 6.5 L14.5 9 L14.5 10.5 L9 9.5 L8.5 13 L10.5 14 L10.5 14.5 L8 14 L5.5 14.5 L5.5 14 L7.5 13 L7 9.5 L1.5 10.5 L1.5 9 L7 6.5 Z" />
    </svg>
  )
}

function ShipIcon() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinecap="square" strokeLinejoin="miter" aria-hidden="true">
      <path d="M2 10.5 L14 10.5 L12.5 13.5 L3.5 13.5 Z" />
      <path d="M5 10.5 L5 5.5 L11 5.5 L11 10.5" />
      <path d="M8 2.5 L8 5.5" />
      <path d="M6.5 3.5 L9.5 3.5" />
    </svg>
  )
}

function GlobeIcon() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinecap="square" strokeLinejoin="miter" aria-hidden="true">
      <circle cx="8" cy="8" r="6" />
      <ellipse cx="8" cy="8" rx="3" ry="6" />
      <path d="M2 8 L14 8" />
    </svg>
  )
}

function WarningIcon() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinecap="square" strokeLinejoin="miter" aria-hidden="true">
      <path d="M8 2 L14.5 13.5 L1.5 13.5 Z" />
      <path d="M8 6.5 L8 10" />
      <path d="M8 11.5 L8 12" />
    </svg>
  )
}

function CaretIcon({ open }) {
  return (
    <svg viewBox="0 0 10 10" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinecap="square" aria-hidden="true" style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 120ms ease' }}>
      <path d="M3.5 2 L7 5 L3.5 8" />
    </svg>
  )
}

function formatAge(sec) {
  if (sec < 60) return `${sec}s ago`
  const m = Math.floor(sec / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  return `${h}h ago`
}

function FreshnessIndicator({ lastUpdated, staleThreshold }) {
  const [now, setNow] = useState(Date.now())

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 10000)
    return () => clearInterval(timer)
  }, [])

  const ageMs = lastUpdated != null ? now - lastUpdated : null
  const ageSec = ageMs !== null ? Math.floor(ageMs / 1000) : null

  let label, dotClass, textClass
  if (ageSec === null) {
    label = 'NO DATA'; dotClass = 'none'; textClass = 'none'
  } else if (ageSec < 30) {
    label = 'LIVE'; dotClass = 'live'; textClass = 'live'
  } else if (ageSec < staleThreshold) {
    label = formatAge(ageSec); dotClass = 'age'; textClass = 'age'
  } else {
    label = 'STALE'; dotClass = 'stale'; textClass = 'stale'
  }

  return (
    <span className="layer-freshness">
      <span className={`freshness-dot ${dotClass}`} aria-hidden="true" />
      <span className={`freshness-text ${textClass}`}>{label}</span>
    </span>
  )
}

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
          <span className="range-value">{fmt(filters.altitudeMin)} FT</span>
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
          <span className="range-value">{fmt(filters.altitudeMax)} FT</span>
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
          <span className="range-value">{filters.speedMin} KT</span>
        </div>
      </div>
      <div className="filter-presets">
        <button onClick={() => { updateFilter('altitudeMin', 10000); updateFilter('altitudeMax', 50000) }}>
          High Alt
        </button>
        <button onClick={() => { updateFilter('altitudeMin', 0); updateFilter('altitudeMax', 10000) }}>
          Low Alt
        </button>
        <button className="preset-reset" onClick={() => { updateFilter('altitudeMin', 0); updateFilter('altitudeMax', 50000) }}>
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
              <span className="checkbox-box" aria-hidden="true" />
              <span className="checkbox-text">{type.charAt(0).toUpperCase() + type.slice(1)}</span>
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
          <span className="range-value">{filters.speedMin} KT</span>
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
              <span className="checkbox-box" aria-hidden="true" />
              <span className="checkbox-text">{formatCategory(cat)}</span>
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
          <span className="range-value">{filters.toneMin}</span>
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
          <span className="range-value">{filters.toneMax}</span>
        </div>
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
          <span className="range-value">{filters.intensityMin}</span>
        </div>
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

function LayerCount({ hook }) {
  if (!hook || hook.rawCount == null) return null
  const { filteredCount, rawCount } = hook
  if (filteredCount === rawCount) {
    return <span className="layer-count mono"><span className="count-filtered">{rawCount.toLocaleString()}</span></span>
  }
  return (
    <span className="layer-count mono">
      <span className="count-filtered">{filteredCount.toLocaleString()}</span>
      <span className="count-sep">/</span>
      <span className="count-raw">{rawCount.toLocaleString()}</span>
    </span>
  )
}

function LayerItem({ layer, isActive, onToggleLayer, isExpanded, onToggleExpand, filterHook }) {
  const FilterPanel = FILTER_PANELS[layer.key]
  const Icon = layer.Icon

  return (
    <div
      className={`layer-item ${isActive ? 'active' : ''} ${isExpanded ? 'expanded' : ''}`}
      style={{ '--accent': layer.color }}
    >
      <div
        className="layer-item-header"
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        onClick={() => onToggleExpand(layer.key)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onToggleExpand(layer.key)
          }
        }}
      >
        <span className="layer-icon"><Icon /></span>
        <span className="layer-label-block">
          <span className="layer-label">{layer.label}</span>
          <LayerCount hook={filterHook} />
          <FreshnessIndicator lastUpdated={filterHook?.lastUpdated ?? null} staleThreshold={filterHook?.staleThreshold ?? 3600} />
        </span>
        <button
          type="button"
          className="layer-toggle"
          aria-pressed={isActive}
          aria-label={`${layer.label} layer`}
          onClick={(e) => { e.stopPropagation(); onToggleLayer(layer.key) }}
        >
          <span className="toggle-cell toggle-on" aria-hidden="true">ON</span>
          <span className="toggle-cell toggle-off" aria-hidden="true">OFF</span>
        </button>
        <button
          className="expand-btn"
          aria-label={isExpanded ? 'Collapse filters' : 'Expand filters'}
          onClick={(e) => { e.stopPropagation(); onToggleExpand(layer.key) }}
        >
          <CaretIcon open={isExpanded} />
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
    { key: 'planes', label: 'Aircraft', Icon: PlaneIcon, color: 'var(--accent-air)' },
    { key: 'ships', label: 'Maritime', Icon: ShipIcon, color: 'var(--accent-sea)' },
    { key: 'events', label: 'World Events', Icon: GlobeIcon, color: 'var(--accent-evt)' },
    { key: 'conflicts', label: 'Conflict Zones', Icon: WarningIcon, color: 'var(--accent-cnf)' },
  ]

  const toggleExpand = (key) => {
    setExpandedPanels((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const activeCount = Object.values(layers).filter(Boolean).length
  const totalCount = layerConfig.length

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-header-row">
          <span className="sidebar-header-mark" aria-hidden="true" />
          <h2>Data Layers</h2>
        </div>
        <div className="sidebar-header-meta mono">
          <span className="meta-dot" aria-hidden="true" />
          <span>ONLINE</span>
          <span className="meta-sep">·</span>
          <span>{activeCount}/{totalCount} STREAMS</span>
        </div>
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
        <span className="footer-pulse" aria-hidden="true" />
        <span className="footer-label mono">BUILD</span>
        <span className="footer-value mono">5/7</span>
        <span className="footer-sep">·</span>
        <span className="footer-version mono">v0.5.0</span>
      </div>
    </aside>
  )
}
