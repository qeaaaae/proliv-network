const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.goto('http://localhost:3100', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  const info = await page.evaluate(() => {
    const rev = [...document.querySelectorAll('[data-reveal]')];
    const shown = rev.filter((e) => e.hasAttribute('data-shown'));
    const title = document.querySelector('.hero-title, h1');
    const cs = title ? getComputedStyle(title) : null;
    const html = document.documentElement;
    return {
      motion: html.classList.contains('motion'),
      revealAttr: 'reveal' in html.dataset,
      total: rev.length,
      shown: shown.length,
      firstRev: rev.slice(0, 5).map((e) => e.className + ' shown=' + e.hasAttribute('data-shown')),
      titleOpacity: cs?.opacity,
      titleTransform: cs?.transform,
      reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await page.screenshot({ path: '.shots/mob-after.png' });
  await browser.close();
})();
