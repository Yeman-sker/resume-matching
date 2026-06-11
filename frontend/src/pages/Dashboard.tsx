import { useEffect } from 'react'
import { useAppStore } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Link } from 'react-router-dom'
import { Briefcase, Users, Zap, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

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
        <p className="text-muted-foreground">连接中...</p>
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
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold">简历-岗位匹配系统</h1>
        <p className="text-muted-foreground">实时监控系统运行状态</p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">简历总数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status.total_resumes.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">岗位总数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status.total_jobs.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">匹配总数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status.total_matches.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">最高匹配分</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats ? stats.max_total_score.toFixed(1) : '-'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">平均匹配分</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats ? stats.avg_total_score.toFixed(1) : '-'}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>系统状态</CardTitle>
            <CardDescription>各模块运行状态</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span>数据生成器</span>
              <span className={`flex items-center gap-1.5 ${status.data_generator_running ? 'text-green-600' : 'text-gray-400'}`}>
                <span className={`inline-block h-2 w-2 rounded-full ${status.data_generator_running ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
                {status.data_generator_running ? '运行中' : '已停止'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Streaming 处理</span>
              <span className={`flex items-center gap-1.5 ${status.streaming_running ? 'text-green-600' : 'text-gray-400'}`}>
                <span className={`inline-block h-2 w-2 rounded-full ${status.streaming_running ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
                {status.streaming_running ? '运行中' : '已停止'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>批处理任务</span>
              <span className={`flex items-center gap-1.5 ${status.batch_running ? 'text-green-600' : 'text-gray-400'}`}>
                <span className={`inline-block h-2 w-2 rounded-full ${status.batch_running ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
                {status.batch_running ? '运行中' : '已停止'}
              </span>
            </div>
            <div className="flex justify-between pt-2 border-t">
              <span className="text-muted-foreground text-sm">最后更新</span>
              <span className="text-muted-foreground text-sm">{status.last_update}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>分数分布</CardTitle>
            <CardDescription>各维度平均分</CardDescription>
          </CardHeader>
          <CardContent>
            {scoreDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={scoreDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="score" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[200px] text-muted-foreground text-sm">
                暂无统计数据
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>快捷入口</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Button asChild variant="outline">
            <Link to="/jobs"><Briefcase className="mr-2 h-4 w-4" />岗位匹配查询 <ArrowRight className="ml-1 h-3 w-3" /></Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/resumes"><Users className="mr-2 h-4 w-4" />简历推荐查询 <ArrowRight className="ml-1 h-3 w-3" /></Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/generator"><Zap className="mr-2 h-4 w-4" />数据生成器 <ArrowRight className="ml-1 h-3 w-3" /></Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}