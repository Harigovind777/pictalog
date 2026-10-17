import { ImagePlus, RefreshCw, X } from 'lucide-react'
import { motion } from 'motion/react'
import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/components/ui/button'
import { Lens } from '@/components/ui/lens'
import { usePhotoPicker } from '@/hooks/use-photo-picker'
import { priceLabel, variantLabel } from '@/lib/catalog'
import type { Paper } from '@/lib/paper'
import type { Product } from '@/lib/types'
import { ImageSlot } from './ImageSlot'
import { type ProductActions, VariantChips } from './ProductCard'

type Props = ProductActions & {
  product: Product
  currency: string
  paper: Paper
  startIndex: number
  onClose: () => void
}

/** A product opened from the grid (Aceternity's expandable card): big photo, every option, and all its details. */
export function ProductDetail({ product, currency, paper, startIndex, onClose, helperOnline, readOnly, onRegenerate, onUpload }: Props) {
  const [index, setIndex] = useState(startIndex)
  const variant = product.variants[Math.min(index, product.variants.length - 1)]
  const titleId = useId()
  const closeRef = useRef<HTMLButtonElement>(null)
  const photo = usePhotoPicker(onUpload && variant ? (file) => onUpload(variant.id, file) : undefined)

  // Behave like a dialog: Escape closes, focus moves in and returns, the page behind doesn't scroll.
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null
    closeRef.current?.focus({ preventScroll: true })
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
      opener?.focus({ preventScroll: true })
    }
  }, [onClose])

  if (!variant) return null
  const name = product.name ?? variant.sku ?? 'Untitled product'
  const price = priceLabel(variant.price_text, currency)
  const details = [
    ['Size', variant.size],
    ['Colour', variant.colour],
    ['Material', variant.material],
    ['Category', product.category],
    ['Brand', product.brand],
    ['Code', variant.sku],
    ...Object.entries(variant.extra),
  ].filter((d): d is [string, string] => Boolean(d[1]))

  const slot = (
    <ImageSlot
      variant={variant}
      alt={`${name}, ${variantLabel(variant)}`}
      paper={paper}
      helperOnline={helperOnline}
      readOnly={readOnly}
      onGenerate={onRegenerate && (() => onRegenerate(variant.id))}
      onUpload={onUpload && photo.pick}
      full
      className="rounded-2xl"
    />
  )

  return createPortal(
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-ink/30 backdrop-blur-sm"
      />
      <div
        className="fixed inset-0 z-50 grid place-items-center sm:p-6"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          layoutId={`card-${product.id}`}
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          className="relative flex size-full flex-col overflow-y-auto bg-card pt-safe pb-safe shadow-xl sm:h-auto sm:max-h-[90svh] sm:max-w-4xl sm:rounded-3xl sm:border md:grid md:grid-cols-[1.1fr_0.9fr] md:pt-0 md:pb-0"
        >
          <motion.div layoutId={`image-${product.id}`} className="p-3">
            {/* Hover to look closer (desktop). */}
            {variant.image_status === 'ready' ? <Lens zoomFactor={2} lensSize={180}>{slot}</Lens> : slot}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0, transition: { delay: 0.12, duration: 0.4 } }}
            exit={{ opacity: 0, transition: { duration: 0.05 } }}
            className="grid content-start gap-6 px-6 pt-3 pb-8 md:py-10 md:pr-10"
          >
            <div className="grid gap-3">
              <motion.h2 layoutId={`title-${product.id}`} id={titleId} className="font-display text-3xl sm:text-4xl">
                {name}
              </motion.h2>
              {price && <p className="text-2xl font-semibold tracking-[-0.01em]">{price}</p>}
            </div>

            <VariantChips product={product} index={index} onSelect={setIndex} size="md" />

            {product.description && <p className="leading-relaxed text-muted-foreground">{product.description}</p>}

            {details.length > 0 && (
              <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2.5 border-t pt-5 text-sm">
                {details.map(([label, value]) => (
                  <div key={label} className="contents">
                    <dt className="text-muted-foreground">{label}</dt>
                    <dd className="font-medium">{value}</dd>
                  </div>
                ))}
              </dl>
            )}

            {!readOnly && variant.image_status === 'ready' && (onRegenerate || onUpload) && (
              <div className="flex flex-wrap gap-2 border-t pt-5">
                {onRegenerate && (
                  <Button variant="outline" onClick={() => onRegenerate(variant.id)}>
                    <RefreshCw />
                    Make a new image
                  </Button>
                )}
                {onUpload && (
                  <Button variant="outline" onClick={photo.pick}>
                    <ImagePlus />
                    Upload your own photo
                  </Button>
                )}
              </div>
            )}
            {photo.input}
          </motion.div>

          <Button
            ref={closeRef}
            size="icon-sm"
            variant="secondary"
            aria-label="Close"
            onClick={onClose}
            className="absolute top-[calc(env(safe-area-inset-top)+0.75rem)] right-3 z-20 bg-tile/85 backdrop-blur hover:bg-tile md:top-3"
          >
            <X />
          </Button>
        </motion.div>
      </div>
    </>,
    document.body,
  )
}
