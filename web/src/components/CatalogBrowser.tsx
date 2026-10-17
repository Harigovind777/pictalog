import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Input } from '@/components/ui/input'
import { categories, filterProducts } from '@/lib/catalog'
import type { Product } from '@/lib/types'
import { cn } from '@/lib/utils'
import { ProductCard } from './ProductCard'

type Props = {
  products: Product[]
  currency: string
  helperOnline?: boolean
  readOnly?: boolean
  onRegenerate?: (variantId: number) => void
  onUpload?: (variantId: number, file: File) => void
}

/** Search, category filter and the product grid. Shared by the owner's catalog view and the public page. */
export function CatalogBrowser({ products, currency, ...cardProps }: Props) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<string | null>(null)
  const allCategories = useMemo(() => categories(products), [products])
  const shown = useMemo(() => filterProducts(products, query, category), [products, query, category])

  return (
    <div className="grid gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative sm:w-72">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search products, codes, colours"
            aria-label="Search products"
            className="bg-tile pl-9"
          />
        </div>
        {allCategories.length > 1 && (
          <div className="-mx-4 flex gap-1.5 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0" role="group" aria-label="Categories">
            {[null, ...allCategories].map((c) => (
              <button
                key={c ?? 'all'}
                type="button"
                aria-pressed={category === c}
                onClick={() => setCategory(c)}
                className={cn(
                  'h-8 shrink-0 rounded-full px-3 text-sm transition-colors outline-ring focus-visible:outline-2',
                  category === c ? 'bg-ink text-white' : 'bg-tile text-muted-foreground hover:text-foreground',
                )}
              >
                {c ?? 'All'}
              </button>
            ))}
          </div>
        )}
      </div>

      {shown.length === 0 ? (
        <p className="py-16 text-center text-muted-foreground">No products match “{query}”. Try a shorter search.</p>
      ) : (
        <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {shown.map((p) => (
            <ProductCard key={p.id} product={p} currency={currency} {...cardProps} />
          ))}
        </div>
      )}
    </div>
  )
}
