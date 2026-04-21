export function formatOptional(value, formatter, fallback = '\u2014') {
  if (value == null || value === '') return fallback
  return formatter ? formatter(value) : value
}

export function formatAltitude(ft) {
  if (ft == null) return '\u2014'
  return `${Number(ft).toLocaleString()} ft`
}

export function formatSpeed(kt) {
  if (kt == null) return '\u2014'
  return `${Number(kt).toFixed(1)} kt`
}

export function formatCoord(lat, lon) {
  if (lat == null || lon == null) return '\u2014'
  const latDir = lat >= 0 ? 'N' : 'S'
  const lonDir = lon >= 0 ? 'E' : 'W'
  return `${Math.abs(lat).toFixed(4)}\u00B0${latDir}, ${Math.abs(lon).toFixed(4)}\u00B0${lonDir}`
}

export function formatTimestamp(ts) {
  if (ts == null) return '\u2014'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return '\u2014'
  return d.toLocaleTimeString()
}

// 0 heading = North; null/undefined = unknown
export function formatHeading(h) {
  if (h == null) return '\u2014'
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  const idx = Math.round(h / 45) % 8
  return `${Math.round(h)}\u00B0 ${dirs[idx]}`
}

export function formatTone(tone) {
  if (tone == null) return '\u2014'
  return tone.toFixed(2)
}

export function copyToClipboard(text) {
  return navigator.clipboard.writeText(text).catch(() => {
    // Fail silently — clipboard may be blocked (HTTP / permissions)
  })
}
