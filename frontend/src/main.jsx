import { luma } from '@luma.gl/core'
import { webgl2Adapter } from '@luma.gl/webgl'

// Force the app onto the WebGL2 adapter deck.gl expects.
luma.registerAdapters([webgl2Adapter])
import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
