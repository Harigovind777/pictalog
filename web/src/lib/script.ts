/** Scripts that need room: Indian scripts carry vowel signs above and below their letters, and Urdu letters join. */
export type Script = 'indic' | 'arabic'

const INDIC = /[ऀ-෿᱐-᱿᳐-᳿꣠-ꣿꫠ-꫿ꯀ-꯿]/
const ARABIC = /[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]/

export function scriptOf(text: string | null | undefined): Script | undefined {
  if (!text) return undefined
  if (ARABIC.test(text)) return 'arabic'
  if (INDIC.test(text)) return 'indic'
  return undefined
}

/** For an element showing a catalog's own words: Urdu reads right to left, and index.css loosens the tight
 *  headline spacing for scripts that need it. */
export function textProps(text: string | null | undefined): { dir: 'auto'; 'data-script': Script | undefined } {
  return { dir: 'auto', 'data-script': scriptOf(text) }
}
