const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const out = 'D:\\Temp\\shots';
  require('fs').mkdirSync(out, { recursive: true });

  const targets = [
    { url: 'https://proliv-network.xyz/', name: 'landing-mobile', w: 390, h: 844 },
    { url: 'https://proliv-network.xyz/', name: 'landing-small', w: 360, h: 740 },
    { url: 'https://app.proliv-network.xyz/auth', name: 'auth-mobile', w: 390, h: 844 },
  ];

  for (const t of targets) {
    const page = await browser.newPage({ viewport: { width: t.w, height: t.h } });
    try {
      await page.goto(t.url, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(1500);
      await page.screenshot({ path: `${out}\\${t.name}-full.png`, fullPage: true });
      await page.screenshot({ path: `${out}\\${t.name}-view.png`, fullPage: false });
      // horizontal overflow check
      const overflow = await page.evaluate(() => ({
        docWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
        offenders: [...document.querySelectorAll('*')].filter(el => el.scrollWidth > window.innerWidth + 2).slice(0, 8).map(el => el.tagName + '.' + (el.className?.baseVal || el.className || ''))
      }));
      console.log(t.name, JSON.stringify(overflow));
      await page.close();
    } catch (e) {
      console.log(t.name, 'ERR', e.message);
    }
  }
  await browser.close();
})();
