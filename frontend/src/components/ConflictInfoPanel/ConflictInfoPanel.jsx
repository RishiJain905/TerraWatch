import './ConflictInfoPanel.css'

function fatalitiesBadgeClass(fatalities) {
  if (fatalities == null) return 'fatalities-zero'
  if (fatalities > 10) return 'fatalities-high'
  if (fatalities >= 1) return 'fatalities-medium'
  return 'fatalities-zero'
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export default function ConflictInfoPanel({ conflict, onClose }) {
  if (!conflict) return null

  return (
    <div className="plane-info-panel">
      <div className="plane-info-header">
        <h3>{conflict.event_type || 'Conflict'}</h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      <div className="plane-info-grid">
        <div className="info-row">
          <span className="info-label">Fatalities</span>
          <span className="info-value">
            <span className={`fatalities-badge ${fatalitiesBadgeClass(conflict.fatalities)}`}>
              {conflict.fatalities ?? 0}
            </span>
          </span>
        </div>
        <div className="info-row">
          <span className="info-label">Country</span>
          <span className="info-value">{conflict.country || '—'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Region</span>
          <span className="info-value">{conflict.region || '—'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Date</span>
          <span className="info-value">{formatDate(conflict.date)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Position</span>
          <span className="info-value mono">
            {conflict.lat?.toFixed(4)}°, {conflict.lon?.toFixed(4)}°
          </span>
        </div>
      </div>
    </div>
  )
}
