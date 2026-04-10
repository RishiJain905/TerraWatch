import { useState, useCallback, useEffect } from 'react'
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
  const [selectedEntity, setSelectedEntity] = useState(null)

  useEffect(() => {
    fetch('/api/metadata')
      .then(res => {
        if (res.ok) return res.json()
        throw new Error('Backend not reachable')
      })
      .then(data => setBackendStatus(data.status || 'ok'))
      .catch(() => setBackendStatus('error'))
  }, [])

  const toggleLayer = useCallback((layer) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }))
  }, [])

  const handleEntityClick = useCallback((type, entity) => {
    setSelectedEntity({ type, entity })
    console.log(`Selected ${type}:`, entity)
  }, [])

  return (
    <div className="app">
      <Header backendStatus={backendStatus} />
      <div className="main-content">
        <Sidebar layers={layers} onToggleLayer={toggleLayer} />
        <div className="globe-wrapper">
          <Globe layers={layers} onEntityClick={handleEntityClick} />
        </div>
      </div>
    </div>
  )
}

export default App
