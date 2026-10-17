import { MoreHorizontal } from 'lucide-react'
import { motion } from 'motion/react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { usePhotoPicker } from '@/hooks/use-photo-picker'
import { priceLabel, variantLabel, variantLabels } from '@/lib/catalog'
import type { Paper } from '@/lib/paper'
import type { Product } from '@/lib/types'
import { cn } from '@/lib/utils'
import { ImageSlot } from './ImageSlot'

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
  /** Opens the product's detail view, starting on the variant shown here. */
  onOpen: (variantIndex: number) => void
}

/** Variant switcher chips, shared by the card and the detail view. */
export function VariantChips({ product, index, onSelect, size = 'sm' }: { product: Product; index: number; onSelect: (i: number) => void; size?: 'sm' | 'md' }) {
  if (product.variants.length < 2) return null
  const labels = variantLabels(product.variants)
  return (
    <div className="relative z-10 flex flex-wrap gap-1.5" role="group" aria-label={`${product.name ?? 'Product'} options`}>
      {product.variants.map((v, i) => (
        <button
          key={v.id}
          type="button"
          aria-pressed={i === index}
          onClick={() => onSelect(i)}
          className={cn(
            'rounded-full border font-medium transition-all duration-200 outline-ring focus-visible:outline-2',
            size === 'sm' ? 'h-7 px-2.5 text-xs' : 'h-9 px-3.5 text-sm',
            i === index ? 'border-ink bg-ink text-white' : 'bg-tile text-ink/70 hover:border-ink/30 hover:text-ink',
          )}
        >
          {labels[i]}
        </button>
      ))}
    </div>
  )
}

export function ProductCard({ product, currency, paper, onOpen, helperOnline, readOnly, onRegenerate, onUpload }: Props) {
  const [index, setIndex] = useState(0)
  const variant = product.variants[Math.min(index, product.variants.length - 1)]
  const photo = usePhotoPicker(onUpload && variant ? (file) => onUpload(variant.id, file) : undefined)
  if (!variant) return null
  const name = product.name ?? variant.sku ?? 'Untitled product'
  const price = priceLabel(variant.price_text, currency)

  return (
    <motion.article
      layoutId={`card-${product.id}`}
      className="group relative grid content-start gap-3 rounded-2xl border bg-card p-2 pb-4 shadow-sm transition-[box-shadow,translate] duration-300 hover:-translate-y-1 hover:shadow-xl"
    >
      <motion.div layoutId={`image-${product.id}`} className="relative">
        <ImageSlot
          variant={variant}
          alt={`${name}, ${variantLabel(variant)}`}
          paper={paper}
          helperOnline={helperOnline}
          readOnly={readOnly}
          onGenerate={onRegenerate && (() => onRegenerate(variant.id))}
          onUpload={onUpload && photo.pick}
          className="[&_button]:relative [&_button]:z-10"
        />
        {!readOnly && variant.image_status === 'ready' && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                size="icon-sm"
                variant="secondary"
                aria-label={`Image options for ${name}`}
                className="absolute top-2 right-2 z-10 bg-tile/85 backdrop-blur hover:bg-tile opacity-100 sm:opacity-0 sm:group-hover:opacity-100 sm:focus-visible:opacity-100 data-[state=open]:opacity-100"
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
      </motion.div>

      <div className="grid gap-1 px-2">
        <motion.h3 layoutId={`title-${product.id}`} className="line-clamp-2 text-[0.9375rem] font-semibold leading-snug tracking-[-0.01em]">
          {/* The whole card opens the detail view; the chips and menus above sit on top of this button. */}
          <button type="button" onClick={() => onOpen(index)} className="text-left outline-none after:absolute after:inset-0 after:rounded-2xl focus-visible:after:ring-2 focus-visible:after:ring-ring focus-visible:after:ring-offset-2">
            {name}
          </button>
        </motion.h3>
        <div className="flex items-baseline justify-between gap-3 text-sm">
          {price && <p className="font-semibold">{price}</p>}
          {product.brand && <p className="truncate text-muted-foreground">{product.brand}</p>}
        </div>
      </div>

      <div className="px-2 empty:hidden">
        <VariantChips product={product} index={index} onSelect={setIndex} />
      </div>
    </motion.article>
  )
}
