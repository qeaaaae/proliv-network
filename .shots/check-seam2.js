const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 4 })
  await page.goto('http://localhost:3100/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  const mark = page.locator('.final-mark')
  await mark.scrollIntoViewIfNeeded()
  await page.waitForTimeout(3800)
  const box = await mark.boundingBox()
  const clip = {
    x: box.x + box.width * (14 / 36),
    y: box.y + box.height * (32.2 / 36),
    width: box.width * (8 / 36),
    height: box.height * (3.4 / 36),
  }
  await page.screenshot({ path: '.shots/seam-fixed.png', clip })
  const st = await page.evaluate(() => {
    const p = document.querySelector('.final-mark path')
    const cs = getComputedStyle(p)
    return { dasharray: cs.strokeDasharray, dashoffset: cs.strokeDashoffset }
  })
  console.log(JSON.stringify(st))
  await browser.close()
})()
