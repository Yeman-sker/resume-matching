interface ScoreBarProps {
  label: string
  value: number
  weight?: string
}

function getScoreColors(value: number): { bar: string; text: string } {
  if (value >= 80) return { bar: '#1f8a65', text: '#1f8a65' }
  if (value >= 60) return { bar: '#78716c', text: '#3b3a33' }
  return { bar: '#f54e00', text: '#f54e00' }
}

export default function ScoreBar({ label, value, weight }: ScoreBarProps) {
  const clampedValue = Math.max(0, Math.min(100, value))
  const colors = getScoreColors(clampedValue)

  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between text-sm">
        <span style={{ color: 'var(--foreground)' }}>
          {label}
          {weight && <span className="ml-1 text-[11px]" style={{ color: 'var(--muted-foreground)' }}>({weight})</span>}
        </span>
        <span className="font-semibold tabular-nums" style={{ color: colors.text }}>
          {clampedValue.toFixed(1)}
        </span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--secondary)' }}>
        <div
          className="grow-bar h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.max(clampedValue, 2)}%`, background: colors.bar }}
        />
      </div>
    </div>
  )
}