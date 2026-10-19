import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ImageGenerationLoader } from '@/components/ui/image-generation-loader'
import { useDevelop } from '@/hooks/use-develop'
import { assetUrl } from '@/lib/api'
import type { Paper } from '@/lib/paper'
import type { Variant } from '@/lib/types'
import { cn } from '@/lib/utils'

type Props = {
  variant: Variant
  alt: string
  paper: Paper
  helperOnline?: boolean
  readOnly?: boolean
  onGenerate?: () => void
  onUpload?: () => void
  /** The detail view shows the full-size photo; grids use the thumbnail. */
  full?: boolean
  className?: string
}

/** The square photo area of a product, in every state an image can be in. */
export function ImageSlot({ variant, alt, paper, helperOnline, readOnly, onGenerate, onUpload, full, className }: Props) {
  const [broken, setBroken] = useState<string | null>(null)
  // The detail view is already a close look, so its photo is in colour straight away.
  const develop = useDevelop<HTMLImageElement>(!full)
  const src = assetUrl(full ? (variant.image_url ?? variant.thumb_url) : (variant.thumb_url ?? variant.image_url))
  const base = cn('relative aspect-square w-full overflow-hidden rounded-xl', className)

  if (variant.image_status === 'ready' && src && broken !== src) {
    // AI photos are shot on white, so they can sit on the catalog's backdrop. Other photos are shown as they are.
    const generated = variant.image_source === 'generated'
    return (
      <div className={cn(base, generated ? 'paper paper-pale' : 'bg-tile')} data-paper={paper}>
        <img
          {...develop}
          src={src}
          alt={alt}
          loading="lazy"
          decoding="async"
          onError={() => setBroken(src)}
          className={cn('develop size-full object-contain', generated && 'on-paper scale-[0.92]')}
        />
      </div>
    )
  }

  if (readOnly) {
    // Viewers of a shared catalog don't need to know why a photo is missing.
    return (
      <div className={cn(base, 'paper paper-pale grid content-end')} data-paper={paper}>
        <p className="p-5 text-sm text-ink/60">Photo coming soon</p>
      </div>
    )
  }

  if (variant.image_status === 'queued' || variant.image_status === 'generating') {
    // Only animate while something is happening: a fast scan while the photo is made, a slow one in the queue,
    // and none while the helper on the Mac is off.
    const waiting = helperOnline === false
    const making = variant.image_status === 'generating'
    return (
      <div className={cn(base, 'paper paper-pale grid place-items-end')} data-paper={paper} role="status">
        {!waiting && (
          <ImageGenerationLoader
            colors={['#a3a3a3', '#0a0a0a']}
            effect={making ? 'shimmer' : 'none'}
            duration={making ? 3200 : 6500}
            overlayOpacity={making ? 0.12 : 0.06}
            bandHeight={making ? 56 : 36}
          />
        )}
        <p className="relative flex w-full items-center gap-2 p-4 text-sm font-medium text-ink/70">
          {making && <span className="pulse-dot size-1.5 rounded-full bg-ink" aria-hidden />}
          {making ? 'Making image…' : waiting ? 'Waiting for the image helper' : 'In the queue'}
        </p>
      </div>
    )
  }

  const message =
    variant.image_status === 'not_enough_detail'
      ? 'Not enough detail'
      : variant.image_status === 'failed'
        ? "Couldn't make this image"
        : broken
          ? "The image link doesn't work"
          : 'No image'
  return (
    <div className={cn(base, 'grey-card grid content-end')}>
      <div className="grid gap-2 p-5">
        <p className="text-sm font-semibold text-ink/80">{message}</p>
        {variant.image_status === 'not_enough_detail' && !readOnly && (
          <p className="text-xs leading-relaxed text-ink/60">Add a name or description so the photo matches the product.</p>
        )}
        {!readOnly && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {onGenerate && (
              <Button size="sm" variant="secondary" className="bg-tile hover:bg-tile/80" onClick={onGenerate}>
                {variant.image_status === 'failed' ? 'Try again' : variant.image_status === 'not_enough_detail' ? 'Generate anyway' : 'Generate'}
              </Button>
            )}
            {onUpload && (
              <Button size="sm" variant="ghost" className="hover:bg-tile/50" onClick={onUpload}>
                Upload photo
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
