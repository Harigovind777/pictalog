// Upload a file into an existing catalog as the signed-in user, screenshot the check screen, then apply.
// usage: node e2e/upload.mjs <state.json> <catalogId> <file> <out-prefix> [apply=yes|no]
import { chromium } from 'playwright'
import path from 'node:path'

const BASE = process.env.BASE_URL ?? 'http://localhost:5173'
const [state, catalogId, file, prefix, apply = 'yes'] = process.argv.slice(2)
const browser = await chromium.launch()
const page = await browser.newPage({ storageState: state, viewport: { width: 1280, height: 900 } })
await page.goto(`${BASE}/catalogs/${catalogId}`)
await page.locator('input[type=file][accept*=".xlsx"]').first().setInputFiles(path.resolve(file))
await page.getByRole('heading', { name: /Check what we found|Reading|couldn't read/ }).waitFor({ timeout: 60_000 })
if (await page.getByRole('heading', { name: /Reading/ }).isVisible()) {
  await page.getByRole('heading', { name: /Check what we found|couldn't read/ }).waitFor({ timeout: 600_000 })
}
await page.waitForTimeout(600)
await page.screenshot({ path: `${prefix}-check.png`, fullPage: true })
console.log('saved check')
if (apply === 'yes' && (await page.getByRole('button', { name: 'Update catalog' }).isVisible())) {
  await page.getByRole('button', { name: 'Update catalog' }).click()
  await page.getByText('Catalog updated').waitFor()
  await page.waitForTimeout(800)
  await page.screenshot({ path: `${prefix}-catalog.png`, fullPage: true })
  console.log('saved catalog')
}
await browser.close()
