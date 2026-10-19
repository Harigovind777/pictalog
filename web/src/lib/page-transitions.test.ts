import { describe, expect, it } from 'vitest'
import { slideDirection } from './page-transitions'

describe('slideDirection', () => {
  it('pushes forward into a catalog and its uploads', () => {
    expect(slideDirection('/', '/catalogs/2')).toBe('forward')
    expect(slideDirection('/catalogs/2', '/catalogs/2/imports/7')).toBe('forward')
  })

  it('slides back when going up', () => {
    expect(slideDirection('/catalogs/2', '/')).toBe('back')
    expect(slideDirection('/catalogs/2/imports/7', '/catalogs/2')).toBe('back')
  })

  it('treats a move between screens at the same depth as forward', () => {
    expect(slideDirection('/catalogs/2', '/catalogs/3')).toBe('forward')
  })
})
