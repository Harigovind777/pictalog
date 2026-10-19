import { motion } from 'motion/react'
import { useDevelop } from '@/hooks/use-develop'
import { SHOWCASE } from '@/lib/showcase'
import { cn } from '@/lib/utils'

// Where the three product tiles float, and how each one bobs.
const TILES = [
  { className: 'left-[4%] top-[14%] w-[44%] rotate-[-4deg]', duration: 5, delay: 0 },
  { className: 'right-[2%] top-[4%] w-[38%] rotate-[3deg]', duration: 4, delay: 0.6 },
  { className: 'right-[12%] bottom-[2%] w-[42%] rotate-[-2deg]', duration: 4.5, delay: 1.2 },
]

/** Real Pictalog photos on their backdrops, floating around a slowly turning ring. Decoration only. */
export function FloatingShowcase({ className }: { className?: string }) {
  const { ref, 'data-developed': developed } = useDevelop()
  return (
    <div ref={ref} className={cn('relative aspect-square w-full max-w-md', className)} aria-hidden>
      <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle,rgb(0_0_0/0.06),transparent_65%)]" />
      <div className="spin-slow absolute inset-[8%] rounded-full border-2 border-dashed border-ink/15" />
      <div className="absolute top-[46%] left-[46%] grid grid-cols-3 gap-2">
        {Array.from({ length: 9 }).map((_, i) => (
          <span key={i} className="size-1.5 rounded-full bg-ink/25" />
        ))}
      </div>
      <div className="absolute bottom-[10%] left-[8%] size-14 rounded-2xl bg-ink shadow-accent-lg" />
      {TILES.map((tile, i) => {
        const s = SHOWCASE[i]
        return (
          <motion.div
            key={s.src}
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: tile.duration, delay: tile.delay, repeat: Infinity, ease: 'easeInOut' }}
            className={cn('absolute rounded-2xl border bg-card p-1.5 shadow-xl', tile.className)}
          >
            <div data-paper={s.paper} className="paper aspect-square overflow-hidden rounded-xl">
              <img
                src={s.src}
                alt=""
                data-developed={developed}
                style={{ transitionDelay: `${300 + i * 350}ms` }}
                className="on-paper develop size-full scale-90 object-contain"
              />
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
