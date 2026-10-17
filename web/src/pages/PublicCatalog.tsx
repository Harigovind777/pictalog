import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { useParams } from 'react-router'
import { CatalogBrowser } from '@/components/CatalogBrowser'
import { Wordmark } from '@/components/Wordmark'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { assetUrl, getPublic, publicPdfUrl } from '@/lib/api'

export function PublicCatalog() {
  const token = useParams().token ?? ''
  const { data: catalog, error } = useQuery({ queryKey: ['public', token], queryFn: () => getPublic(token), retry: false })

  if (error) {
    return (
      <main className="mx-auto grid min-h-svh max-w-md content-center gap-3 px-4 text-center">
        <h1 className="text-2xl font-semibold">This catalog isn't available</h1>
        <p className="text-muted-foreground">It isn't shared, or the link has been turned off. Ask whoever sent it for a new link.</p>
      </main>
    )
  }

  const logo = assetUrl(catalog?.logo_url)
  return (
    <div className="min-h-svh">
      <main className="mx-auto grid max-w-7xl gap-10 px-4 py-10 sm:px-6 sm:py-14">
        {catalog ? (
          <header className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex items-center gap-4">
              {logo && <img src={logo} alt="" className="size-16 rounded-md bg-tile object-contain p-1" />}
              <div className="grid gap-1">
                <p className="text-muted-foreground">{catalog.company_name}</p>
                <h1 className="text-3xl font-semibold sm:text-4xl">{catalog.name}</h1>
              </div>
            </div>
            <Button variant="outline" asChild className="w-fit">
              <a href={publicPdfUrl(token)} download>
                <Download />
                Download PDF
              </a>
            </Button>
          </header>
        ) : (
          <Skeleton className="h-16 w-80" />
        )}
        {catalog && <CatalogBrowser products={catalog.products} currency={catalog.currency} readOnly />}
      </main>
      <footer className="mx-auto max-w-7xl px-4 pb-10 text-sm text-muted-foreground sm:px-6">
        Made with <Wordmark className="text-sm" />
      </footer>
    </div>
  )
}
