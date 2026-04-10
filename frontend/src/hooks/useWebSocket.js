import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = `ws://${window.location.hostname}:8000/ws`

export function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)
  const onMessageRef = useRef(onMessage)

  // Keep onMessage ref current
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL)
      
      ws.onopen = () => {
        setConnected(true)
        console.log('[WS] Connected to TerraWatch backend')
      }
      
      ws.onclose = () => {
        setConnected(false)
        console.log('[WS] Disconnected, reconnecting in 3s...')
        setTimeout(connect, 3000)
      }
      
      ws.onerror = (error) => {
        console.error('[WS] Error:', error)
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          if (onMessageRef.current) {
            onMessageRef.current(data)
          }
        } catch (e) {
          console.error('[WS] Failed to parse message:', e)
        }
      }
      
      wsRef.current = ws
    } catch (e) {
      console.error('[WS] Connection failed:', e)
      setTimeout(connect, 3000)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { connected, lastMessage }
}
