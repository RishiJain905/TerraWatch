// One-off sanity check for terminator + starfield utilities.
// Run with: node scripts/test-terminator.mjs

globalThis.ImageData = class {
  constructor(data, w, h) {
    if (data instanceof Uint8ClampedArray) {
      this.data = data
      this.width = w
      this.height = h
    } else {
      this.width = data
      this.height = w
      this.data = new Uint8ClampedArray(data * w * 4)
    }
  }
}

const { buildTerminatorImage, isNightSide } = await import(
  '../src/utils/terminator.js'
)
const {
  buildPolarCapData,
  POLAR_CAP_RADIUS_METERS,
} = await import('../src/utils/polarCaps.js')
const { getStarfieldDataUrl } = await import('../src/utils/starfield.js')

function alphaAt(img, lon, lat) {
  const x = Math.floor(((lon + 180) / 360) * img.width)
  const y = Math.floor(((90 - lat) / 180) * img.height)
  return img.data[(y * img.width + x) * 4 + 3]
}

const tests = []
function assert(label, cond, detail = '') {
  tests.push({ label, ok: cond, detail })
}

// Summer solstice, noon UTC. Subsolar point at approx (0, +23.45).
const summer = new Date('2026-06-21T12:00:00Z')
const img = buildTerminatorImage(summer, { width: 72, height: 36 })

assert('dims', img.width === 72 && img.height === 36)
assert('sub-solar is day (alpha 0)', alphaAt(img, 0, 23) === 0, `got ${alphaAt(img, 0, 23)}`)
assert('antipode is night', alphaAt(img, 180, 0) >= 120, `got ${alphaAt(img, 180, 0)}`)
assert('N pole midnight sun (day)', alphaAt(img, 0, 89) === 0, `got ${alphaAt(img, 0, 89)}`)
assert('S pole polar night', alphaAt(img, 0, -89) >= 120, `got ${alphaAt(img, 0, -89)}`)
assert('isNightSide antipode', isNightSide(180, 0, summer) === true)
assert('isNightSide subsolar', isNightSide(0, 23, summer) === false)

// Winter solstice, 0h UTC. Sub-solar point approx (180, -23.45).
const winter = new Date('2026-12-21T00:00:00Z')
const img2 = buildTerminatorImage(winter, { width: 72, height: 36 })
assert('winter subsolar day', alphaAt(img2, 180, -23) === 0, `got ${alphaAt(img2, 180, -23)}`)
assert('winter N 85 polar night', alphaAt(img2, 0, 85) >= 120, `got ${alphaAt(img2, 0, 85)}`)
assert('winter S 85 midnight sun', alphaAt(img2, 0, -85) === 0, `got ${alphaAt(img2, 0, -85)}`)

// Every pixel alpha is bounded
let minA = 255, maxA = 0
for (let i = 3; i < img.data.length; i += 4) {
  if (img.data[i] < minA) minA = img.data[i]
  if (img.data[i] > maxA) maxA = img.data[i]
}
assert('alpha in [0, 140]', minA === 0 && maxA === 140, `got [${minA}, ${maxA}]`)

// Polar cap geometry fills the Web Mercator gap without using a full-globe bitmap.
const summerCaps = buildPolarCapData(summer)
assert('two polar caps', summerCaps.length === 2)
assert(
  'polar cap radius exceeds mercator gap',
  POLAR_CAP_RADIUS_METERS >= 550000,
  `got ${POLAR_CAP_RADIUS_METERS}`,
)
assert(
  'summer north cap uses opaque day surface',
  JSON.stringify(summerCaps.find(cap => cap.id === 'north-polar-cap')?.fillColor) === JSON.stringify([26, 29, 36, 255]),
  `got ${JSON.stringify(summerCaps.find(cap => cap.id === 'north-polar-cap')?.fillColor)}`,
)
assert(
  'summer south cap darkens on night side',
  (summerCaps.find(cap => cap.id === 'south-polar-cap')?.fillColor[3] || 0) >= 120,
  `got ${summerCaps.find(cap => cap.id === 'south-polar-cap')?.fillColor[3]}`,
)
const winterCaps = buildPolarCapData(winter)
assert(
  'winter north cap darkens on night side',
  (winterCaps.find(cap => cap.id === 'north-polar-cap')?.fillColor[3] || 0) >= 120,
  `got ${winterCaps.find(cap => cap.id === 'north-polar-cap')?.fillColor[3]}`,
)
assert(
  'winter south cap uses opaque day surface',
  JSON.stringify(winterCaps.find(cap => cap.id === 'south-polar-cap')?.fillColor) === JSON.stringify([26, 29, 36, 255]),
  `got ${JSON.stringify(winterCaps.find(cap => cap.id === 'south-polar-cap')?.fillColor)}`,
)

// Starfield utility
const url = getStarfieldDataUrl()
assert('starfield url starts with url(', url.startsWith('url('))
assert('starfield is svg data url', url.includes('data:image/svg+xml'))
assert('starfield memoized', url === getStarfieldDataUrl())
assert(
  'starfield has ~400 circles',
  (url.match(/%3Ccircle/g) || []).length === 400,
  `got ${(url.match(/%3Ccircle/g) || []).length}`,
)

const fails = tests.filter(t => !t.ok)
for (const t of tests) {
  console.log(`${t.ok ? 'PASS' : 'FAIL'}  ${t.label}${t.detail ? '  — ' + t.detail : ''}`)
}
console.log(`\n${tests.length - fails.length}/${tests.length} passed`)
process.exit(fails.length === 0 ? 0 : 1)
