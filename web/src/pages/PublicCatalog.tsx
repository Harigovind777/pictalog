import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Download } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { CatalogBrowser } from '@/components/CatalogBrowser'
import { CatalogCover } from '@/components/CatalogCover'
import { Wordmark } from '@/components/Wordmark'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { assetUrl, getPublic, publicPdfUrl } from '@/lib/api'
import { coversOf } from '@/lib/catalog'
import { paperFor } from '@/lib/paper'
import { textProps } from '@/lib/script'

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
  const covers = coversOf(catalog?.products ?? []).map((c) => ({ ...c, url: assetUrl(c.url) ?? c.url }))
  return (
    <div className="min-h-svh pt-safe">
      <main className="mx-auto grid max-w-7xl gap-10 px-4 py-10 sm:gap-12 sm:px-6 sm:py-16">
        {catalog ? (
          <header className="grid gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,30rem)] md:items-end md:gap-x-14">
            {covers.length > 0 && (
              <CatalogCover
                covers={covers}
                paper={paperFor(catalog.id)}
                eager
                className="rounded-[1.5rem] shadow-[0_30px_60px_-30px_rgb(0_0_0/0.35)] md:order-2"
              />
            )}
            <div className="grid content-end gap-5 md:order-1 md:pb-1">
              <p className="flex items-center gap-3 font-medium text-ink/70">
                {logo && <img src={logo} alt="" className="size-10 rounded-full border bg-tile object-contain p-1 shadow-sm" />}
                {catalog.company_name}
              </p>
              <div className="grid gap-3">
                <h1 {...textProps(catalog.name)} className="font-catalog font-masthead text-[3.25rem] leading-[0.95] tracking-[-0.025em] break-words sm:text-[5rem] lg:text-[6.5rem]">
                  {catalog.name}
                </h1>
                <p className="text-muted-foreground">
                  {catalog.products.length} {catalog.products.length === 1 ? 'product' : 'products'}
                </p>
              </div>
              <Button variant="outline" asChild className="w-fit">
                <a href={publicPdfUrl(token)} download>
                  <Download />
                  Download PDF
                </a>
              </Button>
            </div>
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
