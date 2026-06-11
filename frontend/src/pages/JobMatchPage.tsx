import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAppStore } from '@/store'
import type { Match } from '@/types'
import MatchCard from '@/components/match/MatchCard'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import EmptyState from '@/components/common/EmptyState'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

const LIMIT_OPTIONS = [10, 20, 50]

export default function JobMatchPage() {
  const { jobs, loading, error, fetchJobs, fetchJobMatches } = useAppStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedJobId = searchParams.get('jobId') || ''
  const [matches, setMatches] = useState<Match[]>([])
  const [totalMatches, setTotalMatches] = useState(0)
  const [search, setSearch] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState<string>('全部部门')
  const [limit, setLimit] = useState(10)
  const [matchesLoading, setMatchesLoading] = useState(false)
  const [matchesError, setMatchesError] = useState<string | null>(null)

  const refreshJobs = useCallback(() => {
    void fetchJobs()
  }, [fetchJobs])

  useEffect(() => {
    refreshJobs()
    const timer = window.setInterval(refreshJobs, 60000)
    return () => window.clearInterval(timer)
  }, [refreshJobs])

  const departments = useMemo(
    () => ['全部部门', ...Array.from(new Set(jobs.map((job) => job.department).filter(Boolean)))],
    [jobs],
  )

  const filteredJobs = useMemo(
    () => jobs.filter((job) => {
      const keyword = search.toLowerCase()
      const matchesSearch = !keyword || job.job_title.toLowerCase().includes(keyword) || job.job_id.toLowerCase().includes(keyword)
      const matchesDept = departmentFilter === '全部部门' || job.department === departmentFilter
      return matchesSearch && matchesDept
    }),
    [departmentFilter, jobs, search],
  )

  const selectedJob = useMemo(
    () => jobs.find((job) => job.job_id === selectedJobId) ?? null,
    [jobs, selectedJobId],
  )

  const loadMatches = useCallback(async () => {
    if (!selectedJobId) {
      setMatches([])
      setTotalMatches(0)
      return
    }
    setMatchesLoading(true)
    setMatchesError(null)
    try {
      const res = await fetchJobMatches(selectedJobId, limit)
      setMatches(res.matches)
      setTotalMatches(res.total_matches)
    } catch (err) {
      setMatches([])
      setTotalMatches(0)
      setMatchesError(err instanceof Error ? err.message : String(err))
    } finally {
      setMatchesLoading(false)
    }
  }, [fetchJobMatches, limit, selectedJobId])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadMatches(), 0)
    return () => window.clearTimeout(timer)
  }, [loadMatches])

  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col gap-6 md:flex-row">
      <div className="shrink-0 space-y-3 md:w-[320px]">
        <Input placeholder="搜索岗位名称..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={departmentFilter} onChange={(e) => setDepartmentFilter(e.target.value)} className="w-full border rounded-md px-3 py-2 text-sm">
          {departments.map((department) => <option key={department} value={department}>{department}</option>)}
        </select>
        <div className="border rounded-lg overflow-auto max-h-[calc(100vh-16rem)]">
          {loading ? <LoadingSpinner /> : filteredJobs.length === 0 ? (
            <EmptyState message={error || '暂无岗位数据，请确保中游数据处理服务正在运行'} />
          ) : filteredJobs.map((job) => (
            <div
              key={job.job_id}
              onClick={() => setSearchParams({ jobId: job.job_id })}
              className={`px-3 py-2.5 cursor-pointer border-b last:border-b-0 hover:bg-accent transition-colors ${selectedJobId === job.job_id ? 'bg-accent' : ''}`}
            >
              <div className="font-medium text-sm">{job.job_title}</div>
              <div className="text-xs text-muted-foreground mt-0.5">{job.job_id} · {job.department} · {job.standard_location || job.location}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 space-y-4">
        {selectedJob ? (
          <>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-lg">{selectedJob.job_title}</CardTitle></CardHeader>
              <CardContent>
                <div className="grid gap-2 text-sm md:grid-cols-4">
                  <div><span className="text-muted-foreground">部门:</span> {selectedJob.department}</div>
                  <div><span className="text-muted-foreground">城市:</span> {selectedJob.standard_location || selectedJob.location}</div>
                  <div><span className="text-muted-foreground">学历:</span> {selectedJob.education_required}</div>
                  <div><span className="text-muted-foreground">经验:</span> {selectedJob.experience_required}</div>
                </div>
                <div className="mt-1 text-sm"><span className="text-muted-foreground">薪资:</span> {selectedJob.salary_range}</div>
                <div className="mt-1 text-sm"><span className="text-muted-foreground">要求技能:</span> {selectedJob.required_skills_standard || selectedJob.skills_required}</div>
                <div className="mt-3 flex items-center gap-3 text-sm text-muted-foreground">
                  <span>匹配候选人: {totalMatches} 人</span>
                  <label className="flex items-center gap-1">显示 Top-N:
                    <select value={limit} onChange={(e) => setLimit(Number(e.target.value))} className="border rounded px-2 py-1 text-foreground">
                      {LIMIT_OPTIONS.map((value) => <option key={value} value={value}>{value}</option>)}
                    </select>
                  </label>
                </div>
              </CardContent>
            </Card>

            {matchesLoading ? <LoadingSpinner /> : matchesError ? <EmptyState message={matchesError} /> : matches.length === 0 ? (
              <EmptyState message="当前岗位暂无匹配的候选人" />
            ) : matches.map((match, idx) => <MatchCard key={match.resume_id} match={match} rank={idx + 1} mode="job" />)}
          </>
        ) : <EmptyState message="请从左侧选择一个岗位查看匹配候选人" />}
      </div>
    </div>
  )
}
