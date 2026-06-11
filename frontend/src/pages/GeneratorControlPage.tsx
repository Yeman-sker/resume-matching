import { useEffect, useState } from 'react'
import { useAppStore } from '@/store'
import type { GeneratorStatus } from '@/types'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Zap, Play, Square, Activity, FileText, Briefcase, TrendingUp } from 'lucide-react'

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
    try { setStatus(await fetchGeneratorStatus()) } catch { setStatus(null) }
  }

  useEffect(() => {
    loadStatus()
    const interval = setInterval(loadStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleStart = async () => {
    setLoading(true)
    try { await startGenerator(intervalConfig); setTimeout(loadStatus, 1000) }
    catch (err) { console.error('Failed to start generator:', err) }
    finally { setLoading(false) }
  }

  const handleStop = async () => {
    if (!confirm('确定要停止数据生成器吗？')) return
    setLoading(true)
    try { await stopGenerator(); setTimeout(loadStatus, 1000) }
    catch (err) { console.error('Failed to stop generator:', err) }
    finally { setLoading(false) }
  }

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
    <div className="space-y-6 stagger">
      <div className="flex items-center gap-2">
        <Zap className="h-5 w-5" style={{ color: 'var(--accent)' }} />
        <div>
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--foreground)' }}>数据生成器控制</h1>
          <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>控制上游数据生成服务的启停和配置</p>
        </div>
      </div>

      <div style={cardStyle}>
        <div style={cardBorderOverlay} />
        <div className="relative">
          <h3 className="flex items-center gap-2 font-semibold mb-4" style={{ color: 'var(--foreground)' }}>
            <Activity className="h-4 w-4" style={{ color: 'var(--accent)' }} />
            运行状态
          </h3>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className={`inline-block h-2.5 w-2.5 rounded-full transition-colors duration-300 ${status?.running ? 'pulse-dot' : ''}`}
                style={{ background: status?.running ? '#1f8a65' : 'var(--muted-foreground)' }} />
              <span className="font-semibold text-lg" style={{ color: 'var(--foreground)' }}>{status?.running ? '运行中' : '已停止'}</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted-foreground)' }}><FileText className="h-3.5 w-3.5" />简历数</div>
                <div className="text-xl font-bold mt-1" style={{ color: 'var(--foreground)' }}>{status?.total_resumes ?? '-'}</div>
              </div>
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted-foreground)' }}><Briefcase className="h-3.5 w-3.5" />岗位数</div>
                <div className="text-xl font-bold mt-1" style={{ color: 'var(--foreground)' }}>{status?.total_jobs ?? '-'}</div>
              </div>
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted-foreground)' }}><TrendingUp className="h-3.5 w-3.5" />简历速率</div>
                <div className="text-xl font-bold mt-1" style={{ color: 'var(--foreground)' }}>{status?.generation_rate?.resumes_per_minute?.toFixed(1) ?? '-'}<span className="text-sm font-normal" style={{ color: 'var(--muted-foreground)' }}> 条/分</span></div>
              </div>
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--muted-foreground)' }}><TrendingUp className="h-3.5 w-3.5" />岗位速率</div>
                <div className="text-xl font-bold mt-1" style={{ color: 'var(--foreground)' }}>{status?.generation_rate?.jobs_per_minute?.toFixed(1) ?? '-'}<span className="text-sm font-normal" style={{ color: 'var(--muted-foreground)' }}> 条/分</span></div>
              </div>
              <div className="p-3 rounded-sm" style={{ background: 'var(--secondary)' }}>
                <div className="text-xs" style={{ color: 'var(--muted-foreground)' }}>缓冲区</div>
                <div className="text-xl font-bold mt-1" style={{ color: 'var(--foreground)' }}>
                  {status ? `R:${status.buffer_size?.resumes ?? 0} J:${status.buffer_size?.jobs ?? 0}` : '-'}
                </div>
              </div>
            </div>

            {status?.last_flush_time && (
              <div className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                最后刷新: {status.last_flush_time}
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
                onClick={handleStart}
                disabled={status?.running || loading}
                className="gap-2"
                style={{ background: status?.running || loading ? 'var(--secondary)' : 'var(--accent)', color: status?.running || loading ? 'var(--muted-foreground)' : '#fff', border: 'none' }}
              >
                <Play className="h-4 w-4" />
                启动生成器
              </Button>
              <Button
                onClick={handleStop}
                disabled={!status?.running || loading}
                variant="outline"
                className="gap-2"
                style={{ borderColor: '#cf2d56', color: '#cf2d56' }}
              >
                <Square className="h-4 w-4" />
                停止生成器
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="text-sm" style={{ color: 'var(--muted-foreground)' }}>简历生成间隔（秒）</label>
                <Input type="number" value={intervalConfig.resume_interval_seconds} onChange={(e) => setIntervalConfig({ ...intervalConfig, resume_interval_seconds: parseInt(e.target.value) || 30 })} disabled={status?.running} />
              </div>
              <div>
                <label className="text-sm" style={{ color: 'var(--muted-foreground)' }}>岗位生成间隔（秒）</label>
                <Input type="number" value={intervalConfig.job_interval_seconds} onChange={(e) => setIntervalConfig({ ...intervalConfig, job_interval_seconds: parseInt(e.target.value) || 60 })} disabled={status?.running} />
              </div>
              <div>
                <label className="text-sm" style={{ color: 'var(--muted-foreground)' }}>HDFS刷新间隔（秒）</label>
                <Input type="number" value={intervalConfig.flush_interval_seconds} onChange={(e) => setIntervalConfig({ ...intervalConfig, flush_interval_seconds: parseInt(e.target.value) || 60 })} disabled={status?.running} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}