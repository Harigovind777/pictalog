import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, Download, MoreHorizontal } from 'lucide-react'
import { motion } from 'motion/react'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { CatalogBrowser } from '@/components/CatalogBrowser'
import { CatalogCover } from '@/components/CatalogCover'
import { useHelperOnline } from '@/components/HelperStatus'
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
import { Skeleton } from '@/components/ui/skeleton'
import { assetUrl, deleteCatalog, pdfUrl, regenerate, updateCatalog, uploadVariantPhoto } from '@/lib/api'
import { coversOf, imageProgress, isWorking } from '@/lib/catalog'
import { easeOut } from '@/lib/motion'
import { shelfMemory } from '@/lib/page-transitions'
import { paperFor } from '@/lib/paper'
import { downloadWithAuth } from '@/lib/links'
import { catalogQuery } from '@/lib/queries'
import { textProps } from '@/lib/script'
import type { Catalog } from '@/lib/types'

export function CatalogView() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const helperOnline = useHelperOnline()
  const { data: catalog, error } = useQuery({
    ...catalogQuery(id),
    refetchInterval: (query) => (query.state.data && isWorking(query.state.data.counts) ? 3000 : false),
  })
  const [editing, setEditing] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const covers = useMemo(
    () => coversOf(catalog?.products ?? []).map((c) => ({ ...c, url: assetUrl(c.url) ?? c.url })),
    [catalog?.products],
  )

  // Going back to the shelf lands on this catalog's cover.
  useEffect(() => {
    shelfMemory.catalogId = id
  }, [id])

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
      shelfMemory.catalogId = null
      navigate('/', { replace: true, viewTransition: true })
      toast.success('Catalog deleted')
    },
  })

  if (error) return <p className="mx-auto max-w-7xl px-4 py-12 text-destructive sm:px-6">{error.message}</p>
  if (!catalog) {
    return (
      <main className="mx-auto grid max-w-7xl gap-8 px-4 pt-12 pb-10 sm:px-6 sm:pt-16">
        <Skeleton className="aspect-[4/3] w-full rounded-[1.5rem] md:hidden" />
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

  const status = making
    ? helperOnline === false
      ? 'Waiting for the image helper on your Mac'
      : 'Making images'
    : null

  return (
    <main className="mx-auto grid max-w-7xl gap-8 px-4 pt-3 pb-12 sm:gap-12 sm:px-6 sm:pt-6 sm:pb-16">
      <header className="grid gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,30rem)] md:items-end md:gap-x-14">
        <Link
          to="/"
          viewTransition
          className="-ml-1 inline-flex w-fit items-center gap-0.5 rounded-full py-1 pr-2 text-sm font-medium text-muted-foreground transition-colors outline-ring hover:text-foreground focus-visible:outline-2 md:col-span-2"
        >
          <ChevronLeft className="size-4" />
          All catalogs
        </Link>
        {catalog.products.length > 0 && (
          <CatalogCover
            covers={covers}
            paper={paper}
            morph
            eager
            emptyText="The cover fills in as photos are made"
            className="rounded-[1.5rem] shadow-[0_30px_60px_-30px_rgb(0_0_0/0.35)] md:order-2"
          />
        )}
        <div className="grid content-end gap-5 md:order-1 md:pb-1">
          <div className="grid gap-3">
            <h1 {...textProps(catalog.name)} className="w-fit font-catalog font-masthead text-[3.25rem] leading-[0.95] tracking-[-0.025em] break-words [view-transition-name:catalog-title] sm:text-[5rem] lg:text-[6.5rem]">
              {catalog.name}
            </h1>
            <p className="text-muted-foreground">
              {catalog.products.length === 0
                ? 'No products yet'
                : `${catalog.products.length} ${catalog.products.length === 1 ? 'product' : 'products'}` +
                  (variantCount > catalog.products.length ? ` in ${variantCount} sizes and colours` : '')}
              {catalog.share_enabled && '. Anyone with the link can view it.'}
            </p>
          </div>

          {status && (
            <div className="grid max-w-md gap-2" role="status">
              <div className="flex justify-between gap-4 text-sm">
                <span className="inline-flex items-center gap-2 font-medium">
                  <span className={helperOnline === false ? 'size-1.5 rounded-full bg-greycard' : 'pulse-dot size-1.5 rounded-full bg-ink'} aria-hidden />
                  {status}
                </span>
                <span className="text-muted-foreground tabular-nums">
                  {progress.done} of {progress.total}
                </span>
              </div>
              <div className="h-0.5 overflow-hidden rounded-full bg-ink/10">
                <motion.div
                  initial={false}
                  animate={{ scaleX: progress.done / progress.total }}
                  transition={{ duration: 0.8, ease: easeOut }}
                  className="h-full origin-left bg-ink"
                />
              </div>
            </div>
          )}

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
      </header>

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
      void queryClient.invalidateQueries({ queryKey: ['catalogs'] })
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
