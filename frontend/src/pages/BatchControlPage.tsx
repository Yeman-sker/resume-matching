import { useCallback, useEffect, useState } from 'react'
import { isAxiosError } from 'axios'
import { useAppStore } from '@/store'
import type { BatchStatus } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const RESULT_LABELS: Record<string, string> = {
  success: '成功',
  failed: '失败',
  skipped: '跳过（数据不足）',
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

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold">批处理控制</h1>
        <p className="text-muted-foreground">手动触发模型训练与匹配计算，查看批处理任务状态</p>
      </div>

      {serviceError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          批处理服务未连接：{serviceError}
        </div>
      )}
      {actionError && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          {actionError}
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>运行状态</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <span className={`inline-block h-3 w-3 rounded-full ${running ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
            <span className="font-medium">
              {!connected
                ? '服务未连接'
                : running
                  ? `任务运行中（${TRIGGER_LABELS[status?.current_run?.trigger ?? ''] ?? '-'}触发${elapsed !== null ? `，已耗时 ${formatDuration(elapsed)}` : ''}）`
                  : '空闲'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Metric
              title="上次运行结果"
              value={lastRun ? `${RESULT_LABELS[lastRun.result] ?? lastRun.result}（${TRIGGER_LABELS[lastRun.trigger] ?? '-'}触发）` : '-'}
            />
            <Metric title="上次运行耗时" value={lastRun ? formatDuration(lastRun.duration_seconds) : '-'} />
            <Metric title="下次自动运行" value={paused ? '已暂停' : status?.next_scheduled_run ?? '-'} />
            <Metric title="自动调度" value={connected ? (paused ? '已暂停' : '每 10 分钟') : '-'} />
          </div>

          {lastRun && (
            <div className="text-sm text-muted-foreground">
              上次运行时间: {lastRun.started_at} ~ {lastRun.finished_at}
            </div>
          )}
          {lastRun?.result === 'failed' && lastRun.error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 whitespace-pre-wrap">
              {lastRun.error}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>控制面板</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-3">
            <Button onClick={() => void runAction(triggerBatch)} disabled={!connected || running || loading}>
              立即训练并匹配
            </Button>
            <Button
              onClick={() => void runAction(paused ? resumeBatchSchedule : pauseBatchSchedule)}
              disabled={!connected || loading}
              variant="outline"
            >
              {paused ? '恢复自动调度' : '暂停自动调度'}
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            批处理任务 = 模型训练 + 匹配计算，整体执行。任务每 10 分钟自动运行一次，手动触发不影响定时计划；任务运行期间无法重复触发。
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>上次运行日志</CardTitle></CardHeader>
        <CardContent>
          {status?.last_run_log ? (
            <pre className="max-h-80 overflow-auto rounded-md bg-gray-950 p-3 text-xs leading-5 text-gray-100 whitespace-pre-wrap">
              {status.last_run_log}
            </pre>
          ) : (
            <p className="text-sm text-muted-foreground">暂无日志</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-1"><CardDescription>{title}</CardDescription></CardHeader>
      <CardContent><div className="text-xl font-bold">{value}</div></CardContent>
    </Card>
  )
}
