import { useEffect } from 'react'
import { useSystemStore } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function Dashboard() {
  const { status, connectWS, disconnectWS } = useSystemStore()

  useEffect(() => {
    connectWS()
    return () => disconnectWS()
  }, [connectWS, disconnectWS])

  if (!status) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">连接中...</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">简历-岗位匹配系统</h1>
        <p className="text-muted-foreground">实时监控系统运行状态</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>简历总数</CardTitle>
            <CardDescription>已处理的简历数量</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{status.total_resumes}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>岗位总数</CardTitle>
            <CardDescription>已处理的岗位数量</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{status.total_jobs}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>匹配总数</CardTitle>
            <CardDescription>已完成的匹配记录</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{status.total_matches}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>系统状态</CardTitle>
          <CardDescription>各模块运行状态</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span>数据生成器</span>
            <span className={status.data_generator_running ? 'text-green-600' : 'text-gray-400'}>
              {status.data_generator_running ? '运行中' : '已停止'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Streaming 处理</span>
            <span className={status.streaming_running ? 'text-green-600' : 'text-gray-400'}>
              {status.streaming_running ? '运行中' : '已停止'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>批处理任务</span>
            <span className={status.batch_running ? 'text-green-600' : 'text-gray-400'}>
              {status.batch_running ? '运行中' : '已停止'}
            </span>
          </div>
          <div className="flex justify-between pt-2 border-t">
            <span className="text-muted-foreground">最后更新</span>
            <span className="text-muted-foreground">{status.last_update}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
