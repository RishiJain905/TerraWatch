/**
 * terminator.js — Day/night shading as a procedural raster.
 *
 * Builds an RGBA ImageData covering the full world where each pixel's alpha
 * encodes how far it is past the solar terminator. Rendered via BitmapLayer
 * in Globe.jsx, this avoids every failure mode of the polygon approach
 * (antimeridian splits, pole closure, winding order) because pixels are
 * independent of one another.
 *
 * Solar math: classic NOAA low-precision equations.
 *   declination δ = -23.45° · cos(2π/365 · (DOY + 10))
 *   subsolar lon  = (12 - UTC_hours) · 15
 *   sin(elev)     = sin(lat)·sin(δ) + cos(lat)·cos(δ)·cos((lon - subLon)·π/180)
 *
 * Elevation → alpha mapping (twilight band):
 *   elev ≥ +2°                     → fully transparent (day)
 *   +2° > elev > -12°              → smoothstep ramp (civil + nautical twilight)
 *   elev ≤ -12°                    → NIGHT_ALPHA (astronomical night)
 *
 * The ~14° twilight band matches real Earth's soft terminator and visually
 * reads as "planet from space" rather than a hard knife edge.
 */

const DEG = Math.PI / 180

// Night side tint. Deep blue-black so the basemap still shows through faintly.
const NIGHT_R = 4
const NIGHT_G = 8
const NIGHT_B = 24
const NIGHT_ALPHA = 140

// Twilight band thresholds in sin(elevation) space.
const TWILIGHT_TOP = Math.sin(2 * DEG)
const TWILIGHT_BOTTOM = Math.sin(-12 * DEG)

/** Day of year 1..366 from a Date. */
function getDayOfYear(date) {
  const start = Date.UTC(date.getUTCFullYear(), 0, 0)
  return Math.floor((date.getTime() - start) / 86400000)
}

/** Solar declination in radians. */
function getSolarDeclination(date) {
  return -23.45 * DEG * Math.cos((2 * Math.PI / 365) * (getDayOfYear(date) + 10))
}

/** Subsolar longitude in degrees (east positive). */
function getSubsolarLongitude(date) {
  const hours =
    date.getUTCHours() +
    date.getUTCMinutes() / 60 +
    date.getUTCSeconds() / 3600
  return (12 - hours) * 15
}

/** Smoothstep(0, 1, t). */
function smoothstep(t) {
  const x = t < 0 ? 0 : t > 1 ? 1 : t
  return x * x * (3 - 2 * x)
}

/**
 * Build an RGBA ImageData representing the night-side shading for a given date.
 *
 * @param {Date}   date
 * @param {Object} [opts]
 * @param {number} [opts.width=720]
 * @param {number} [opts.height=360]
 * @returns {ImageData}
 */
export function buildTerminatorImage(date = new Date(), opts = {}) {
  const width = opts.width || 720
  const height = opts.height || 360

  const decl = getSolarDeclination(date)
  const subLon = getSubsolarLongitude(date)
  const sinDecl = Math.sin(decl)
  const cosDecl = Math.cos(decl)

  const data = new Uint8ClampedArray(width * height * 4)

  // Precompute per-row sin/cos(lat) so the inner loop is just a cos() per pixel.
  const sinLat = new Float64Array(height)
  const cosLat = new Float64Array(height)
  for (let y = 0; y < height; y++) {
    const lat = 90 - ((y + 0.5) * 180) / height
    const latRad = lat * DEG
    sinLat[y] = Math.sin(latRad)
    cosLat[y] = Math.cos(latRad)
  }

  for (let y = 0; y < height; y++) {
    const rowSin = sinLat[y] * sinDecl
    const rowCos = cosLat[y] * cosDecl
    for (let x = 0; x < width; x++) {
      const lon = -180 + ((x + 0.5) * 360) / width
      const hourAngle = (lon - subLon) * DEG
      const sinElev = rowSin + rowCos * Math.cos(hourAngle)

      let alpha
      if (sinElev >= TWILIGHT_TOP) {
        alpha = 0
      } else if (sinElev <= TWILIGHT_BOTTOM) {
        alpha = NIGHT_ALPHA
      } else {
        const t = (TWILIGHT_TOP - sinElev) / (TWILIGHT_TOP - TWILIGHT_BOTTOM)
        alpha = Math.round(smoothstep(t) * NIGHT_ALPHA)
      }

      const i = (y * width + x) * 4
      data[i] = NIGHT_R
      data[i + 1] = NIGHT_G
      data[i + 2] = NIGHT_B
      data[i + 3] = alpha
    }
  }

  return new ImageData(data, width, height)
}

/** Convenience: true if a lon/lat is on the astronomical night side for `date`. */
export function isNightSide(lon, lat, date = new Date()) {
  const decl = getSolarDeclination(date)
  const subLon = getSubsolarLongitude(date)
  const sinElev =
    Math.sin(lat * DEG) * Math.sin(decl) +
    Math.cos(lat * DEG) * Math.cos(decl) * Math.cos((lon - subLon) * DEG)
  return sinElev <= TWILIGHT_BOTTOM
}
