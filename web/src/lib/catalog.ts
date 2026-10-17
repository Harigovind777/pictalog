import type { Catalog, ImageStatus, Product, Variant } from './types'

const norm = (text: string | null | undefined) => (text ?? '').trim().toLowerCase()

export function filterProducts(products: Product[], query: string, category: string | null): Product[] {
  const q = norm(query)
  const cat = category ? norm(category) : null
  return products.filter((p) => {
    if (cat && norm(p.category) !== cat) return false
    if (!q) return true
    const haystack = [
      p.name, p.brand, p.description,
      ...p.variants.flatMap((v) => [v.sku, v.colour, v.size, v.material]),
    ]
    return haystack.some((field) => norm(field).includes(q))
  })
}

export function categories(products: Product[]): string[] {
  const byKey = new Map<string, string>()
  for (const p of products) {
    const label = (p.category ?? '').trim()
    if (label && !byKey.has(norm(label))) byKey.set(norm(label), label)
  }
  return [...byKey.values()].sort((a, b) => a.localeCompare(b))
}

type Counts = Catalog['counts']

export function imageProgress(counts: Counts): { done: number; total: number } {
  const total = (['ready', 'queued', 'generating', 'failed'] as ImageStatus[]).reduce((n, s) => n + (counts[s] ?? 0), 0)
  return { done: counts.ready ?? 0, total }
}

export function isWorking(counts: Counts): boolean {
  return (counts.queued ?? 0) + (counts.generating ?? 0) > 0
}

export function priceLabel(priceText: string | null, currency: string): string {
  const text = (priceText ?? '').trim()
  return text && currency && /^[\d.,\s]+$/.test(text) ? `${currency}${text}` : text
}

export function variantLabel(v: Variant): string {
  const parts = [v.size, v.colour, v.material].filter(Boolean)
  return parts.length ? parts.join(', ') : (v.sku ?? 'Standard')
}
