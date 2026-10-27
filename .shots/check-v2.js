const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://localhost:3100', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // routes - big locks
  const routes = await page.locator('.routes-frame, section:has(.route-leader)').last();
  await page.evaluate(() => {
    document.querySelectorAll('.route-leader')[1].scrollIntoView({ block: 'center' });
  });
  await page.waitForTimeout(2300);
  await page.screenshot({ path: '.shots/v2-routes.png' });

  // packet flow zone
  await page.evaluate(() => {
    document.querySelector('.packet-flow').scrollIntoView({ block: 'center' });
  });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: '.shots/v2-flow.png' });

  // bottom of page
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(800);
  await page.screenshot({ path: '.shots/v2-bottom.png' });

  await page.close();

  // mobile 390
  const m = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await m.goto('http://localhost:3100', { waitUntil: 'networkidle' });
  await m.waitForTimeout(1200);
  await m.screenshot({ path: '.shots/v2-mob-hero.png' });
  await m.evaluate(() => document.querySelectorAll('.route-leader')[1].scrollIntoView({ block: 'center' }));
  await m.waitForTimeout(1800);
  await m.screenshot({ path: '.shots/v2-mob-routes.png' });
  await m.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await m.waitForTimeout(800);
  await m.screenshot({ path: '.shots/v2-mob-bottom.png' });
  await m.close();

  // tablet 768
  const t = await browser.newPage({ viewport: { width: 768, height: 1024 } });
  await t.goto('http://localhost:3100', { waitUntil: 'networkidle' });
  await t.waitForTimeout(1200);
  await t.evaluate(() => document.querySelectorAll('.route-leader')[1].scrollIntoView({ block: 'center' }));
  await t.waitForTimeout(1000);
  await t.screenshot({ path: '.shots/v2-tab-routes.png' });
  await t.close();

  await browser.close();
})();
