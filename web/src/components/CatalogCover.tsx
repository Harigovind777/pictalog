import type { CSSProperties, ReactNode } from 'react'
import { useDevelop } from '@/hooks/use-develop'
import type { Paper } from '@/lib/paper'
import { textProps } from '@/lib/script'
import type { Cover } from '@/lib/types'
import { cn } from '@/lib/utils'

// Where each photo stands in a group shot of one, two or three products: left and width are percent of the cover's
// width, bottom is percent of a 4:3 cover's height. Products keep that distance from the floor on taller covers too,
// so the shelf's tall cover and the page's wide one line up as one grows into the other.
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
  /** This cover grows into the catalog's page (or back onto the shelf) when moving between them. */
  morph?: boolean
  /** The products drift against the paper as the shelf scrolls (index.css). */
  parallax?: boolean
  /** Load the photos straight away: the cover is on screen from the start. */
  eager?: boolean
  /** The catalog's name, printed across the top of the paper like a magazine cover. */
  title?: ReactNode
}

/** A catalog's cover: up to three of its products, shot together on the catalog's backdrop. */
export function CatalogCover({ covers, paper, className, emptyText = 'No photos yet', morph, parallax, eager, title }: Props) {
  const shown = covers.slice(0, 3)
  const spots = ARRANGEMENTS[shown.length]
  // The group shot develops into colour together, one product a beat after another.
  const { ref, 'data-developed': developed } = useDevelop()
  return (
    <div
      ref={ref}
      data-paper={paper}
      className={cn('paper relative aspect-[4/3] overflow-hidden rounded-2xl [container-type:inline-size]', className)}
      style={morph ? { viewTransitionName: 'catalog-cover' } : undefined}
    >
      {title && (
        // On the way into the catalog, the name flies up into the page's headline. It's only as wide as its words,
        // like the headline, so the two match as one becomes the other.
        <h2
          {...textProps(typeof title === 'string' ? title : null)}
          className="absolute top-[6%] left-[7%] line-clamp-3 max-w-[86%] font-catalog font-masthead text-[11cqw] leading-[0.95] tracking-[-0.025em] text-ink"
          style={morph ? { viewTransitionName: 'catalog-title' } : undefined}
        >
          {title}
        </h2>
      )}
      {shown.length === 0 && (
        <p className="absolute inset-x-0 bottom-0 p-5 text-sm text-ink/50">{emptyText}</p>
      )}
      {shown.map((cover, i) => {
        const spot = spots[i]
        const style: CSSProperties = {
          left: `${spot.left}%`,
          width: `${spot.width}%`,
          bottom: `${spot.bottom * 0.75}cqw`,
          transitionDelay: `${i * 180}ms`,
        }
        return cover.generated ? (
          <img
            key={cover.url}
            src={cover.url}
            alt=""
            loading={eager ? 'eager' : 'lazy'}
            decoding="async"
            data-developed={developed}
            className={cn('on-paper develop absolute aspect-square object-contain', parallax && 'shelf-parallax')}
            style={style}
          />
        ) : (
          // A photo the owner uploaded keeps its own background, so it's laid on the paper like a print.
          <span key={cover.url} className={cn('absolute grid aspect-square place-items-center p-[6%]', parallax && 'shelf-parallax')} style={style}>
            <img
              src={cover.url}
              alt=""
              loading={eager ? 'eager' : 'lazy'}
              decoding="async"
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
