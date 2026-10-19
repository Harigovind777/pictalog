/** The languages Pictalog reads product lists in, each named in its own script: the ones scripts/eval_languages.py
 *  measures. Santali (Ol Chiki) and Manipuri (Meetei Mayek) lists are read from spreadsheets and typed text, but no
 *  model on the Mac reads those scripts from a photo yet. */
export const LANGUAGES: { name: string; native: string; lang: string; photos: boolean }[] = [
  { name: 'English', native: 'English', lang: 'en', photos: true },
  { name: 'Hindi', native: 'हिन्दी', lang: 'hi', photos: true },
  { name: 'Marathi', native: 'मराठी', lang: 'mr', photos: true },
  { name: 'Nepali', native: 'नेपाली', lang: 'ne', photos: true },
  { name: 'Bengali', native: 'বাংলা', lang: 'bn', photos: true },
  { name: 'Assamese', native: 'অসমীয়া', lang: 'as', photos: true },
  { name: 'Punjabi', native: 'ਪੰਜਾਬੀ', lang: 'pa', photos: true },
  { name: 'Gujarati', native: 'ગુજરાતી', lang: 'gu', photos: true },
  { name: 'Odia', native: 'ଓଡ଼ିଆ', lang: 'or', photos: true },
  { name: 'Tamil', native: 'தமிழ்', lang: 'ta', photos: true },
  { name: 'Telugu', native: 'తెలుగు', lang: 'te', photos: true },
  { name: 'Kannada', native: 'ಕನ್ನಡ', lang: 'kn', photos: true },
  { name: 'Malayalam', native: 'മലയാളം', lang: 'ml', photos: true },
  { name: 'Urdu', native: 'اردو', lang: 'ur', photos: true },
  { name: 'Santali', native: 'ᱥᱟᱱᱛᱟᱲᱤ', lang: 'sat', photos: false },
  { name: 'Manipuri', native: 'ꯃꯤꯇꯩꯂꯣꯟ', lang: 'mni', photos: false },
]

const SEEN = 'pictalog:languages-announced'
let announcedThisVisit = false

/** True the first time on this device, so the news that lists can be in India's languages is shown once. */
export function firstLanguagesVisit(storage?: Pick<Storage, 'getItem' | 'setItem'>): boolean {
  try {
    const store = storage ?? window.localStorage
    if (store.getItem(SEEN)) return false
    store.setItem(SEEN, '1')
    return true
  } catch {
    // Private windows and blocked storage can't remember it: once per visit instead.
    const first = !announcedThisVisit
    announcedThisVisit = true
    return first
  }
}
