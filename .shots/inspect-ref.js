const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('https://ranteis.eu/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  const info = await page.evaluate(() => {
    return [...document.querySelectorAll('.dot-field')].map((el) => {
      const cs = getComputedStyle(el)
      const r = el.getBoundingClientRect()
      const parent = el.parentElement
      const pr = parent.getBoundingClientRect()
      return {
        cls: el.className,
        position: cs.position,
        left: cs.left, right: cs.right, top: cs.top, bottom: cs.bottom,
        width: cs.width, height: cs.height, zIndex: cs.zIndex, opacity: cs.opacity,
        rect: { x: r.x, y: r.y, w: r.width, h: r.height },
        parentClass: parent.className,
        parentRect: { x: pr.x, y: pr.y, w: pr.width, h: pr.height },
        canvasW: el.width, canvasH: el.height,
      }
    })
  })
  console.log(JSON.stringify(info, null, 2))
  // also check what the section looks like: does the canvas overlap the sheet?
  await browser.close()
})()
