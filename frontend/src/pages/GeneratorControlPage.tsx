import { useEffect, useState } from 'react'
import { useAppStore } from '@/store'
import type { GeneratorStatus } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function GeneratorControlPage() {
  const { startGenerator, stopGenerator, fetchGeneratorStatus } = useAppStore()
  const [status, setStatus] = useState<GeneratorStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [intervalConfig, setIntervalConfig] = useState({
    resume_interval_seconds: 30,
    job_interval_seconds: 60,
    flush_interval_seconds: 60,
  })

  const loadStatus = async () => {
    try {
      const s = await fetchGeneratorStatus()
      setStatus(s)
    } catch {
      setStatus(null)
    }
  }

  useEffect(() => {
    loadStatus()
    const interval = setInterval(loadStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleStart = async () => {
    setLoading(true)
    try {
      await startGenerator(intervalConfig)
      setTimeout(loadStatus, 1000)
    } catch (err) {
      console.error('Failed to start generator:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    if (!confirm('确定要停止数据生成器吗？')) return
    setLoading(true)
    try {
      await stopGenerator()
      setTimeout(loadStatus, 1000)
    } catch (err) {
      console.error('Failed to stop generator:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold">数据生成器控制</h1>
        <p className="text-muted-foreground">控制上游数据生成服务的启停和配置</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>运行状态</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <span className={`inline-block h-3 w-3 rounded-full ${status?.running ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
            <span className="font-medium">{status?.running ? '运行中' : '已停止'}</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card>
              <CardHeader className="pb-1">
                <CardDescription>已生成简历</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold">{status?.total_resumes ?? '-'}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1">
                <CardDescription>已生成岗位</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold">{status?.total_jobs ?? '-'}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1">
                <CardDescription>简历速率</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold">{status?.generation_rate?.resumes_per_minute?.toFixed(1) ?? '-'} 条/分钟</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1">
                <CardDescription>岗位速率</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold">{status?.generation_rate?.jobs_per_minute?.toFixed(1) ?? '-'} 条/分钟</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1">
                <CardDescription>缓冲区</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold">
                  {status ? `简历:${status.buffer_size?.resumes ?? 0} 岗位:${status.buffer_size?.jobs ?? 0}` : '-'}
                </div>
              </CardContent>
            </Card>
          </div>

          {status?.last_flush_time && (
            <div className="text-sm text-muted-foreground">
              最后刷新时间: {status.last_flush_time}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>控制面板</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Button onClick={handleStart} disabled={status?.running || loading}>
              启动生成器
            </Button>
            <Button onClick={handleStop} disabled={!status?.running || loading} variant="destructive">
              停止生成器
            </Button>
          </div>

          <div className="grid grid-cols-3 gap-4 pt-2">
            <div>
              <label className="text-sm text-muted-foreground">简历生成间隔（秒）</label>
              <Input
                type="number"
                value={intervalConfig.resume_interval_seconds}
                onChange={(e) => setIntervalConfig({ ...intervalConfig, resume_interval_seconds: parseInt(e.target.value) || 30 })}
                disabled={status?.running}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">岗位生成间隔（秒）</label>
              <Input
                type="number"
                value={intervalConfig.job_interval_seconds}
                onChange={(e) => setIntervalConfig({ ...intervalConfig, job_interval_seconds: parseInt(e.target.value) || 60 })}
                disabled={status?.running}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">HDFS刷新间隔（秒）</label>
              <Input
                type="number"
                value={intervalConfig.flush_interval_seconds}
                onChange={(e) => setIntervalConfig({ ...intervalConfig, flush_interval_seconds: parseInt(e.target.value) || 60 })}
                disabled={status?.running}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}