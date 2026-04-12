import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`

export function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  const reconnectTimerRef = useRef(null)
  // Generation counter: each connect() call increments this.
  // Cleanup only closes the WS if the generation still matches —
  // prevents React StrictMode / hot-reload from killing the NEW connection.
  const generationRef = useRef(0)

  // Keep onMessage ref current
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  const connect = useCallback(() => {
    const gen = ++generationRef.current

    try {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        setConnected(true)
        console.log('[WS] Connected to TerraWatch backend')
      }

      ws.onclose = () => {
        setConnected(false)
        // Only reconnect if this is still the active generation
        if (generationRef.current === gen) {
          console.log('[WS] Disconnected, reconnecting in 3s...')
          reconnectTimerRef.current = setTimeout(connect, 3000)
        }
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
      if (generationRef.current === gen) {
        reconnectTimerRef.current = setTimeout(connect, 3000)
      }
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      // Increment generation so stale reconnect timers and onclose
      // handlers know they're outdated and don't fire.
      generationRef.current++
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { connected, lastMessage }
}
