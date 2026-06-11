import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAppStore } from '@/store'
import type { Job, Match } from '@/types'
import MatchCard from '@/components/match/MatchCard'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import EmptyState from '@/components/common/EmptyState'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

export default function JobMatchPage() {
  const { jobs, fetchJobs, fetchJobMatches } = useAppStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedJobId = searchParams.get('jobId') || ''
  const [matches, setMatches] = useState<Match[]>([])
  const [totalMatches, setTotalMatches] = useState(0)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [search, setSearch] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState<string>('全部部门')
  const [matchesLoading, setMatchesLoading] = useState(false)

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  const departments = ['全部部门', ...Array.from(new Set(jobs.map((j) => j.department).filter(Boolean)))]

  const filteredJobs = jobs.filter((job) => {
    const matchesSearch = !search || job.job_title.toLowerCase().includes(search.toLowerCase()) || job.job_id.toLowerCase().includes(search.toLowerCase())
    const matchesDept = departmentFilter === '全部部门' || job.department === departmentFilter
    return matchesSearch && matchesDept
  })

  useEffect(() => {
    if (selectedJobId && jobs.length > 0) {
      const job = jobs.find((j) => j.job_id === selectedJobId)
      if (job) setSelectedJob(job)
      setMatchesLoading(true)
      fetchJobMatches(selectedJobId, 50).then((res) => {
        setMatches(res.matches)
        setTotalMatches(res.total_matches)
        setMatchesLoading(false)
      }).catch(() => setMatchesLoading(false))
    }
  }, [selectedJobId, jobs])

  const handleSelectJob = (jobId: string) => {
    setSearchParams({ jobId })
  }

  return (
    <div className="flex gap-6 min-h-[calc(100vh-8rem)]">
      <div className="w-[320px] shrink-0 space-y-3">
        <Input
          placeholder="搜索岗位名称..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className="w-full border rounded-md px-3 py-2 text-sm"
        >
          {departments.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <div className="border rounded-lg overflow-auto max-h-[calc(100vh-16rem)]">
          {filteredJobs.length === 0 ? (
            <EmptyState message="暂无岗位数据" />
          ) : (
            filteredJobs.map((job) => (
              <div
                key={job.job_id}
                onClick={() => handleSelectJob(job.job_id)}
                className={`px-3 py-2.5 cursor-pointer border-b last:border-b-0 hover:bg-accent transition-colors ${
                  selectedJobId === job.job_id ? 'bg-accent' : ''
                }`}
              >
                <div className="font-medium text-sm">{job.job_title}</div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {job.job_id} · {job.department} · {job.standard_location || job.location}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="flex-1 space-y-4">
        {selectedJob ? (
          <>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{selectedJob.job_title}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-2 text-sm">
                  <div><span className="text-muted-foreground">部门:</span> {selectedJob.department}</div>
                  <div><span className="text-muted-foreground">城市:</span> {selectedJob.standard_location || selectedJob.location}</div>
                  <div><span className="text-muted-foreground">学历:</span> {selectedJob.education_required}</div>
                  <div><span className="text-muted-foreground">经验:</span> {selectedJob.experience_required}</div>
                </div>
                <div className="mt-1 text-sm">
                  <span className="text-muted-foreground">薪资:</span> {selectedJob.salary_range}
                </div>
                <div className="mt-1 text-sm text-muted-foreground">
                  匹配候选人: {totalMatches} 人
                </div>
              </CardContent>
            </Card>

            {matchesLoading ? (
              <LoadingSpinner />
            ) : matches.length === 0 ? (
              <EmptyState message="暂无匹配的候选人" />
            ) : (
              matches.map((match, idx) => (
                <MatchCard key={match.resume_id} match={match} rank={idx + 1} mode="job" />
              ))
            )}
          </>
        ) : (
          <EmptyState message="请从左侧选择一个岗位查看匹配候选人" />
        )}
      </div>
    </div>
  )
}