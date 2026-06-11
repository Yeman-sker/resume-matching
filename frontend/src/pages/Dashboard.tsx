import { useEffect } from 'react'
import { useAppStore } from '@/store'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Link } from 'react-router-dom'
import { Briefcase, Users, Zap, ArrowRight, FileText, Trophy, BarChart3, Activity, Radio } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
}

function StatCard({ title, value, icon }: StatCardProps) {
  return (
    <div className="card--stat" style={{ position: 'relative', background: 'var(--card)', borderRadius: '4px', paddingInline: '1.5rem', paddingTop: '1.25rem', paddingBottom: '1.5rem' }}>
      <div style={{ position: 'absolute', inset: 0, borderRadius: '4px', border: '1px solid var(--border)', pointerEvents: 'none' }} />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium" style={{ color: 'var(--muted-foreground)' }}>{title}</p>
          <p className="text-2xl font-bold mt-1" style={{ color: 'var(--foreground)' }}>{value}</p>
        </div>
        <div className="flex items-center justify-center h-9 w-9 rounded" style={{ background: 'var(--secondary)', color: 'var(--foreground)' }}>
          {icon}
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { status, stats, connectWS, disconnectWS, fetchStats } = useAppStore()

  useEffect(() => {
    connectWS()
    fetchStats()
    const statsInterval = setInterval(() => fetchStats(), 60000)
    return () => {
      disconnectWS()
      clearInterval(statsInterval)
    }
  }, [connectWS, disconnectWS, fetchStats])

  if (!status) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <Radio className="h-8 w-8 mx-auto animate-pulse" style={{ color: 'var(--muted-foreground)' }} />
          <p style={{ color: 'var(--muted-foreground)' }}>正在连接后端...</p>
          <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>请确保后端服务（端口 8002）正在运行</p>
        </div>
      </div>
    )
  }

  const scoreDistribution = stats?.score_distribution
    ? Object.entries(stats.score_distribution).map(([key, value]) => ({
        name: key.replace('_avg', '').replace('_', ' '),
        score: Math.round(value * 10) / 10,
      }))
    : []

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight" style={{ color: 'var(--foreground)' }}>
          简历-岗位匹配系统
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted-foreground)' }}>
          实时监控系统运行状态与数据分析
        </p>
      </div>

      <div className="grid gap-4 grid-cols-2 md:grid-cols-5">
        <StatCard
          title="简历总数"
          value={status.total_resumes.toLocaleString()}
          icon={<FileText className="h-4 w-4" />}
        />
        <StatCard
          title="岗位总数"
          value={status.total_jobs.toLocaleString()}
          icon={<Briefcase className="h-4 w-4" />}
        />
        <StatCard
          title="匹配总数"
          value={status.total_matches.toLocaleString()}
          icon={<BarChart3 className="h-4 w-4" />}
        />
        <StatCard
          title="最高匹配分"
          value={stats ? stats.max_total_score.toFixed(1) : '-'}
          icon={<Trophy className="h-4 w-4" />}
        />
        <StatCard
          title="平均匹配分"
          value={stats ? stats.avg_total_score.toFixed(1) : '-'}
          icon={<Activity className="h-4 w-4" />}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="card" style={{ position: 'relative', background: 'var(--card)', borderRadius: '4px', padding: '1.5rem' }}>
          <div style={{ position: 'absolute', inset: 0, borderRadius: '4px', border: '1px solid var(--border)', pointerEvents: 'none' }} />
          <div className="mb-4">
            <h3 className="font-semibold" style={{ color: 'var(--foreground)' }}>系统状态</h3>
            <p className="text-xs mt-0.5" style={{ color: 'var(--muted-foreground)' }}>各模块运行状态</p>
          </div>
          <div className="space-y-3">
            <StatusRow label="数据生成器" running={status.data_generator_running} />
            <StatusRow label="Streaming 处理" running={status.streaming_running} />
            <StatusRow label="批处理任务" running={status.batch_running} />
            <div className="flex justify-between pt-3" style={{ borderTop: '1px solid var(--border)' }}>
              <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>最后更新</span>
              <span className="text-xs font-mono" style={{ color: 'var(--muted-foreground)' }}>{status.last_update}</span>
            </div>
          </div>
        </div>

        <div className="card" style={{ position: 'relative', background: 'var(--card)', borderRadius: '4px', padding: '1.5rem' }}>
          <div style={{ position: 'absolute', inset: 0, borderRadius: '4px', border: '1px solid var(--border)', pointerEvents: 'none' }} />
          <div className="mb-4">
            <h3 className="font-semibold" style={{ color: 'var(--foreground)' }}>分数分布</h3>
            <p className="text-xs mt-0.5" style={{ color: 'var(--muted-foreground)' }}>各维度平均分</p>
          </div>
          {scoreDistribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={scoreDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} />
                <Tooltip contentStyle={{ borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--card)', color: 'var(--foreground)' }} />
                <Bar dataKey="score" fill="#1f8a65" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[200px] text-sm" style={{ color: 'var(--muted-foreground)' }}>
              暂无统计数据
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ position: 'relative', background: 'var(--card)', borderRadius: '4px', padding: '1.5rem' }}>
        <div style={{ position: 'absolute', inset: 0, borderRadius: '4px', border: '1px solid var(--border)', pointerEvents: 'none' }} />
        <h3 className="font-semibold mb-4" style={{ color: 'var(--foreground)' }}>快捷入口</h3>
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-3">
          <Link to="/jobs" className="flex items-center gap-3 p-3 rounded-sm transition-colors" style={{ background: 'var(--secondary)' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--warm-card-03)' }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--secondary)' }}>
            <Briefcase className="h-5 w-5 shrink-0" style={{ color: 'var(--accent)' }} />
            <div className="min-w-0">
              <div className="font-medium text-sm" style={{ color: 'var(--foreground)' }}>岗位匹配</div>
              <div className="text-xs" style={{ color: 'var(--muted-foreground)' }}>查看岗位的候选人匹配</div>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 shrink-0" style={{ color: 'var(--muted-foreground)' }} />
          </Link>
          <Link to="/resumes" className="flex items-center gap-3 p-3 rounded-sm transition-colors" style={{ background: 'var(--secondary)' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--warm-card-03)' }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--secondary)' }}>
            <Users className="h-5 w-5 shrink-0" style={{ color: 'var(--accent)' }} />
            <div className="min-w-0">
              <div className="font-medium text-sm" style={{ color: 'var(--foreground)' }}>简历推荐</div>
              <div className="text-xs" style={{ color: 'var(--muted-foreground)' }}>查看简历的推荐岗位</div>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 shrink-0" style={{ color: 'var(--muted-foreground)' }} />
          </Link>
          <Link to="/generator" className="flex items-center gap-3 p-3 rounded-sm transition-colors" style={{ background: 'var(--secondary)' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--warm-card-03)' }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--secondary)' }}>
            <Zap className="h-5 w-5 shrink-0" style={{ color: 'var(--accent)' }} />
            <div className="min-w-0">
              <div className="font-medium text-sm" style={{ color: 'var(--foreground)' }}>生成器控制</div>
              <div className="text-xs" style={{ color: 'var(--muted-foreground)' }}>启停数据生成服务</div>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 shrink-0" style={{ color: 'var(--muted-foreground)' }} />
          </Link>
        </div>
      </div>
    </div>
  )
}

function StatusRow({ label, running }: { label: string; running: boolean }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm font-medium" style={{ color: 'var(--foreground)' }}>{label}</span>
      <span className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-medium"
        style={{ background: running ? 'rgba(31,138,101,0.12)' : 'var(--secondary)', color: running ? '#1f8a65' : 'var(--muted-foreground)' }}>
        <span className="inline-block h-1.5 w-1.5 rounded-full"
          style={{ background: running ? '#1f8a65' : 'var(--warm-text-mid)' }} />
        {running ? '运行中' : '已停止'}
      </span>
    </div>
  )
}