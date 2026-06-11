import { create } from 'zustand'
import type { SystemStatus } from '@/types'

interface SystemStore {
  status: SystemStatus | null
  setStatus: (status: SystemStatus) => void
  ws: WebSocket | null
  reconnectTimer: number | null
  connectWS: () => void
  disconnectWS: () => void
}

export const useSystemStore = create<SystemStore>((set, get) => ({
  status: null,
  ws: null,
  reconnectTimer: null,

  setStatus: (status) => set({ status }),

  connectWS: () => {
    const currentWS = get().ws
    if (
      currentWS?.readyState === WebSocket.OPEN ||
      currentWS?.readyState === WebSocket.CONNECTING
    ) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.hostname}:8002/ws`)

    ws.onopen = () => console.log('WebSocket connected')
    ws.onmessage = (event) => {
      const status = JSON.parse(event.data)
      set({ status })
    }
    ws.onerror = (error) => console.error('WebSocket error:', error)
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      const reconnectTimer = window.setTimeout(() => get().connectWS(), 3000)
      set({ ws: null, reconnectTimer })
    }

    set({ ws, reconnectTimer: null })
  },

  disconnectWS: () => {
    const { ws, reconnectTimer } = get()
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer)
    }
    if (ws) {
      ws.onclose = null
      ws.close()
    }
    set({ ws: null, reconnectTimer: null })
  },
}))
