import type { CSSProperties } from 'react'
import { useDevelop } from '@/hooks/use-develop'
import type { Paper } from '@/lib/paper'
import type { Cover } from '@/lib/types'
import { cn } from '@/lib/utils'

// Where each photo stands in a group shot of one, two or three products (percent of the cover's width and height).
// Photos never overlap: the white around each product drops out, but two products crossing would show through.
const ARRANGEMENTS: { left: number; width: number; bottom: number }[][] = [
  [],
  [{ left: 20, width: 60, bottom: 5 }],
  [
    { left: 4, width: 45, bottom: 9 },
    { left: 51, width: 45, bottom: 7 },
  ],
  [
    { left: 1, width: 34, bottom: 14 },
    { left: 65, width: 34, bottom: 14 },
    { left: 30, width: 40, bottom: 8 },
  ],
]

type Props = {
  covers: Cover[]
  paper: Paper
  className?: string
  emptyText?: string
}

/** A catalog's cover: up to three of its products, shot together on the catalog's backdrop. */
export function CatalogCover({ covers, paper, className, emptyText = 'No photos yet' }: Props) {
  const shown = covers.slice(0, 3)
  const spots = ARRANGEMENTS[shown.length]
  // The group shot develops into colour together, one product a beat after another.
  const { ref, 'data-developed': developed } = useDevelop()
  return (
    <div ref={ref} data-paper={paper} className={cn('paper relative aspect-[4/3] overflow-hidden rounded-2xl', className)}>
      {shown.length === 0 && (
        <p className="absolute inset-x-0 bottom-0 p-5 text-sm text-ink/50">{emptyText}</p>
      )}
      {shown.map((cover, i) => {
        const spot = spots[i]
        const style: CSSProperties = {
          left: `${spot.left}%`,
          width: `${spot.width}%`,
          bottom: `${spot.bottom}%`,
          transitionDelay: `${i * 180}ms`,
        }
        return cover.generated ? (
          <img
            key={cover.url}
            src={cover.url}
            alt=""
            loading="lazy"
            data-developed={developed}
            className="on-paper develop absolute aspect-square object-contain"
            style={style}
          />
        ) : (
          // A photo the owner uploaded keeps its own background, so it's laid on the paper like a print.
          <span key={cover.url} className="absolute grid aspect-square place-items-center p-[6%]" style={style}>
            <img
              src={cover.url}
              alt=""
              loading="lazy"
              data-developed={developed}
              className="develop size-full rounded-xl bg-tile object-cover shadow-[0_10px_24px_-10px_rgb(0_0_0/0.45)]"
              style={{ transitionDelay: `${i * 180}ms` }}
            />
          </span>
        )
      })}
    </div>
  )
}
