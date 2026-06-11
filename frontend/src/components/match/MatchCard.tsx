import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Match } from '@/types'
import ScoreBar from '@/components/match/ScoreBar'

interface MatchCardProps {
  match: Match
  rank: number
  mode: 'job' | 'resume'
}

function getScoreBand(value: number): string {
  if (value >= 80) return '#1f8a65'
  if (value >= 60) return '#78716c'
  return '#f54e00'
}

export default function MatchCard({ match, rank, mode }: MatchCardProps) {
  const navigate = useNavigate()
  const [showReason, setShowReason] = useState(false)
  const title = mode === 'job' ? match.resume_name : match.job_title
  const subtitle = mode === 'job' ? match.job_title : match.resume_name
  const from = mode === 'job' ? 'jobs' : 'resumes'
  const fromId = mode === 'job' ? match.job_id : match.resume_id
  const bandColor = getScoreBand(match.total_score)
  const matchedList = match.matched_skills ? match.matched_skills.split('|').filter((s) => s && s !== '无') : []
  const missingList = match.missing_skills ? match.missing_skills.split('|').filter((s) => s && s !== '无') : []

  return (
    <div className="card-lift relative" style={{ background: 'var(--card)', borderRadius: '4px', borderLeft: `3px solid ${bandColor}` }}>
      <div style={{ position: 'absolute', inset: 0, borderRadius: '4px', border: '1px solid var(--border)', borderLeft: 'none', pointerEvents: 'none' }} />
      <div className="relative p-4 space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center h-5 w-5 rounded-sm text-xs font-semibold"
                style={{ background: 'var(--secondary)', color: 'var(--muted-foreground)' }}>
                {rank}
              </span>
              <h3 className="font-semibold text-sm truncate" style={{ color: 'var(--foreground)' }}>{title}</h3>
            </div>
            <p className="text-xs mt-0.5" style={{ color: 'var(--muted-foreground)' }}>{subtitle}</p>
          </div>
          <div className="text-right shrink-0 ml-3">
            <div className="text-xl font-bold tabular-nums" style={{ color: bandColor }}>{match.total_score.toFixed(1)}</div>
            <div className="text-[11px] font-medium" style={{ color: bandColor }}>综合分</div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-x-4 gap-y-1.5 md:grid-cols-2">
          <ScoreBar label="语义分" value={match.semantic_score} weight="60%" />
          <ScoreBar label="技能分" value={match.skill_score} weight="40%" />
          <ScoreBar label="学历分" value={match.education_score} weight="20%" />
          <ScoreBar label="经验分" value={match.experience_score} weight="15%" />
          <ScoreBar label="城市分" value={match.city_score} weight="10%" />
          <ScoreBar label="薪资分" value={match.salary_score} weight="10%" />
        </div>

        <div className="space-y-1">
          {matchedList.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {matchedList.slice(0, 6).map((skill) => (
                <span key={skill} className="inline-flex items-center rounded-sm px-1.5 py-0.5 text-[11px] font-medium"
                  style={{ background: 'rgba(31,138,101,0.12)', color: '#1f8a65' }}>
                  {skill}
                </span>
              ))}
              {matchedList.length > 6 && <span className="text-[11px]" style={{ color: 'var(--muted-foreground)' }}>+{matchedList.length - 6}</span>}
            </div>
          )}
          {missingList.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {missingList.slice(0, 4).map((skill) => (
                <span key={skill} className="inline-flex items-center rounded-sm px-1.5 py-0.5 text-[11px] font-medium"
                  style={{ background: 'rgba(207,45,86,0.10)', color: '#cf2d56' }}>
                  {skill}
                </span>
              ))}
              {missingList.length > 4 && <span className="text-[11px]" style={{ color: 'var(--muted-foreground)' }}>+{missingList.length - 4}</span>}
            </div>
          )}
        </div>

        {match.reason && (
          <div>
            <button
              className="text-xs font-medium transition-opacity hover:opacity-75"
              style={{ color: 'var(--accent)' }}
              onClick={() => setShowReason((v) => !v)}
            >
              <span
                className="inline-block transition-transform duration-200"
                style={{ transform: showReason ? 'rotate(90deg)' : 'none' }}
              >
                ▶
              </span>{' '}
              {showReason ? '收起推荐理由' : '展开推荐理由'}
            </button>
            <div
              style={{
                display: 'grid',
                gridTemplateRows: showReason ? '1fr' : '0fr',
                opacity: showReason ? 1 : 0,
                transition: 'grid-template-rows 0.35s var(--ease-out-soft), opacity 0.3s ease',
              }}
            >
              <div className="overflow-hidden">
                <div className="mt-2 p-3 rounded-sm text-xs whitespace-pre-line" style={{ background: 'var(--secondary)', color: 'var(--muted-foreground)' }}>
                  {match.reason}
                </div>
              </div>
            </div>
          </div>
        )}

        <button
          onClick={() => navigate(`/match/${match.resume_id}/${match.job_id}?from=${from}&fromId=${fromId}`)}
          className="group text-xs font-medium transition-opacity hover:opacity-75"
          style={{ color: 'var(--accent)' }}
        >
          查看详情 <span className="inline-block transition-transform duration-200 group-hover:translate-x-0.5">→</span>
        </button>
      </div>
    </div>
  )
}