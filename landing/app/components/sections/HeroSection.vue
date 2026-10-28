<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { pricingPlans } from '~/data/product'

const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string
import BaseButton from '~/components/ui/BaseButton.vue'
import GlassMark from '~/components/ui/GlassMark.vue'

const { t } = useI18n()

const titleWords = computed(() => {
  const [first = '', ...rest] = t('hero.titleBefore').split(' ')
  return { first, rest: rest.join(' ') }
})

const monthly = pricingPlans.find(plan => plan.months === 1)!

const facts = computed(() => [
  { value: `${monthly.priceRub} ₽`, label: t('hero.facts.priceLabel') },
  { value: t('hero.facts.trialValue'), label: t('hero.facts.trialLabel') },
  { value: t('hero.facts.trafficValue'), label: t('hero.facts.trafficLabel') },
  { value: t('hero.facts.countriesValue'), label: t('hero.facts.countriesLabel') }
])

const active = ref(0)
let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  timer = setInterval(() => {
    active.value = (active.value + 1) % facts.value.length
  }, 2600)
})

onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <section class="hero" aria-labelledby="hero-title">
    <div class="content-frame hero-grid">
      <div class="hero-visual" v-reveal:fade>
        <GlassMark />
      </div>

      <div class="hero-copy">
        <h1 id="hero-title" class="hero-title">
          <span class="hero-line" v-reveal><span class="plate hero-plate">{{ titleWords.first }}</span></span>
          <span class="hero-line hero-line--muted" v-reveal style="--delay: .08s">{{ titleWords.rest }}</span>
          <span class="hero-line" v-reveal style="--delay: .16s"><span class="plate hero-plate">{{ t('hero.titleAccent') }}</span></span>
        </h1>
        <p class="hero-lead" v-reveal style="--delay: .24s">{{ t('hero.description') }}</p>
        <div class="hero-actions" v-reveal style="--delay: .32s">
          <BaseButton :href="cabinetUrl">{{ t('actions.startTrial') }}</BaseButton>
          <BaseButton href="#pricing" variant="secondary" trail="arrow-down">{{ t('actions.viewPricing') }}</BaseButton>
        </div>
      </div>
    </div>

    <div class="content-frame">
      <div class="facts-board" v-reveal style="--delay: .4s">
        <ul class="facts">
          <li
            v-for="(fact, index) in facts"
            :key="fact.label"
            class="fact"
            :class="{ 'is-active': active === index }"
          >
            <span class="fact-value numeric">
              <span class="fact-plate" aria-hidden="true" />
              <span class="fact-number">{{ fact.value }}</span>
            </span>
            <span class="fact-label">{{ fact.label }}</span>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  display: grid;
  align-content: center;
  gap: clamp(28px, 4vh, 48px);
  min-height: calc(100svh - var(--header-height));
  padding-block: clamp(12px, 2vh, 28px) clamp(28px, 4vh, 44px);
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, .92fr) minmax(0, 1fr);
  align-items: center;
  gap: clamp(24px, 4vw, 64px);
}

.hero-visual {
  position: relative;
  max-width: 600px;
  justify-self: center;
  width: 100%;
}

.hero-copy {
  display: grid;
  justify-items: start;
  gap: clamp(20px, 2.6vw, 30px);
}

.hero-title {
  display: grid;
  justify-items: start;
  gap: .2em;
  font-size: clamp(28px, 3.9vw, 60px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -.035em;
}

.hero-line {
  display: block;
  white-space: nowrap;
}

.hero-line--muted {
  padding-inline: .16em;
  color: var(--fg);
}

.hero-plate {
  display: inline-block;
  padding: .08em .16em .12em;
  border-radius: .14em;
}

.hero-lead {
  max-width: 44ch;
  padding-left: .1em;
  color: var(--fg-secondary);
  font-size: clamp(15px, 1.3vw, 18px);
  line-height: 1.6;
  text-wrap: pretty;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.facts-board {
  position: relative;
}

.facts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0;
  padding: 0;
  list-style: none;
}

.fact {
  display: grid;
  justify-items: center;
  gap: 10px;
  padding: 6px 12px;
  text-align: center;
}

.fact + .fact {
  border-left: 1px solid var(--line);
}

.fact-value {
  position: relative;
  display: inline-grid;
  place-items: center;
  padding: .06em .22em .1em;
  font-family: var(--font-display);
  font-size: clamp(24px, 3.1vw, 42px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -.04em;
  white-space: nowrap;
}

.fact-plate {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: var(--plate);
  border-radius: .16em;
  opacity: 0;
  transform: scale(.82);
  transition: opacity 420ms var(--ease), transform 620ms var(--ease-out);
}

.fact-plate::after {
  position: absolute;
  inset: 0;
  content: '';
  background: var(--texture-noise-tile) repeat;
  background-size: 72px 72px;
  opacity: .16;
  mix-blend-mode: multiply;
}

.fact-number {
  position: relative;
  transition: color 320ms var(--ease);
}

.fact.is-active .fact-plate {
  opacity: 1;
  transform: none;
}

.fact.is-active .fact-number {
  color: var(--plate-ink);
}

.fact-label {
  color: var(--fg-secondary);
  font-size: 13px;
  font-weight: 650;
}

@media (max-width: 900px) {
  .hero-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }

  .hero-visual {
    max-width: 440px;
  }

  .hero-copy {
    justify-items: center;
    text-align: center;
  }

  .hero-title {
    justify-items: center;
  }

  .hero-actions {
    justify-content: center;
  }
}

@media (max-width: 620px) {
  .hero {
    min-height: 0;
  }

  .hero-actions {
    width: 100%;
  }

  .hero-actions .base-button {
    flex: 1 1 100%;
  }

  .facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    row-gap: 18px;
  }

  .fact:nth-child(3) {
    border-left: 0;
  }
}
</style>
