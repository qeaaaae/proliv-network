<script setup lang="ts">
import { TELEGRAM_BOT_URL } from '../../utils/links'
</script>

<template>
  <section class="final-cta" aria-labelledby="final-cta-title">
    <LightFlare />
    <div class="final-mark" aria-hidden="true" data-reveal>
      <svg viewBox="0 0 32 32">
        <path
          pathLength="1"
          d="M16 4c4.2 5.6 8 10.2 8 15a8 8 0 1 1-16 0c0-4.8 3.8-9.4 8-15z"
        />
      </svg>
    </div>
    <div class="cta-inner">
      <h2 id="final-cta-title" class="cta-title" data-reveal>
        Попробуйте Network <AccentMark>3 дня бесплатно</AccentMark>
      </h2>
      <p class="cta-text" data-reveal style="--delay: 0.08s">
        Пробный период подключается через личный кабинет без привязки банковской карты
      </p>
      <BaseButton class="cta-button" data-reveal style="--delay: 0.16s" :href="TELEGRAM_BOT_URL" target="_blank" rel="noopener">
        Попробовать бесплатно
      </BaseButton>
    </div>
  </section>
</template>

<style scoped>
.final-cta {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 26px;
  min-height: clamp(480px, 48vw, 640px);
  padding: clamp(48px, 6vw, 80px) 24px;
  text-align: center;
}

.final-mark {
  position: absolute;
  z-index: -1;
  top: 50%;
  left: 50%;
  height: 84%;
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
}

.final-mark svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.final-mark path {
  fill: none;
  stroke: rgba(125, 211, 252, 0.22);
  stroke-width: 0.35px;
  stroke-linejoin: round;
}

html.motion .final-mark path {
  stroke-dasharray: 1;
  stroke-dashoffset: 1px;
  transition: stroke-dashoffset 2.8s var(--ease-out) 0.2s;
}

html.motion .final-mark[data-shown] path {
  stroke-dashoffset: 0;
}

.cta-inner {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  max-width: 640px;
  margin: 0 auto;
}

.cta-title {
  font-family: var(--font-display);
  font-size: clamp(28px, 4.4vw, 52px);
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.03em;
  max-width: 16ch;
  text-wrap: balance;
}

.cta-text {
  max-width: 520px;
  color: var(--fg-secondary);
  font-size: 17px;
}

.cta-button {
  margin-top: 10px;
}
</style>
