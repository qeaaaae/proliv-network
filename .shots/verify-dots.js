const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  for (const vw of [1920, 1440]) {
    const page = await browser.newPage({ viewport: { width: vw, height: 950 } })
    await page.goto('http://localhost:3100/', { waitUntil: 'networkidle' })
    await page.waitForTimeout(2200)
    const h = await page.evaluate(() => document.body.scrollHeight)
    for (const y of [0, Math.min(1000, h - 900)]) {
      await page.evaluate((v) => window.scrollTo({ top: v, behavior: 'instant' }), y)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `.shots/dots-${vw}-${y}.png` })
    }
    await page.close()
  }
  await browser.close()
})()
