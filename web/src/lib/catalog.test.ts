import { describe, expect, it } from 'vitest'
import { categories, coversOf, filterProducts, imageProgress, isWorking, priceLabel, variantLabel, variantLabels } from './catalog'
import type { Product, Variant } from './types'

function variant(over: Partial<Variant> = {}): Variant {
  return {
    id: 1, sku: null, size: null, colour: null, material: null, price_text: null, price_value: null, extra: {},
    image_url: null, thumb_url: null, image_status: 'ready', image_source: 'generated', ...over,
  }
}

function product(over: Partial<Product> = {}): Product {
  return { id: 1, name: 'Tee', brand: null, category: null, description: null, variants: [variant()], ...over }
}

const products = [
  product({ id: 1, name: 'Classic Tee', brand: 'Acme', category: 'Apparel', variants: [variant({ sku: 'T-100', colour: 'Red' })] }),
  product({ id: 2, name: 'Coffee Mug', category: 'Kitchen', description: 'Stoneware', variants: [variant({ size: '350 ml' })] }),
  product({ id: 3, name: 'Bowl', category: 'kitchen ', variants: [variant()] }),
]

describe('priceLabel', () => {
  it('adds the currency to bare numbers in any digits', () => {
    expect(priceLabel('1,299', '₹')).toBe('₹1,299')
    expect(priceLabel('१,२९९', '₹')).toBe('₹१,२९९')
    expect(priceLabel('৳ ২৫০', '₹')).toBe('৳ ২৫০')
  })
})

describe('filterProducts', () => {
  it('matches sku and colour', () => {
    expect(filterProducts(products, 't-100', null).map((p) => p.id)).toEqual([1])
    expect(filterProducts(products, 'RED', null).map((p) => p.id)).toEqual([1])
  })
  it('matches name, brand, description and size', () => {
    expect(filterProducts(products, 'acme', null).map((p) => p.id)).toEqual([1])
    expect(filterProducts(products, 'stoneware', null).map((p) => p.id)).toEqual([2])
    expect(filterProducts(products, '350', null).map((p) => p.id)).toEqual([2])
  })
  it('filters by category ignoring case and spaces', () => {
    expect(filterProducts(products, '', 'Kitchen').map((p) => p.id)).toEqual([2, 3])
  })
  it('returns everything for an empty query', () => {
    expect(filterProducts(products, '  ', null)).toHaveLength(3)
  })
})

describe('categories', () => {
  it('categories sorted unique', () => {
    expect(categories(products)).toEqual(['Apparel', 'Kitchen'])
  })
})

describe('imageProgress', () => {
  it('imageProgress ignores not_enough_detail', () => {
    expect(imageProgress({ ready: 3, queued: 2, generating: 1, not_enough_detail: 4, none: 1, failed: 1 })).toEqual({
      done: 3,
      total: 7,
    })
    expect(imageProgress({})).toEqual({ done: 0, total: 0 })
  })
  it('isWorking while anything is queued or generating', () => {
    expect(isWorking({ ready: 2 })).toBe(false)
    expect(isWorking({ ready: 2, queued: 1 })).toBe(true)
    expect(isWorking({ generating: 1 })).toBe(true)
  })
})

describe('labels', () => {
  it('priceLabel adds the currency only to bare numbers', () => {
    expect(priceLabel('499', '₹')).toBe('₹499')
    expect(priceLabel('$12', '₹')).toBe('$12')
    expect(priceLabel('on request', '₹')).toBe('on request')
    expect(priceLabel(null, '₹')).toBe('')
    expect(priceLabel('1,299.00', '')).toBe('1,299.00')
  })
  it('variantLabel joins size, colour and material', () => {
    expect(variantLabel(variant({ size: 'M', colour: 'Red' }))).toBe('M, Red')
    expect(variantLabel(variant({ sku: 'T-1' }))).toBe('T-1')
    expect(variantLabel(variant())).toBe('Standard')
  })
})

describe('variantLabels', () => {
  it('shows only what differs between variants', () => {
    const vs = [
      variant({ id: 1, size: 'S', colour: 'Red', material: 'Cotton' }),
      variant({ id: 2, size: 'S', colour: 'Navy', material: 'Cotton' }),
      variant({ id: 3, size: 'M', colour: 'Red', material: 'Cotton' }),
    ]
    expect(variantLabels(vs)).toEqual(['S, Red', 'S, Navy', 'M, Red'])
  })
  it('falls back to codes, then numbers, when nothing differs', () => {
    expect(variantLabels([variant({ sku: 'A' }), variant({ sku: 'B' })])).toEqual(['A', 'B'])
    expect(variantLabels([variant(), variant()])).toEqual(['Option 1', 'Option 2'])
  })
})

describe('coversOf', () => {
  it('takes the first finished photo of each of the first products, up to three', () => {
    const covers = coversOf([
      product({ id: 1, variants: [variant({ image_status: 'queued' }), variant({ thumb_url: '/a-thumb', image_url: '/a' })] }),
      product({ id: 2, variants: [variant({ image_status: 'failed', thumb_url: '/x' })] }),
      product({ id: 3, variants: [variant({ image_url: '/b', image_source: 'uploaded' })] }),
      product({ id: 4, variants: [variant({ thumb_url: '/c' })] }),
      product({ id: 5, variants: [variant({ thumb_url: '/d' })] }),
    ])
    expect(covers).toEqual([
      { url: '/a-thumb', generated: true },
      { url: '/b', generated: false },
      { url: '/c', generated: true },
    ])
  })
})
