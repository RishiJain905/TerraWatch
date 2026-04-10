import { useEffect, useRef, useState } from 'react'

const WS_URL = `ws://${window.location.hostname}:8000/ws`

export function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (event) => onMessage(JSON.parse(event.data))
    wsRef.current = ws

    return () => ws.close()
  }, [onMessage])

  return { connected }
}
