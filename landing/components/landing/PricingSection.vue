<script setup lang="ts">
import { computed, ref } from 'vue'

interface Period {
  label: string
  months: number
  price: number
  note: string
}

const periods: Period[] = [
  { label: '1 месяц', months: 1, price: 179, note: 'за 1 месяц' },
  { label: '3 месяца', months: 3, price: 499, note: 'за 3 месяца' },
  { label: '6 месяцев', months: 6, price: 949, note: 'за 6 месяцев' },
  { label: '12 месяцев', months: 12, price: 1749, note: 'за 12 месяцев' },
]

const selected = ref(0)

const current = computed(() => periods[selected.value])
const priceNote = computed(() => {
  const period = current.value
  if (period.months === 1) return period.note
  return `${period.note} · ~${Math.round(period.price / period.months)} ₽/мес`
})
</script>

<template>
  <section id="pricing" class="landing-block" aria-labelledby="pricing-title">
    <div class="content-frame">
      <DotField class="dot-field--right" />

      <header class="block-head">
        <h2 id="pricing-title">
          Один тариф<br /><AccentMark>Меняется только срок</AccentMark>
        </h2>
      </header>

      <div class="plan card" data-reveal data-shown>
        <div class="plan-main">
          <p class="plan-name">Proliv Network</p>

          <div class="periods" role="group" aria-label="Срок подписки">
            <button
              v-for="(period, index) in periods"
              :key="period.label"
              type="button"
              class="period-pill"
              :aria-pressed="selected === index"
              @click="selected = index"
            >
              {{ period.label }}
            </button>
          </div>

          <div class="price" aria-live="polite">
            <p class="price-value numeric">{{ current.price }} ₽</p>
            <p class="price-note">{{ priceNote }}</p>
          </div>

          <div class="plan-actions">
            <BaseButton>Подключить Network</BaseButton>
            <BaseButton variant="secondary">Попробовать бесплатно</BaseButton>
          </div>
        </div>

        <div class="plan-side">
          <p class="plan-label">В тарифе</p>
          <ul class="plan-list">
            <li>
              <svg class="plan-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M7 20V4m0 0L4 7m3-3 3 3" />
                <path d="M17 4v16m0 0 3-3m-3 3-3-3" />
              </svg>
              <span><strong class="numeric">1000 ГБ</strong> трафика в месяц</span>
            </li>
            <li>
              <svg class="plan-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <rect x="7" y="2.5" width="10" height="19" rx="2.5" />
                <path d="M10.5 18.5h3" />
              </svg>
              <span><strong class="numeric">5</strong> устройств</span>
            </li>
            <li>
              <svg class="plan-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <path d="M3 12h18" />
                <path d="M12 3c2.5 2.6 3.9 5.7 3.9 9s-1.4 6.4-3.9 9c-2.5-2.6-3.9-5.7-3.9-9s1.4-6.4 3.9-9Z" />
              </svg>
              <span><strong class="numeric">2</strong> локации</span>
            </li>
            <li>
              <svg class="plan-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3Z" />
                <path d="M9.5 12l2 2 3.5-4" />
              </svg>
              <span><strong class="numeric">VLESS Reality</strong></span>
            </li>
          </ul>

          <p class="plan-label">Дополнительно</p>
          <ul class="plan-list plan-list--addons">
            <li>
              <svg class="plan-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v8M8 12h8" />
              </svg>
              <span class="addon-copy">
                <span>Дополнительный трафик</span>
                <small>Покупка от 10 ГБ</small>
              </span>
              <strong class="numeric addon-price">0,50 ₽ за 1 ГБ</strong>
            </li>
            <li>
              <svg class="plan-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v8M8 12h8" />
              </svg>
              <span class="addon-copy">
                <span>Дополнительное устройство</span>
                <small>За устройство</small>
              </span>
              <strong class="numeric addon-price">29 ₽</strong>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.plan {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 32px;
  padding: clamp(24px, 4vw, 44px);
}

.plan-name {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 20px;
  color: var(--accent);
}

.periods {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 22px 0 30px;
}

.period-pill {
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 15px;
  color: var(--muted);
  background: transparent;
  border: 1px solid var(--border);
  transition:
    color 0.18s ease,
    background-color 0.18s ease,
    border-color 0.18s ease;
}

.period-pill:hover {
  color: var(--text);
  border-color: var(--border-strong);
}

.period-pill[aria-pressed='true'] {
  background: var(--accent-soft);
  color: var(--accent);
  border-color: rgba(125, 211, 252, 0.35);
}

.price-value {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(40px, 6vw, 64px);
  line-height: 1.05;
  letter-spacing: -0.01em;
}

.price-note {
  margin-top: 8px;
  color: var(--muted);
}

.plan-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 30px;
}

.plan-side {
  border-left: 1px solid var(--border);
  padding-left: 32px;
}

.plan-label {
  font-size: 13px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 12px;
}

.plan-list + .plan-label {
  margin-top: 22px;
}

.plan-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
}

.plan-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--accent);
}

.addon-copy {
  display: flex;
  flex-direction: column;
}

.addon-copy small {
  color: var(--muted);
  font-size: 13px;
}

.addon-price {
  margin-left: auto;
  white-space: nowrap;
}

@media (max-width: 820px) {
  .plan {
    grid-template-columns: 1fr;
  }

  .plan-side {
    border-left: 0;
    padding-left: 0;
  }
}
</style>
