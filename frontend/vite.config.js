import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'
const wsProxyTarget = process.env.VITE_WS_PROXY_TARGET || 'ws://localhost:8000'
const EXPECTED_WS_PROXY_CODES = new Set(['ECONNRESET', 'EPIPE'])

function isExpectedWsProxyError(error) {
  if (!error) {
    return false
  }

  if (EXPECTED_WS_PROXY_CODES.has(error.code)) {
    return true
  }

  const message = String(error.message || '').toLowerCase()
  return message.includes('socket hang up') || message.includes('aborted')
}

function configureWsProxy(proxy) {
  proxy.on('error', (error, _req, socket) => {
    if (isExpectedWsProxyError(error)) {
      if (socket && !socket.destroyed) {
        socket.destroy()
      }
      return
    }

    console.error('[vite][ws-proxy] unexpected socket error:', error)
  })
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
      },
      '/ws': {
        target: wsProxyTarget,
        ws: true,
        changeOrigin: true,
        configure: configureWsProxy,
      },
    },
  },
})
