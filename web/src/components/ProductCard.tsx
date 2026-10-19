import { MoreHorizontal } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { usePhotoPicker } from '@/hooks/use-photo-picker'
import { priceLabel, variantLabel, variantLabels } from '@/lib/catalog'
import type { Paper } from '@/lib/paper'
import { textProps } from '@/lib/script'
import type { Product } from '@/lib/types'
import { cn } from '@/lib/utils'
import { ImageSlot } from './ImageSlot'
import { VariantSlider } from './VariantSlider'

export type ProductActions = {
  helperOnline?: boolean
  readOnly?: boolean
  onRegenerate?: (variantId: number) => void
  onUpload?: (variantId: number, file: File) => void
}

type Props = ProductActions & {
  product: Product
  currency: string
  paper: Paper
  /** Opens the product's page, starting on the photo shown here. */
  onOpen: (variantIndex: number) => void
}

/** Variant switcher chips for the product page. Picking one slides the photos to it. */
export function VariantChips({ product, index, onSelect }: { product: Product; index: number; onSelect: (i: number) => void }) {
  if (product.variants.length < 2) return null
  const labels = variantLabels(product.variants)
  return (
    <div className="flex flex-wrap gap-1.5" role="group" aria-label={`${product.name ?? 'Product'} options`}>
      {product.variants.map((v, i) => (
        <button
          key={v.id}
          type="button"
          aria-pressed={i === index}
          onClick={() => onSelect(i)}
          className={cn(
            'relative h-9 rounded-full px-3.5 text-sm font-medium transition-colors duration-200 outline-ring focus-visible:outline-2',
            i === index ? 'text-white' : 'border bg-tile text-ink/70 hover:border-ink/30 hover:text-ink',
          )}
        >
          {i === index && (
            <motion.span
              layoutId={`chip-${product.id}`}
              transition={{ type: 'spring', bounce: 0.18, duration: 0.45 }}
              className="absolute inset-0 rounded-full bg-ink"
            />
          )}
          <span className="relative">{labels[i]}</span>
        </button>
      ))}
    </div>
  )
}

/** A product in the grid, set like a catalog page: the photo on its paper, the name in the catalog's type below. */
export function ProductCard({ product, currency, paper, onOpen, helperOnline, readOnly, onRegenerate, onUpload }: Props) {
  const [index, setIndex] = useState(0)
  const labels = useMemo(() => variantLabels(product.variants), [product.variants])
  const variant = product.variants[Math.min(index, product.variants.length - 1)]
  const photo = usePhotoPicker(onUpload && variant ? (file) => onUpload(variant.id, file) : undefined)
  if (!variant) return null
  const name = product.name ?? variant.sku ?? 'Untitled product'
  const price = priceLabel(variant.price_text, currency)
  const caption = product.variants.length > 1 ? labels[index] : product.brand

  return (
    <article className="group relative grid content-start gap-3">
      {/* Above the card-wide button, so the photos can be swiped. */}
      <div className="relative z-10">
        <VariantSlider
          count={product.variants.length}
          index={index}
          onIndexChange={setIndex}
          dots={variant.image_status === 'ready'}
          onSlideClick={onOpen}
          label={`Photos of ${name}`}
          className="rounded-[1.25rem]"
          renderSlide={(i) => {
            const v = product.variants[i]
            return (
              <ImageSlot
                variant={v}
                alt={`${name}, ${variantLabel(v)}`}
                paper={paper}
                helperOnline={helperOnline}
                readOnly={readOnly}
                onGenerate={onRegenerate && (() => onRegenerate(v.id))}
                onUpload={onUpload && photo.pick}
                className="rounded-[1.25rem]"
              />
            )
          }}
        />
        {!readOnly && variant.image_status === 'ready' && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                size="icon-sm"
                variant="secondary"
                aria-label={`Image options for ${name}`}
                className="absolute top-2 right-2 bg-tile/85 opacity-100 backdrop-blur hover:bg-tile data-[state=open]:opacity-100 sm:opacity-0 sm:group-hover:opacity-100 sm:focus-visible:opacity-100"
              >
                <MoreHorizontal />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {onRegenerate && <DropdownMenuItem onSelect={() => onRegenerate(variant.id)}>Make a new image</DropdownMenuItem>}
              {onUpload && <DropdownMenuItem onSelect={photo.pick}>Upload your own photo</DropdownMenuItem>}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
        {photo.input}
      </div>

      <div className="grid gap-1 px-1">
        <h3 {...textProps(name)} className="line-clamp-2 font-catalog text-[1.0625rem] leading-[1.2] sm:text-lg">
          {/* The whole card opens the product page; the photos and menu sit above this button. */}
          <button
            type="button"
            onClick={() => onOpen(index)}
            className="text-left outline-none after:absolute after:inset-0 after:rounded-[1.25rem] focus-visible:after:ring-2 focus-visible:after:ring-ring focus-visible:after:ring-offset-2"
          >
            {name}
          </button>
        </h3>
        <div className="flex items-baseline justify-between gap-3 text-[0.8125rem]">
          {price && <span className="shrink-0 font-semibold">{price}</span>}
          {/* The caption follows the swipe, naming the size or colour in view. */}
          <span className="relative min-w-0 overflow-hidden text-right text-muted-foreground">
            <AnimatePresence mode="popLayout" initial={false}>
              <motion.span
                key={caption ?? ''}
                initial={{ y: '100%', opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: '-100%', opacity: 0 }}
                transition={{ type: 'spring', bounce: 0, duration: 0.35 }}
                className="block truncate"
              >
                {caption || '\u00a0'}
              </motion.span>
            </AnimatePresence>
          </span>
        </div>
      </div>
    </article>
  )
}
