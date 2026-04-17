import '../InfoPanel/infoPanel.css'
import './PlaneInfoPanel.css'

export default function PlaneInfoPanel({ plane, onClose }) {
  if (!plane) return null

  const formatAlt = (alt) => {
    if (!alt && alt !== 0) return '—'
    return `${alt.toLocaleString()} FT`
  }

  const formatSpeed = (speed) => {
    if (!speed && speed !== 0) return '—'
    return `${speed.toFixed(0)} KT`
  }

  const formatHeading = (h) => {
    if (!h && h !== 0) return '—'
    const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    const idx = Math.round(h / 45) % 8
    return `${h.toFixed(0)}° ${dirs[idx]}`
  }

  return (
    <div className="plane-info-panel" data-type="plane">
      <div className="plane-info-header">
        <h3>
          <span className="type-glyph" aria-hidden="true" />
          {plane.callsign || plane.id}
        </h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      <div className="plane-info-grid">
        <div className="info-row">
          <span className="info-label">ICAO24</span>
          <span className="info-value mono">{plane.id}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Callsign</span>
          <span className="info-value">{plane.callsign || '—'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Altitude</span>
          <span className="info-value">{formatAlt(plane.alt)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Speed</span>
          <span className="info-value">{formatSpeed(plane.speed)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Heading</span>
          <span className="info-value">{formatHeading(plane.heading)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Squawk</span>
          <span className="info-value mono">{plane.squawk || '—'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Position</span>
          <span className="info-value mono">
            {plane.lat?.toFixed(4)}°, {plane.lon?.toFixed(4)}°
          </span>
        </div>
      </div>
    </div>
  )
}
