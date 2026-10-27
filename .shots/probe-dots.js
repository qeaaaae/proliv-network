const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1920, height: 950 } })
  await page.goto('http://localhost:3100/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2500)

  const info = await page.evaluate(() => {
    return [...document.querySelectorAll('.dot-field')].map((el) => {
      const r = el.getBoundingClientRect()
      return {
        cls: el.className, ready: el.classList.contains('is-ready'),
        cssW: getComputedStyle(el).width, cssH: getComputedStyle(el).height,
        rect: { x: r.x, y: r.y, w: r.width, h: r.height },
        canvas: { w: el.width, h: el.height },
      }
    })
  })
  console.log(JSON.stringify(info, null, 2))

  await page.screenshot({ path: '.shots/dots-zoom.png', clip: { x: 0, y: 0, width: 500, height: 950 } })
  await browser.close()
})()
