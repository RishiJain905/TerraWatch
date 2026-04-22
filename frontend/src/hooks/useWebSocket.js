import { useEffect, useRef, useState, useCallback } from 'react'

const DEV_BACKEND_PORT = '8000'
const RECONNECT_DELAY_MS = 3000

function normalizeWsUrl(url) {
  if (!url) {
    return null
  }

  const trimmed = url.trim()
  if (!trimmed) {
    return null
  }

  if (trimmed.startsWith('ws://') || trimmed.startsWith('wss://')) {
    return trimmed
  }

  if (trimmed.startsWith('http://')) {
    return `ws://${trimmed.slice('http://'.length)}`
  }

  if (trimmed.startsWith('https://')) {
    return `wss://${trimmed.slice('https://'.length)}`
  }

  if (trimmed.startsWith('/')) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}${trimmed}`
  }

  return `ws://${trimmed}`
}

function resolveWsUrl() {
  const envUrl = normalizeWsUrl(import.meta.env.VITE_WS_URL)
  if (envUrl) {
    return envUrl
  }

  // In local dev, prefer direct backend socket to avoid Vite ws proxy noise.
  if (import.meta.env.DEV) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.hostname}:${DEV_BACKEND_PORT}/ws`
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws`
}

const WS_URL = resolveWsUrl()

export function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  const reconnectTimerRef = useRef(null)
  // Generation counter: each connect() call increments this.
  // Cleanup only closes the WS if the generation still matches.
  // This prevents StrictMode / hot-reload from killing the new connection.
  const generationRef = useRef(0)

  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  const connect = useCallback(() => {
    const gen = ++generationRef.current

    try {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        setConnected(true)
        console.log('[WS] Connected to TerraWatch backend', { url: WS_URL })
      }

      ws.onclose = () => {
        setConnected(false)
        if (generationRef.current === gen) {
          console.log('[WS] Disconnected, reconnecting in 3s...', { url: WS_URL })
          reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY_MS)
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
        reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY_MS)
      }
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      generationRef.current++
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'cleanup')
      }
    }
  }, [connect])

  return { connected, lastMessage }
}
