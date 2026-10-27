const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const m = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await m.goto('http://localhost:3100', { waitUntil: 'networkidle' });
  await m.waitForTimeout(1600);
  await m.screenshot({ path: '.shots/m-hero.png' });
  await m.evaluate(() => document.querySelector('.locations-frame, section')?.scrollIntoView());
  await m.evaluate(() => window.scrollBy(0, 500));
  await m.waitForTimeout(1400);
  await m.screenshot({ path: '.shots/m-mid.png' });
  await m.evaluate(() => document.querySelectorAll('.route-leader')[1].scrollIntoView({ block: 'center' }));
  await m.waitForTimeout(1600);
  await m.screenshot({ path: '.shots/m-routes.png' });
  await m.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await m.waitForTimeout(1400);
  await m.screenshot({ path: '.shots/m-bottom.png' });
  const horiz = await m.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  console.log('horiz overflow:', horiz);
  await browser.close();
})();
