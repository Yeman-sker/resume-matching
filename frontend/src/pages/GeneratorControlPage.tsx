import { useCallback, useEffect, useState } from 'react'
import { useAppStore } from '@/store'
import type { GeneratorStatus } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function GeneratorControlPage() {
  const { startGenerator, stopGenerator, fetchGeneratorStatus } = useAppStore()
  const [status, setStatus] = useState<GeneratorStatus | null>(null)
  const [serviceError, setServiceError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [intervalConfig, setIntervalConfig] = useState({
    resume_interval_seconds: 30,
    job_interval_seconds: 60,
    flush_interval_seconds: 60,
  })

  const loadStatus = useCallback(async () => {
    try {
      const nextStatus = await fetchGeneratorStatus()
      setStatus(nextStatus)
      setServiceError(null)
    } catch (err) {
      setStatus(null)
      setServiceError(err instanceof Error ? err.message : String(err))
    }
  }, [fetchGeneratorStatus])

  useEffect(() => {
    const initial = window.setTimeout(() => void loadStatus(), 0)
    const interval = window.setInterval(() => void loadStatus(), 5000)
    return () => {
      window.clearTimeout(initial)
      window.clearInterval(interval)
    }
  }, [loadStatus])

  const handleStart = async () => {
    setLoading(true)
    try {
      await startGenerator(intervalConfig)
      window.setTimeout(() => void loadStatus(), 1000)
    } catch (err) {
      setServiceError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    if (!confirm('确定要停止数据生成器吗？')) return
    setLoading(true)
    try {
      await stopGenerator()
      window.setTimeout(() => void loadStatus(), 1000)
    } catch (err) {
      setServiceError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const running = status?.running ?? false
  const connected = !serviceError

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold">数据生成器控制</h1>
        <p className="text-muted-foreground">控制上游数据生成服务的启停和配置</p>
      </div>

      {serviceError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          生成器服务未连接：{serviceError}
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>运行状态</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <span className={`inline-block h-3 w-3 rounded-full ${running ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
            <span className="font-medium">{connected ? (running ? '运行中' : '已停止') : '服务未连接'}</span>
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <Metric title="已生成简历" value={status?.total_resumes ?? '-'} />
            <Metric title="已生成岗位" value={status?.total_jobs ?? '-'} />
            <Metric title="简历速率" value={`${status?.generation_rate?.resumes_per_minute?.toFixed(1) ?? '-'} 条/分钟`} />
            <Metric title="岗位速率" value={`${status?.generation_rate?.jobs_per_minute?.toFixed(1) ?? '-'} 条/分钟`} />
            <Metric title="缓冲区" value={status ? `简历:${status.buffer_size?.resumes ?? 0} 岗位:${status.buffer_size?.jobs ?? 0}` : '-'} />
          </div>

          {status?.last_flush_time && <div className="text-sm text-muted-foreground">最后刷新时间: {status.last_flush_time}</div>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>控制面板</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Button onClick={handleStart} disabled={!connected || running || loading}>启动生成器 / 应用配置</Button>
            <Button onClick={handleStop} disabled={!connected || !running || loading} variant="destructive">停止生成器</Button>
          </div>

          <div className="grid gap-4 pt-2 md:grid-cols-3">
            <NumberInput label="简历生成间隔（秒）" value={intervalConfig.resume_interval_seconds} disabled={running} onChange={(value) => setIntervalConfig({ ...intervalConfig, resume_interval_seconds: value })} />
            <NumberInput label="岗位生成间隔（秒）" value={intervalConfig.job_interval_seconds} disabled={running} onChange={(value) => setIntervalConfig({ ...intervalConfig, job_interval_seconds: value })} />
            <NumberInput label="HDFS刷新间隔（秒）" value={intervalConfig.flush_interval_seconds} disabled={running} onChange={(value) => setIntervalConfig({ ...intervalConfig, flush_interval_seconds: value })} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>最近生成数据预览</CardTitle></CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <PreviewList title="最新 5 条简历" rows={status?.recent_resumes?.map((resume) => `${resume.resume_id || '-'} · ${resume.name || '-'} · ${resume.education || '-'} · ${resume.skills || '-'}`) ?? []} />
          <PreviewList title="最新 5 条岗位" rows={status?.recent_jobs?.map((job) => `${job.job_id || '-'} · ${job.job_title || '-'} · ${job.department || '-'} · ${job.salary_range || '-'}`) ?? []} />
        </CardContent>
      </Card>
    </div>
  )
}

function Metric({ title, value }: { title: string; value: string | number }) {
  return (
    <Card>
      <CardHeader className="pb-1"><CardDescription>{title}</CardDescription></CardHeader>
      <CardContent><div className="text-xl font-bold">{value}</div></CardContent>
    </Card>
  )
}

function NumberInput({ label, value, disabled, onChange }: { label: string; value: number; disabled: boolean; onChange: (value: number) => void }) {
  return (
    <label className="block">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Input type="number" value={value} disabled={disabled} onChange={(e) => onChange(parseInt(e.target.value) || value)} />
    </label>
  )
}

function PreviewList({ title, rows }: { title: string; rows: string[] }) {
  return (
    <div className="rounded-md border p-3">
      <h3 className="mb-2 text-sm font-medium">{title}</h3>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">暂无数据</p>
      ) : (
        <ul className="space-y-1 text-sm">
          {rows.map((row) => <li key={row} className="truncate text-muted-foreground">{row}</li>)}
        </ul>
      )}
    </div>
  )
}
