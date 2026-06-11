import { useCallback, useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { useAppStore } from '@/store'
import type { MatchDetail as MatchDetailType } from '@/types'
import ScoreBar from '@/components/match/ScoreBar'
import ScoreRing from '@/components/match/ScoreRing'
import SkillTags from '@/components/match/SkillTags'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import { ArrowLeft, User, Briefcase, Target } from 'lucide-react'

export default function MatchDetailPage() {
  const { resumeId, jobId } = useParams()
  const [searchParams] = useSearchParams()
  const { fetchMatchDetail } = useAppStore()
  const [detail, setDetail] = useState<MatchDetailType | null>(null)
  const [loading, setLoading] = useState(true)

  const from = searchParams.get('from')
  const fromId = searchParams.get('fromId')
  const backLink = from === 'resumes'
    ? `/resumes?resumeId=${fromId || resumeId || ''}`
    : `/jobs?jobId=${fromId || jobId || ''}`

  const loadDetail = useCallback(async () => {
    if (resumeId && jobId) {
      setLoading(true)
      try {
        const data = await fetchMatchDetail(resumeId, jobId)
        setDetail(data)
      } catch {
        setDetail(null)
      } finally {
        setLoading(false)
      }
    }
  }, [fetchMatchDetail, jobId, resumeId])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDetail(), 0)
    return () => window.clearTimeout(timer)
  }, [loadDetail])

  if (loading) return <LoadingSpinner />
  if (!detail) return <div className="text-center py-12" style={{ color: 'var(--muted-foreground)' }}>未找到匹配详情</div>

  const { resume, job, scores, matched_skills, missing_skills, reason } = detail
  const formatSkills = (s: string) => s ? s.split('|').filter(Boolean) : []

  const cardStyle: React.CSSProperties = {
    position: 'relative',
    background: 'var(--card)',
    borderRadius: '4px',
    padding: '1.5rem',
  }
  const cardBorderOverlay: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    borderRadius: '4px',
    border: '1px solid var(--border)',
    pointerEvents: 'none',
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to={backLink} className="inline-flex items-center gap-1 text-sm transition-opacity hover:opacity-75" style={{ color: 'var(--accent)' }}>
          <ArrowLeft className="h-4 w-4" />
          返回列表
        </Link>
        <div className="flex items-center gap-2 mt-2">
          <Target className="h-5 w-5" style={{ color: 'var(--accent)' }} />
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--foreground)' }}>匹配详情</h1>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div style={cardStyle}>
          <div style={cardBorderOverlay} />
          <div className="relative">
            <h3 className="flex items-center gap-2 font-semibold text-sm mb-3" style={{ color: 'var(--foreground)' }}>
              <User className="h-4 w-4" style={{ color: 'var(--accent)' }} />
              简历信息
            </h3>
            <div className="text-sm space-y-1.5">
              <InfoRow label="姓名" value={resume.name} />
              <InfoRow label="学历" value={resume.education} />
              <InfoRow label="经验" value={`${resume.experience_years_num}年`} />
              <InfoRow label="城市" value={resume.standard_location || resume.location} />
              <InfoRow label="期望薪资" value={`${resume.expected_salary}万/年`} />
              <InfoRow label="技能" value={formatSkills(resume.skill_items_raw || resume.skills).join('、')} />
              {resume.certifications && resume.certifications !== '无' && (
                <InfoRow label="证书" value={resume.certifications} />
              )}
            </div>
          </div>
        </div>

        <div style={cardStyle}>
          <div style={cardBorderOverlay} />
          <div className="relative">
            <h3 className="flex items-center gap-2 font-semibold text-sm mb-3" style={{ color: 'var(--foreground)' }}>
              <Briefcase className="h-4 w-4" style={{ color: 'var(--accent)' }} />
              岗位信息
            </h3>
            <div className="text-sm space-y-1.5">
              <InfoRow label="岗位" value={job.job_title} />
              <InfoRow label="部门" value={job.department} />
              <InfoRow label="城市" value={job.standard_location || job.location} />
              <InfoRow label="学历要求" value={job.education_required} />
              <InfoRow label="经验要求" value={job.experience_required} />
              <InfoRow label="薪资范围" value={job.salary_range} />
              <InfoRow label="必备技能" value={formatSkills(job.required_skill_items_raw || job.skills_required).join('、')} />
              {job.preferred_skill_items_raw && (
                <InfoRow label="加分技能" value={formatSkills(job.preferred_skill_items_raw).join('、')} />
              )}
            </div>
          </div>
        </div>
      </div>

      <div style={cardStyle}>
        <div style={cardBorderOverlay} />
        <div className="relative">
          <h3 className="flex items-center gap-2 font-semibold mb-4" style={{ color: 'var(--foreground)' }}>
            <Target className="h-4 w-4" style={{ color: 'var(--accent)' }} />
            匹配评分
          </h3>
          <div className="flex justify-center mb-6">
            <ScoreRing score={scores.total_score} size={140} />
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-sm flex items-center gap-2" style={{ color: 'var(--foreground)' }}>
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: '#1f8a65' }} />
                语义分
                <span className="font-normal text-[11px]" style={{ color: 'var(--muted-foreground)' }}>(权重 60%)</span>
              </h4>
              <div className="pl-4 space-y-1" style={{ borderLeft: '2px solid var(--secondary)' }}>
                <ScoreBar label="TF-IDF 分" value={scores.tfidf_score} />
                <ScoreBar label="Word2Vec 分" value={scores.word2vec_score} />
              </div>
              <ScoreBar label="语义分" value={scores.semantic_score} />
            </div>

            <div className="space-y-2">
              <h4 className="font-semibold text-sm flex items-center gap-2" style={{ color: 'var(--foreground)' }}>
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: '#78716c' }} />
                规则分
                <span className="font-normal text-[11px]" style={{ color: 'var(--muted-foreground)' }}>(权重 40%)</span>
              </h4>
              <div className="pl-4 space-y-1" style={{ borderLeft: '2px solid var(--secondary)' }}>
                <ScoreBar label="技能分" value={scores.skill_score} weight="40%" />
                <ScoreBar label="学历分" value={scores.education_score} weight="20%" />
                <ScoreBar label="经验分" value={scores.experience_score} weight="15%" />
                <ScoreBar label="城市分" value={scores.city_score} weight="10%" />
                <ScoreBar label="薪资分" value={scores.salary_score} weight="10%" />
                <ScoreBar label="证书分" value={scores.certificate_score} weight="5%" />
              </div>
              <ScoreBar label="规则分" value={scores.rule_score} />
            </div>
          </div>
        </div>
      </div>

      <div style={cardStyle}>
        <div style={cardBorderOverlay} />
        <div className="relative">
          <h3 className="font-semibold text-sm mb-3" style={{ color: 'var(--foreground)' }}>技能匹配</h3>
          <SkillTags matched={matched_skills || []} missing={missing_skills || []} />
          <div className="flex gap-4 mt-2 text-xs" style={{ color: 'var(--muted-foreground)' }}>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: 'rgba(31,138,101,0.12)' }} />
              共同技能
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: 'rgba(207,45,86,0.10)' }} />
              缺失技能
            </span>
          </div>
        </div>
      </div>

      {reason && (
        <div style={cardStyle}>
          <div style={cardBorderOverlay} />
          <div className="relative">
            <h3 className="font-semibold text-sm mb-2" style={{ color: 'var(--foreground)' }}>推荐理由</h3>
            <div className="text-sm whitespace-pre-line leading-relaxed" style={{ color: 'var(--muted-foreground)' }}>{reason}</div>
          </div>
        </div>
      )}
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between py-0.5" style={{ borderBottom: '1px dashed var(--border)' }}>
      <span style={{ color: 'var(--muted-foreground)' }}>{label}</span>
      <span className="font-medium text-right" style={{ color: 'var(--foreground)' }}>{value}</span>
    </div>
  )
}