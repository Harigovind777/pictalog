import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { DiffSummary } from '@/components/DiffSummary'
import { useHelperOnline } from '@/components/HelperStatus'
import { ItemsGrid } from '@/components/ItemsGrid'
import { MappingRow } from '@/components/MappingRow'
import { UploadButton } from '@/components/UploadButton'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { applyImport, getImport, setMapping } from '@/lib/api'
import { hasEnoughDetail, removeItem, updateItem } from '@/lib/items'
import type { ExtractedItem, ImportOut, ItemField } from '@/lib/types'

const isReading = (imp?: ImportOut) => imp?.status === 'parsing' || imp?.status === 'needs_ai'

export function ImportCheck() {
  const params = useParams()
  const catalogId = Number(params.id)
  const importId = Number(params.importId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const helperOnline = useHelperOnline()
  const { data: imp, error } = useQuery({
    queryKey: ['import', importId],
    queryFn: () => getImport(importId),
    refetchInterval: (query) => (isReading(query.state.data) ? 3000 : false),
  })
  const [items, setItems] = useState<ExtractedItem[] | null>(null)
  const [edited, setEdited] = useState(false)

  useEffect(() => {
    if (imp?.status === 'ready_for_review' && !edited) setItems(imp.items)
  }, [imp, edited])

  const mapping = useMutation({
    mutationFn: ({ header, field }: { header: string; field: ItemField | null }) => setMapping(importId, { [header]: field }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['import', importId], updated)
      setEdited(false)
      setItems(updated.items)
    },
    onError: (e) => toast.error(e.message),
  })
  const apply = useMutation({
    mutationFn: () => applyImport(importId, items ?? []),
    onSuccess: (catalog) => {
      queryClient.setQueryData(['catalog', catalogId], catalog)
      void queryClient.invalidateQueries({ queryKey: ['catalogs'] })
      toast.success('Catalog updated')
      navigate(`/catalogs/${catalogId}`)
    },
    onError: (e) => toast.error(e.message),
  })

  // An example value under each column heading, taken from the first row we read.
  const sample = useMemo(() => {
    const first: Record<string, string> = {}
    const item = imp?.items[0]
    if (!imp || !item) return first
    for (const header of imp.headers) {
      const field = imp.mapping[header]
      const key = (field === 'price' ? 'price_text' : field) as keyof ExtractedItem | null
      first[header] = key ? ((item[key] as string | null) ?? '') : (item.extra[header] ?? '')
    }
    return first
  }, [imp])

  if (error) return <Page><p className="text-destructive">{error.message}</p></Page>
  if (!imp) return <Page><Skeleton className="h-10 w-80" /></Page>

  if (isReading(imp)) {
    return (
      <Page>
        <div className="grid max-w-xl gap-6">
          <div className="studio-light aspect-[3/1] rounded-lg" />
          <div className="grid gap-2">
            <h1 className="text-3xl font-semibold">Reading {imp.filename}</h1>
            <p className="text-muted-foreground">
              {helperOnline === false
                ? "The image helper on your Mac is off. It will read this file as soon as it's back, and this page updates by itself."
                : 'The AI is picking out each product, price, size and colour. This page updates by itself.'}
            </p>
          </div>
        </div>
      </Page>
    )
  }

  if (imp.status === 'failed') {
    return (
      <Page>
        <div className="grid max-w-xl gap-4">
          <h1 className="text-3xl font-semibold">We couldn't read {imp.filename}</h1>
          <p className="text-muted-foreground">{imp.error}</p>
          <div className="flex gap-2">
            <UploadButton catalogId={catalogId} label="Try another file" />
            <Button variant="ghost" asChild>
              <Link to={`/catalogs/${catalogId}`}>Back to catalog</Link>
            </Button>
          </div>
        </div>
      </Page>
    )
  }

  if (imp.status === 'applied') {
    return (
      <Page>
        <h1 className="text-3xl font-semibold">This file has already been added</h1>
        <Button asChild className="w-fit">
          <Link to={`/catalogs/${catalogId}`}>Open catalog</Link>
        </Button>
      </Page>
    )
  }

  const rows = items ?? imp.items
  const withPhoto = rows.filter(hasEnoughDetail).length
  return (
    <>
      <Page>
        <div className="grid gap-2">
          <h1 className="text-3xl font-semibold sm:text-4xl">Check what we found</h1>
          <p className="text-muted-foreground">
            {rows.length} {rows.length === 1 ? 'row' : 'rows'} from {imp.filename}
            {imp.method === 'ai' && ', read by AI. Please check names and prices.'}
          </p>
        </div>

        {imp.diff && <DiffSummary diff={imp.diff} />}

        {imp.method === 'table' && (
          <section className="grid gap-3">
            <div className="grid gap-1">
              <h2 className="text-lg font-semibold">Columns</h2>
              <p className="text-sm text-muted-foreground">
                Fix any column we guessed wrong.{edited && ' Changing a column resets the edits you made below.'}
              </p>
            </div>
            <MappingRow
              headers={imp.headers}
              mapping={imp.mapping}
              sample={sample}
              disabled={mapping.isPending}
              onChange={(header, field) => mapping.mutate({ header, field })}
            />
          </section>
        )}

        <section className="grid gap-3 pb-24">
          <h2 className="text-lg font-semibold">Products</h2>
          <ItemsGrid
            items={rows}
            onChange={(index, field, value) => {
              setEdited(true)
              setItems(updateItem(rows, index, field, value))
            }}
            onRemove={(index) => {
              setEdited(true)
              setItems(removeItem(rows, index))
            }}
          />
        </section>
      </Page>

      <div className="fixed inset-x-0 bottom-0 z-20 border-t bg-sweep/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <p className="text-sm text-muted-foreground">
            {withPhoto} of {rows.length} will get a photo
          </p>
          <Button size="lg" disabled={apply.isPending || rows.length === 0} onClick={() => apply.mutate()}>
            {apply.isPending ? 'Updating catalog…' : 'Update catalog'}
          </Button>
        </div>
      </div>
    </>
  )
}

function Page({ children }: { children: React.ReactNode }) {
  return <main className="mx-auto grid max-w-7xl gap-8 px-4 py-8 sm:px-6 sm:py-12">{children}</main>
}
