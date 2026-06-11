interface SkillTagsProps {
  matched: string[]
  missing: string[]
}

export default function SkillTags({ matched, missing }: SkillTagsProps) {
  const filteredMissing = missing.filter((s) => s && s !== "无")
  return (
    <div className="flex flex-wrap gap-1.5">
      {matched.map((skill) => (
        <span key={skill} className="inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium"
          style={{ background: 'rgba(31,138,101,0.12)', color: '#1f8a65' }}>
          {skill}
        </span>
      ))}
      {filteredMissing.map((skill) => (
        <span key={skill} className="inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium"
          style={{ background: 'rgba(207,45,86,0.10)', color: '#cf2d56' }}>
          {skill}
        </span>
      ))}
    </div>
  )
}