// ─── luma.gl / deck.gl fixes ────────────────────────────────────────────────
import { luma } from '@luma.gl/core'
import { webgl2Adapter, WebGLCanvasContext } from '@luma.gl/webgl'

// 1. Force WebGL-only
luma.registerAdapters([webgl2Adapter])

// 2. Patch getMaxDrawingBufferSize with try-catch (this.device check above is unreliable
//    due to Vite module scoping / prototype mismatches in dev mode)
const _orig = WebGLCanvasContext.prototype.getMaxDrawingBufferSize
WebGLCanvasContext.prototype.getMaxDrawingBufferSize = function () {
  try {
    return _orig.call(this)
  } catch (e) {
    // ResizeObserver fired before device was ready — return safe 1K fallback
    console.warn('[TerraWatch] getMaxDrawingBufferSize: device not ready, using fallback', e.message)
    return [1024, 1024]
  }
}

// ─── React app ───────────────────────────────────────────────────────────────
import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
