import { useEffect, useState } from 'react'
import './Header.css'

function formatUtc(d) {
  const hh = String(d.getUTCHours()).padStart(2, '0')
  const mm = String(d.getUTCMinutes()).padStart(2, '0')
  const ss = String(d.getUTCSeconds()).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

function formatUtcDate(d) {
  const y = d.getUTCFullYear()
  const mo = String(d.getUTCMonth() + 1).padStart(2, '0')
  const da = String(d.getUTCDate()).padStart(2, '0')
  return `${y}-${mo}-${da}`
}

function statusLabel(s) {
  switch (s) {
    case 'ok': return 'LINK'
    case 'checking': return 'SYNC'
    case 'error': return 'DOWN'
    default: return String(s || '').toUpperCase()
  }
}

export default function Header({ backendStatus }) {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className="header">
      <div className="header-left">
        <span className="logo-mark" aria-hidden="true" />
        <h1 className="logo">TERRAWATCH</h1>
        <span className="logo-divider" aria-hidden="true" />
        <span className="subtitle mono">// LIVE GEOINT PLATFORM</span>
      </div>
      <div className="header-right">
        <div className="header-chip clock" aria-label="Current UTC time">
          <span className="chip-label">UTC</span>
          <span className="chip-value mono">{formatUtc(now)}</span>
          <span className="chip-sep">·</span>
          <span className="chip-sub mono">{formatUtcDate(now)}</span>
        </div>
        <div className={`header-chip status status-${backendStatus}`} aria-live="polite">
          <span className="status-square" aria-hidden="true" />
          <span className="chip-label">BACKEND</span>
          <span className="chip-value mono">{statusLabel(backendStatus)}</span>
        </div>
      </div>
    </header>
  )
}
