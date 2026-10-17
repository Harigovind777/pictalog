import { MoreHorizontal } from 'lucide-react'
import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { priceLabel, variantLabel } from '@/lib/catalog'
import type { Product } from '@/lib/types'
import { cn } from '@/lib/utils'
import { ImageSlot } from './ImageSlot'

type Props = {
  product: Product
  currency: string
  helperOnline?: boolean
  readOnly?: boolean
  onRegenerate?: (variantId: number) => void
  onUpload?: (variantId: number, file: File) => void
}

export function ProductCard({ product, currency, helperOnline, readOnly, onRegenerate, onUpload }: Props) {
  const [index, setIndex] = useState(0)
  const fileInput = useRef<HTMLInputElement>(null)
  const variant = product.variants[Math.min(index, product.variants.length - 1)]
  if (!variant) return null
  const name = product.name ?? variant.sku ?? 'Untitled product'
  const price = priceLabel(variant.price_text, currency)
  const pickPhoto = () => fileInput.current?.click()

  return (
    <article className="group grid content-start gap-3">
      <div className="relative">
        <ImageSlot
          variant={variant}
          alt={`${name}, ${variantLabel(variant)}`}
          helperOnline={helperOnline}
          readOnly={readOnly}
          onGenerate={onRegenerate && (() => onRegenerate(variant.id))}
          onUpload={onUpload && pickPhoto}
        />
        {!readOnly && variant.image_status === 'ready' && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                size="icon"
                variant="secondary"
                aria-label={`Image options for ${name}`}
                className="absolute top-2 right-2 size-8 bg-tile/90 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 sm:focus-visible:opacity-100 data-[state=open]:opacity-100"
              >
                <MoreHorizontal />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {onRegenerate && <DropdownMenuItem onSelect={() => onRegenerate(variant.id)}>Make a new image</DropdownMenuItem>}
              {onUpload && <DropdownMenuItem onSelect={pickPhoto}>Upload your own photo</DropdownMenuItem>}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
        {onUpload && (
          <input
            ref={fileInput}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) onUpload(variant.id, file)
              e.target.value = ''
            }}
          />
        )}
      </div>

      <div className="grid gap-1">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="line-clamp-2 font-medium leading-snug">{name}</h3>
          {price && <p className="shrink-0 font-semibold tabular-nums">{price}</p>}
        </div>
        {product.brand && <p className="text-sm text-muted-foreground">{product.brand}</p>}
      </div>

      {product.variants.length > 1 && (
        <div className="flex flex-wrap gap-1.5" role="group" aria-label={`${name} options`}>
          {product.variants.map((v, i) => (
            <button
              key={v.id}
              type="button"
              aria-pressed={i === index}
              onClick={() => setIndex(i)}
              className={cn(
                'h-7 rounded-full border px-2.5 text-xs transition-colors outline-ring focus-visible:outline-2',
                i === index ? 'border-ink bg-ink text-white' : 'bg-tile hover:border-ink/40',
              )}
            >
              {variantLabel(v)}
            </button>
          ))}
        </div>
      )}
    </article>
  )
}
