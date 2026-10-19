import { useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react'
import { motion, useReducedMotion, useScroll, useTransform } from 'motion/react'
import { useLayoutEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { assetUrl } from '@/lib/api'
import { shelfMemory } from '@/lib/page-transitions'
import { paperFor } from '@/lib/paper'
import { catalogQuery } from '@/lib/queries'
import type { CatalogSummary } from '@/lib/types'
import { CatalogCover } from './CatalogCover'

const dateFormat = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

/**
 * Where the shelf scrolls to for each item to sit in its place: the middle on phones, the content edge on wider
 * screens (each item's scroll-snap-align says which).
 */
function snapPositions(shelf: HTMLElement): number[] {
  const items = Array.from(shelf.children) as HTMLElement[]
  const atStart = items.length > 0 && getComputedStyle(items[0]).scrollSnapAlign.includes('start')
  const padding = parseFloat(getComputedStyle(shelf).scrollPaddingLeft) || 0
  const end = shelf.scrollWidth - shelf.clientWidth
  return items.map((item) =>
    Math.min(end, Math.max(0, atStart ? item.offsetLeft - padding : item.offsetLeft - (shelf.clientWidth - item.offsetWidth) / 2)),
  )
}

/**
 * The owner's catalogs as covers on a shelf: swipe along it, the covers in place come into focus while those
 * leaving step back, and opening one grows its cover into the catalog's page.
 */
export function CatalogShelf({ catalogs, onNew }: { catalogs: CatalogSummary[]; onNew: () => void }) {
  const ref = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const still = useReducedMotion()
  // Coming back from a catalog: its cover is already in the middle when the screen slides in, so it can grow back
  // into place.
  const [arrival] = useState(() => catalogs.findIndex((c) => c.id === shelfMemory.catalogId))
  const [active, setActive] = useState(Math.max(0, arrival))
  const [opening, setOpening] = useState(shelfMemory.catalogId)
  const total = catalogs.length + 1
  const { scrollXProgress } = useScroll({ container: ref })
  const thumbX = useTransform(scrollXProgress, (p) => `${p * (total - 1) * 100}%`)

  useLayoutEffect(() => {
    const shelf = ref.current
    if (shelf && arrival >= 0) shelf.scrollLeft = snapPositions(shelf)[arrival]
  }, [arrival])

  function onScroll() {
    const shelf = ref.current
    if (!shelf) return
    let nearest = 0
    let distance = Infinity
    // Ties go to the later item, so the end of the shelf counts as reaching its last item.
    snapPositions(shelf).forEach((left, i) => {
      const d = Math.abs(left - shelf.scrollLeft)
      if (d <= distance) [nearest, distance] = [i, d]
    })
    setActive(nearest)
  }

  function go(step: number) {
    const shelf = ref.current
    const left = shelf && snapPositions(shelf)[active + step]
    if (shelf && left !== undefined && left !== null) shelf.scrollTo({ left, behavior: still ? 'instant' : 'smooth' })
  }

  // Touching or pointing at a cover starts fetching its catalog, so it usually opens with no wait at all.
  const prefetch = (id: number) => void queryClient.prefetchQuery(catalogQuery(id))

  return (
    <section aria-label="Catalogs" className="grid gap-5 sm:gap-7">
      <div
        ref={ref}
        onScroll={onScroll}
        className="no-scrollbar relative flex snap-x snap-mandatory gap-3 overflow-x-auto overscroll-x-contain px-[9vw] py-3 sm:gap-6 sm:scroll-px-[max(1.5rem,calc(50vw-38.5rem))] sm:px-[max(1.5rem,calc(50vw-38.5rem))]"
      >
        {catalogs.map((c, i) => (
          <div key={c.id} className="shelf-item w-[82vw] shrink-0 snap-center sm:w-[22rem] sm:snap-start lg:w-[24rem]">
            <Link
              to={`/catalogs/${c.id}`}
              viewTransition
              onClick={() => {
                shelfMemory.catalogId = c.id
                setOpening(c.id)
              }}
              onPointerEnter={() => prefetch(c.id)}
              onPointerDown={() => prefetch(c.id)}
              onFocus={() => prefetch(c.id)}
              className="group grid gap-4 rounded-[1.75rem] outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-4 focus-visible:ring-offset-background"
            >
              <CatalogCover
                paper={paperFor(c.id)}
                covers={c.covers.map((cover) => ({ ...cover, url: assetUrl(cover.url) ?? cover.url }))}
                emptyText={c.product_count === 0 ? 'Upload a product list to fill this catalog' : 'The cover fills in as photos are made'}
                title={c.name}
                morph={opening === c.id}
                parallax
                eager={i < 4}
                className="aspect-[4/5] rounded-[1.5rem] shadow-[0_30px_60px_-30px_rgb(0_0_0/0.35)]"
              />
              <p className="px-1 text-sm text-muted-foreground">
                {plural(c.product_count, 'product', 'products')}
                {c.variant_count > c.product_count && ` in ${plural(c.variant_count, 'size or colour', 'sizes and colours')}`}
                , updated {dateFormat.format(new Date(c.updated_at + 'Z'))}
              </p>
            </Link>
          </div>
        ))}

        <div className="shelf-item w-[82vw] shrink-0 snap-center sm:w-[22rem] sm:snap-start lg:w-[24rem]">
          <button
            type="button"
            onClick={onNew}
            className="group grid w-full gap-4 rounded-[1.75rem] text-left outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-4 focus-visible:ring-offset-background"
          >
            <span className="relative grid aspect-[4/5] place-items-center rounded-[1.5rem] border-2 border-dashed border-ink/15 transition-colors duration-300 [container-type:inline-size] group-hover:border-ink/40">
              <span className="absolute inset-x-[7%] top-[6%] font-catalog text-[11cqw] leading-[0.95] tracking-[-0.025em] text-ink/40 transition-colors duration-300 group-hover:text-ink">
                New catalog
              </span>
              <span className="grid size-16 place-items-center rounded-full bg-ink text-white shadow-accent-lg transition-transform duration-300 group-hover:scale-110">
                <Plus className="size-6" />
              </span>
            </span>
            <span className="px-1 text-sm text-muted-foreground">Name it, then upload your product list.</span>
          </button>
        </div>
      </div>

      {/* Where you are on the shelf. */}
      <div className="mx-auto flex w-full max-w-7xl items-center gap-4 px-4 sm:px-6">
        <span className="w-14 text-sm tabular-nums text-muted-foreground" aria-live="polite">
          {active + 1} of {total}
        </span>
        <div className="relative h-0.5 flex-1 overflow-hidden rounded-full bg-ink/10" aria-hidden>
          <motion.div style={{ x: thumbX, width: `${100 / total}%` }} className="absolute inset-y-0 left-0 rounded-full bg-ink" />
        </div>
        <div className="flex gap-2 pointer-coarse:hidden">
          <Button variant="outline" size="icon-sm" aria-label="Previous catalog" disabled={active === 0} onClick={() => go(-1)}>
            <ChevronLeft />
          </Button>
          <Button variant="outline" size="icon-sm" aria-label="Next catalog" disabled={active === total - 1} onClick={() => go(1)}>
            <ChevronRight />
          </Button>
        </div>
      </div>
    </section>
  )
}
