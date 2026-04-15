/**
 * terminator.js — Solar terminator calculations using NOAA solar equations.
 *
 * Provides:
 *   getTerminatorPolygon(date) → [lon, lat][] forming the night-side polygon
 *   isNightSide(lon, lat, date) → boolean convenience wrapper
 */

const DEG = Math.PI / 180
const RAD = 180 / Math.PI

// ── helpers ────────────────────────────────────────────────────────────────

/** Day of year (1-366) */
function getDayOfYear(date) {
  const start = new Date(date.getUTCFullYear(), 0, 0)
  const diff = date - start
  return Math.floor(diff / 86400000) + 1
}

/** Solar declination in radians: δ = -23.45° × cos(2π/365 × (d + 10)) */
function getSolarDeclination(date) {
  const doy = getDayOfYear(date)
  return -23.45 * DEG * Math.cos((2 * Math.PI / 365) * (doy + 10))
}

/** Subsolar longitude in degrees: ~15°/hour west from 0° at 12:00 UTC */
function getSubsolarLongitude(date) {
  const hours = date.getUTCHours() + date.getUTCMinutes() / 60 + date.getUTCSeconds() / 3600
  return (12 - hours) * 15
}

/**
 * Solar elevation angle — returns sin(elevation).
 * sin(elev) = sin(lat)*sin(dec) + cos(lat)*cos(dec)*cos(hourAngle)
 *
 * @param {number} lonDeg  — longitude in degrees
 * @param {number} latDeg  — latitude in degrees
 * @param {number} decRad — solar declination in radians
 * @param {number} subSolarLonDeg — subsolar longitude in degrees
 * @returns {number} sin of solar elevation angle
 */
function solarElevationSin(lonDeg, latDeg, decRad, subSolarLonDeg) {
  const latRad = latDeg * DEG
  const hourAngle = (lonDeg - subSolarLonDeg) * DEG
  return (
    Math.sin(latRad) * Math.sin(decRad) +
    Math.cos(latRad) * Math.cos(decRad) * Math.cos(hourAngle)
  )
}

/** True when a point is on the night side (sun below horizon). */
function isNight(lonDeg, latDeg, decRad, subSolarLonDeg) {
  return solarElevationSin(lonDeg, latDeg, decRad, subSolarLonDeg) < 0
}

/**
 * Find the terminator longitude at a given latitude using bisection.
 * Searches the 360° longitude range for where solar elevation ≈ 0.
 *
 * @param {number} latDeg       — latitude in degrees
 * @param {number} decRad       — solar declination in radians
 * @param {number} subSolarLonDeg — subsolar longitude in degrees
 * @returns {number} longitude in degrees where the terminator crosses this latitude
 */
function findTerminatorLongitude(latDeg, decRad, subSolarLonDeg) {
  // At the poles the terminator is undefined — return subsolar lon
  if (Math.abs(latDeg) > 89) return subSolarLonDeg

  // We bisect across the full -180..180 range (as a continuous strip).
  // Find one point that is day and one that is night, then bisect between them.
  const lonStart = -180
  const lonEnd   = 180

  let lo = lonStart
  let hi = lonEnd
  let loIsNight = isNight(lo, latDeg, decRad, subSolarLonDeg)

  // Walk across the range to find a day→night (or night→day) crossing.
  // We choose the segment [lo, hi] where the night/day status changes.
  const steps = 72 // 5° steps
  let found = false
  let segLo = lo
  let segLoNight = loIsNight
  for (let i = 1; i <= steps; i++) {
    const segHi = lo + (i / steps) * (hi - lo)
    const segHiNight = isNight(segHi, latDeg, decRad, subSolarLonDeg)
    if (segLoNight !== segHiNight) {
      // Crossing found — bisection target is within [segLo, segHi]
      lo = segLo
      hi = segHi
      found = true
      break
    }
    segLo = segHi
    segLoNight = segHiNight
  }

  if (!found) {
    // Polar day or polar night — return subsolar longitude as fallback
    return subSolarLonDeg
  }

  // Bisection: 50 iterations for sub-arcsecond precision
  for (let i = 0; i < 50; i++) {
    const mid = (lo + hi) / 2
    if (isNight(lo, latDeg, decRad, subSolarLonDeg) === isNight(mid, latDeg, decRad, subSolarLonDeg)) {
      lo = mid
    } else {
      hi = mid
    }
  }

  return (lo + hi) / 2
}

// ── public API ──────────────────────────────────────────────────────────────

/**
 * Generate an array of [lon, lat] coordinates forming the night-side polygon.
 *
 * Algorithm:
 *  1. Sample 36 latitudes from -90 to +90 (every 5°).
 *  2. Walk terminator from south to north on one side.
 *  3. Walk north to south on the opposite side (lon + 180).
 *  4. Close the polygon by repeating the first point.
 *
 * @param {Date} date — UTC date for solar position
 * @returns {Array<[number, number]>} array of [longitude, latitude] pairs
 */
export function getTerminatorPolygon(date) {
  const decRad = getSolarDeclination(date)
  const subSolarLon = getSubsolarLongitude(date)

  const latitudes = []
  for (let lat = -90; lat <= 90; lat += 5) {
    latitudes.push(lat)
  }

  // Forward pass: south → north
  const eastBound = []
  for (const lat of latitudes) {
    const lon = findTerminatorLongitude(lat, decRad, subSolarLon)
    eastBound.push([lon, lat])
  }

  // Reverse pass: north → south on the night-opposite side (lon + 180)
  const westBound = []
  for (let i = latitudes.length - 1; i >= 0; i--) {
    const [lon, lat] = eastBound[i]
    westBound.push([lon + 180, lat])
  }

  // Close polygon
  const polygon = [...eastBound, ...westBound, eastBound[0]]
  return polygon
}

/**
 * Convenience wrapper — returns true if the given lon/lat is on the night side.
 *
 * @param {number} lonDeg — longitude in degrees
 * @param {number} latDeg — latitude in degrees
 * @param {Date}   date   — UTC date for solar position
 * @returns {boolean}
 */
export function isNightSide(lonDeg, latDeg, date) {
  const decRad = getSolarDeclination(date)
  const subSolarLon = getSubsolarLongitude(date)
  return isNight(lonDeg, latDeg, decRad, subSolarLon)
}