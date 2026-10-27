const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('https://proliv-network.xyz/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'D:\\Temp\\shots\\drop-desktop.png' });
  const el = await page.$('.hero-visual');
  if (el) await el.screenshot({ path: 'D:\\Temp\\shots\\drop-zoom.png' });
  await browser.close();
})();
