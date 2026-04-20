import '../InfoPanel/infoPanel.css'
import './EventInfoPanel.css'
import { formatOptional, formatTone, formatCoord } from '../../utils/formatters'

function toneBadgeClass(tone) {
  if (tone == null) return 'tone-neutral'
  if (tone < -2) return 'tone-negative'
  if (tone > 2) return 'tone-positive'
  return 'tone-neutral'
}

function formatDate(dateStr) {
  if (dateStr == null || dateStr === '') return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function EventInfoPanel({ event, onClose }) {
  if (!event) return null

  return (
    <div className="plane-info-panel" data-type="event">
      <div className="plane-info-header">
        <h3>
          <span className="type-glyph" aria-hidden="true" />
          Event
        </h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      <div className="plane-info-grid">
        <div className="info-row full-width">
          <span className="info-value event-text">{formatOptional(event.event_text, null, '—')}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Tone</span>
          <span className="info-value">
            <span className={`tone-badge ${toneBadgeClass(event.tone)}`}>
              {formatTone(event.tone)}
            </span>
          </span>
        </div>
        <div className="info-row">
          <span className="info-label">Category</span>
          <span className="info-value">{formatOptional(event.category, null, '—')}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Date</span>
          <span className="info-value">{formatDate(event.date)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Position</span>
          <span className="info-value mono">
            {formatCoord(event.lat, event.lon)}
          </span>
        </div>
        {event.source_url ? (
          <div className="info-row full-width">
            <a
              className="source-link"
              href={event.source_url}
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
