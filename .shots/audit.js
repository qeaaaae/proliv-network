const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' }).catch(() => {})
  await page.waitForTimeout(1500)
  const h = await page.evaluate(() => document.body.scrollHeight)
  const step = 880
  for (let y = 0; y < h; y += step) {
    await page.evaluate((v) => window.scrollTo({ top: v, behavior: 'instant' }), y)
    await page.waitForTimeout(1400)
    await page.screenshot({ path: `.shots/audit-${String(y).padStart(4, '0')}.png` })
  }
  // mobile pass
  await page.setViewportSize({ width: 390, height: 844 })
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }))
  await page.waitForTimeout(1200)
  await page.screenshot({ path: '.shots/audit-mobile-hero.png' })
  await browser.close()
})()
