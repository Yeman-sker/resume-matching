import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAppStore } from '@/store'
import type { Match } from '@/types'
import MatchCard from '@/components/match/MatchCard'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import EmptyState from '@/components/common/EmptyState'
import { Input } from '@/components/ui/input'
import { Users, Search } from 'lucide-react'

const LIMIT_OPTIONS = [10, 20, 50]

export default function ResumeRecommendPage() {
  const { resumes, fetchResumes, fetchResumeRecommendations } = useAppStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedResumeId = searchParams.get('resumeId') || ''
  const [matches, setMatches] = useState<Match[]>([])
  const [totalMatches, setTotalMatches] = useState(0)
  const [selectedResume, setSelectedResume] = useState<typeof resumes[0] | null>(null)
  const [search, setSearch] = useState('')
  const [limit, setLimit] = useState(20)
  const [matchesLoading, setMatchesLoading] = useState(false)

  const refreshResumes = useCallback(() => { void fetchResumes() }, [fetchResumes])

  useEffect(() => {
    refreshResumes()
    const timer = window.setInterval(refreshResumes, 60000)
    return () => window.clearInterval(timer)
  }, [refreshResumes])

  const filteredResumes = useMemo(
    () => resumes.filter((r) => {
      if (!search) return true
      return r.name.toLowerCase().includes(search.toLowerCase()) || r.resume_id.toLowerCase().includes(search.toLowerCase())
    }),
    [resumes, search],
  )

  useEffect(() => {
    if (selectedResumeId && resumes.length > 0) {
      const r = resumes.find((r) => r.resume_id === selectedResumeId)
      if (r) setSelectedResume(r)
      setMatchesLoading(true)
      fetchResumeRecommendations(selectedResumeId, limit).then((res) => {
        setMatches(res.matches); setTotalMatches(res.total_matches)
      }).catch(() => { setMatches([]); setTotalMatches(0) }).finally(() => setMatchesLoading(false))
    }
  }, [selectedResumeId, resumes, limit])

  const handleSelectResume = (resumeId: string) => setSearchParams({ resumeId })

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Users className="h-5 w-5" style={{ color: 'var(--accent)' }} />
        <div>
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--foreground)' }}>简历推荐查询</h1>
          <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>选择简历，查看最推荐的岗位</p>
        </div>
      </div>

      <div className="flex min-h-[calc(100vh-12rem)] gap-6">
        <div className="shrink-0 w-[320px] space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: 'var(--muted-foreground)' }} />
            <Input placeholder="搜索姓名..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          <div className="rounded-sm overflow-auto max-h-[calc(100vh-16rem)]" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
            {filteredResumes.length === 0 ? (
              <EmptyState message="暂无简历数据" />
            ) : filteredResumes.map((resume) => (
              <div
                key={resume.resume_id}
                onClick={() => handleSelectResume(resume.resume_id)}
                className={`list-row px-3 py-2.5 cursor-pointer ${selectedResumeId === resume.resume_id ? 'list-row--selected' : ''}`}
              >
                <div className="font-medium text-sm" style={{ color: 'var(--foreground)' }}>{resume.name}</div>
                <div className="text-xs mt-0.5" style={{ color: 'var(--muted-foreground)' }}>
                  {resume.resume_id} · {resume.education} · {resume.experience_years_num}年经验
                </div>
                {resume.skill_items_raw && (
                  <div className="text-xs mt-0.5 truncate" style={{ color: 'var(--muted-foreground)' }}>
                    {resume.skill_items_raw.replace(/\|/g, '、')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 space-y-4">
          {selectedResume ? (
            <>
              <div key={selectedResume.resume_id} className="anim-enter p-4 space-y-2" style={{ background: 'var(--card)', borderRadius: '4px', border: '1px solid var(--border)' }}>
                <h3 className="font-semibold" style={{ color: 'var(--foreground)' }}>{selectedResume.name}</h3>
                <div className="grid gap-1.5 text-sm md:grid-cols-4">
                  <div><span style={{ color: 'var(--muted-foreground)' }}>学历:</span> <span style={{ color: 'var(--foreground)' }}>{selectedResume.education}</span></div>
                  <div><span style={{ color: 'var(--muted-foreground)' }}>经验:</span> <span style={{ color: 'var(--foreground)' }}>{selectedResume.experience_years_num}年</span></div>
                  <div><span style={{ color: 'var(--muted-foreground)' }}>城市:</span> <span style={{ color: 'var(--foreground)' }}>{selectedResume.standard_location || selectedResume.location}</span></div>
                  <div><span style={{ color: 'var(--muted-foreground)' }}>期望薪资:</span> <span style={{ color: 'var(--foreground)' }}>{selectedResume.expected_salary}万/年</span></div>
                </div>
                <div className="flex items-center gap-3 text-sm pt-1" style={{ color: 'var(--muted-foreground)' }}>
                  <span>推荐岗位: {totalMatches} 个</span>
                  <label className="flex items-center gap-1">显示 Top-N:
                    <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}
                      className="rounded-sm px-2 py-1 text-sm"
                      style={{ background: 'var(--card)', color: 'var(--foreground)', border: '1px solid var(--border)' }}>
                      {LIMIT_OPTIONS.map((v) => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </label>
                </div>
              </div>

              {matchesLoading ? <LoadingSpinner /> : matches.length === 0 ? (
                <EmptyState message="该简历暂无推荐的岗位" />
              ) : (
                <div key={`${selectedResumeId}-${limit}`} className="stagger space-y-4">
                  {matches.map((match, idx) => <MatchCard key={match.job_id} match={match} rank={idx + 1} mode="resume" />)}
                </div>
              )}
            </>
          ) : <EmptyState message="请从左侧选择一份简历查看推荐岗位" />}
        </div>
      </div>
    </div>
  )
}