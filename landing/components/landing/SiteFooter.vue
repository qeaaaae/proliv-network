<script setup lang="ts">
const documents = [
  { label: 'Политика конфиденциальности', to: '/privacy' },
  { label: 'Обработка персональных данных', to: '/personal-data' },
  { label: 'Публичная оферта', to: '/offer' },
  { label: 'Условия использования', to: '/terms' },
]
</script>

<template>
  <footer class="site-footer">
    <div class="footer-grid">
      <div class="footer-brand">
        <ProlivLogo />
        <p class="footer-tagline">Быстрая приватная сеть для всех устройств</p>
        <ServiceStatus />
      </div>

      <nav class="footer-column" aria-labelledby="footer-docs-title">
        <h2 id="footer-docs-title">Документы</h2>
        <ul class="footer-list">
          <li v-for="doc in documents" :key="doc.to">
            <NuxtLink class="footer-link" :to="doc.to">{{ doc.label }}</NuxtLink>
          </li>
        </ul>
      </nav>

      <nav class="footer-column" aria-labelledby="footer-contact-title">
        <h2 id="footer-contact-title">Связь</h2>
        <ul class="footer-list">
          <li>
            <a
              class="footer-link"
              href="https://t.me/prolivnet_bot"
              target="_blank"
              rel="noopener"
            >Telegram-бот</a>
          </li>
          <li>
            <a
              class="footer-link"
              href="https://t.me/proliv_support"
              target="_blank"
              rel="noopener"
            >Поддержка</a>
          </li>
          <li>
            <span class="footer-text">info@proliv.net</span>
          </li>
        </ul>
      </nav>
    </div>

    <div class="footer-bottom">
      <div class="footer-legal">
        <span>ИП — реквизиты появятся после регистрации</span>
        <span>© 2026 Proliv Network</span>
      </div>
      <ul class="payment-marks" aria-label="Способы оплаты">
        <li><img src="/images/payments/yookassa.svg" alt="ЮKassa" width="92" height="22" loading="lazy"></li>
        <li><img src="/images/payments/heleket.svg" alt="Heleket" width="26" height="26" loading="lazy"></li>
        <li><img src="/images/payments/cryptobot.svg" alt="CryptoBot" width="35" height="19" loading="lazy"></li>
        <li>Карта МИР</li>
      </ul>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  border-top: 1px solid var(--border);
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 32px;
  padding: 40px clamp(24px, 4vw, 48px);
}

.footer-tagline {
  margin-top: 12px;
  color: var(--muted);
  font-size: 14px;
}

.footer-column h2 {
  margin-bottom: 14px;
  color: var(--muted);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.footer-link {
  display: block;
  padding: 6px 0;
  color: var(--text);
  font-size: 15px;
  transition: color 0.18s ease;
}

.footer-link:hover {
  color: var(--accent);
}

.footer-text {
  display: block;
  margin-top: 6px;
  color: var(--muted);
  font-size: 15px;
}

.footer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px clamp(24px, 4vw, 48px) 28px;
  border-top: 1px solid var(--border);
}

.footer-legal {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--muted);
  font-size: 13px;
}

.payment-marks {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.payment-marks li {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 6px 14px;
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  color: var(--muted);
  font-size: 13px;
}

.payment-marks img {
  display: block;
  filter: grayscale(1) brightness(1.6);
  opacity: 0.85;
}

@media (max-width: 720px) {
  .footer-grid {
    grid-template-columns: 1fr;
  }

  .footer-bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
