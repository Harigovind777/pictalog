// Walks the main flow in a real browser and saves screenshots. Verification tooling, not part of the app.
// usage: node e2e/flow.mjs <out-dir> [sample-file] [width]
import { chromium } from 'playwright'
import path from 'node:path'

const BASE = process.env.BASE_URL ?? 'http://localhost:5173'
const [outDir = '/tmp/pictalog-shots', sample = '../samples/apparel.xlsx', width = '1280'] = process.argv.slice(2)
const email = `owner+${Date.now()}@example.com`

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: Number(width), height: 900 } })
const shot = async (name) => {
  await page.waitForTimeout(600)
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: true })
  console.log('saved', name)
}

await page.goto(`${BASE}/signup`)
await shot('01-signup')
await page.getByLabel('Company name').fill('Kerala Weaves')
await page.getByLabel('Email').fill(email)
await page.getByLabel('Password').fill('password123')
await page.getByRole('button', { name: 'Create account' }).click()
await page.getByRole('heading', { name: 'Catalogs' }).waitFor()
await shot('02-catalogs-empty')

await page.getByRole('button', { name: 'New catalog' }).first().click()
await page.getByLabel('Name').fill('Spring 2026')
await page.getByRole('button', { name: 'Create catalog' }).click()
await page.getByRole('heading', { name: 'Add your products' }).waitFor()
await shot('03-catalog-empty')

await page.locator('input[type=file][accept*=".xlsx"]').first().setInputFiles(path.resolve(sample))
await page.getByRole('heading', { name: /Check what we found|Reading/ }).waitFor({ timeout: 60_000 })
await shot('04-check')

const update = page.getByRole('button', { name: 'Update catalog' })
if (await update.isVisible()) {
  await update.click()
  await page.getByText('Catalog updated').waitFor()
  await shot('05-catalog-making-images')
}

await page.context().storageState({ path: path.join(outDir, 'state.json') })
console.log('catalog url', page.url())
await browser.close()
