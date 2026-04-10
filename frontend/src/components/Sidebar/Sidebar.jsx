import './Sidebar.css'

export default function Sidebar({ layers, onToggleLayer }) {
  const layerConfig = [
    { key: 'planes', label: 'Aircraft', icon: '✈️', color: '#ff6464' },
    { key: 'ships', label: 'Maritime', icon: '🚢', color: '#64c8ff' },
    { key: 'events', label: 'World Events', icon: '🌍', color: '#ffc864' },
    { key: 'conflicts', label: 'Conflict Zones', icon: '⚠️', color: '#ff3232' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Data Layers</h2>
      </div>
      <div className="layer-list">
        {layerConfig.map(layer => (
          <div
            key={layer.key}
            className={`layer-item ${layers[layer.key] ? 'active' : ''}`}
            onClick={() => onToggleLayer(layer.key)}
          >
            <span className="layer-icon">{layer.icon}</span>
            <span className="layer-label">{layer.label}</span>
            <div
              className="layer-toggle"
              style={{ '--toggle-color': layer.color }}
            >
              <div className="toggle-knob" />
            </div>
          </div>
        ))}
      </div>
      <div className="sidebar-footer">
        <p className="phase-label">Phase 1 of 7</p>
      </div>
    </aside>
  )
}
