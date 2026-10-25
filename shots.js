const { chromium } = require('playwright')

const targets = [
  { name: 'ranteis', url: 'https://ranteis.eu/' },
  { name: 'proliv', url: 'http://localhost:8080/' },
]

const scrolls = [0, 700, 1500, 2400, 3400, 4600]

;(async () => {
  const browser = await chromium.launch()
  for (const t of targets) {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
    await page.goto(t.url, { waitUntil: 'networkidle' }).catch(() => {})
    await page.waitForTimeout(1800)
    for (const y of scrolls) {
      await page.evaluate((v) => window.scrollTo({ top: v, behavior: 'instant' }), y)
      await page.waitForTimeout(900)
      await page.screenshot({ path: `.shots/${t.name}-${y}.png` })
    }
    await page.close()
  }
  await browser.close()
})()
