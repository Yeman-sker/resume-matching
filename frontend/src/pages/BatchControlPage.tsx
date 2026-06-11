import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { isAxiosError } from 'axios'
import { useAppStore } from '@/store'
import type { BatchProgress, BatchProgressSnapshot, BatchRunRecord, BatchStatus } from '@/types'
import { Button } from '@/components/ui/button'
import {
  Activity,
  BarChart3,
  Check,
  CheckCircle2,
  Clock,
  Database,
  HardDriveDownload,
  History,
  Layers,
  Loader2,
  Network,
  Pause,
  Play,
  RefreshCw,
  Shuffle,
  Timer,
  TriangleAlert,
  Workflow,
  X,
  XCircle,
} from 'lucide-react'

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

// 与 batch_job.py 的 report_progress 阶段一一对应（index 1-6）
const PIPELINE_STAGES = [
  { icon: Database, label: '读取数据', desc: '从 HDFS 读取清洗后的简历与岗位' },
  { icon: BarChart3, label: '训练 TF-IDF', desc: 'CountVectorizer + IDF' },
  { icon: Network, label: '训练 Word2Vec', desc: '100 维词向量 · 30 轮迭代' },
  { icon: Layers, label: '生成语义向量', desc: '简历与岗位向量化' },
  { icon: Shuffle, label: '构建匹配管道', desc: '笛卡尔积 + 多维评分' },
  { icon: HardDriveDownload, label: '计算并写入', desc: '匹配结果与模型存入 HDFS' },
]

const PIPELINE_KEYFRAMES = `
@keyframes batch-pop { 0% { transform: scale(0.3); opacity: 0; } 60% { transform: scale(1.12); } 100% { transform: scale(1); opacity: 1; } }
@keyframes batch-pulse-ring { 0% { box-shadow: 0 0 0 0 rgba(245, 78, 0, 0.30); } 70% { box-shadow: 0 0 0 9px rgba(245, 78, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(245, 78, 0, 0); } }
@keyframes batch-pulse-green { 0% { box-shadow: 0 0 0 0 rgba(31, 138, 101, 0.35); } 70% { box-shadow: 0 0 0 6px rgba(31, 138, 101, 0); } 100% { box-shadow: 0 0 0 0 rgba(31, 138, 101, 0); } }
@keyframes batch-fade-up { from { opacity: 0; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }
@keyframes batch-shimmer { from { transform: translateX(-120%); } to { transform: translateX(320%); } }
@keyframes batch-indeterminate { from { left: -35%; } to { left: 105%; } }
`

type StageState = 'pending' | 'active' | 'done' | 'failed' | 'skipped'
type RunPhase = 'idle' | 'running' | 'done'

