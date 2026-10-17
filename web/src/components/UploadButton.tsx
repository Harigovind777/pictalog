import { Upload } from 'lucide-react'
import { useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
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

export function UploadButton({ catalogId, label = 'Upload file' }: { catalogId: number; label?: string }) {
  const input = useRef<HTMLInputElement>(null)
  const { busy, upload } = useUpload(catalogId)
  return (
    <>
      <Button onClick={() => input.current?.click()} disabled={busy}>
        <Upload />
        {busy ? 'Reading file…' : label}
      </Button>
      <FileInput inputRef={input} onFile={upload} />
    </>
  )
}

/** Big drop area for an empty catalog. */
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
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={cn(
        'grid place-items-center gap-4 rounded-lg border-2 border-dashed bg-tile px-6 py-16 text-center transition-colors',
        over && 'border-amber bg-amber/5',
      )}
    >
      <div className="grid max-w-md gap-2">
        <h2 className="text-xl font-semibold">Add your products</h2>
        <p className="text-muted-foreground">
          Drop in a spreadsheet, CSV, Word file, PDF, or a photo of a printed price list. You'll check what we found
          before anything is added.
        </p>
      </div>
      <Button size="lg" onClick={() => input.current?.click()} disabled={busy}>
        <Upload />
        {busy ? 'Reading file…' : 'Choose a file'}
      </Button>
      <FileInput inputRef={input} onFile={upload} />
    </div>
  )
}
