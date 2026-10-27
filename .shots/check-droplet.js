const { chromium } = require('playwright')

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)

  const mark = await page.locator('.final-mark')
  await mark.scrollIntoViewIfNeeded()
  // wait past the 2.8s transition + 0.2s delay
  await page.waitForTimeout(3600)

  const info = await page.evaluate(() => {
    const path = document.querySelector('.final-mark path')
    const cs = getComputedStyle(path)
    const len = path.getTotalLength()
    const box = path.getBBox()
    return {
      dasharray: cs.strokeDasharray,
      dashoffset: cs.strokeDashoffset,
      pathLength: path.getAttribute('pathLength'),
      totalLen: len,
      bbox: box,
      shown: document.querySelector('.final-mark').hasAttribute('data-shown'),
      motion: document.documentElement.classList.contains('motion'),
    }
  })
  console.log(JSON.stringify(info, null, 2))

  // capture a sequence during a second pass to see if it redraws
  await page.screenshot({ path: '.shots/droplet-final.png' })

  // also check: sample the path near its start/end to see rendered coverage
  const seam = await page.evaluate(() => {
    const path = document.querySelector('.final-mark path')
    const len = path.getTotalLength()
    const pts = []
    for (const f of [0, 0.005, 0.01, 0.02, 0.5, 0.98, 0.99, 0.995, 1]) {
      const p = path.getPointAtLength(len * f)
      pts.push({ f, x: +p.x.toFixed(2), y: +p.y.toFixed(2) })
    }
    return pts
  })
  console.log(JSON.stringify(seam))
  await browser.close()
})()
