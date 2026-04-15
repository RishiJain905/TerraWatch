/**
 * Starfield generator — seeded PRNG for stable star positions on a large-radius sphere.
 *
 * Uses mulberry32 as the PRNG so positions never shift between re-renders.
 * Stars are uniformly distributed on the sphere via the inverse-transform method
 * and categorised into white / blue-white / warm colour variants.
 */

/** Mulberry32 — simple 32-bit seeded PRNG returning values in [0, 1). */
function mulberry32(seed) {
  let s = seed | 0
  return function () {
    s = (s + 0x6d2b79f5) | 0
    let t = Math.imul(s ^ (s >>> 15), 1 | s)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * Generate a stable set of star positions on a large-radius sphere.
 *
 * @param {Object}   opts
 * @param {number}   opts.count        - Number of stars to generate (default 800)
 * @param {number}   opts.radius       - Sphere radius in metres (default 20 000 000)
 * @param {number}   opts.seed         - PRNG seed (default 42)
 * @param {number}   opts.minBrightness - Minimum brightness 0-1 (default 0.3)
 * @param {number}   opts.maxBrightness - Maximum brightness 0-1 (default 1.0)
 * @returns {Array<{position: [number,number,number], color: [number,number,number,number], radius: number}>}
 */
export function generateStarfield({
  count = 800,
  radius = 20000000,
  seed = 42,
  minBrightness = 0.3,
  maxBrightness = 1.0,
} = {}) {
  const rand = mulberry32(seed)
  const stars = []

  for (let i = 0; i < count; i++) {
    // Uniform distribution on sphere
    const u = rand()
    const v = rand()
    const theta = 2 * Math.PI * u
    const phi = Math.acos(2 * v - 1)

    // Convert to geographic coordinates
    const lat = (Math.PI / 2 - phi) * (180 / Math.PI)
    let lon = (theta * 180 / Math.PI) % 360
    if (lon > 180) lon -= 360
    if (lon < -180) lon += 360

    // Brightness
    const brightness = minBrightness + rand() * (maxBrightness - minBrightness)

    // Visual radius (80–280 km)
    const starRadius = 80000 + rand() * 200000

    // Colour variant
    const colorRoll = rand()
    let color
    if (colorRoll < 0.7) {
      color = [255, 255, 255] // white
    } else if (colorRoll < 0.85) {
      color = [180, 200, 255] // blue-white
    } else {
      color = [255, 220, 180] // warm
    }

    stars.push({
      position: [lon, lat, radius],
      color: [...color, Math.round(brightness * 255)],
      radius: starRadius,
    })
  }

  return stars
}