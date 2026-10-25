const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  await page.evaluate(() => window.scrollTo({ top: 750, behavior: 'instant' }))
  await page.waitForTimeout(2200)
  for (let i = 0; i < 8; i++) {
    await page.screenshot({ path: `.shots/w${String(i).padStart(2, '0')}.png`, clip: { x: 720, y: 330, width: 690, height: 300 } })
    await page.waitForTimeout(700)
  }
  await page.goto('http://localhost:8080/status', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  await page.screenshot({ path: '.shots/our-status.png', fullPage: true })
  await browser.close()
})()
