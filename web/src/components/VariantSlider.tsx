import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useReducedMotion } from 'motion/react'
import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

type Props = {
  count: number
  index: number
  onIndexChange: (index: number) => void
  renderSlide: (index: number) => ReactNode
  /** Tapping a photo (not a button on it). */
  onSlideClick?: (index: number) => void
  label: string
  /** Every photo is rendered up front (the product page); grids render each one as it's reached. */
  eager?: boolean
  /** Show where you are among the photos. Off while the photo in view is a status message, which sits there. */
  dots?: boolean
  size?: 'sm' | 'lg'
  className?: string
}

/**
 * A product's photos side by side, one per size or colour. Swipe (or scroll sideways, or use the arrows) and each
 * photo snaps into place; the browser does the scrolling, so it keeps the phone's own momentum and feel.
 */
export function VariantSlider({ count, index, onIndexChange, renderSlide, onSlideClick, label, eager, dots = true, size = 'sm', className }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  // While gliding to a photo picked elsewhere (a chip, an arrow), the photos passed on the way aren't selections.
  const gliding = useRef<number | null>(null)
  const mounted = useRef(false)
  const still = useReducedMotion()
  // Photos are rendered as they're reached (and the next one ahead), and stay rendered so swiping back is instant.
  const [reached, setReached] = useState(index + 1)
  if (index + 1 > reached) setReached(index + 1)

  useEffect(() => {
    const el = ref.current
    const first = !mounted.current
    mounted.current = true
    if (!el || Math.round(el.scrollLeft / el.clientWidth) === index) return
    gliding.current = index
    el.scrollTo({ left: index * el.clientWidth, behavior: first || still ? 'instant' : 'smooth' })
  }, [index, still])

  function onScroll() {
    const el = ref.current
    if (!el || el.clientWidth === 0) return
    const at = el.scrollLeft / el.clientWidth
    if (gliding.current !== null) {
      if (Math.abs(at - gliding.current) < 0.02) gliding.current = null
      return
    }
    const i = Math.min(count - 1, Math.max(0, Math.round(at)))
    if (i !== index) onIndexChange(i)
  }

  function onClick(event: MouseEvent, i: number) {
    if ((event.target as Element).closest('button, a, [role="menuitem"]')) return
    onSlideClick?.(i)
  }

  if (count < 2) {
    return (
      <div className={cn('relative overflow-hidden', onSlideClick && 'cursor-pointer', className)} onClick={(e) => onClick(e, 0)}>
        {renderSlide(0)}
      </div>
    )
  }

  const takeOver = () => (gliding.current = null)
  return (
    <div
      className={cn('group/slider relative overflow-hidden', className)}
      role="group"
      aria-roledescription="carousel"
      aria-label={label}
    >
      <div
        ref={ref}
        onScroll={onScroll}
        onPointerDown={takeOver}
        onTouchStart={takeOver}
        onWheel={takeOver}
        className="no-scrollbar flex snap-x snap-mandatory overflow-x-auto overscroll-x-contain rounded-[inherit]"
      >
        {Array.from({ length: count }, (_, i) => (
          <div
            key={i}
            role="group"
            aria-roledescription="slide"
            aria-label={`${i + 1} of ${count}`}
            className={cn('w-full shrink-0 snap-center snap-always', onSlideClick && 'cursor-pointer')}
            onClick={(e) => onClick(e, i)}
          >
            {eager || i <= reached ? renderSlide(i) : <div className="aspect-square" />}
          </div>
        ))}
      </div>

      {/* Where you are among the photos. */}
      <div
        className={cn(
          'pointer-events-none absolute inset-x-0 z-30 flex justify-center transition-opacity duration-300',
          size === 'sm' ? 'bottom-2.5' : 'bottom-4',
          !dots && 'opacity-0',
        )}
        aria-hidden
      >
        {count <= 10 ? (
          <div className="flex items-center gap-1 rounded-full bg-tile/70 px-1.5 py-1 backdrop-blur-sm">
            {Array.from({ length: count }, (_, i) => (
              <span
                key={i}
                className={cn(
                  'h-[3px] rounded-full transition-[width,background-color] duration-300 ease-out',
                  i === index ? 'w-4 bg-ink' : 'w-1.5 bg-ink/25',
                )}
              />
            ))}
          </div>
        ) : (
          <span className="rounded-full bg-tile/80 px-2 py-0.5 text-xs font-medium tabular-nums backdrop-blur-sm">
            {index + 1} / {count}
          </span>
        )}
      </div>

      {/* Arrows for a mouse; on touch screens, swipe. */}
      {[
        { step: -1, show: index > 0, Icon: ChevronLeft, side: 'left-2', name: 'Previous photo' },
        { step: 1, show: index < count - 1, Icon: ChevronRight, side: 'right-2', name: 'Next photo' },
      ].map(({ step, show, Icon, side, name }) =>
        show ? (
          <button
            key={step}
            type="button"
            aria-label={name}
            onClick={() => onIndexChange(index + step)}
            className={cn(
              'absolute top-1/2 z-30 grid -translate-y-1/2 place-items-center rounded-full bg-tile/90 text-ink shadow-md backdrop-blur transition-[opacity,scale] duration-200 outline-ring hover:scale-105 focus-visible:opacity-100 focus-visible:outline-2 pointer-coarse:hidden',
              size === 'sm' ? 'size-8 opacity-0 group-hover/slider:opacity-100' : 'size-10 opacity-70 hover:opacity-100',
              side,
            )}
          >
            <Icon className="size-4" />
          </button>
        ) : null,
      )}
    </div>
  )
}
