export function formatAltitude(feet) {
  return `${Math.round(feet)} ft`
}

export function formatSpeed(knots) {
  return `${knots.toFixed(1)} kts`
}

export function formatCoord(lat, lon) {
  const latDir = lat >= 0 ? 'N' : 'S'
  const lonDir = lon >= 0 ? 'E' : 'W'
  return `${Math.abs(lat).toFixed(4)}°${latDir}, ${Math.abs(lon).toFixed(4)}°${lonDir}`
}

export function formatTimestamp(ts) {
  return new Date(ts).toLocaleTimeString()
}
