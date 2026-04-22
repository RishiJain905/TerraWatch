/**
 * starfield.js — Stable, seeded SVG starfield for the globe background.
 *
 * Produces a data-URL SVG of ~400 dots at mulberry32-seeded positions, sized
 * 1920×1080. Used as a CSS background-image on the globe container so stars
 * sit *behind* the DeckGL canvas. Zero WebGL cost, never occluded by the
 * globe, no positions to recompute on resize or pan.
 */

const WIDTH = 1920
const HEIGHT = 1080
const STAR_COUNT = 400
const SEED = 42

/** mulberry32 — 32-bit seeded PRNG. */
function mulberry32(seed) {
  let s = seed | 0
  return function rand() {
    s = (s + 0x6d2b79f5) | 0
    let t = Math.imul(s ^ (s >>> 15), 1 | s)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

let cached = null

/**
 * Return a memoized `data:image/svg+xml,...` URL containing a seeded starfield.
 * Safe to call repeatedly — the URL is generated exactly once per page load.
 */
export function getStarfieldDataUrl() {
  if (cached) return cached

  const rand = mulberry32(SEED)
  const parts = [
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${WIDTH} ${HEIGHT}' preserveAspectRatio='xMidYMid slice'>`,
    `<rect width='100%' height='100%' fill='#05060a'/>`,
  ]

  for (let i = 0; i < STAR_COUNT; i++) {
    const cx = (rand() * WIDTH).toFixed(1)
    const cy = (rand() * HEIGHT).toFixed(1)
    const roll = rand()

    // Size distribution: mostly tiny, a few brighter.
    let r
    if (roll < 0.75) r = 0.4 + rand() * 0.5
    else if (roll < 0.95) r = 0.9 + rand() * 0.7
    else r = 1.6 + rand() * 0.9

    const alpha = (0.35 + rand() * 0.55).toFixed(2)

    // Color variants: white / blue-white / warm.
    const tint = rand()
    let fill
    if (tint < 0.7) fill = '#ffffff'
    else if (tint < 0.9) fill = '#cfe0ff'
    else fill = '#ffe7c8'

    parts.push(
      `<circle cx='${cx}' cy='${cy}' r='${r.toFixed(2)}' fill='${fill}' fill-opacity='${alpha}'/>`
    )
  }

  parts.push('</svg>')

  const svg = parts.join('')
  // encodeURIComponent keeps the URL valid across browsers without base64 bloat.
  cached = `url("data:image/svg+xml;utf8,${encodeURIComponent(svg)}")`
  return cached
}
