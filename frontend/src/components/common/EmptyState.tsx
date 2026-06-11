interface EmptyStateProps {
  message: string
}

export default function EmptyState({ message }: EmptyStateProps) {
  return (
    <div className="flex items-center justify-center py-12 text-muted-foreground">
      {message}
    </div>
  )
}