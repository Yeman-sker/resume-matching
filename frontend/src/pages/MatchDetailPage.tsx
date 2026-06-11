import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { useAppStore } from '@/store'
import type { MatchDetail as MatchDetailType } from '@/types'
import ScoreBar from '@/components/match/ScoreBar'
import SkillTags from '@/components/match/SkillTags'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function MatchDetailPage() {
  const { resumeId, jobId } = useParams()
  const [searchParams] = useSearchParams()
  const { fetchMatchDetail } = useAppStore()
  const [detail, setDetail] = useState<MatchDetailType | null>(null)
  const [loading, setLoading] = useState(true)

  const from = searchParams.get('from')
  const fromId = searchParams.get('fromId')
  const backLink = from === 'resumes' ? `/resumes?resumeId=${fromId}` : `/jobs?jobId=${fromId}`

  useEffect(() => {
    if (resumeId && jobId) {
      setLoading(true)
      fetchMatchDetail(resumeId, jobId)
        .then((data) => setDetail(data))
        .catch(() => setDetail(null))
        .finally(() => setLoading(false))
    }
  }, [resumeId, jobId])

  if (loading) return <LoadingSpinner />
  if (!detail) return <div className="text-center py-12 text-muted-foreground">未找到匹配详情</div>

  const { resume, job, scores, matched_skills, missing_skills, reason } = detail
  const formatSkills = (s: string) => s ? s.split('|').filter(Boolean) : []

  return (
    <div className="space-y-6">
      <div>
        <Link to={backLink} className="text-sm text-primary hover:underline">← 返回</Link>
        <h1 className="text-2xl font-bold mt-1">匹配详情</h1>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">简历信息</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1.5">
            <div><span className="text-muted-foreground">姓名:</span> {resume.name}</div>
            <div><span className="text-muted-foreground">学历:</span> {resume.education}</div>
            <div><span className="text-muted-foreground">经验:</span> {resume.experience_years_num}年</div>
            <div><span className="text-muted-foreground">城市:</span> {resume.standard_location || resume.location}</div>
            <div><span className="text-muted-foreground">期望薪资:</span> {resume.expected_salary}万/年</div>
            <div><span className="text-muted-foreground">技能:</span> {formatSkills(resume.standard_skills || resume.skills).join('、')}</div>
            {resume.certifications && resume.certifications !== '无' && (
              <div><span className="text-muted-foreground">证书:</span> {resume.certifications}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">岗位信息</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1.5">
            <div><span className="text-muted-foreground">岗位:</span> {job.job_title}</div>
            <div><span className="text-muted-foreground">部门:</span> {job.department}</div>
            <div><span className="text-muted-foreground">城市:</span> {job.standard_location || job.location}</div>
            <div><span className="text-muted-foreground">学历要求:</span> {job.education_required}</div>
            <div><span className="text-muted-foreground">经验要求:</span> {job.experience_required}</div>
            <div><span className="text-muted-foreground">薪资范围:</span> {job.salary_range}</div>
            <div><span className="text-muted-foreground">必备技能:</span> {formatSkills(job.required_skills_standard || job.skills_required).join('、')}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>匹配评分</CardTitle>
            <div className="text-2xl font-bold">{scores.total_score.toFixed(1)}</div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium text-sm">语义分 (权重 60%)</h4>
            <div className="pl-4 space-y-1">
              <ScoreBar label="TF-IDF 分" value={scores.tfidf_score} />
              <ScoreBar label="Word2Vec 分" value={scores.word2vec_score} />
            </div>
            <ScoreBar label="语义分" value={scores.semantic_score} />
          </div>

          <div className="space-y-2">
            <h4 className="font-medium text-sm">规则分 (权重 40%)</h4>
            <div className="pl-4 space-y-1">
              <ScoreBar label="技能分" value={scores.skill_score} weight="40%" />
              <ScoreBar label="学历分" value={scores.education_score} weight="20%" />
              <ScoreBar label="经验分" value={scores.experience_score} weight="15%" />
              <ScoreBar label="城市分" value={scores.city_score} weight="10%" />
              <ScoreBar label="薪资分" value={scores.salary_score} weight="10%" />
              <ScoreBar label="证书分" value={scores.certificate_score} weight="5%" />
            </div>
            <ScoreBar label="规则分" value={scores.rule_score} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">技能匹配</CardTitle>
        </CardHeader>
        <CardContent>
          <SkillTags matched={matched_skills || []} missing={missing_skills || []} />
          <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
            <span>绿色 = 共同技能</span>
            <span>红色 = 缺失技能</span>
          </div>
        </CardContent>
      </Card>

      {reason && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">推荐理由</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm whitespace-pre-line">{reason}</div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}