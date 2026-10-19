import { useMutation, useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { motion } from 'motion/react'
import { Fragment, useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { CatalogShelf } from '@/components/CatalogShelf'
import { FloatingShowcase } from '@/components/FloatingShowcase'
import { SectionLabel } from '@/components/SectionLabel'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { createCatalog } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { firstLanguagesVisit, LANGUAGES } from '@/lib/languages'
import { fadeInUp, stagger } from '@/lib/motion'
import { shelfMemory } from '@/lib/page-transitions'
import { catalogsQuery } from '@/lib/queries'

export function Catalogs() {
  const { data, isLoading, error } = useQuery(catalogsQuery)
  const { user } = useAuth()
  const [open, setOpen] = useState(false)

  const products = data?.reduce((n, c) => n + c.product_count, 0) ?? 0

  useEffect(() => {
    // Told once, after signing in: people who stay signed in never see the languages on the sign-in page.
    if (firstLanguagesVisit()) {
      toast("Your lists can be in India's languages", { description: <LanguagesNews />, duration: 12_000 })
    }
  }, [])

  return (
    <main className="grid gap-8 py-8 sm:gap-10 sm:py-14">
      {data && data.length === 0 ? (
        <section className="mx-auto grid w-full max-w-7xl items-center gap-10 px-4 sm:px-6 md:grid-cols-[1.1fr_0.9fr] md:gap-14">
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
        <div className="mx-auto grid w-full max-w-7xl gap-3 px-4 sm:px-6">
          <h1 className="font-display text-[2.75rem] sm:text-7xl">Your catalogs</h1>
          {data && (
            <div className="flex items-center justify-between gap-4">
              <p className="text-muted-foreground">
                {data.length} {data.length === 1 ? 'catalog' : 'catalogs'} with {products} {products === 1 ? 'product' : 'products'}
              </p>
              <Button onClick={() => setOpen(true)} className="shrink-0">
                <Plus />
                New catalog
              </Button>
            </div>
          )}
        </div>
      )}

      {isLoading && (
        <div className="flex gap-3 overflow-hidden px-[9vw] sm:gap-6 sm:px-[max(1.5rem,calc(50vw-38.5rem))]">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="aspect-[4/5] w-[82vw] shrink-0 rounded-[1.5rem] sm:w-[22rem] lg:w-[24rem]" />
          ))}
        </div>
      )}
      {error && <p className="mx-auto w-full max-w-7xl px-4 text-destructive sm:px-6">{error.message}</p>}

      {data && data.length > 0 && <CatalogShelf catalogs={data} onNew={() => setOpen(true)} />}

      <NewCatalogDialog open={open} onOpenChange={setOpen} />
    </main>
  )
}

const NEWS = ['hi', 'ta', 'bn', 'ur']

function LanguagesNews() {
  const shown = LANGUAGES.filter((l) => NEWS.includes(l.lang))
  return (
    <>
      Upload a list in{' '}
      {shown.map((l) => (
        <Fragment key={l.lang}>
          <bdi lang={l.lang}>{l.native}</bdi>,{' '}
        </Fragment>
      ))}
      or {LANGUAGES.length - 1 - shown.length} more besides English. Names stay in their own script.
    </>
  )
}

function NewCatalogDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [currency, setCurrency] = useState('₹')
  const mutation = useMutation({
    mutationFn: () => createCatalog(name.trim(), currency.trim()),
    onSuccess: (catalog) => {
      shelfMemory.catalogId = catalog.id
      navigate(`/catalogs/${catalog.id}`, { viewTransition: true })
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
