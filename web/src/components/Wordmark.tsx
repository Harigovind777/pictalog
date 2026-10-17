import { cn } from '@/lib/utils'

/** "Pictalog" with the i-dot drawn as an amber studio light. */
export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-baseline font-heading text-xl font-bold tracking-[-0.04em]', className)}>
      P
      <span className="relative inline-block">
        ı
        <span className="absolute left-1/2 top-[0.12em] size-[0.22em] -translate-x-1/2 rounded-full bg-amber" aria-hidden />
      </span>
      ctalog
    </span>
  )
}
