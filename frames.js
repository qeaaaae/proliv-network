const { chromium } = require('playwright')

// verify reveal survives SPA navigation back + capture current look
;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  // go to a doc page and back
  await page.goto('http://localhost:8080/privacy', { waitUntil: 'networkidle' })
  await page.waitForTimeout(800)
  await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  const hidden = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[data-reveal]')]
    const vis = els.filter((el) => getComputedStyle(el).opacity !== '0')
    return { total: els.length, shown: els.filter((e) => e.hasAttribute('data-shown')).length, visible: vis.length }
  })
  console.log('reveal stats:', JSON.stringify(hidden))
  await page.screenshot({ path: '.shots/back-0.png' })
  await page.evaluate(() => window.scrollTo({ top: 750, behavior: 'instant' }))
  await page.waitForTimeout(2000)
  await page.screenshot({ path: '.shots/back-750.png' })
  await page.evaluate(() => window.scrollTo({ top: 4600, behavior: 'instant' }))
  await page.waitForTimeout(1200)
  await page.screenshot({ path: '.shots/back-4600.png' })
  await browser.close()
})()
