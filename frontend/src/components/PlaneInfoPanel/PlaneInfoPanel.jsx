import { useState } from 'react'
import { formatOptional, formatAltitude, formatSpeed, formatHeading, formatCoord, formatTimestamp, copyToClipboard } from '../../utils/formatters'
import '../InfoPanel/infoPanel.css'
import './PlaneInfoPanel.css'

export default function PlaneInfoPanel({ plane, onClose }) {
  if (!plane) return null

  const [copiedId, setCopiedId] = useState(null)

  const handleCopy = (id, text) => {
    copyToClipboard(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 1500)
  }

  return (
    <div className="plane-info-panel" data-type="plane">
      <div className="plane-info-header">
        <h3>
          <span className="type-glyph" aria-hidden="true" />
          {plane.callsign ?? plane.id ?? '—'}
        </h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      <div className="plane-info-grid">
        <div className="info-row">
          <span className="info-label">ICAO24</span>
          <span className="info-value mono">
            {formatOptional(plane.id, null, '—')}
            {plane.id && <button type="button" className={`copy-btn${copiedId === 'icao24' ? ' copied' : ''}`} onClick={() => handleCopy('icao24', plane.id)} aria-label="Copy ICAO24" title="Copy to clipboard">{copiedId === 'icao24' ? 'COPIED!' : 'COPY'}</button>}
          </span>
        </div>
        <div className="info-row">
          <span className="info-label">Callsign</span>
          <span className="info-value">
            {formatOptional(plane.callsign, null, '—')}
            {plane.callsign && <button type="button" className={`copy-btn${copiedId === 'callsign' ? ' copied' : ''}`} onClick={() => handleCopy('callsign', plane.callsign)} aria-label="Copy callsign" title="Copy to clipboard">{copiedId === 'callsign' ? 'COPIED!' : 'COPY'}</button>}
          </span>
        </div>
        <div className="info-row">
          <span className="info-label">Altitude</span>
          <span className="info-value">{formatAltitude(plane.alt)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Speed</span>
          <span className="info-value">{formatSpeed(plane.speed)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Heading</span>
          {/* 0 heading = North; null/undefined = unknown */}
          <span className="info-value">{formatHeading(plane.heading)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Squawk</span>
          <span className="info-value mono">{formatOptional(plane.squawk, null, '—')}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Position</span>
          <span className="info-value mono">{formatCoord(plane.lat, plane.lon)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Last Contact</span>
          <span className="info-value">{formatTimestamp(plane.last_contact)}</span>
        </div>
      </div>
    </div>
  )
}
