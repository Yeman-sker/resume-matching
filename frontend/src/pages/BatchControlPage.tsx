import { useCallback, useEffect, useState } from 'react'
import { isAxiosError } from 'axios'
import { useAppStore } from '@/store'
import type { BatchStatus } from '@/types'
import { Button } from '@/components/ui/button'
import { Activity, Clock, History, Pause, Play, RefreshCw, Timer, Workflow } from 'lucide-react'

const RESULT_LABELS: Record<string, string> = {
  success: '成功',
  failed: '失败',
  skipped: '跳过（数据不足）',
}

const RESULT_COLORS: Record<string, string> = {
  success: '#1f8a65',
  failed: '#cf2d56',
  skipped: '#f54e00',
}

const TRIGGER_LABELS: Record<string, string> = {
  manual: '手动',
  scheduled: '定时',
}

function extractErrorMessage(err: unknown): string {
  if (isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return err instanceof Error ? err.message : String(err)
}

function elapsedSeconds(startedAt: string): number | null {
  const start = new Date(startedAt.replace(' ', 'T')).getTime()
  if (Number.isNaN(start)) return null
  return Math.max(0, Math.floor((Date.now() - start) / 1000))
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.floor(seconds / 60)} 分 ${Math.round(seconds % 60)} 秒`
}

export default function BatchControlPage() {
  const { fetchBatchStatus, triggerBatch, pauseBatchSchedule, resumeBatchSchedule } = useAppStore()
  const [status, setStatus] = useState<BatchStatus | null>(null)
  const [serviceError, setServiceError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [, setTick] = useState(0)

  const loadStatus = useCallback(async () => {
    try {
      const nextStatus = await fetchBatchStatus()
      setStatus(nextStatus)
      setServiceError(null)
    } catch (err) {
      setStatus(null)
      setServiceError(extractErrorMessage(err))
    }
  }, [fetchBatchStatus])

  useEffect(() => {
    const initial = window.setTimeout(() => void loadStatus(), 0)
    const interval = window.setInterval(() => void loadStatus(), 5000)
    return () => {
      window.clearTimeout(initial)
      window.clearInterval(interval)
    }
  }, [loadStatus])

  const running = status?.running ?? false

  useEffect(() => {
    if (!running) return
    const ticker = window.setInterval(() => setTick((t) => t + 1), 1000)
    return () => window.clearInterval(ticker)
  }, [running])

  const runAction = async (action: () => Promise<void>) => {
    setLoading(true)
    setActionError(null)
    try {
      await action()
      window.setTimeout(() => void loadStatus(), 1000)
    } catch (err) {
      setActionError(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const connected = !serviceError
  const lastRun = status?.last_run ?? null
  const paused = status?.schedule_paused ?? false
  const elapsed = status?.current_run ? elapsedSeconds(status.current_run.started_at) : null
  const triggerDisabled = !connected || running || loading

  const cardStyle: React.CSSProperties = {
    position: 'relative',
    background: 'var(--card)',
    borderRadius: '4px',
    padding: '1.5rem',
  }
  const cardBorderOverlay: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    borderRadius: '4px',
    border: '1px solid var(--border)',
    pointerEvents: 'none',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Workflow className="h-5 w-5" style={{ color: 'var(--accent)' }} />
        <div>
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--foreground)' }}>批处理控制</h1>
          <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>手动触发模型训练与匹配计算，查看批处理任务状态</p>
        </div>
      </div>

      {serviceError && (
        <div className="rounded-md px-4 py-3 text-sm" style={{ background: 'var(--card)', border: '1px solid #cf2d5640', color: '#cf2d56' }}>
          批处理服务未连接：{serviceError}
        </div>
      )}
      {actionError && (
        <div className="rounded-md px-4 py-3 text-sm" style={{ background: 'var(--card)', border: '1px solid #f54e0040', color: '#f54e00' }}>
          {actionError}
        </div>
      )}

      <div style={cardStyle}>
        <div style={cardBorderOverlay} />
        <div className="relative">
          <h3 className="flex items-center gap-2 font-semibold mb-4" style={{ color: 'var(--foreground)' }}>
            <Activity className="h-4 w-4" style={{ color: 'var(--accent)' }} />
            运行状态
          </h3>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: running ? '#1f8a65' : 'var(--muted-foreground)' }} />
              <span className="font-semibold text-lg" style={{ color: 'var(--foreground)' }}>
                {!connected
                  ? '服务未连接'
                  : running
                    ? `任务运行中（${TRIGGER_LABELS[status?.current_run?.trigger ?? ''] ?? '-'}触发${elapsed !== null ? `，已耗时 ${formatDuration(elapsed)}` : ''}）`
                    : '空闲'}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted-foreground)' }}><History className="h-3.5 w-3.5" />上次运行结果</div>
                <div className="text-lg font-bold mt-1" style={{ color: lastRun ? RESULT_COLORS[lastRun.result] ?? 'var(--foreground)' : 'var(--foreground)' }}>
                  {lastRun ? RESULT_LABELS[lastRun.result] ?? lastRun.result : '-'}
                </div>
              </div>
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted-foreground)' }}><Timer className="h-3.5 w-3.5" />上次运行耗时</div>
                <div className="text-lg font-bold mt-1" style={{ color: 'var(--foreground)' }}>{lastRun ? formatDuration(lastRun.duration_seconds) : '-'}</div>
              </div>
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted-foreground)' }}><Clock className="h-3.5 w-3.5" />下次自动运行</div>
                <div className="text-lg font-bold mt-1" style={{ color: 'var(--foreground)' }}>
                  {paused ? '已暂停' : status?.next_scheduled_run?.slice(11) ?? '-'}
                </div>
              </div>
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted-foreground)' }}><RefreshCw className="h-3.5 w-3.5" />自动调度</div>
                <div className="text-lg font-bold mt-1" style={{ color: 'var(--foreground)' }}>{connected ? (paused ? '已暂停' : '每 10 分钟') : '-'}</div>
              </div>
            </div>

            {lastRun && (
              <div className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                上次运行时间: {lastRun.started_at} ~ {lastRun.finished_at}（{TRIGGER_LABELS[lastRun.trigger] ?? '-'}触发）
              </div>
            )}
            {lastRun?.result === 'failed' && lastRun.error && (
              <div className="rounded-md px-3 py-2 text-sm whitespace-pre-wrap" style={{ background: 'var(--secondary)', border: '1px solid #cf2d5640', color: '#cf2d56' }}>
                {lastRun.error}
              </div>
            )}
          </div>
        </div>
      </div>

      <div style={cardStyle}>
        <div style={cardBorderOverlay} />
        <div className="relative">
          <h3 className="font-semibold mb-4" style={{ color: 'var(--foreground)' }}>控制面板</h3>
          <div className="space-y-4">
            <div className="flex gap-3">
              <Button
                onClick={() => void runAction(triggerBatch)}
                disabled={triggerDisabled}
                className="gap-2"
                style={{ background: triggerDisabled ? 'var(--secondary)' : 'var(--accent)', color: triggerDisabled ? 'var(--muted-foreground)' : '#fff', border: 'none' }}
              >
                <Play className="h-4 w-4" />
                立即训练并匹配
              </Button>
              <Button
                onClick={() => void runAction(paused ? resumeBatchSchedule : pauseBatchSchedule)}
                disabled={!connected || loading}
                variant="outline"
                className="gap-2"
                style={{ borderColor: 'var(--border)', color: 'var(--foreground)' }}
              >
                {paused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
                {paused ? '恢复自动调度' : '暂停自动调度'}
              </Button>
            </div>
            <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
              批处理任务 = 模型训练 + 匹配计算，整体执行。任务每 10 分钟自动运行一次，手动触发不影响定时计划；任务运行期间无法重复触发。
            </p>
          </div>
        </div>
      </div>

      <div style={cardStyle}>
        <div style={cardBorderOverlay} />
        <div className="relative">
          <h3 className="font-semibold mb-4" style={{ color: 'var(--foreground)' }}>上次运行日志</h3>
          {status?.last_run_log ? (
            <pre className="max-h-80 overflow-auto rounded-sm p-3 text-xs leading-5 font-mono whitespace-pre-wrap" style={{ background: '#26251e', color: '#f2f1ed' }}>
              {status.last_run_log}
            </pre>
          ) : (
            <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>暂无日志</p>
          )}
        </div>
      </div>
    </div>
  )
}
