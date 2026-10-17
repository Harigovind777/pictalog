import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, MoreHorizontal } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { CatalogBrowser } from '@/components/CatalogBrowser'
import { useHelperOnline } from '@/components/HelperStatus'
import { SectionLabel } from '@/components/SectionLabel'
import { ShareDialog } from '@/components/ShareDialog'
import { UploadButton, UploadDropzone } from '@/components/UploadButton'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { deleteCatalog, getCatalog, pdfUrl, regenerate, updateCatalog, uploadVariantPhoto } from '@/lib/api'
import { imageProgress, isWorking } from '@/lib/catalog'
import { paperFor } from '@/lib/paper'
import { downloadWithAuth } from '@/lib/links'
import type { Catalog } from '@/lib/types'

export function CatalogView() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const helperOnline = useHelperOnline()
  const { data: catalog, error } = useQuery({
    queryKey: ['catalog', id],
    queryFn: () => getCatalog(id),
    refetchInterval: (query) => (query.state.data && isWorking(query.state.data.counts) ? 3000 : false),
  })
  const [editing, setEditing] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['catalog', id] })
  const regen = useMutation({ mutationFn: regenerate, onSuccess: refresh, onError: (e) => toast.error(e.message) })
  const photo = useMutation({
    mutationFn: ({ variantId, file }: { variantId: number; file: File }) => uploadVariantPhoto(variantId, file),
    onSuccess: () => {
      toast.success('Photo added')
      void refresh()
    },
    onError: (e) => toast.error(e.message),
  })
  const remove = useMutation({
    mutationFn: () => deleteCatalog(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['catalogs'] })
      navigate('/', { replace: true })
      toast.success('Catalog deleted')
    },
  })

  if (error) return <p className="mx-auto max-w-7xl px-4 py-12 text-destructive sm:px-6">{error.message}</p>
  if (!catalog) {
    return (
      <main className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 sm:py-14">
        <Skeleton className="h-14 w-72 rounded-2xl" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-5">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="aspect-square rounded-[1.25rem]" />
          ))}
        </div>
      </main>
    )
  }

  const variantCount = catalog.products.reduce((n, p) => n + p.variants.length, 0)
  const progress = imageProgress(catalog.counts)
  const making = progress.done < progress.total && isWorking(catalog.counts)
  const paper = paperFor(catalog.id)

  async function downloadPdf() {
    try {
      await downloadWithAuth(pdfUrl(id), `${catalog!.name}.pdf`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'The download failed.')
    }
  }

  return (
    <main className="mx-auto grid max-w-7xl gap-8 px-4 py-8 sm:gap-10 sm:px-6 sm:py-14">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="grid gap-4">
          <SectionLabel live={making && helperOnline !== false}>
            {making ? (helperOnline === false ? 'Waiting for your Mac' : 'Making images') : catalog.share_enabled ? 'Shared' : 'Catalog'}
          </SectionLabel>
          <h1 className="font-display text-[2.75rem] break-words sm:text-7xl">{catalog.name}</h1>
          <p className="text-muted-foreground">
            {catalog.products.length === 0
              ? 'No products yet'
              : `${catalog.products.length} ${catalog.products.length === 1 ? 'product' : 'products'}` +
                (variantCount > catalog.products.length ? `, ${variantCount} variants` : '')}
          </p>
        </div>
        {catalog.products.length > 0 && (
          <div className="flex flex-wrap gap-1.5 max-sm:[&>button]:px-3 sm:gap-2">
            <UploadButton catalogId={id} label="Upload new file" shortLabel="Upload" />
            <ShareDialog catalog={catalog} />
            <Button variant="outline" onClick={downloadPdf}>
              <Download />
              PDF
            </Button>
            <CatalogMenu onEdit={() => setEditing(true)} onDelete={() => setConfirmDelete(true)} />
          </div>
        )}
      </div>

      {making && (
        <div className="grid max-w-md gap-2.5 rounded-2xl border bg-card p-4 shadow-sm" role="status">
          <div className="flex justify-between text-sm">
            <span className="font-medium">{helperOnline === false ? 'Waiting for the image helper on your Mac' : 'Making images'}</span>
            <span className="text-muted-foreground">
              {progress.done} of {progress.total}
            </span>
          </div>
          <Progress
            value={(progress.done / progress.total) * 100}
            className="h-2 bg-muted [&>[data-slot=progress-indicator]]:bg-brand-gradient [&>[data-slot=progress-indicator]]:shadow-accent"
          />
        </div>
      )}

      {catalog.products.length === 0 ? (
        <UploadDropzone catalogId={id} />
      ) : (
        <CatalogBrowser
          products={catalog.products}
          currency={catalog.currency}
          paper={paper}
          helperOnline={helperOnline}
          onRegenerate={(variantId) => regen.mutate(variantId)}
          onUpload={(variantId, file) => photo.mutate({ variantId, file })}
        />
      )}

      <EditCatalogDialog catalog={catalog} open={editing} onOpenChange={setEditing} />
      <AlertDialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete “{catalog.name}”?</AlertDialogTitle>
            <AlertDialogDescription>
              All its products and images are removed, and its share link stops working. This can't be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep catalog</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={() => remove.mutate()}>
              Delete catalog
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  )
}

function CatalogMenu({ onEdit, onDelete }: { onEdit: () => void; onDelete: () => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" aria-label="More catalog options">
          <MoreHorizontal />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onSelect={onEdit}>Rename or change currency</DropdownMenuItem>
        <DropdownMenuItem variant="destructive" onSelect={onDelete}>
          Delete catalog
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function EditCatalogDialog({ catalog, open, onOpenChange }: { catalog: Catalog; open: boolean; onOpenChange: (o: boolean) => void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState(catalog.name)
  const [currency, setCurrency] = useState(catalog.currency)
  const mutation = useMutation({
    mutationFn: () => updateCatalog(catalog.id, { name: name.trim(), currency: currency.trim() }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['catalog', catalog.id], updated)
      onOpenChange(false)
      toast.success('Catalog saved')
    },
    onError: (e) => toast.error(e.message),
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    mutation.mutate()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={submit} className="grid gap-5">
          <DialogHeader>
            <DialogTitle>Catalog details</DialogTitle>
          </DialogHeader>
          <div className="grid gap-2">
            <Label htmlFor="edit-name">Name</Label>
            <Input id="edit-name" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="edit-currency">Currency symbol</Label>
            <Input id="edit-currency" value={currency} onChange={(e) => setCurrency(e.target.value)} maxLength={8} className="w-28" />
          </div>
          <DialogFooter>
            <Button type="submit" size="lg" disabled={mutation.isPending || !name.trim()}>
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
