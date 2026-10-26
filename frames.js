const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  // mobile viewport like the user's screenshot
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
  await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1800)
  for (const y of [0, 800, 1600, 2600, 3600, 4600]) {
    await page.evaluate((v) => window.scrollTo({ top: v, behavior: 'instant' }), y)
    await page.waitForTimeout(700)
    await page.screenshot({ path: `.shots/m-${y}.png` })
  }
  await browser.close()
})()
