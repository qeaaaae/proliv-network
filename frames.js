const { chromium } = require('playwright')

// time-lapse of OUR locations section to verify wheel rotation + rain
;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' }).catch(() => {})
  await page.waitForTimeout(1500)
  await page.evaluate(() => window.scrollTo({ top: 750, behavior: 'instant' }))
  await page.waitForTimeout(2200)
  for (let i = 0; i < 8; i++) {
    await page.screenshot({ path: `.shots/p${String(i).padStart(2, '0')}.png` })
    await page.waitForTimeout(500)
  }
  await browser.close()
})()
