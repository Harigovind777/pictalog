import { ImagePlus, RefreshCw, X } from 'lucide-react'
import { motion, useDragControls } from 'motion/react'
import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/components/ui/button'
import { Lens } from '@/components/ui/lens'
import { useMediaQuery } from '@/hooks/use-media-query'
import { usePhotoPicker } from '@/hooks/use-photo-picker'
import { priceLabel, variantLabel } from '@/lib/catalog'
import type { Paper } from '@/lib/paper'
import { textProps } from '@/lib/script'
import type { Product } from '@/lib/types'
import { ImageSlot } from './ImageSlot'
import { type ProductActions, VariantChips } from './ProductCard'
import { VariantSlider } from './VariantSlider'

type Props = ProductActions & {
  product: Product
  currency: string
  paper: Paper
  startIndex: number
  onClose: () => void
}

const sheet = { type: 'spring', bounce: 0, duration: 0.5 } as const

/**
 * A product's page. On a phone it's a sheet that slides up and can be dragged back down; on a wider screen it opens
 * in the middle. Every size and colour is a photo you can swipe to.
 */
export function ProductDetail({ product, currency, paper, startIndex, onClose, helperOnline, readOnly, onRegenerate, onUpload }: Props) {
  const [index, setIndex] = useState(startIndex)
  const variant = product.variants[Math.min(index, product.variants.length - 1)]
  const titleId = useId()
  const closeRef = useRef<HTMLButtonElement>(null)
  const photo = usePhotoPicker(onUpload && variant ? (file) => onUpload(variant.id, file) : undefined)
  const wide = useMediaQuery('(min-width: 768px)')
  const finePointer = useMediaQuery('(hover: hover) and (pointer: fine)')
  const drag = useDragControls()
  const count = product.variants.length

  // Behave like a dialog: Escape closes, the arrow keys move between photos, focus moves in and returns, and the
  // page behind doesn't scroll.
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null
    closeRef.current?.focus({ preventScroll: true })
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowRight') setIndex((i) => Math.min(count - 1, i + 1))
      if (e.key === 'ArrowLeft') setIndex((i) => Math.max(0, i - 1))
    }
    window.addEventListener('keydown', onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
      opener?.focus({ preventScroll: true })
    }
  }, [onClose, count])

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

  return createPortal(
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className="fixed inset-0 z-50 bg-ink/40 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <div className="pointer-events-none fixed inset-0 z-50 flex items-end justify-center md:items-center md:p-6">
        <motion.div
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          initial={wide ? { opacity: 0, scale: 0.96, y: 24 } : { y: '100%' }}
          animate={wide ? { opacity: 1, scale: 1, y: 0 } : { y: 0 }}
          exit={wide ? { opacity: 0, scale: 0.97, y: 12 } : { y: '100%' }}
          transition={sheet}
          drag={wide ? false : 'y'}
          dragListener={false}
          dragControls={drag}
          dragConstraints={{ top: 0, bottom: 0 }}
          dragElastic={{ top: 0, bottom: 0.8 }}
          onDragEnd={(_, info) => {
            if (info.offset.y > 120 || info.velocity.y > 600) onClose()
          }}
          className="pointer-events-auto relative flex max-h-[94svh] w-full flex-col overflow-hidden rounded-t-[1.75rem] bg-card shadow-xl md:max-h-[90svh] md:max-w-5xl md:rounded-[1.75rem]"
        >
          {/* Grab here to pull the sheet down. */}
          <div
            onPointerDown={(e) => drag.start(e)}
            className="flex h-6 shrink-0 cursor-grab touch-none justify-center pt-2.5 active:cursor-grabbing md:hidden"
            aria-hidden
          >
            <span className="h-1 w-10 rounded-full bg-ink/15" />
          </div>

          <div className="grid overflow-y-auto overscroll-contain pb-safe md:grid-cols-[1.1fr_0.9fr] md:pb-0">
            <div className="px-3 md:sticky md:top-0 md:self-start md:p-3">
              <VariantSlider
                count={count}
                index={index}
                onIndexChange={setIndex}
                dots={variant.image_status === 'ready'}
                label={`Photos of ${name}`}
                eager
                size="lg"
                className="rounded-[1.25rem]"
                renderSlide={(i) => {
                  const v = product.variants[i]
                  const slot = (
                    <ImageSlot
                      variant={v}
                      alt={`${name}, ${variantLabel(v)}`}
                      paper={paper}
                      helperOnline={helperOnline}
                      readOnly={readOnly}
                      onGenerate={onRegenerate && (() => onRegenerate(v.id))}
                      onUpload={onUpload && photo.pick}
                      full
                      className="rounded-[1.25rem]"
                    />
                  )
                  // Hover to look closer, with a mouse.
                  return finePointer && v.image_status === 'ready' ? (
                    <Lens zoomFactor={2} lensSize={180}>
                      {slot}
                    </Lens>
                  ) : (
                    slot
                  )
                }}
              />
            </div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0, transition: { delay: 0.12, duration: 0.45, ease: [0.16, 1, 0.3, 1] } }}
              className="grid content-start gap-6 px-6 pt-5 pb-10 md:py-12 md:pr-12 md:pl-6"
            >
              <div className="grid gap-3">
                <h2 id={titleId} {...textProps(name)} className="font-catalog text-[2rem] leading-[1.05] sm:text-[2.6rem]">
                  {name}
                </h2>
                {price && <p className="font-catalog text-2xl">{price}</p>}
              </div>

              <VariantChips product={product} index={index} onSelect={setIndex} />

              {product.description && (
                <p {...textProps(product.description)} className="max-w-prose leading-relaxed text-muted-foreground">
                  {product.description}
                </p>
              )}

              {details.length > 0 && (
                <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-3 border-t pt-5 text-sm">
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
          </div>

          <Button
            ref={closeRef}
            size="icon-sm"
            variant="secondary"
            aria-label="Close"
            onClick={onClose}
            className="absolute top-8 right-5 z-40 bg-tile/85 backdrop-blur hover:bg-tile md:top-5"
          >
            <X />
          </Button>
        </motion.div>
      </div>
    </>,
    document.body,
  )
}
