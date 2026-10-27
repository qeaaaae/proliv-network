const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('https://app.proliv-network.xyz/auth', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(1800);
  await page.screenshot({ path: 'cab_auth_desktop.png' });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'cab_auth_mobile.png' });

  await browser.close();
  console.log('done');
})();
