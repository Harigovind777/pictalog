import { cn } from '@/lib/utils'

/** "Pictalog", set wide and heavy, with the i-dot drawn as a ring: a camera lens. Takes the text colour. */
export function Wordmark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-baseline font-heading text-xl font-extrabold tracking-[-0.045em] [font-stretch:125%]',
        className,
      )}
    >
      P
      <span className="relative inline-block">
        ı
        <span
          className="absolute left-[calc(50%+0.0225em)] top-[0.16em] size-[0.27em] -translate-x-1/2 rounded-full border-[0.075em] border-current"
          aria-hidden
        />
      </span>
      ctalog
    </span>
  )
}
