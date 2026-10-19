import { describe, expect, it } from 'vitest'
import { firstLanguagesVisit, LANGUAGES } from './languages'
import { scriptOf } from './script'

function memoryStorage() {
  const items = new Map<string, string>()
  return { getItem: (k: string) => items.get(k) ?? null, setItem: (k: string, v: string) => void items.set(k, v) }
}

describe('LANGUAGES', () => {
  it('are the ones scripts/eval_languages.py measures, each named in its own script', () => {
    expect(LANGUAGES.map((l) => l.lang)).toEqual([
      'en', 'hi', 'mr', 'ne', 'bn', 'as', 'pa', 'gu', 'or', 'ta', 'te', 'kn', 'ml', 'ur', 'sat', 'mni',
    ])
    for (const l of LANGUAGES.slice(1)) expect(scriptOf(l.native), l.name).toBeDefined()
    expect(LANGUAGES.filter((l) => !l.photos).map((l) => l.name)).toEqual(['Santali', 'Manipuri'])
  })
})

describe('firstLanguagesVisit', () => {
  it('is true once on a device', () => {
    const storage = memoryStorage()
    expect(firstLanguagesVisit(storage)).toBe(true)
    expect(firstLanguagesVisit(storage)).toBe(false)
  })

  it('is true once per visit where storage is blocked', () => {
    const blocked = {
      getItem: () => {
        throw new Error('SecurityError')
      },
      setItem: () => {},
    }
    expect(firstLanguagesVisit(blocked)).toBe(true)
    expect(firstLanguagesVisit(blocked)).toBe(false)
  })
})
