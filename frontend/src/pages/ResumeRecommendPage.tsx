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

export default function ResumeRecommendPage() {
  const { resumes, loading, error, fetchResumes, fetchResumeRecommendations } = useAppStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedResumeId = searchParams.get('resumeId') || ''
  const [matches, setMatches] = useState<Match[]>([])
  const [totalMatches, setTotalMatches] = useState(0)
  const [search, setSearch] = useState('')
  const [limit, setLimit] = useState(10)
  const [matchesLoading, setMatchesLoading] = useState(false)
  const [matchesError, setMatchesError] = useState<string | null>(null)

  const refreshResumes = useCallback(() => {
    void fetchResumes()
  }, [fetchResumes])

  useEffect(() => {
    refreshResumes()
    const timer = window.setInterval(refreshResumes, 60000)
    return () => window.clearInterval(timer)
  }, [refreshResumes])

  const filteredResumes = useMemo(
    () => resumes.filter((resume) => {
      const keyword = search.toLowerCase()
      return !keyword || resume.name.toLowerCase().includes(keyword) || resume.resume_id.toLowerCase().includes(keyword)
    }),
    [resumes, search],
  )

  const selectedResume = useMemo(
    () => resumes.find((resume) => resume.resume_id === selectedResumeId) ?? null,
    [resumes, selectedResumeId],
  )

  const loadRecommendations = useCallback(async () => {
    if (!selectedResumeId) {
      setMatches([])
      setTotalMatches(0)
      return
    }
    setMatchesLoading(true)
    setMatchesError(null)
    try {
      const res = await fetchResumeRecommendations(selectedResumeId, limit)
      setMatches(res.matches)
      setTotalMatches(res.total_matches)
    } catch (err) {
      setMatches([])
      setTotalMatches(0)
      setMatchesError(err instanceof Error ? err.message : String(err))
    } finally {
      setMatchesLoading(false)
    }
  }, [fetchResumeRecommendations, limit, selectedResumeId])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadRecommendations(), 0)
    return () => window.clearTimeout(timer)
  }, [loadRecommendations])

  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col gap-6 md:flex-row">
      <div className="shrink-0 space-y-3 md:w-[320px]">
        <Input placeholder="搜索姓名..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <div className="border rounded-lg overflow-auto max-h-[calc(100vh-14rem)]">
          {loading ? <LoadingSpinner /> : filteredResumes.length === 0 ? (
            <EmptyState message={error || '暂无简历数据，请确保中游数据处理服务正在运行'} />
          ) : filteredResumes.map((resume) => (
            <div
              key={resume.resume_id}
              onClick={() => setSearchParams({ resumeId: resume.resume_id })}
              className={`px-3 py-2.5 cursor-pointer border-b last:border-b-0 hover:bg-accent transition-colors ${selectedResumeId === resume.resume_id ? 'bg-accent' : ''}`}
            >
              <div className="font-medium text-sm">{resume.name}</div>
              <div className="text-xs text-muted-foreground mt-0.5">{resume.resume_id} · {resume.education} · {resume.experience_years_num}年经验</div>
              {resume.standard_skills && <div className="text-xs text-muted-foreground mt-0.5 truncate">{resume.standard_skills.replace(/\|/g, '、')}</div>}
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 space-y-4">
        {selectedResume ? (
          <>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-lg">{selectedResume.name}</CardTitle></CardHeader>
              <CardContent>
                <div className="grid gap-2 text-sm md:grid-cols-4">
                  <div><span className="text-muted-foreground">学历:</span> {selectedResume.education}</div>
                  <div><span className="text-muted-foreground">经验:</span> {selectedResume.experience_years_num}年</div>
                  <div><span className="text-muted-foreground">城市:</span> {selectedResume.standard_location || selectedResume.location}</div>
                  <div><span className="text-muted-foreground">期望薪资:</span> {selectedResume.expected_salary}万/年</div>
                </div>
                <div className="mt-1 text-sm"><span className="text-muted-foreground">技能:</span> {selectedResume.standard_skills || selectedResume.skills}</div>
                <div className="mt-3 flex items-center gap-3 text-sm text-muted-foreground">
                  <span>推荐岗位: {totalMatches} 个</span>
                  <label className="flex items-center gap-1">显示 Top-N:
                    <select value={limit} onChange={(e) => setLimit(Number(e.target.value))} className="border rounded px-2 py-1 text-foreground">
                      {LIMIT_OPTIONS.map((value) => <option key={value} value={value}>{value}</option>)}
                    </select>
                  </label>
                </div>
              </CardContent>
            </Card>

            {matchesLoading ? <LoadingSpinner /> : matchesError ? <EmptyState message={matchesError} /> : matches.length === 0 ? (
              <EmptyState message="当前简历暂无推荐岗位" />
            ) : matches.map((match, idx) => <MatchCard key={match.job_id} match={match} rank={idx + 1} mode="resume" />)}
          </>
        ) : <EmptyState message="请从左侧选择一份简历查看推荐岗位" />}
      </div>
    </div>
  )
}