function extractErrorMessage(err: unknown): string {
  if (isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return err instanceof Error ? err.message : String(err)
}

function parseTs(value: string): number | null {
  const ts = new Date(value.replace(' ', 'T')).getTime()
  return Number.isNaN(ts) ? null : ts
}

function elapsedSeconds(startedAt: string, nowMs: number): number | null {
  const start = parseTs(startedAt)
  if (start === null) return null
  return Math.max(0, Math.floor((nowMs - start) / 1000))
}

function formatDuration(seconds: number): string {
  if (seconds < 1) return '<1 秒'
  if (seconds < 60) return `${Math.round(seconds)} 秒`
  return `${Math.floor(seconds / 60)} 分 ${Math.round(seconds % 60)} 秒`
}

function nowString(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function StageCircle({ state, icon: Icon }: { state: StageState; icon: typeof Database }) {
  const base = 'flex h-7 w-7 shrink-0 items-center justify-center rounded-full'
  if (state === 'done' || state === 'failed' || state === 'skipped') {
    const bg = state === 'done' ? '#1f8a65' : state === 'failed' ? '#cf2d56' : '#f54e00'
    const Mark = state === 'done' ? Check : state === 'failed' ? X : TriangleAlert
    return (
      <div key={state} className={base} style={{ background: bg, animation: 'batch-pop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both' }}>
        <Mark className="h-3.5 w-3.5 text-white" strokeWidth={3} />
      </div>
    )
  }
  if (state === 'active') {
    return (
      <div key={state} className={base} style={{ background: 'var(--card)', border: '1.5px solid var(--accent)', animation: 'batch-pulse-ring 1.8s ease-out infinite' }}>
        <Loader2 className="h-3.5 w-3.5 animate-spin" style={{ color: 'var(--accent)' }} />
      </div>
    )
  }
  return (
    <div className={base} style={{ background: 'var(--card)', border: '1.5px solid var(--border)' }}>
      <Icon className="h-3.5 w-3.5" style={{ color: 'var(--muted-foreground)' }} />
    </div>
  )
}

function PipelineView({
  progress,
  logTail,
  doneRun,
  nowMs,
}: {
  progress: BatchProgress | null
  logTail: string
  doneRun: BatchRunRecord | null
  nowMs: number
}) {
  const logRef = useRef<HTMLPreElement>(null)
  useEffect(() => {
    const el = logRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logTail])

  const events = useMemo(() => progress?.events ?? [], [progress])
  const total = PIPELINE_STAGES.length
  const finished = doneRun !== null
  const result = doneRun?.result ?? null
  const current = progress?.current ?? 0
  const starting = !finished && current === 0
  const finishedAtMs = doneRun ? parseTs(doneRun.finished_at) : null

  const stageStarts = useMemo(
    () =>
      PIPELINE_STAGES.map((_, i) => {
        const event = events.find((e) => e.index === i + 1)
        return event ? parseTs(event.at) : null
      }),
    [events],
  )
  const stageMessages = useMemo(
    () =>
      PIPELINE_STAGES.map((_, i) => {
        let message: string | null = null
        for (const e of events) {
          if (e.index === i + 1 && e.message) message = e.message
        }
        return message
      }),
    [events],
  )

  const stageState = (i: number): StageState => {
    const idx = i + 1
    if (finished) {
      if (result === 'success') return 'done'
      if (idx < current) return 'done'
      if (idx === current) return result === 'failed' ? 'failed' : 'skipped'
      return 'pending'
    }
    if (idx < current) return 'done'
    if (idx === current) return 'active'
    return 'pending'
  }

  const stageDurationText = (i: number, state: StageState): string => {
    const start = stageStarts[i]
    if (start === null || state === 'pending') return ''
    const end =
      state === 'done'
        ? stageStarts[i + 1] ?? finishedAtMs ?? nowMs
        : state === 'active'
          ? nowMs
          : finishedAtMs ?? nowMs
    return formatDuration(Math.max(0, (end - start) / 1000))
  }

  const basePercent = current > 0 ? ((current - 0.5) / total) * 100 : 0
  const percent = finished && result === 'success' ? 100 : basePercent
  const barColor =
    result === 'failed'
      ? '#cf2d56'
      : result === 'skipped'
        ? '#f54e00'
        : finished
          ? '#1f8a65'
          : 'var(--accent)'

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold" style={{ color: 'var(--muted-foreground)' }}>执行流水线</span>
        <span className="text-xs font-medium tabular-nums" style={{ color: finished ? barColor : 'var(--muted-foreground)' }}>
          {starting ? '启动中' : `${Math.round(percent)}%`}
        </span>
      </div>

      <div className="relative h-1.5 overflow-hidden rounded-full" style={{ background: 'var(--border)' }}>
        {starting ? (
          <div
            className="absolute top-0 h-full w-[32%] rounded-full"
            style={{ background: 'var(--accent)', animation: 'batch-indeterminate 1.3s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite' }}
          />
        ) : (
          <div
            className="relative h-full overflow-hidden rounded-full"
            style={{ width: `${percent}%`, background: barColor, transition: 'width 0.8s cubic-bezier(0.22, 1, 0.36, 1), background 0.4s ease' }}
          >
            {!finished && (
              <div
                className="absolute inset-y-0 w-1/2"
                style={{ background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)', animation: 'batch-shimmer 1.6s ease-in-out infinite' }}
              />
            )}
          </div>
        )}
      </div>

      {starting && (
        <div className="mt-3 flex items-center gap-2 text-sm" style={{ color: 'var(--muted-foreground)', animation: 'batch-fade-up 0.4s ease both' }}>
          <Loader2 className="h-4 w-4 animate-spin" style={{ color: 'var(--accent)' }} />
          正在启动 Spark 引擎，准备执行环境...
        </div>
      )}

      {finished && result && (
        <div
          key={result}
          className="mt-3 flex items-center gap-2 rounded-sm px-3 py-2 text-sm font-medium"
          style={{ background: `${RESULT_COLORS[result]}14`, color: RESULT_COLORS[result], animation: 'batch-fade-up 0.4s ease both' }}
        >
          {result === 'success' ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : result === 'failed' ? <XCircle className="h-4 w-4 shrink-0" /> : <TriangleAlert className="h-4 w-4 shrink-0" />}
          {result === 'success'
            ? `任务完成，耗时 ${formatDuration(doneRun.duration_seconds)}`
            : result === 'failed'
              ? '任务失败，详情见下方错误信息'
              : '数据不足，本轮已跳过'}
        </div>
      )}

      <div className="mt-4">
        {PIPELINE_STAGES.map((stage, i) => {
          const state = stageState(i)
          const durationText = stageDurationText(i, state)
          const message = state === 'pending' ? null : stageMessages[i]
          return (
            <div key={stage.label} className="flex gap-3">
              <div className="flex flex-col items-center">
                <StageCircle state={state} icon={stage.icon} />
                {i < total - 1 && (
                  <div className="my-1 w-[2px] flex-1 rounded-full" style={{ background: 'var(--border)', minHeight: 14 }}>
                    <div
                      className="w-full rounded-full"
                      style={{ height: state === 'done' ? '100%' : '0%', background: '#1f8a65', transition: 'height 0.45s ease' }}
                    />
                  </div>
                )}
              </div>
              <div className={i < total - 1 ? 'min-w-0 flex-1 pb-5' : 'min-w-0 flex-1'}>
                <div className="flex items-baseline justify-between gap-2">
                  <span
                    className="text-sm font-medium"
                    style={{ color: state === 'pending' ? 'var(--muted-foreground)' : state === 'active' ? 'var(--accent)' : 'var(--foreground)' }}
                  >
                    {stage.label}
                  </span>
                  {durationText && (
                    <span className="shrink-0 text-xs tabular-nums" style={{ color: 'var(--muted-foreground)' }}>{durationText}</span>
                  )}
                </div>
                <div className="mt-0.5 truncate text-xs" style={{ color: 'var(--muted-foreground)' }}>
                  {message ? (
                    <span key={message} className="inline-block" style={{ animation: 'batch-fade-up 0.35s ease both' }}>{message}</span>
                  ) : (
                    stage.desc
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {logTail && !finished && (
        <pre
          ref={logRef}
          className="mt-2 max-h-36 overflow-auto rounded-sm p-3 font-mono text-xs leading-5 whitespace-pre-wrap"
          style={{ background: '#26251e', color: '#f2f1ed', animation: 'batch-fade-up 0.4s ease both' }}
        >
          {logTail}
        </pre>
      )}
    </div>
  )
}

export default function BatchControlPage() {
  const { fetchBatchStatus, fetchBatchProgress, triggerBatch, pauseBatchSchedule, resumeBatchSchedule } = useAppStore()
  const [status, setStatus] = useState<BatchStatus | null>(null)
  const [serviceError, setServiceError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState<RunPhase>('idle')
  const [progressSnap, setProgressSnap] = useState<BatchProgressSnapshot | null>(null)
  const [doneRun, setDoneRun] = useState<BatchRunRecord | null>(null)
  const [nowMs, setNowMs] = useState(() => Date.now())

  const loadStatus = useCallback(async (): Promise<BatchStatus | null> => {
    try {
      const nextStatus = await fetchBatchStatus()
      setStatus(nextStatus)
      setServiceError(null)
      return nextStatus
    } catch (err) {
      setStatus(null)
      setServiceError(extractErrorMessage(err))
      return null
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

  // 发现任务在运行（定时触发或刷新页面），进入运行展示
  useEffect(() => {
    if (phase === 'idle' && status?.running) {
      setProgressSnap(null)
      setDoneRun(null)
      setPhase('running')
    }
  }, [phase, status?.running])

  // 运行期间每秒轮询实时进度，任务结束后切换到完成态
  useEffect(() => {
    if (phase !== 'running') return
    let stopped = false
    let failures = 0
    const poll = async () => {
      try {
        const snap = await fetchBatchProgress()
        if (stopped) return
        failures = 0
        if (snap.running) {
          setProgressSnap(snap)
          return
        }
        const finalStatus = await loadStatus()
        if (stopped) return
        setDoneRun(finalStatus?.last_run ?? null)
        setPhase('done')
      } catch {
        failures += 1
        if (failures >= 5 && !stopped) setPhase('idle')
      }
    }
    void poll()
    const timer = window.setInterval(() => void poll(), 1000)
    return () => {
      stopped = true
      window.clearInterval(timer)
    }
  }, [phase, fetchBatchProgress, loadStatus])

  // 完成动画展示一段时间后平滑收起
  useEffect(() => {
    if (phase !== 'done') return
    const timer = window.setTimeout(() => setPhase('idle'), 3500)
    return () => window.clearTimeout(timer)
  }, [phase])

  // 运行/完成期间每秒刷新计时
  useEffect(() => {
    if (phase === 'idle') return
    setNowMs(Date.now())
    const ticker = window.setInterval(() => setNowMs(Date.now()), 1000)
    return () => window.clearInterval(ticker)
  }, [phase])

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

  const handleTrigger = () =>
    void runAction(async () => {
      await triggerBatch()
      setDoneRun(null)
      setProgressSnap({
        running: true,
        current_run: { trigger: 'manual', started_at: nowString(), progress: null, log_tail: '' },
      })
      setPhase('running')
    })

  const connected = !serviceError
  const lastRun = status?.last_run ?? null
  const paused = status?.schedule_paused ?? false
  const running = (status?.running ?? false) || phase === 'running'
  const currentRun = progressSnap?.current_run ?? status?.current_run ?? null
  const elapsed = running && currentRun ? elapsedSeconds(currentRun.started_at, nowMs) : null
  const triggerDisabled = !connected || running || loading
  const showPipeline = phase !== 'idle'

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
      <style>{PIPELINE_KEYFRAMES}</style>
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
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{
                  background: running ? '#1f8a65' : 'var(--muted-foreground)',
                  animation: running ? 'batch-pulse-green 1.8s ease-out infinite' : undefined,
                }}
              />
              <span className="font-semibold text-lg" style={{ color: 'var(--foreground)' }}>
                {!connected
                  ? '服务未连接'
                  : running
                    ? `任务运行中（${TRIGGER_LABELS[currentRun?.trigger ?? ''] ?? '-'}触发${elapsed !== null ? `，已耗时 ${formatDuration(elapsed)}` : ''}）`
                    : '空闲'}
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateRows: showPipeline ? '1fr' : '0fr',
                opacity: showPipeline ? 1 : 0,
                transition: 'grid-template-rows 0.55s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.4s ease',
              }}
            >
              <div className="overflow-hidden">
                <div className="rounded-sm p-4" style={{ background: 'var(--secondary)' }}>
                  <PipelineView
                    progress={currentRun?.progress ?? null}
                    logTail={currentRun?.log_tail ?? ''}
                    doneRun={phase === 'done' ? doneRun : null}
                    nowMs={nowMs}
                  />
                </div>
              </div>
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
                onClick={handleTrigger}
                disabled={triggerDisabled}
                className="gap-2"
                style={{ background: triggerDisabled ? 'var(--secondary)' : 'var(--accent)', color: triggerDisabled ? 'var(--muted-foreground)' : '#fff', border: 'none' }}
              >
                {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {running ? '任务执行中...' : '立即训练并匹配'}
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
