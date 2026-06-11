import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAppStore } from '@/store'
import type { Resume, Match } from '@/types'
import MatchCard from '@/components/match/MatchCard'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import EmptyState from '@/components/common/EmptyState'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

export default function ResumeRecommendPage() {
  const { resumes, fetchResumes, fetchResumeRecommendations } = useAppStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedResumeId = searchParams.get('resumeId') || ''
  const [matches, setMatches] = useState<Match[]>([])
  const [totalMatches, setTotalMatches] = useState(0)
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null)
  const [search, setSearch] = useState('')
  const [matchesLoading, setMatchesLoading] = useState(false)

  useEffect(() => {
    fetchResumes()
  }, [fetchResumes])

  const filteredResumes = resumes.filter((resume) => {
    if (!search) return true
    return (
      resume.name.toLowerCase().includes(search.toLowerCase()) ||
      resume.resume_id.toLowerCase().includes(search.toLowerCase())
    )
  })

  useEffect(() => {
    if (selectedResumeId && resumes.length > 0) {
      const resume = resumes.find((r) => r.resume_id === selectedResumeId)
      if (resume) setSelectedResume(resume)
      setMatchesLoading(true)
      fetchResumeRecommendations(selectedResumeId, 50).then((res) => {
        setMatches(res.matches)
        setTotalMatches(res.total_matches)
        setMatchesLoading(false)
      }).catch(() => setMatchesLoading(false))
    }
  }, [selectedResumeId, resumes])

  const handleSelectResume = (resumeId: string) => {
    setSearchParams({ resumeId })
  }

  return (
    <div className="flex gap-6 min-h-[calc(100vh-8rem)]">
      <div className="w-[320px] shrink-0 space-y-3">
        <Input
          placeholder="搜索姓名..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="border rounded-lg overflow-auto max-h-[calc(100vh-14rem)]">
          {filteredResumes.length === 0 ? (
            <EmptyState message="暂无简历数据" />
          ) : (
            filteredResumes.map((resume) => (
              <div
                key={resume.resume_id}
                onClick={() => handleSelectResume(resume.resume_id)}
                className={`px-3 py-2.5 cursor-pointer border-b last:border-b-0 hover:bg-accent transition-colors ${
                  selectedResumeId === resume.resume_id ? 'bg-accent' : ''
                }`}
              >
                <div className="font-medium text-sm">{resume.name}</div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {resume.resume_id} · {resume.education} · {resume.experience_years_num}年经验
                </div>
                {resume.standard_skills && (
                  <div className="text-xs text-muted-foreground mt-0.5 truncate">
                    {resume.standard_skills.replace(/\|/g, '、')}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="flex-1 space-y-4">
        {selectedResume ? (
          <>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{selectedResume.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-2 text-sm">
                  <div><span className="text-muted-foreground">学历:</span> {selectedResume.education}</div>
                  <div><span className="text-muted-foreground">经验:</span> {selectedResume.experience_years_num}年</div>
                  <div><span className="text-muted-foreground">城市:</span> {selectedResume.standard_location || selectedResume.location}</div>
                  <div><span className="text-muted-foreground">期望薪资:</span> {selectedResume.expected_salary}万/年</div>
                </div>
                <div className="mt-1 text-sm text-muted-foreground">
                  推荐岗位: {totalMatches} 个
                </div>
              </CardContent>
            </Card>

            {matchesLoading ? (
              <LoadingSpinner />
            ) : matches.length === 0 ? (
              <EmptyState message="暂无推荐的岗位" />
            ) : (
              matches.map((match, idx) => (
                <MatchCard key={match.job_id} match={match} rank={idx + 1} mode="resume" />
              ))
            )}
          </>
        ) : (
          <EmptyState message="请从左侧选择一份简历查看推荐岗位" />
        )}
      </div>
    </div>
  )
}