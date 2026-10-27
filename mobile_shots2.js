const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const out = 'D:\\Temp\\shots';
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.goto('https://proliv-network.xyz/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(1200);

  const total = await page.evaluate(() => document.documentElement.scrollHeight);
  const steps = Math.ceil(total / 700);
  for (let i = 0; i <= steps; i++) {
    await page.evaluate(y => window.scrollTo({ top: y, behavior: 'instant' }), i * 700);
    await page.waitForTimeout(450);
    await page.screenshot({ path: `${out}\\m-${String(i).padStart(2, '0')}.png` });
  }
  console.log('shots:', steps + 1, 'totalH:', total);
  await browser.close();
})();
