// Screenshot one page as the signed-in user from flow.mjs. usage: node e2e/shot.mjs <state.json> <path> <out.png> [width] [full]
import { chromium } from 'playwright'

const BASE = process.env.BASE_URL ?? 'http://localhost:5173'
const [state, route, out, width = '1280', full = 'full'] = process.argv.slice(2)
const browser = await chromium.launch()
const page = await browser.newPage({
  storageState: state,
  viewport: { width: Number(width), height: Number(width) < 600 ? 844 : 900 },
  deviceScaleFactor: Number(width) < 600 ? 2 : 1,
})
await page.goto(BASE + route)
await page.waitForLoadState('networkidle')
await page.waitForTimeout(800)
await page.screenshot({ path: out, fullPage: full === 'full' })
await browser.close()
console.log('saved', out)
