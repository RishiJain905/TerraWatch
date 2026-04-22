import { useState } from 'react'
import { formatOptional, formatAltitude, formatSpeed, formatHeading, formatCoord, formatRelativeTime, copyToClipboard } from '../../utils/formatters'
import '../InfoPanel/infoPanel.css'
import './PlaneInfoPanel.css'

function formatAirport(routeAirport) {
  if (!routeAirport) return '—'

  const iata = routeAirport.iata?.trim()
  const icao = routeAirport.icao?.trim()
  const parts = []

  if (iata) parts.push(iata)
  if (icao) parts.push(icao)

  if (!parts.length) {
    return routeAirport.name?.trim() || '—'
  }

  return parts.join(' / ')
}

function formatFlightCode(route, key) {
  const iata = route?.[`${key}_iata`]?.trim()
  const icao = route?.[`${key}_icao`]?.trim()

  if (iata && icao) return `${iata} / ${icao}`
  if (iata || icao) return iata || icao
  return '—'
}

function formatAirline(route) {
  const name = route?.airline_name?.trim()
  const iata = route?.airline_iata?.trim()
  const icao = route?.airline_icao?.trim()
  const codeParts = [iata, icao].filter(Boolean)

  if (name && codeParts.length) {
    return `${name} (${codeParts.join(' / ')})`
  }

  if (name) return name
  if (codeParts.length) return codeParts.join(' / ')
  return '—'
}

function formatRouteStatus(routeStatus) {
  switch (routeStatus) {
    case 'loading':
      return 'Loading route...'
    case 'ok':
      return 'Resolved'
    case 'not_found':
      return 'Not available'
    case 'rate_limited':
      return 'Rate limited'
    case 'error':
      return 'Unavailable'
    default:
      return 'Not available'
  }
}

export default function PlaneInfoPanel({ plane, route, routeStatus, onClose }) {
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
          <span className="info-value">{formatRelativeTime(plane.timestamp)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Airline</span>
          <span className="info-value">{routeStatus === 'loading' ? 'Loading route...' : formatAirline(route)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Flight IATA/ICAO</span>
          <span className="info-value mono">{routeStatus === 'loading' ? 'Loading route...' : formatFlightCode(route, 'flight')}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Departure</span>
          <span className="info-value mono">{routeStatus === 'loading' ? 'Loading route...' : formatAirport(route?.departure)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Arrival</span>
          <span className="info-value mono">{routeStatus === 'loading' ? 'Loading route...' : formatAirport(route?.arrival)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Route status</span>
          <span className="info-value">{formatRouteStatus(routeStatus)}</span>
        </div>
      </div>
    </div>
  )
}
