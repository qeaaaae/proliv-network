const { chromium } = require('playwright');

const overview = {
  subscription: {
    plan: '90 дней',
    until: '2027-01-15T00:00:00Z',
    trafficUsedGb: 47.3,
    trafficLimitGb: 200,
    resetAt: '2026-11-01T00:00:00Z',
    devices: [
      { id: 'd1', name: 'iPhone 15', platform: 'ios', hwid: 'a1', lastSeen: '2026-10-20T10:00:00Z' },
      { id: 'd2', name: 'MacBook', platform: 'macos', hwid: 'b2', lastSeen: '2026-10-19T09:00:00Z' },
    ],
    deviceLimit: 3,
    locations: ['uk', 'de', 'ee'],
    subscriptionUrl: 'https://sub.proliv-network.xyz/s/abc123',
  },
  bonusBalance: 120,
  trialDays: 3,
  trialAvailable: false,
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  await page.route('**/api/auth/me', r => r.fulfill({ json: { id: 1, name: 'Рафаэль', username: 'rafael' } }));
  await page.route('**/api/overview', r => r.fulfill({ json: overview }));
  await page.route('**/api/account', r => r.fulfill({ json: {} }));

  await page.goto('https://app.proliv-network.xyz/', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(2200);
  await page.screenshot({ path: 'cab_index_desktop.png', fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(900);
  await page.screenshot({ path: 'cab_index_mobile.png', fullPage: true });

  await browser.close();
  console.log('done');
})();
