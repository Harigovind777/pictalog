import { describe, expect, it } from 'vitest'
import { PAPERS, paperFor } from './paper'

describe('paperFor', () => {
  it('gives a catalog the same backdrop every time', () => {
    expect(paperFor(7)).toBe(paperFor(7))
  })

  it('gives neighbouring catalogs different backdrops', () => {
    const papers = [1, 2, 3, 4, 5, 6].map(paperFor)
    expect(new Set(papers).size).toBe(PAPERS.length)
  })
})
