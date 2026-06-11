import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAppStore } from '@/store'
import type { Match } from '@/types'
import MatchCard from '@/components/match/MatchCard'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import EmptyState from '@/components/common/EmptyState'
import { Input } from '@/components/ui/input'
import { Briefcase, Search } from 'lucide-react'

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

  const refreshJobs = useCallback(() => { void fetchJobs() }, [fetchJobs])

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
    if (!selectedJobId) { setMatches([]); setTotalMatches(0); return }
    setMatchesLoading(true); setMatchesError(null)
    try {
      const res = await fetchJobMatches(selectedJobId, limit)
      setMatches(res.matches); setTotalMatches(res.total_matches)
    } catch (err) {
      setMatches([]); setTotalMatches(0); setMatchesError(err instanceof Error ? err.message : String(err))
    } finally { setMatchesLoading(false) }
  }, [fetchJobMatches, limit, selectedJobId])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadMatches(), 0)
    return () => window.clearTimeout(timer)
  }, [loadMatches])

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Briefcase className="h-5 w-5" style={{ color: 'var(--accent)' }} />
        <div>
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--foreground)' }}>岗位匹配查询</h1>
          <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>选择岗位，查看最匹配的候选人</p>
        </div>
      </div>

      <div className="flex min-h-[calc(100vh-12rem)] gap-6">
        <div className="shrink-0 w-[320px] space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: 'var(--muted-foreground)' }} />
            <Input placeholder="搜索岗位名称..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          <select value={departmentFilter} onChange={(e) => setDepartmentFilter(e.target.value)}
            className="w-full rounded-sm px-3 py-2 text-sm"
            style={{ background: 'var(--card)', color: 'var(--foreground)', border: '1px solid var(--border)' }}>
            {departments.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
          <div className="rounded-sm overflow-auto max-h-[calc(100vh-18rem)]" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
            {loading ? <LoadingSpinner /> : filteredJobs.length === 0 ? (
              <EmptyState message={error || '暂无岗位数据'} />
            ) : filteredJobs.map((job) => (
              <div
                key={job.job_id}
                onClick={() => setSearchParams({ jobId: job.job_id })}
                className={`list-row px-3 py-2.5 cursor-pointer ${selectedJobId === job.job_id ? 'list-row--selected' : ''}`}
              >
                <div className="font-medium text-sm" style={{ color: 'var(--foreground)' }}>{job.job_title}</div>
                <div className="text-xs mt-0.5" style={{ color: 'var(--muted-foreground)' }}>{job.job_id} · {job.department} · {job.standard_location || job.location}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 space-y-4">
          {selectedJob ? (
            <>
              <div key={selectedJob.job_id} className="anim-enter p-4 space-y-2" style={{ background: 'var(--card)', borderRadius: '4px', border: '1px solid var(--border)' }}>
                <h3 className="font-semibold" style={{ color: 'var(--foreground)' }}>{selectedJob.job_title}</h3>
                <div className="grid gap-1.5 text-sm md:grid-cols-4">
                  <div><span style={{ color: 'var(--muted-foreground)' }}>部门:</span> <span style={{ color: 'var(--foreground)' }}>{selectedJob.department}</span></div>
                  <div><span style={{ color: 'var(--muted-foreground)' }}>城市:</span> <span style={{ color: 'var(--foreground)' }}>{selectedJob.standard_location || selectedJob.location}</span></div>
                  <div><span style={{ color: 'var(--muted-foreground)' }}>学历:</span> <span style={{ color: 'var(--foreground)' }}>{selectedJob.education_required}</span></div>
                  <div><span style={{ color: 'var(--muted-foreground)' }}>经验:</span> <span style={{ color: 'var(--foreground)' }}>{selectedJob.experience_required}</span></div>
                </div>
                <div className="text-sm"><span style={{ color: 'var(--muted-foreground)' }}>薪资:</span> <span style={{ color: 'var(--foreground)' }}>{selectedJob.salary_range}</span></div>
                <div className="text-sm"><span style={{ color: 'var(--muted-foreground)' }}>要求技能:</span> <span style={{ color: 'var(--foreground)' }}>{selectedJob.required_skill_items_raw || selectedJob.skills_required}</span></div>
                <div className="flex items-center gap-3 text-sm pt-1" style={{ color: 'var(--muted-foreground)' }}>
                  <span>匹配候选人: {totalMatches} 人</span>
                  <label className="flex items-center gap-1">显示 Top-N:
                    <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}
                      className="rounded-sm px-2 py-1 text-sm"
                      style={{ background: 'var(--card)', color: 'var(--foreground)', border: '1px solid var(--border)' }}>
                      {LIMIT_OPTIONS.map((v) => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </label>
                </div>
              </div>

              {matchesLoading ? <LoadingSpinner /> : matchesError ? <EmptyState message={matchesError} /> : matches.length === 0 ? (
                <EmptyState message="当前岗位暂无匹配的候选人" />
              ) : (
                <div key={`${selectedJobId}-${limit}`} className="stagger space-y-4">
                  {matches.map((match, idx) => <MatchCard key={match.resume_id} match={match} rank={idx + 1} mode="job" />)}
                </div>
              )}
            </>
          ) : <EmptyState message="请从左侧选择一个岗位查看匹配候选人" />}
        </div>
      </div>
    </div>
  )
}