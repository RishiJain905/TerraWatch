import '../InfoPanel/infoPanel.css'
import './ConflictInfoPanel.css'

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

function formatTone(tone) {
  if (tone == null) return '—'
  return tone.toFixed(2)
}

function toneBadgeClass(tone) {
  if (tone == null) return 'tone-neutral'
  if (tone < -2) return 'tone-negative'
  if (tone > 2) return 'tone-positive'
  return 'tone-neutral'
}

function formatPosition(lat, lon) {
  if (lat == null || lon == null) return '—'
  return `${lat.toFixed(4)}°, ${lon.toFixed(4)}°`
}

export default function ConflictInfoPanel({ conflict, onClose }) {
  if (!conflict) return null

  return (
    <div className="plane-info-panel" data-type="conflict">
      <div className="plane-info-header">
        <h3>
          <span className="type-glyph" aria-hidden="true" />
          {conflict.event_text || conflict.category || 'Conflict'}
        </h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      <div className="plane-info-grid">
        <div className="info-row">
          <span className="info-label">Tone</span>
          <span className="info-value">
            <span className={`tone-badge ${toneBadgeClass(conflict.tone)}`}>
              {formatTone(conflict.tone)}
            </span>
          </span>
        </div>
        <div className="info-row">
          <span className="info-label">Category</span>
          <span className="info-value">{conflict.category || '—'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Date</span>
          <span className="info-value">{formatDate(conflict.date)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Position</span>
          <span className="info-value mono">
            {formatPosition(conflict.lat, conflict.lon)}
          </span>
        </div>
        {conflict.source_url && (
          <div className="info-row full-width">
            <a
              className="source-link"
              href={conflict.source_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              VIEW SOURCE →
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
