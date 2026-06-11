interface ScoreBarProps {
  label: string
  value: number
  weight?: string
}

function getScoreColor(value: number): string {
  if (value >= 80) return 'bg-green-500'
  if (value >= 60) return 'bg-yellow-500'
  return 'bg-red-500'
}

export default function ScoreBar({ label, value, weight }: ScoreBarProps) {
  const clampedValue = Math.max(0, Math.min(100, value))
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span>
          {label}
          {weight && <span className="text-muted-foreground ml-1 text-xs">({weight})</span>}
        </span>
        <span className="font-medium">{clampedValue.toFixed(1)}</span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${getScoreColor(clampedValue)}`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  )
}