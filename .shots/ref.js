const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('https://ranteis.eu/', { waitUntil: 'networkidle' }).catch(() => {})
  await page.waitForTimeout(2500)
  const h = await page.evaluate(() => document.body.scrollHeight)
  const step = 880
  for (let y = 0; y < Math.min(h, 6000); y += step) {
    await page.evaluate((v) => window.scrollTo({ top: v, behavior: 'instant' }), y)
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `.shots/ref-${String(y).padStart(4, '0')}.png` })
  }
  await browser.close()
})()
