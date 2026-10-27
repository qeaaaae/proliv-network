<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { pricingPlans } from '~/data/product'

const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string
import AccentMark from '~/components/ui/AccentMark.vue'
import BaseButton from '~/components/ui/BaseButton.vue'

const { t } = useI18n()
const priceFormatter = new Intl.NumberFormat('ru-RU')
const monthly = pricingPlans.find(plan => plan.months === 1)!

const periods = computed(() => pricingPlans.map((plan) => {
  const url = new URL('/purchases', cabinetUrl)
  url.searchParams.set('duration', String(plan.durationDays))
  const saving = Math.round((1 - plan.priceRub / (monthly.priceRub * plan.months)) * 100)
  return {
    id: plan.id,
    label: t(plan.labelKey),
    price: priceFormatter.format(plan.priceRub),
    note: plan.months === 1
      ? t('pricing.priceFor', { period: t(plan.labelKey) })
      : t('pricing.average', { price: priceFormatter.format(Math.round(plan.priceRub / plan.months)) }),
    saving: saving > 0 ? t('pricing.saving', { percent: saving }) : '',
    url: url.href
  }
}))

const included = computed(() => [
  { value: t('pricing.included.trafficValue'), label: t('pricing.included.trafficLabel') },
  { value: t('pricing.included.devicesValue'), label: t('pricing.included.devicesLabel') },
  { value: t('pricing.included.locationsValue'), label: t('pricing.included.locationsLabel') },
  { value: t('pricing.included.lteValue'), label: t('pricing.included.lteLabel') }
])

const addons = computed(() => [
  { title: t('pricing.addons.trafficTitle'), note: t('pricing.addons.trafficNote'), price: t('pricing.addons.trafficPrice') },
  { title: t('pricing.addons.deviceTitle'), note: t('pricing.addons.deviceNote'), price: t('pricing.addons.devicePrice') }
])
</script>

<template>
  <section id="pricing" class="landing-block" aria-labelledby="pricing-title">
    <div class="content-frame">
      <header class="split-head" v-reveal>
        <h2 id="pricing-title" class="two-tone">
          <span>{{ t('pricing.titleBefore') }}</span>
          <span><AccentMark>{{ t('pricing.titleAccent') }}</AccentMark></span>
        </h2>
      </header>

      <ul class="periods" :style="{ '--count': periods.length }">
        <li
          v-for="(period, index) in periods"
          :key="period.id"
          class="period card"
          :style="{ '--index': index, '--delay': `${index * .07}s` }"
          v-reveal
        >
          <svg class="period-art" viewBox="0 0 1600 500" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
            <path class="art-cloud" d="M214 150a20 20 0 0 1 38-10 24 24 0 0 1 44 6 16 16 0 0 1 3 32h-80a17 17 0 0 1-5-28ZM1004 152a16 16 0 0 1 30-8 19 19 0 0 1 35 5 13 13 0 0 1 2 25h-63a14 14 0 0 1-4-22Z" />
            <path class="art-trail" d="M-40 262C400 262 800 240 1100 210S1340 180 1400 176" />
            <circle class="art-stop" cx="200" cy="259.8" r="6" />
            <circle class="art-stop" cx="600" cy="246.4" r="6" />
            <circle class="art-stop" cx="1000" cy="219.4" r="6" />
            <g class="art-plane">
              <g transform="translate(1478 186) rotate(-10) scale(.62)">
                <path class="art-speed" d="M-150 -6H-110M-170 20H-120M-140 44H-104" />
                <path class="art-wing" d="M118-72-96-6-22 14ZM118-72-22 14-8 76Z" />
                <path d="M-22 14-42 44-8 76" />
              </g>
            </g>
          </svg>

          <div class="period-head">
            <h3>{{ period.label }}</h3>
            <span v-if="period.saving" class="period-saving plate">{{ period.saving }}</span>
          </div>
          <p class="period-price numeric">{{ period.price }}<span>₽</span></p>
          <p class="period-note">{{ period.note }}</p>
          <BaseButton class="period-action" :href="period.url" variant="secondary" size="small">{{ t('actions.chooseInCabinet') }}</BaseButton>
        </li>
      </ul>

      <div class="tariff card" v-reveal style="--delay: .1s">
        <ul class="tariff-figures">
          <li v-for="item in included" :key="item.label">
            <strong class="numeric">{{ item.value }}</strong>
            <span>{{ item.label }}</span>
          </li>
        </ul>
        <div class="tariff-extra">
          <ul class="tariff-addons">
            <li v-for="addon in addons" :key="addon.title">
              <span>{{ addon.title }}<small>{{ addon.note }}</small></span>
              <strong class="numeric">{{ addon.price }}</strong>
            </li>
          </ul>
          <BaseButton :href="cabinetUrl">{{ t('actions.startTrial') }}</BaseButton>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.periods {
  --gap: 12px;

  display: grid;
  grid-template-columns: repeat(var(--count), minmax(0, 1fr));
  gap: var(--gap);
  margin: 0 0 var(--gap);
  padding: 0;
  list-style: none;
}

