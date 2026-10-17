import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowRight, Plus } from 'lucide-react'
import { motion } from 'motion/react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { CatalogCover } from '@/components/CatalogCover'
import { FloatingShowcase } from '@/components/FloatingShowcase'
import { SectionLabel } from '@/components/SectionLabel'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { assetUrl, createCatalog, listCatalogs } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { fadeInUp, stagger } from '@/lib/motion'
import { paperFor } from '@/lib/paper'
import { cn } from '@/lib/utils'

const dateFormat = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

export function Catalogs() {
  const { data, isLoading, error } = useQuery({ queryKey: ['catalogs'], queryFn: listCatalogs })
  const { user } = useAuth()
  const [open, setOpen] = useState(false)

  const totals = data && {
    catalogs: data.length,
    products: data.reduce((n, c) => n + c.product_count, 0),
    variants: data.reduce((n, c) => n + c.variant_count, 0),
  }

  return (
    <main className="mx-auto grid max-w-7xl gap-8 px-4 py-8 sm:gap-12 sm:px-6 sm:py-14">
      {data && data.length === 0 ? (
        <section className="grid items-center gap-10 md:grid-cols-[1.1fr_0.9fr] md:gap-14">
          <motion.div variants={stagger} initial="hidden" animate="visible" className="grid max-w-xl gap-6">
            <motion.div variants={fadeInUp}>
              <SectionLabel live>{user?.company_name ?? 'Your studio'}</SectionLabel>
            </motion.div>
            <motion.h1 variants={fadeInUp} className="font-display text-[2.75rem] sm:text-6xl lg:text-7xl">
              Make your first catalog
            </motion.h1>
            <motion.p variants={fadeInUp} className="text-lg leading-relaxed text-muted-foreground">
              Give it a name, then upload your product list. Every product and every size or colour gets its own
              studio photo, like these.
            </motion.p>
            <motion.div variants={fadeInUp}>
              <Button size="lg" onClick={() => setOpen(true)} className="w-full sm:w-auto">
                <Plus />
                New catalog
              </Button>
            </motion.div>
          </motion.div>
          <FloatingShowcase className="mx-auto" />
        </section>
      ) : (
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div className="grid gap-4">
            <SectionLabel>{user?.company_name ?? 'Your studio'}</SectionLabel>
            <h1 className="font-display text-[2.75rem] sm:text-7xl">
              Your catalogs
            </h1>
          </div>
          {data && (
            <Button size="lg" onClick={() => setOpen(true)} className="w-full sm:w-auto">
              <Plus />
              New catalog
            </Button>
          )}
        </div>
      )}

      {totals && totals.catalogs > 0 && (
        <dl className="dot-pattern relative grid grid-cols-3 overflow-hidden rounded-2xl bg-ink px-2 py-6 text-white sm:py-8">
          <div className="pointer-events-none absolute -top-24 -right-16 size-64 rounded-full bg-white/10 blur-[90px]" aria-hidden />
          {[
            ['Catalogs', totals.catalogs],
            ['Products', totals.products],
            ['Sizes and colours', totals.variants],
          ].map(([label, value], i) => (
            <div key={label} className={cn('relative grid gap-1 px-3 text-center sm:px-6', i > 0 && 'border-l border-white/10')}>
              <dd className="font-display text-3xl sm:text-5xl">{value}</dd>
              <dt className="text-xs text-white/60 sm:text-sm">{label}</dt>
            </div>
          ))}
        </dl>
      )}

      {isLoading && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="aspect-[4/3] rounded-2xl" />
          ))}
        </div>
      )}
      {error && <p className="text-destructive">{error.message}</p>}

      {data && data.length > 0 && (
        <motion.ul variants={stagger} initial="hidden" animate="visible" className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((c) => (
            <motion.li key={c.id} variants={fadeInUp}>
              <Link
                to={`/catalogs/${c.id}`}
                className="group relative grid h-full gap-4 overflow-hidden rounded-2xl border bg-card p-2 pb-5 shadow-md transition-[box-shadow,translate] duration-300 outline-none hover:-translate-y-1 hover:shadow-xl focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <span className="pointer-events-none absolute inset-0 bg-gradient-to-br from-ink/[0.03] to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" aria-hidden />
                <CatalogCover
                  paper={paperFor(c.id)}
                  covers={c.covers.map((cover) => ({ ...cover, url: assetUrl(cover.url) ?? cover.url }))}
                  emptyText="Upload a product list to fill this catalog"
                  className="rounded-xl"
                />
                <div className="relative grid gap-1 px-3">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="truncate text-xl font-semibold tracking-[-0.01em]">{c.name}</h2>
                    <ArrowRight className="size-4 shrink-0 text-muted-foreground transition-transform duration-200 group-hover:translate-x-1 group-hover:text-brand" aria-hidden />
                  </div>
                  <div className="flex justify-between gap-4 text-sm text-muted-foreground">
                    <span>
                      {c.product_count} {c.product_count === 1 ? 'product' : 'products'}
                      {c.variant_count > c.product_count && `, ${c.variant_count} variants`}
                    </span>
                    <span>{dateFormat.format(new Date(c.updated_at + 'Z'))}</span>
                  </div>
                </div>
              </Link>
            </motion.li>
          ))}
        </motion.ul>
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
            <Input id="catalog-currency" value={currency} onChange={(e) => setCurrency(e.target.value)} maxLength={8} className="w-28" />
            <p className="text-sm text-muted-foreground">Added to prices that are written as plain numbers.</p>
          </div>
          <DialogFooter>
            <Button type="submit" size="lg" disabled={mutation.isPending || !name.trim()}>
              {mutation.isPending ? 'Creating…' : 'Create catalog'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
