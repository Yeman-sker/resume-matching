interface ScoreRingProps {
  score: number
  size?: number
  label?: string
}

function getScoreColor(value: number): string {
  if (value >= 80) return '#1f8a65'
  if (value >= 60) return '#78716c'
  return '#f54e00'
}

export default function ScoreRing({ score, size = 140, label = '综合分' }: ScoreRingProps) {
  const clamped = Math.max(0, Math.min(100, score))
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (clamped / 100) * circumference
  const color = getScoreColor(clamped)
  const center = size / 2

  return (
    <div className="inline-flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle cx={center} cy={center} r={radius} fill="none" stroke="var(--secondary)" strokeWidth="8" />
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-700"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color }}>{clamped.toFixed(1)}</span>
          <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>{label}</span>
        </div>
      </div>
    </div>
  )
}