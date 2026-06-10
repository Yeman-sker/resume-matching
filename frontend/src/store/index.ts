import { create } from 'zustand'
import type { SystemStatus } from '@/types'

interface SystemStore {
  status: SystemStatus | null
  setStatus: (status: SystemStatus) => void
  ws: WebSocket | null
  connectWS: () => void
  disconnectWS: () => void
}

export const useSystemStore = create<SystemStore>((set, get) => ({
  status: null,
  ws: null,

  setStatus: (status) => set({ status }),

  connectWS: () => {
    const ws = new WebSocket('ws://localhost:8002/ws')

    ws.onopen = () => console.log('WebSocket connected')
    ws.onmessage = (event) => {
      const status = JSON.parse(event.data)
      set({ status })
    }
    ws.onerror = (error) => console.error('WebSocket error:', error)
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setTimeout(() => get().connectWS(), 3000)
    }

    set({ ws })
  },

  disconnectWS: () => {
    const { ws } = get()
    if (ws) {
      ws.close()
      set({ ws: null })
    }
  },
}))
