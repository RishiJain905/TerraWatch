import { useState, useEffect } from 'react'
import Globe from './components/Globe/Globe'
import Header from './components/Header/Header'
import Sidebar from './components/Sidebar/Sidebar'
import './index.css'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [layers, setLayers] = useState({
    planes: true,
    ships: true,
    events: false,
    conflicts: false,
  })

  useEffect(() => {
    // Check backend connectivity
    fetch('/api/metadata')
      .then(res => {
        if (res.ok) return res.json()
        throw new Error('Backend not reachable')
      })
      .then(data => setBackendStatus(data.status || 'connected'))
      .catch(() => setBackendStatus('error'))
  }, [])

  const toggleLayer = (layer) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }))
  }

  return (
    <div className="app">
      <Header backendStatus={backendStatus} />
      <div className="main-content">
        <Sidebar layers={layers} onToggleLayer={toggleLayer} />
        <div className="globe-wrapper">
          <Globe />
          <div className="status-bar">
            Phase 1 — Globe Shell
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
