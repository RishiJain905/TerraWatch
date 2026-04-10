import { useState, useEffect } from 'react'

function App() {
  const [status, setStatus] = useState('connecting')

  useEffect(() => {
    fetch('/api/metadata')
      .then(res => res.json())
      .then(data => setStatus(data.status || 'connected'))
      .catch(() => setStatus('error'))
  }, [])

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      fontFamily: 'system-ui, sans-serif',
      background: '#0a0a0f',
      color: '#ffffff'
    }}>
      <div style={{ padding: '20px' }}>
        <h1>TerraWatch</h1>
        <p>Backend Status: {status}</p>
      </div>
    </div>
  )
}

export default App
