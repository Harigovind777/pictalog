import { Upload } from 'lucide-react'
import { motion } from 'motion/react'
import { useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { SectionLabel } from '@/components/SectionLabel'
import { uploadImport } from '@/lib/api'
import { cn } from '@/lib/utils'

const ACCEPT = '.xlsx,.xlsm,.xls,.ods,.csv,.tsv,.json,.docx,.pdf,.txt,.md,.png,.jpg,.jpeg,.webp,.heic,image/*'

function useUpload(catalogId: number) {
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  async function upload(file: File | undefined) {
    if (!file) return
    setBusy(true)
    try {
      const imp = await uploadImport(catalogId, file)
      navigate(`/catalogs/${catalogId}/imports/${imp.id}`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'The upload failed.')
    } finally {
      setBusy(false)
    }
  }
  return { busy, upload }
}

function FileInput({ inputRef, onFile }: { inputRef: React.RefObject<HTMLInputElement | null>; onFile: (f?: File) => void }) {
  return (
    <input
      ref={inputRef}
      type="file"
      accept={ACCEPT}
      hidden
      onChange={(e) => {
        onFile(e.target.files?.[0])
        e.target.value = ''
      }}
    />
  )
}

type UploadButtonProps = { catalogId: number; label?: string; /** Shown instead of the label on phones. */ shortLabel?: string }

export function UploadButton({ catalogId, label = 'Upload file', shortLabel }: UploadButtonProps) {
  const input = useRef<HTMLInputElement>(null)
  const { busy, upload } = useUpload(catalogId)
  return (
    <>
      <Button onClick={() => input.current?.click()} disabled={busy} aria-label={busy ? undefined : label}>
        <Upload />
        {busy ? (
          'Reading file…'
        ) : shortLabel ? (
          <>
            <span className="sm:hidden">{shortLabel}</span>
            <span className="max-sm:hidden">{label}</span>
          </>
        ) : (
          label
        )}
      </Button>
      <FileInput inputRef={input} onFile={upload} />
    </>
  )
}

const FORMATS = ['Excel', 'CSV', 'Word', 'PDF', 'Photo of a price list']

/** Big drop area for an empty catalog (Aceternity's file upload): a faded tile grid and a card that lifts on hover. */
export function UploadDropzone({ catalogId }: { catalogId: number }) {
  const input = useRef<HTMLInputElement>(null)
  const { busy, upload } = useUpload(catalogId)
  const [over, setOver] = useState(false)

  function onDrop(event: DragEvent) {
    event.preventDefault()
    setOver(false)
    void upload(event.dataTransfer.files[0])
  }

  return (
    <motion.div
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      initial="rest"
      whileHover="lift"
      animate={over ? 'lift' : 'rest'}
      className="relative overflow-hidden rounded-2xl border bg-card px-6 py-14 shadow-md sm:py-20"
    >
      <div className="absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,white,transparent_75%)]" aria-hidden>
        <GridPattern />
      </div>
      <div className="relative grid justify-items-center gap-8 text-center">
        <div className="grid max-w-lg justify-items-center gap-4">
          <SectionLabel>Step 1 of 2</SectionLabel>
          <h2 className="font-display text-4xl sm:text-5xl">
            Add your products
          </h2>
          <p className="leading-relaxed text-muted-foreground">
            Drop in your product list, or tap the card. You'll check what we found before anything is added, then
            every product gets its photo.
          </p>
        </div>

        <button
          type="button"
          onClick={() => input.current?.click()}
          disabled={busy}
          aria-label={busy ? 'Reading file' : 'Choose a file'}
          className="relative grid size-32 place-items-center rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-4"
        >
          <motion.span
            variants={{ rest: { opacity: 0 }, lift: { opacity: 1 } }}
            className={cn('absolute inset-0 rounded-2xl border-2 border-dashed border-brand/50', over && 'border-brand')}
            aria-hidden
          />
          <motion.span
            variants={{ rest: { x: 0, y: 0 }, lift: { x: 14, y: -14 } }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="relative grid size-32 place-items-center rounded-2xl bg-white shadow-[0_10px_50px_rgb(15_23_42/0.12)]"
          >
            <span className="grid size-12 place-items-center rounded-xl bg-brand-gradient text-white shadow-accent">
              <Upload className="size-5" />
            </span>
            <span className="absolute bottom-3 text-xs font-medium text-muted-foreground">
              {busy ? 'Reading…' : over ? 'Drop it' : 'Choose a file'}
            </span>
          </motion.span>
        </button>

        <ul className="flex flex-wrap justify-center gap-1.5" aria-label="Files you can use">
          {FORMATS.map((f) => (
            <li key={f} className="rounded-full border bg-white px-3 py-1 text-xs font-medium text-muted-foreground">
              {f}
            </li>
          ))}
        </ul>
      </div>
      <FileInput inputRef={input} onFile={upload} />
    </motion.div>
  )
}

/** Aceternity's tile grid, in the app's greys. */
function GridPattern() {
  const columns = 41
  const rows = 13
  return (
    <div className="flex shrink-0 scale-105 flex-wrap items-center justify-center gap-px bg-muted">
      {Array.from({ length: rows * columns }).map((_, index) => (
        <div
          key={index}
          className={cn(
            'size-10 shrink-0 rounded-[2px] bg-sweep',
            index % 2 === 1 && 'shadow-[0_0_1px_3px_rgb(255_255_255)_inset]',
          )}
        />
      ))}
    </div>
  )
}
