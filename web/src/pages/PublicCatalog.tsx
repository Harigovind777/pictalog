import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Download } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { CatalogBrowser } from '@/components/CatalogBrowser'
import { SectionLabel } from '@/components/SectionLabel'
import { Wordmark } from '@/components/Wordmark'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { assetUrl, getPublic, publicPdfUrl } from '@/lib/api'
import { paperFor } from '@/lib/paper'

export function PublicCatalog() {
  const token = useParams().token ?? ''
  const { data: catalog, error } = useQuery({ queryKey: ['public', token], queryFn: () => getPublic(token), retry: false })

  if (error) {
    return (
      <main className="mx-auto grid min-h-svh max-w-md content-center gap-3 px-4 text-center">
        <h1 className="font-display text-4xl">This catalog isn't available</h1>
        <p className="text-muted-foreground">It isn't shared, or the link has been turned off. Ask whoever sent it for a new link.</p>
      </main>
    )
  }

  const logo = assetUrl(catalog?.logo_url)
  return (
    <div className="min-h-svh pt-safe">
      <main className="mx-auto grid max-w-7xl gap-10 px-4 py-10 sm:gap-12 sm:px-6 sm:py-16">
        {catalog ? (
          <header className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div className="grid gap-5">
              <div className="flex items-center gap-3">
                {logo && <img src={logo} alt="" className="size-11 rounded-full border bg-tile object-contain p-1 shadow-sm" />}
                <SectionLabel>{catalog.company_name}</SectionLabel>
              </div>
              <h1 className="font-display text-[2.75rem] break-words sm:text-7xl">{catalog.name}</h1>
            </div>
            <Button variant="outline" asChild className="w-fit">
              <a href={publicPdfUrl(token)} download>
                <Download />
                Download PDF
              </a>
            </Button>
          </header>
        ) : (
          <Skeleton className="h-24 w-80 rounded-2xl" />
        )}
        {catalog && (
          <CatalogBrowser products={catalog.products} currency={catalog.currency} paper={paperFor(catalog.id)} readOnly />
        )}
      </main>
      {/* The inverted closing section: every shared catalog invites its viewers to make their own. */}
      <footer className="mx-auto max-w-7xl px-4 pb-safe sm:px-6">
        <div className="dot-pattern relative mb-8 grid gap-6 overflow-hidden rounded-2xl bg-ink px-6 py-12 text-white sm:px-12 sm:py-16 md:grid-cols-[1.2fr_0.8fr] md:items-end">
          <div className="pointer-events-none absolute -top-24 -right-20 size-80 rounded-full bg-white/10 blur-[110px]" aria-hidden />
          <div className="relative grid gap-4">
            <p className="inline-flex items-baseline gap-2 text-white/70">
              Made with <Wordmark className="text-xl text-white" />
            </p>
            <h2 className="font-display text-4xl sm:text-5xl">
              Your price list could look like this.
            </h2>
            <p className="max-w-md leading-relaxed text-white/70">
              Upload a spreadsheet, PDF or a photo of a printed list, and get a studio photo for every product.
            </p>
          </div>
          <Button variant="inverse" size="lg" asChild className="relative w-full sm:w-fit md:justify-self-end">
            <Link to="/signup">
              Make your own catalog
              <ArrowRight className="transition-transform duration-200 group-hover/button:translate-x-1" />
            </Link>
          </Button>
        </div>
      </footer>
    </div>
  )
}
