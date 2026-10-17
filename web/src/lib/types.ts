// Mirrors the server's response models (pictalog/schemas.py and the api/ modules).

export type User = { id: number; email: string; company_name: string; logo_url: string | null }
export type AuthOut = { token: string; user: User }

export type ImageStatus = 'none' | 'not_enough_detail' | 'queued' | 'generating' | 'ready' | 'failed'
export type ImageSource = 'none' | 'generated' | 'provided' | 'uploaded'

export type Variant = {
  id: number
  sku: string | null
  size: string | null
  colour: string | null
  material: string | null
  price_text: string | null
  price_value: string | null
  extra: Record<string, string>
  image_url: string | null
  thumb_url: string | null
  image_status: ImageStatus
  image_source: ImageSource
}

export type Product = {
  id: number
  name: string | null
  brand: string | null
  category: string | null
  description: string | null
  variants: Variant[]
}

export type CatalogSummary = {
  id: number
  name: string
  currency: string
  product_count: number
  variant_count: number
  updated_at: string
}

export type Catalog = {
  id: number
  name: string
  currency: string
  share_enabled: boolean
  share_token: string | null
  products: Product[]
  counts: Partial<Record<ImageStatus, number>>
}

export type PublicCatalog = Omit<Catalog, 'share_enabled' | 'share_token'> & {
  company_name: string
  logo_url: string | null
}

export const ITEM_FIELDS = [
  'name', 'sku', 'price', 'size', 'colour', 'material', 'brand', 'category', 'description', 'image_url',
] as const
export type ItemField = (typeof ITEM_FIELDS)[number]

export type ExtractedItem = {
  name: string | null
  sku: string | null
  price_text: string | null
  size: string | null
  colour: string | null
  material: string | null
  brand: string | null
  category: string | null
  description: string | null
  image_url: string | null
  extra: Record<string, string>
}

export type DiffSummary = {
  new: number
  changed: number
  removed: number
  unchanged: number
  new_names: string[]
  changed_names: string[]
  removed_names: string[]
}

export type ImportStatus = 'parsing' | 'needs_ai' | 'ready_for_review' | 'applied' | 'failed'

export type ImportOut = {
  id: number
  catalog_id: number
  status: ImportStatus
  method: 'table' | 'ai' | null
  filename: string
  headers: string[]
  mapping: Record<string, ItemField | null>
  items: ExtractedItem[]
  diff: DiffSummary | null
  error: string | null
}

export type HelperStatus = { online: boolean; last_seen_at: string | null; engine: string | null }
export type ShareOut = { share_enabled: boolean; share_token: string | null }
