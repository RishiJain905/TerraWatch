import { useState, useCallback } from 'react'
import Globe from './components/Globe/Globe'
import Header from './components/Header/Header'
import Sidebar from './components/Sidebar/Sidebar'
import './index.css'

function App() {
  const [layers, setLayers] = useState({
    planes: true,
    ships: true,
    events: false,
    conflicts: false,
  })

  const [selectedEntity, setSelectedEntity] = useState(null)

  const toggleLayer = useCallback((layer) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }))
  }, [])

  const handleEntityClick = useCallback((type, entity) => {
    setSelectedEntity({ type, entity })
    console.log(`Selected ${type}:`, entity)
  }, [])

  return (
    <div className="app">
      <Header />
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
