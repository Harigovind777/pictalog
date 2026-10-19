import { AnimatePresence, motion } from 'motion/react'
import { useCallback, useMemo, useState } from 'react'
import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input'
import { categories, filterProducts } from '@/lib/catalog'
import type { Paper } from '@/lib/paper'
import type { Product } from '@/lib/types'
import { cn } from '@/lib/utils'
import { type ProductActions, ProductCard } from './ProductCard'
import { ProductDetail } from './ProductDetail'

type Props = ProductActions & {
  products: Product[]
  currency: string
  paper: Paper
}

/** Search hints drawn from this catalog, so they show the kinds of things people can type. */
function searchHints(products: Product[]): string[] {
  const first = products.find((p) => p.name)?.name
  const code = products.flatMap((p) => p.variants).find((v) => v.sku)?.sku
  const colour = products.flatMap((p) => p.variants).find((v) => v.colour)?.colour
  return [
    first && `Search “${first.toLowerCase()}”`,
    code && `Search a code like ${code}`,
    colour && `Search a colour like ${colour.toLowerCase()}`,
    'Search products, codes, colours',
  ].filter((h): h is string => Boolean(h))
}

/** Search, category filter and the product grid. Shared by the owner's catalog view and the public page. */
export function CatalogBrowser({ products, currency, paper, ...actions }: Props) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<string | null>(null)
  const [open, setOpen] = useState<{ id: number; index: number } | null>(null)
  const allCategories = useMemo(() => categories(products), [products])
  const shown = useMemo(() => filterProducts(products, query, category), [products, query, category])
  const hints = useMemo(() => searchHints(products), [products])
  const openProduct = open && products.find((p) => p.id === open.id)
  const close = useCallback(() => setOpen(null), [])

  return (
    <div className="grid gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <PlaceholdersAndVanishInput placeholders={hints} onValueChange={setQuery} label="Search products" className="sm:w-80" />
        {allCategories.length > 1 && (
          <div className="no-scrollbar -mx-4 flex gap-1 overflow-x-auto px-4 py-1 sm:mx-0 sm:px-0" role="group" aria-label="Categories">
            {[null, ...allCategories].map((c) => (
              <button
                key={c ?? 'all'}
                type="button"
                aria-pressed={category === c}
                onClick={() => setCategory(c)}
                className={cn(
                  'relative h-9 shrink-0 rounded-full px-4 text-sm font-medium transition-colors outline-ring first-letter:uppercase focus-visible:outline-2',
                  category === c ? 'text-white' : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {category === c && (
                  <motion.span
                    layoutId="category-pill"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.5 }}
                    className="absolute inset-0 rounded-full bg-ink shadow-md"
                  />
                )}
                <span className="relative">{c ?? 'All'}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {shown.length === 0 ? (
        <p className="py-16 text-center text-muted-foreground">No products match “{query}”. Try a shorter search.</p>
      ) : (
        // Filtering slides the remaining products into their new places. Long catalogs skip that, and products far
        // down the page aren't drawn until they're near.
        <div className="relative grid grid-cols-2 gap-x-3 gap-y-7 sm:grid-cols-3 sm:gap-x-5 sm:gap-y-10 lg:grid-cols-4 xl:grid-cols-5">
          <AnimatePresence mode="popLayout" initial={false}>
            {shown.map((p) => (
              <motion.div
                key={p.id}
                layout={shown.length <= 80 ? 'position' : false}
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.94 }}
                transition={{ type: 'spring', bounce: 0.12, duration: 0.5 }}
                className="[contain-intrinsic-size:auto_20rem] [content-visibility:auto]"
              >
                <ProductCard
                  product={p}
                  currency={currency}
                  paper={paper}
                  onOpen={(index) => setOpen({ id: p.id, index })}
                  {...actions}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <AnimatePresence>
        {openProduct && (
          <ProductDetail
            key={openProduct.id}
            product={openProduct}
            currency={currency}
            paper={paper}
            startIndex={open.index}
            onClose={close}
            {...actions}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