.period {
  display: grid;
  grid-template-rows: auto 1fr auto auto;
  gap: 10px;
  min-height: 400px;
  padding: 22px;
}

.period-art {
  position: absolute;
  z-index: -1;
  top: 0;
  left: calc(var(--index) * -1 * (100% + var(--gap)));
  width: calc(var(--count) * 100% + (var(--count) - 1) * var(--gap));
  max-width: none;
  height: 100%;
  opacity: .5;
  fill: none;
  stroke: rgb(255 255 255 / 55%);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: opacity 420ms var(--ease);
}

.art-cloud {
  opacity: .45;
}

.art-trail {
  stroke: var(--plate);
  stroke-dasharray: 8 12;
  animation: art-trail 1.6s linear infinite;
}

.art-stop {
  fill: var(--bg);
  stroke: var(--plate);
  stroke-width: 2;
}

.art-plane {
  animation: art-plane 4.2s var(--ease) infinite;
}

.art-wing {
  fill: rgb(125 211 252 / 8%);
  stroke: var(--plate);
}

.art-speed {
  stroke-dasharray: 4 8;
  opacity: .7;
}

.period-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.period-head h3 {
  font-size: 18px;
  letter-spacing: -.03em;
}

.period-saving {
  padding: 5px 10px 6px;
  font-size: 12px;
  font-weight: 800;
  border-radius: var(--radius-pill);
}

.period-price {
  display: flex;
  align-items: flex-start;
  align-self: end;
  gap: .08em;
  font-family: var(--font-display);
  font-size: clamp(40px, 4.2vw, 62px);
  font-weight: 800;
  line-height: .95;
  letter-spacing: -.05em;
}

.period-price span {
  margin-top: .1em;
  font-size: .4em;
  letter-spacing: 0;
}

.period-note {
  min-height: 2.6em;
  color: var(--fg-secondary);
  font-size: 14px;
  font-weight: 600;
}

.period-action {
  justify-self: start;
  background-color: rgb(10 12 14 / 60%);
}

.tariff {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
}

.tariff-figures {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0;
  padding: 0;
  list-style: none;
}

.tariff-figures li {
  display: grid;
  align-content: center;
  gap: 6px;
  padding: 22px 20px;
}

.tariff-figures li + li {
  border-left: 1px dashed var(--line-strong);
}

.tariff-figures strong {
  font-family: var(--font-display);
  font-size: clamp(22px, 2.2vw, 32px);
  font-weight: 800;
  letter-spacing: -.04em;
  white-space: nowrap;
}

.tariff-figures span {
  color: var(--fg-secondary);
  font-size: 13px;
  font-weight: 600;
}

.tariff-extra {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 22px;
  border-left: 1px solid var(--line);
}

.tariff-addons {
  display: grid;
  flex: 1;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.tariff-addons li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.tariff-addons li + li {
  padding-top: 8px;
  border-top: 1px dashed var(--line-strong);
}

.tariff-addons span {
  display: grid;
  font-size: 14px;
  font-weight: 650;
}

.tariff-addons small {
  color: var(--fg-tertiary);
  font-size: 12px;
  font-weight: 550;
}

.tariff-addons strong {
  font-size: 14px;
  font-weight: 800;
  white-space: nowrap;
}

@keyframes art-trail {
  to { stroke-dashoffset: -40; }
}

@keyframes art-plane {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-10px, 12px); }
}

@media (hover: hover) and (pointer: fine) {
  .period:hover {
    border-color: var(--line-dash);
  }

  .period:hover .period-art {
    opacity: 1;
  }
}

@media (max-width: 1080px) {
  .tariff {
    grid-template-columns: minmax(0, 1fr);
  }

  .tariff-extra {
    border-top: 1px solid var(--line);
    border-left: 0;
  }
}

@media (max-width: 900px) {
  .periods {
    grid-template-columns: none;
    grid-auto-columns: minmax(250px, 78%);
    grid-auto-flow: column;
    margin-inline: calc(var(--content-gutter) * -1);
    padding-inline: var(--content-gutter);
    overflow-x: auto;
    scroll-padding-inline: var(--content-gutter);
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
  }

  .period {
    scroll-snap-align: start;
  }

  .tariff-figures {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .tariff-figures li:nth-child(3) {
    border-left: 0;
  }

  .tariff-figures li:nth-child(n + 3) {
    border-top: 1px dashed var(--line-strong);
  }
}

@media (max-width: 560px) {
  .tariff-extra {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
