export function createPlaneIcon(altitude) {
  let color
  if (altitude < 10000) {
    color = '0, 255, 100'
  } else if (altitude <= 30000) {
    color = '255, 255, 0'
  } else {
    color = '255, 100, 100'
  }

  const svgString = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <polygon points="32,4 44,56 32,48 20,56" fill="rgb(${color})" stroke="white" stroke-width="2"/>
</svg>`

  return `data:image/svg+xml;base64,${btoa(svgString)}`
}
