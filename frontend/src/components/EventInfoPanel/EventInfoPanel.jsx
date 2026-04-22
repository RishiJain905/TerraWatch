import { useState } from 'react'
import '../InfoPanel/infoPanel.css'
import './EventInfoPanel.css'
import { formatOptional, formatTone, formatCoord, formatRelativeTime, copyToClipboard } from '../../utils/formatters'

function toneBadgeClass(tone) {
  if (tone == null) return 'tone-neutral'
  if (tone < -2) return 'tone-negative'
  if (tone > 2) return 'tone-positive'
  return 'tone-neutral'
}

export default function EventInfoPanel({ event, onClose }) {
  if (!event) return null

  const [copiedId, setCopiedId] = useState(null)

  const handleCopy = (id, text) => {
    copyToClipboard(text).then(() => {
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 1500)
    })
  }

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
          <span className="info-label">ID</span>
          <span className="info-value mono">
            {formatOptional(event.id?.replace(/^gdelt_/, ''), null, '—')}
            {event.id && (
              <button
                type="button"
                className={`copy-btn${copiedId === 'event-id' ? ' copied' : ''}`}
                onClick={() => handleCopy('event-id', event.id.replace(/^gdelt_/, ''))}
                aria-label="Copy event ID"
                title="Copy to clipboard"
              >
                {copiedId === 'event-id' ? 'COPIED!' : 'COPY'}
              </button>
            )}
          </span>
        </div>
        <div className="info-row">
          <span className="info-label">Date</span>
          <span className="info-value">{formatRelativeTime(event.date)}</span>
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
              className="info-external-link"
              href={event.source_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="View source (opens in new tab)"
            >
              View source <span aria-hidden="true">↗</span>
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
