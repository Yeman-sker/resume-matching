interface SkillTagsProps {
  matched: string[]
  missing: string[]
}

export default function SkillTags({ matched, missing }: SkillTagsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {matched.map((skill) => (
        <span key={skill} className="inline-flex items-center rounded-full bg-green-100 text-green-800 px-2.5 py-0.5 text-xs font-medium">
          {skill}
        </span>
      ))}
      {missing.map((skill) => (
        <span key={skill} className="inline-flex items-center rounded-full bg-red-100 text-red-800 px-2.5 py-0.5 text-xs font-medium">
          {skill}
        </span>
      ))}
    </div>
  )
}