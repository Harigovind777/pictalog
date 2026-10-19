import { describe, expect, it } from 'vitest'
import { scriptOf, textProps } from './script'

describe('scriptOf', () => {
  it('names the script that needs room: Indian scripts and Urdu', () => {
    expect(scriptOf('Classic Tee')).toBeUndefined()
    expect(scriptOf('बनारसी साड़ी')).toBe('indic')
    expect(scriptOf('Silk பட்டுப் புடவை')).toBe('indic')
    expect(scriptOf('ᱥᱟᱲᱤ')).toBe('indic')
    expect(scriptOf('کشمیری شال')).toBe('arabic')
    expect(scriptOf(null)).toBeUndefined()
  })
})

describe('textProps', () => {
  it('lets the browser pick the direction and marks the script', () => {
    expect(textProps('کشمیری شال')).toEqual({ dir: 'auto', 'data-script': 'arabic' })
    expect(textProps('Tee')).toEqual({ dir: 'auto', 'data-script': undefined })
  })
})
