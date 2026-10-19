import { cn } from '@/lib/utils'

/** A small status line above a headline: a black dot and a few words. `live` makes the dot pulse. */
export function SectionLabel({ children, live, className }: { children: React.ReactNode; live?: boolean; className?: string }) {
  return (
    <p className={cn('inline-flex w-fit items-center gap-2 text-sm font-medium text-ink/65', className)}>
      <span className={cn('size-2 rounded-full bg-ink', live && 'pulse-dot')} aria-hidden />
      {children}
    </p>
  )
}
