import type { ExtractedItem, ItemField } from './types'

export type TextField = Exclude<keyof ExtractedItem, 'extra'>

export const FIELD_LABELS: Record<ItemField, string> = {
  name: 'Name',
  sku: 'Code / SKU',
  price: 'Price',
  size: 'Size',
  colour: 'Colour',
  material: 'Material',
  brand: 'Brand',
  category: 'Category',
  description: 'Description',
  image_url: 'Image link',
}

export function emptyItem(): ExtractedItem {
  return {
    name: null, sku: null, price_text: null, size: null, colour: null, material: null, brand: null, category: null,
    description: null, image_url: null, extra: {},
  }
}

export function updateItem(items: ExtractedItem[], index: number, field: TextField, value: string): ExtractedItem[] {
  return items.map((item, i) => (i === index ? { ...item, [field]: value.trim() ? value : null } : item))
}

export function removeItem(items: ExtractedItem[], index: number): ExtractedItem[] {
  return items.filter((_, i) => i !== index)
}

/** Same rule as the server (pictalog/catalog/detail.py): a real word in the name or description. */
export function hasEnoughDetail(item: ExtractedItem): boolean {
  let name = item.name ?? ''
  if (item.sku && name.trim().toLowerCase() === item.sku.trim().toLowerCase()) name = ''
  const tokens = `${name} ${item.description ?? ''}`.split(/\s+/)
  return tokens.some((t) => !/\d/.test(t) && (t.match(/\p{L}/gu)?.length ?? 0) >= 3)
}
