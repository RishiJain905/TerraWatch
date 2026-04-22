# Terminator Raster Visual Tuning Guide

## Current State

The terminator implementation uses a procedural raster, not a polygon layer:
- `frontend/src/utils/terminator.js` builds an `ImageData` day/night texture
- `frontend/src/components/Globe/Globe.jsx` paints that texture into a canvas
- `BitmapLayer` renders the canvas over the globe
- The raster is recomputed every 60 seconds

## Visual Tuning

If the night-side shading feels too strong or too weak, tune the layer alpha in `Globe.jsx`:
- Lower alpha for a lighter overlay
- Higher alpha for a darker overlay

If the twilight band feels too sharp, adjust the gradient math in `terminator.js`:
- Widen the transition band for a softer sunrise/sunset edge
- Narrow it for a harder day/night split

If the overlay ever looks misaligned after zoom or pan, check the canvas rebuild path in `Globe.jsx`:
- The layer should always use the latest canvas created from `buildTerminatorImage(now)`
- Rebuild timing should stay on the 60 second interval

## Validation

After any change, verify:
- Night side is shaded and day side stays clear
- Terminator tracks the live clock as the globe rotates
- No console errors appear during map movement or redraws
