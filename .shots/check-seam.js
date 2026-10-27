const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 4 })
  await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1200)

  const mark = page.locator('.final-mark')
  await mark.scrollIntoViewIfNeeded()
  await page.waitForTimeout(3600)

  // clip = tight box around bottom tip of the droplet (svg viewBox -2..34, mark ~centered)
  const box = await mark.boundingBox()
  // path coords: viewBox -2..34, tip at (16,33) -> fraction (18/36, 35/36)
  const clip = {
    x: box.x + box.width * (14 / 36),
    y: box.y + box.height * (32.2 / 36),
    width: box.width * (8 / 36),
    height: box.height * (3.4 / 36),
  }
  await page.screenshot({ path: '.shots/seam-dashed.png', clip })

  // kill the dash entirely -> pure geometry
  await page.evaluate(() => {
    document.querySelector('.final-mark path').style.strokeDasharray = 'none'
  })
  await page.waitForTimeout(300)
  await page.screenshot({ path: '.shots/seam-solid.png', clip })
  await browser.close()
})()
