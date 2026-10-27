const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://localhost:3100/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1200)
  const routes = page.locator('.routes')
  await routes.scrollIntoViewIfNeeded()
  await page.waitForTimeout(2500)
  // catch the packet at several phases: mid-flight, inside lock, post-encrypt
  for (const [name, delay] of [['a', 0], ['b', 700], ['c', 1400]]) {
    await page.screenshot({ path: `.shots/pkt-${name}.png`, clip: { x: 300, y: 100, width: 1140, height: 640 } })
    await page.waitForTimeout(delay)
  }
  await browser.close()
})()
