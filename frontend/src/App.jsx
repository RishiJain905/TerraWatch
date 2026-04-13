import { useState, useCallback, useEffect } from 'react'
import Globe from './components/Globe/Globe'
import Header from './components/Header/Header'
import Sidebar from './components/Sidebar/Sidebar'
import PlaneInfoPanel from './components/PlaneInfoPanel/PlaneInfoPanel'
import ShipInfoPanel from './components/ShipInfoPanel/ShipInfoPanel'
import EventInfoPanel from './components/EventInfoPanel/EventInfoPanel'
import ConflictInfoPanel from './components/ConflictInfoPanel/ConflictInfoPanel'
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
  const [selectedPlane, setSelectedPlane] = useState(null)
  const [selectedShip, setSelectedShip] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [selectedConflict, setSelectedConflict] = useState(null)

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
    if (type === 'plane') {
      setSelectedPlane(entity)
      setSelectedShip(null)
      setSelectedEvent(null)
      setSelectedConflict(null)
    } else if (type === 'ship') {
      setSelectedShip(entity)
      setSelectedPlane(null)
      setSelectedEvent(null)
      setSelectedConflict(null)
    } else if (type === 'event') {
      setSelectedEvent(entity)
      setSelectedPlane(null)
      setSelectedShip(null)
      setSelectedConflict(null)
    } else if (type === 'conflict') {
      setSelectedConflict(entity)
      setSelectedPlane(null)
      setSelectedShip(null)
      setSelectedEvent(null)
    }
    console.log(`Selected ${type}:`, entity)
  }, [])

  return (
    <div className="app">
      <Header backendStatus={backendStatus} />
      <div className="main-content">
        <Sidebar layers={layers} onToggleLayer={toggleLayer} />
        <div className="globe-wrapper">
          <Globe layers={layers} onEntityClick={handleEntityClick} />
          {selectedPlane && (
            <PlaneInfoPanel
              plane={selectedPlane}
              onClose={() => setSelectedPlane(null)}
            />
          )}
          {selectedShip && (
            <ShipInfoPanel
              ship={selectedShip}
              onClose={() => setSelectedShip(null)}
            />
          )}
          {selectedEvent && (
            <EventInfoPanel
              event={selectedEvent}
              onClose={() => setSelectedEvent(null)}
            />
          )}
          {selectedConflict && (
            <ConflictInfoPanel
              conflict={selectedConflict}
              onClose={() => setSelectedConflict(null)}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default App
