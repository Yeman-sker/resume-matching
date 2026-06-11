import { create } from 'zustand'
import api from '@/lib/api'
import type {
  SystemStatus,
  Job,
  Resume,
  MatchDetail,
  Stats,
  JobsResponse,
  ResumesResponse,
  JobMatchesResponse,
  ResumeRecommendationsResponse,
  GeneratorStatus,
  GeneratorConfig,
  BatchStatus,
  BatchProgressSnapshot,
} from '@/types'

function getErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

interface AppStore {
  status: SystemStatus | null
  ws: WebSocket | null
  reconnectTimer: number | null
  connectWS: () => void
  disconnectWS: () => void

  jobs: Job[]
  resumes: Resume[]
  stats: Stats | null
  loading: boolean
  error: string | null

  fetchJobs: (page?: number, pageSize?: number) => Promise<void>
  fetchResumes: (page?: number, pageSize?: number) => Promise<void>
  fetchJobMatches: (jobId: string, limit?: number) => Promise<JobMatchesResponse>
  fetchResumeRecommendations: (resumeId: string, limit?: number) => Promise<ResumeRecommendationsResponse>
  fetchMatchDetail: (resumeId: string, jobId: string) => Promise<MatchDetail>
  fetchStats: () => Promise<void>
  fetchGeneratorStatus: () => Promise<GeneratorStatus>
  startGenerator: (config?: GeneratorConfig) => Promise<void>
  stopGenerator: () => Promise<void>
  fetchBatchStatus: () => Promise<BatchStatus>
  fetchBatchProgress: () => Promise<BatchProgressSnapshot>
  triggerBatch: () => Promise<void>
  pauseBatchSchedule: () => Promise<void>
  resumeBatchSchedule: () => Promise<void>
}

export const useAppStore = create<AppStore>((set, get) => ({
  status: null,
  ws: null,
  reconnectTimer: null,

  jobs: [],
  resumes: [],
  stats: null,
  loading: false,
  error: null,

  connectWS: () => {
    const currentWS = get().ws
    if (currentWS?.readyState === WebSocket.OPEN || currentWS?.readyState === WebSocket.CONNECTING) return
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.hostname}:8002/ws`)
    ws.onopen = () => console.log('WebSocket connected')
    ws.onmessage = (event) => {
      try {
        const status = JSON.parse(event.data) as SystemStatus
        set({ status })
      } catch (err) {
        console.error('Invalid WebSocket message:', getErrorMessage(err))
      }
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
    if (reconnectTimer !== null) window.clearTimeout(reconnectTimer)
    if (ws) { ws.onclose = null; ws.close() }
    set({ ws: null, reconnectTimer: null })
  },

  fetchJobs: async (page = 1, pageSize = 200) => {
    set({ loading: true, error: null })
    try {
      const res = await api.get<JobsResponse>('/api/jobs', { params: { page, page_size: pageSize } })
      set({ jobs: res.data.jobs, loading: false })
    } catch (err: unknown) {
      set({ error: getErrorMessage(err), loading: false })
    }
  },

  fetchResumes: async (page = 1, pageSize = 200) => {
    set({ loading: true, error: null })
    try {
      const res = await api.get<ResumesResponse>('/api/resumes', { params: { page, page_size: pageSize } })
      set({ resumes: res.data.resumes, loading: false })
    } catch (err: unknown) {
      set({ error: getErrorMessage(err), loading: false })
    }
  },

  fetchJobMatches: async (jobId: string, limit = 50) => {
    const res = await api.get<JobMatchesResponse>(`/api/jobs/${jobId}/matches`, { params: { limit } })
    return res.data
  },

  fetchResumeRecommendations: async (resumeId: string, limit = 50) => {
    const res = await api.get<ResumeRecommendationsResponse>(`/api/resumes/${resumeId}/recommendations`, { params: { limit } })
    return res.data
  },

  fetchMatchDetail: async (resumeId: string, jobId: string) => {
    const res = await api.get<MatchDetail>(`/api/matches/${resumeId}/${jobId}`)
    return res.data
  },

  fetchStats: async () => {
    try {
      const res = await api.get<Stats>('/api/stats')
      set({ stats: res.data })
    } catch (err: unknown) {
      console.error('Failed to fetch stats:', getErrorMessage(err))
    }
  },

  fetchGeneratorStatus: async () => {
    const res = await api.get<GeneratorStatus>('/api/generator/status')
    return res.data
  },

  startGenerator: async (config?: GeneratorConfig) => {
    await api.post('/api/generator/start', config)
  },

  stopGenerator: async () => {
    await api.post('/api/generator/stop')
  },

  fetchBatchStatus: async () => {
    const res = await api.get<BatchStatus>('/api/batch/status')
    return res.data
  },

  fetchBatchProgress: async () => {
    const res = await api.get<BatchProgressSnapshot>('/api/batch/progress')
    return res.data
  },

  triggerBatch: async () => {
    await api.post('/api/batch/trigger')
  },

  pauseBatchSchedule: async () => {
    await api.post('/api/batch/schedule/pause')
  },

  resumeBatchSchedule: async () => {
    await api.post('/api/batch/schedule/resume')
  },
}))
