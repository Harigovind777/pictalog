import { useMutation, useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { createCatalog, listCatalogs } from '@/lib/api'

const dateFormat = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

export function Catalogs() {
  const { data, isLoading, error } = useQuery({ queryKey: ['catalogs'], queryFn: listCatalogs })
  const [open, setOpen] = useState(false)

  return (
    <main className="mx-auto grid max-w-7xl gap-8 px-4 py-8 sm:px-6 sm:py-12">
      <div className="flex items-end justify-between gap-4">
        <h1 className="text-3xl font-semibold sm:text-4xl">Catalogs</h1>
        {data && data.length > 0 && (
          <Button onClick={() => setOpen(true)}>
            <Plus />
            New catalog
          </Button>
        )}
      </div>

      {isLoading && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
      )}
      {error && <p className="text-destructive">{error.message}</p>}

      {data && data.length === 0 && (
        <div className="grid max-w-xl gap-4 py-8">
          <h2 className="text-2xl font-semibold">Make your first catalog</h2>
          <p className="text-muted-foreground">
            Give it a name, then upload your product list. Every product and every size or colour gets its own realistic
            photo.
          </p>
          <div>
            <Button size="lg" onClick={() => setOpen(true)}>
              <Plus />
              New catalog
            </Button>
          </div>
        </div>
      )}

      {data && data.length > 0 && (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((c) => (
            <li key={c.id}>
              <Link
                to={`/catalogs/${c.id}`}
                className="grid h-full gap-6 rounded-lg bg-tile p-5 transition-colors outline-ring hover:bg-white/60 focus-visible:outline-2"
              >
                <h2 className="text-lg font-semibold">{c.name}</h2>
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>
                    {c.product_count} {c.product_count === 1 ? 'product' : 'products'}
                    {c.variant_count > c.product_count && `, ${c.variant_count} variants`}
                  </span>
                  <span>{dateFormat.format(new Date(c.updated_at + 'Z'))}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <NewCatalogDialog open={open} onOpenChange={setOpen} />
    </main>
  )
}

function NewCatalogDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [currency, setCurrency] = useState('₹')
  const mutation = useMutation({
    mutationFn: () => createCatalog(name.trim(), currency.trim()),
    onSuccess: (catalog) => navigate(`/catalogs/${catalog.id}`),
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
            <DialogTitle>New catalog</DialogTitle>
            <DialogDescription>You'll upload your product list on the next screen.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-2">
            <Label htmlFor="catalog-name">Name</Label>
            <Input id="catalog-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Summer 2026" required autoFocus />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="catalog-currency">Currency symbol</Label>
            <Input id="catalog-currency" value={currency} onChange={(e) => setCurrency(e.target.value)} maxLength={8} className="w-24" />
            <p className="text-sm text-muted-foreground">Added to prices that are written as plain numbers.</p>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={mutation.isPending || !name.trim()}>
              {mutation.isPending ? 'Creating…' : 'Create catalog'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
