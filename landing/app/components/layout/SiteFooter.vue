<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { supportEmail, supportUrl, telegramBotUrl } from '~/data/product'
import { legalDocuments } from '~/data/legal'
import { brandLogoUrl, paymentMarks } from '~/data/assets'
import BaseButton from '~/components/ui/BaseButton.vue'
import NavigationButton from '~/components/ui/NavigationButton.vue'
import ServiceStatus from '~/components/layout/ServiceStatus.vue'

const { t } = useI18n()
const year = new Date().getFullYear()
</script>

<template>
  <div class="site-closing">
    <div class="content-frame">
      <slot />
      <footer class="site-footer">
        <div class="footer-grid">
          <div class="footer-brand">
            <NavigationButton class="footer-logo" target="/" :aria-label="t('brand.name')">
              <img :src="brandLogoUrl" alt="" width="70" height="28">
            </NavigationButton>
            <p>{{ t('footer.description') }}</p>
            <ServiceStatus />
          </div>

          <div class="footer-column">
            <h2>{{ t('footer.legalLabel') }}</h2>
            <BaseButton
              v-for="document in Object.values(legalDocuments)"
              :key="document.id"
              class="footer-link"
              :href="`/${document.id}`"
              variant="secondary"
              size="small"
              trail="arrow-up-right"
            >
              {{ document.label }}
            </BaseButton>
          </div>

          <div class="footer-column">
            <h2>{{ t('footer.contactsLabel') }}</h2>
            <BaseButton class="footer-link" :href="telegramBotUrl" variant="telegram" size="small" trail="plane">{{ t('footer.links.bot') }}</BaseButton>
            <BaseButton class="footer-link" :href="supportUrl" variant="secondary" size="small" trail="arrow-up-right">{{ t('footer.links.support') }}</BaseButton>
            <a class="footer-mail" :href="`mailto:${supportEmail}`">{{ supportEmail }}</a>
          </div>
        </div>

        <div class="footer-bottom">
          <div class="footer-legal">
            <span>© {{ year }} {{ t('brand.name') }}</span>
          </div>
          <ul class="payment-marks" :aria-label="t('footer.paymentsLabel')">
            <li v-for="mark in paymentMarks" :key="mark.id">
              <img :src="mark.src" :alt="mark.alt" :width="mark.width" :height="mark.height" loading="lazy">
            </li>
          </ul>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.site-closing {
  padding-block: clamp(64px, 8vw, 104px) 24px;
}

.site-footer {
  margin-top: clamp(40px, 5vw, 64px);
  border-top: 1px solid var(--line);
}

.footer-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) minmax(0, 1fr);
  gap: clamp(28px, 4vw, 56px);
  padding-block: clamp(32px, 4vw, 48px);
}

.footer-brand {
  display: grid;
  align-content: start;
  justify-items: start;
  gap: 16px;
}

.footer-logo img {
  display: block;
  width: auto;
  height: 28px;
}

.footer-brand p {
  max-width: 32ch;
  color: var(--fg-secondary);
  font-size: 14px;
}

.footer-column {
  display: grid;
  align-content: start;
  gap: 8px;
}

.footer-column h2 {
  margin-bottom: 6px;
  color: var(--fg-secondary);
  font-family: var(--font-text);
  font-size: 14px;
  font-weight: 650;
}

.footer-link {
  justify-content: space-between;
  width: 100%;
}

.footer-mail {
  padding: 8px 2px 0;
  color: var(--fg-tertiary);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}

.footer-bottom {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 24px;
  padding-top: 20px;
  color: var(--fg-tertiary);
  font-size: 13px;
  border-top: 1px dashed var(--line-strong);
}

.footer-legal {
  display: grid;
  gap: 4px;
}

.payment-marks {
  display: flex;
  align-items: center;
  gap: 20px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.payment-marks img {
  display: block;
  opacity: .6;
  transition: opacity 200ms var(--ease);
}

.payment-marks img:hover {
  opacity: 1;
}

@media (max-width: 860px) {
  .footer-grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }

  .footer-brand {
    grid-column: 1 / -1;
  }
}

@media (max-width: 600px) {
  .footer-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .footer-bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
