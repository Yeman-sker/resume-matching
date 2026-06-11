import { useNavigate } from 'react-router-dom'
import type { Match } from '@/types'
import ScoreBar from '@/components/match/ScoreBar'

interface MatchCardProps {
  match: Match
  rank: number
  mode: 'job' | 'resume'
}

export default function MatchCard({ match, rank, mode }: MatchCardProps) {
  const navigate = useNavigate()
  const title = mode === 'job' ? match.resume_name : match.job_title
  const subtitle = mode === 'job' ? match.job_title : match.resume_name

  const matchedList = match.matched_skills
    ? match.matched_skills.split('|').filter(Boolean)
    : []
  const missingList = match.missing_skills
    ? match.missing_skills.split('|').filter(Boolean)
    : []

  return (
    <div className="border rounded-lg p-4 space-y-3 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-base">
            <span className="text-muted-foreground mr-1">#{rank}</span>
            {title}
          </h3>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">{match.total_score.toFixed(1)}</div>
          <div className="text-xs text-muted-foreground">综合分</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-2">
        <ScoreBar label="语义分" value={match.semantic_score} weight="60%" />
        <ScoreBar label="技能分" value={match.skill_score} weight="40%" />
        <ScoreBar label="学历分" value={match.education_score} weight="20%" />
        <ScoreBar label="经验分" value={match.experience_score} weight="15%" />
        <ScoreBar label="城市分" value={match.city_score} weight="10%" />
        <ScoreBar label="薪资分" value={match.salary_score} weight="10%" />
      </div>

      <div className="space-y-1">
        <div className="text-xs">
          <span className="text-green-700 font-medium">共同技能: </span>
          <span className="text-green-600">
            {matchedList.length > 0 ? matchedList.join('、') : '无'}
          </span>
        </div>
        {missingList.length > 0 && (
          <div className="text-xs">
            <span className="text-red-700 font-medium">缺失技能: </span>
            <span className="text-red-600">{missingList.join('、')}</span>
          </div>
        )}
      </div>

      <button
        onClick={() => navigate(`/match/${match.resume_id}/${match.job_id}`)}
        className="text-sm text-primary hover:underline"
      >
        查看详情 →
      </button>
    </div>
  )
}