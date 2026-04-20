import '../InfoPanel/infoPanel.css'
import './ShipInfoPanel.css'
import { formatOptional, formatSpeed, formatHeading, formatCoord } from '../../utils/formatters'
import { SHIP_TYPE_COLORS } from '../../utils/shipIcons'

function formatLastSeen(timestamp) {
  if (timestamp == null) return '—'
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  if (isNaN(then)) return '—'
  const diffSec = Math.max(0, Math.floor((now - then) / 1000))
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  return `${diffHr}h ago`
}

export default function ShipInfoPanel({ ship, onClose }) {
  if (!ship) return null

  const typeColor = SHIP_TYPE_COLORS[ship.ship_type]?.hex || SHIP_TYPE_COLORS.other?.hex

  return (
    <div className="ship-info-panel" data-type="ship">
      <div className="ship-info-header">
        <h3>
          <span className="ship-type-dot" style={{ backgroundColor: typeColor }}></span>
          {ship.name || `MMSI ${ship.id}`}
        </h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      <div className="ship-info-grid">
        <div className="info-row">
          <span className="info-label">MMSI</span>
          <span className="info-value mono">{formatOptional(ship.id, null, '—')}</span>
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
          <span className="info-value">{formatLastSeen(ship.timestamp)}</span>
        </div>
      </div>
    </div>
  )
}
