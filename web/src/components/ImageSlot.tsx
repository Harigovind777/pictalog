import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { assetUrl } from '@/lib/api'
import type { Variant } from '@/lib/types'
import { cn } from '@/lib/utils'

type Props = {
  variant: Variant
  alt: string
  helperOnline?: boolean
  readOnly?: boolean
  onGenerate?: () => void
  onUpload?: () => void
  className?: string
}

/** The square photo area of a product, in every state an image can be in. */
export function ImageSlot({ variant, alt, helperOnline, readOnly, onGenerate, onUpload, className }: Props) {
  const [broken, setBroken] = useState<string | null>(null)
  const src = assetUrl(variant.thumb_url ?? variant.image_url)
  const base = cn('relative aspect-square w-full overflow-hidden rounded-md', className)

  if (variant.image_status === 'ready' && src && broken !== src) {
    return (
      <div className={cn(base, 'bg-tile')}>
        <img src={src} alt={alt} loading="lazy" onError={() => setBroken(src)} className="size-full object-contain" />
      </div>
    )
  }

  if (readOnly) {
    // Viewers of a shared catalog don't need to know why a photo is missing.
    return (
      <div className={cn(base, 'grey-card grid content-end')}>
        <p className="p-5 text-sm text-ink/70">Photo coming soon</p>
      </div>
    )
  }

  if (variant.image_status === 'queued' || variant.image_status === 'generating') {
    const waiting = helperOnline === false
    return (
      <div className={cn(base, 'studio-light grid place-items-end')} role="status">
        <p className="w-full p-3 text-sm text-ink/80">
          {variant.image_status === 'generating' ? 'Making image…' : waiting ? 'Waiting for the image helper' : 'In the queue'}
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
        <p className="text-sm font-medium text-ink/80">{message}</p>
        {variant.image_status === 'not_enough_detail' && !readOnly && (
          <p className="text-xs text-ink/60">Add a name or description so the photo matches the product.</p>
        )}
        {!readOnly && (
          <div className="flex flex-wrap gap-2">
            {onGenerate && (
              <Button size="sm" variant="secondary" className="bg-tile/90" onClick={onGenerate}>
                {variant.image_status === 'failed' ? 'Try again' : variant.image_status === 'not_enough_detail' ? 'Generate anyway' : 'Generate'}
              </Button>
            )}
            {onUpload && (
              <Button size="sm" variant="ghost" onClick={onUpload}>
                Upload photo
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
