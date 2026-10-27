<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { telegramBotUrl } from '~/data/product'

const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string
import AccentMark from '~/components/ui/AccentMark.vue'
import BaseButton from '~/components/ui/BaseButton.vue'

const { t } = useI18n()
const orbits = [
  { size: 380, speed: 16, delay: 0 },
  { size: 600, speed: 26, delay: -9 },
  { size: 820, speed: 38, delay: -20 }
]
</script>

<template>
  <section class="final card" aria-labelledby="final-title">
    <div class="final-sky" aria-hidden="true">
      <span class="final-pulse" />
      <span
        v-for="orbit in orbits"
        :key="orbit.size"
        class="final-orbit"
        :style="{ '--size': `${orbit.size}px`, '--speed': `${orbit.speed}s`, '--delay': `${orbit.delay}s` }"
      >
        <svg viewBox="0 0 24 24">
          <path d="M22 12c0-.8-1.4-1.5-3-1.5h-5L8 2H5l4 8.5H4L2 7H.5l1 5-1 5H2l2-3.5h5L5 22h3l6-8.5h5c1.6 0 3-.7 3-1.5Z" />
        </svg>
      </span>
    </div>

    <div class="final-copy">
      <h2 id="final-title" class="two-tone final-title" v-reveal>
        <span>{{ t('finalCta.titleBefore') }}</span>
        <span><AccentMark>{{ t('finalCta.titleAccent') }}</AccentMark></span>
      </h2>
      <p v-reveal style="--delay: .08s">{{ t('finalCta.description') }}</p>
      <div class="final-actions" v-reveal style="--delay: .16s">
        <BaseButton :href="cabinetUrl">{{ t('actions.startTrial') }}</BaseButton>
        <BaseButton :href="telegramBotUrl" variant="telegram" trail="plane">{{ t('footer.links.bot') }}</BaseButton>
      </div>
    </div>
  </section>
</template>

<style scoped>
.final {
  display: grid;
  place-items: center;
  min-height: clamp(460px, 44vw, 600px);
  padding: clamp(36px, 5vw, 72px) clamp(20px, 4vw, 56px);
  text-align: center;
  border-radius: var(--radius-sheet);
}

.final-sky {
  position: absolute;
  z-index: -1;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  -webkit-mask-image: radial-gradient(closest-side, #000 55%, transparent 100%);
  mask-image: radial-gradient(closest-side, #000 55%, transparent 100%);
}

.final-orbit,
.final-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
}

.final-orbit {
  width: var(--size);
  height: var(--size);
  margin: calc(var(--size) / -2) 0 0 calc(var(--size) / -2);
  border: 1px dashed var(--line-dash);
  animation: final-orbit var(--speed) linear infinite;
  animation-delay: var(--delay);
}

.final-orbit svg {
  position: absolute;
  top: -9px;
  left: calc(50% - 9px);
  width: 18px;
  height: 18px;
  fill: var(--plate);
  filter: drop-shadow(0 0 8px rgb(125 211 252 / 40%));
}

.final-pulse {
  width: 200px;
  height: 200px;
  margin: -100px 0 0 -100px;
  border: 1px solid rgb(125 211 252 / 40%);
  animation: final-pulse 3.2s var(--ease-out) infinite;
}

.final-copy {
  display: grid;
  justify-items: center;
  gap: 22px;
}

.final-title {
  font-size: clamp(32px, 5vw, 68px);
}

.final-copy p {
  max-width: 44ch;
  color: var(--fg-secondary);
  font-size: 16px;
  text-wrap: pretty;
}

.final-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

@keyframes final-orbit {
  to { transform: rotate(360deg); }
}

@keyframes final-pulse {
  0% { opacity: 0; transform: scale(.4); }
  20% { opacity: 1; }
  100% { opacity: 0; transform: scale(4.6); }
}

@media (max-width: 520px) {
  .final-actions {
    width: 100%;
  }

  .final-actions .base-button {
    flex: 1 1 100%;
  }
}
</style>
