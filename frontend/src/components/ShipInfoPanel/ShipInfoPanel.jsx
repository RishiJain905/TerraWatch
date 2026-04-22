import { useState } from 'react'
import '../InfoPanel/infoPanel.css'
import './ShipInfoPanel.css'
import { formatOptional, formatSpeed, formatHeading, formatCoord, formatRelativeTime, copyToClipboard } from '../../utils/formatters'
import { SHIP_TYPE_COLORS } from '../../utils/shipIcons'

export default function ShipInfoPanel({ ship, onClose }) {
  if (!ship) return null

  const [copiedId, setCopiedId] = useState(null)
  const shipTitle = formatOptional(ship.name, null, ship.id ? `MMSI ${ship.id}` : 'Unknown vessel')

  const handleCopy = (id, text) => {
    copyToClipboard(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 1500)
  }

  const typeColor = SHIP_TYPE_COLORS[ship.ship_type]?.hex || SHIP_TYPE_COLORS.other?.hex

  return (
    <div className="ship-info-panel" data-type="ship">
      <div className="ship-info-header">
        <h3>
          <span className="ship-type-dot" style={{ backgroundColor: typeColor }}></span>
          {shipTitle}
        </h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      <div className="ship-info-grid">
        <div className="info-row">
          <span className="info-label">MMSI</span>
          <span className="info-value mono">
            {formatOptional(ship.id, null, '—')}
            {ship.id && <button type="button" className={`copy-btn${copiedId === 'mmsi' ? ' copied' : ''}`} onClick={() => handleCopy('mmsi', ship.id)} aria-label="Copy MMSI" title="Copy to clipboard">{copiedId === 'mmsi' ? 'COPIED!' : 'COPY'}</button>}
          </span>
        </div>
        <div className="info-row">
          <span className="info-label">Type</span>
          <span className="info-value">
            <span className="ship-type-badge" style={{ backgroundColor: typeColor }}>
              {(ship.ship_type || 'unknown').charAt(0).toUpperCase() + (ship.ship_type || 'unknown').slice(1)}
            </span>
          </span>
        </div>
        <div className="info-row">
          <span className="info-label">Heading</span>
          <span className="info-value">{formatHeading(ship.heading)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Speed</span>
          <span className="info-value">{formatSpeed(ship.speed)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Destination</span>
          <span className="info-value">{formatOptional(ship.destination, null, '—')}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Position</span>
          <span className="info-value mono">{formatCoord(ship.lat, ship.lon)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Last Seen</span>
          <span className="info-value">{formatRelativeTime(ship.timestamp)}</span>
        </div>
      </div>
    </div>
  )
}
