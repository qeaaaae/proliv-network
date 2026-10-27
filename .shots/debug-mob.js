const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const logs = [];
  page.on('console', (m) => logs.push(m.type() + ': ' + m.text()));
  page.on('pageerror', (e) => logs.push('PAGEERROR: ' + e.message));
  await page.goto('http://localhost:3100', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  const info = await page.evaluate(() => ({
    scrollW: document.documentElement.scrollWidth,
    clientW: document.documentElement.clientWidth,
    innerW: window.innerWidth,
    bodyKids: document.body.innerHTML.length,
    nuxtKids: document.querySelector('#__nuxt')?.children.length,
    firstVisible: [...document.querySelectorAll('section, .frame, .sheet')]
      .slice(0, 8)
      .map((el) => {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return `${el.className.split(' ')[0]} x=${Math.round(r.x)} w=${Math.round(r.width)} h=${Math.round(r.height)} disp=${cs.display}`;
      }),
    bodyText: document.body.innerText.slice(0, 120),
  }));
  console.log(JSON.stringify(info, null, 2));
  console.log('LOGS:', logs.slice(0, 15).join(' | '));
  await browser.close();
})();
