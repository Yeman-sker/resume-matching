import { useEffect } from 'react'
import { useAppStore } from '@/store'

export default function useWebSocket() {
  const connectWS = useAppStore((state) => state.connectWS)
  const disconnectWS = useAppStore((state) => state.disconnectWS)

  useEffect(() => {
    connectWS()
    return disconnectWS
  }, [connectWS, disconnectWS])
}
