import { FileX } from 'lucide-react'

interface EmptyStateProps {
  message: string
  icon?: React.ReactNode
}

export default function EmptyState({ message, icon }: EmptyStateProps) {
  return (
    <div className="anim-enter flex flex-col items-center justify-center py-16 text-muted-foreground">
      <div className="mb-3 text-4xl opacity-30">{icon || <FileX className="h-10 w-10" />}</div>
      <p className="text-sm">{message}</p>
    </div>
  )
}