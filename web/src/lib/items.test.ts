import { describe, expect, it } from 'vitest'
import { emptyItem, hasEnoughDetail, removeItem, updateItem } from './items'

const items = [
  { ...emptyItem(), name: 'Tee', size: 'S' },
  { ...emptyItem(), name: 'Mug' },
]

describe('updateItem', () => {
  it('updateItem does not mutate', () => {
    const next = updateItem(items, 0, 'colour', 'Red')
    expect(next[0].colour).toBe('Red')
    expect(items[0].colour).toBeNull()
    expect(next[1]).toBe(items[1])
  })
  it('turns blank text into null', () => {
    expect(updateItem(items, 0, 'size', '  ')[0].size).toBeNull()
  })
})

describe('removeItem', () => {
  it('removeItem removes only that row', () => {
    expect(removeItem(items, 0).map((i) => i.name)).toEqual(['Mug'])
    expect(items).toHaveLength(2)
  })
})

describe('hasEnoughDetail', () => {
  it('matches the server rule', () => {
    expect(hasEnoughDetail({ ...emptyItem(), name: 'Cotton T-Shirt' })).toBe(true)
    expect(hasEnoughDetail({ ...emptyItem(), name: 'SKU-10023' })).toBe(false)
    expect(hasEnoughDetail({ ...emptyItem(), description: 'Blue ceramic mug' })).toBe(true)
    expect(hasEnoughDetail({ ...emptyItem(), name: 'MUG', sku: 'mug' })).toBe(false)
    expect(hasEnoughDetail(emptyItem())).toBe(false)
  })
})
