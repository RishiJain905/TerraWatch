import '../InfoPanel/infoPanel.css'
import './ConflictInfoPanel.css'
import { formatOptional, formatTone, formatCoord } from '../../utils/formatters'

function formatDate(dateStr) {
  if (dateStr == null || dateStr === '') return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function toneBadgeClass(tone) {
  if (tone == null) return 'tone-neutral'
  if (tone < -2) return 'tone-negative'
  if (tone > 2) return 'tone-positive'
  return 'tone-neutral'
}

export default function ConflictInfoPanel({ conflict, onClose }) {
  if (!conflict) return null

  return (
    <div className="plane-info-panel" data-type="conflict">
      <div className="plane-info-header">
        <h3>
          <span className="type-glyph" aria-hidden="true" />
          {formatOptional(conflict.event_text, null, formatOptional(conflict.category, null, 'Conflict'))}
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
          <span className="info-value">{formatOptional(conflict.category, null, '—')}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Date</span>
          <span className="info-value">{formatDate(conflict.date)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Position</span>
          <span className="info-value mono">
            {formatCoord(conflict.lat, conflict.lon)}
          </span>
        </div>
        {conflict.source_url ? (
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
        ) : (
          <div className="info-row full-width">
            <span className="info-label">Source</span>
            <span className="info-value">—</span>
          </div>
        )}
      </div>
    </div>
  )
}
