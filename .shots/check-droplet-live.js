const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://localhost:3100/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  await page.locator('.final-cta').scrollIntoViewIfNeeded()
  await page.waitForTimeout(4200)
  const el = await page.locator('.final-mark')
  await el.screenshot({ path: '.shots/droplet-live.png' })
  const st = await page.evaluate(() => {
    const p = document.querySelector('.final-mark path')
    const cs = getComputedStyle(p)
    return {
      dasharray: cs.strokeDasharray, dashoffset: cs.strokeDashoffset,
      anim: cs.animationName, shown: document.querySelector('.final-mark').hasAttribute('data-shown'),
    }
  })
  console.log(JSON.stringify(st))
  await browser.close()
})()
