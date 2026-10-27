<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string
import AccentMark from '~/components/ui/AccentMark.vue'
import BaseButton from '~/components/ui/BaseButton.vue'

const { t } = useI18n()
const steps = [
  { title: 'connect.steps.trial.title', text: 'connect.steps.trial.text' },
  { title: 'connect.steps.app.title', text: 'connect.steps.app.text' },
  { title: 'connect.steps.connect.title', text: 'connect.steps.connect.text' }
]
const platforms = [
  'connect.platforms.android',
  'connect.platforms.ios',
  'connect.platforms.windows',
  'connect.platforms.macos',
  'connect.platforms.linux',
  'connect.platforms.androidTv',
  'connect.platforms.appleTv'
]
</script>

<template>
  <section id="connect" class="landing-block" aria-labelledby="connect-title">
    <div class="content-frame">
      <header class="split-head" v-reveal>
        <h2 id="connect-title" class="two-tone">
          <span>{{ t('connect.titleBefore') }}</span>
          <span><AccentMark>{{ t('connect.titleAccent') }}</AccentMark></span>
        </h2>
        <BaseButton class="connect-action" :href="cabinetUrl">{{ t('actions.startTrial') }}</BaseButton>
      </header>

      <ol class="steps">
        <li
          v-for="(step, index) in steps"
          :key="step.title"
          class="step card"
          :style="{ '--delay': `${index * .08}s` }"
          v-reveal
        >
          <span class="step-number numeric" aria-hidden="true">{{ index + 1 }}</span>
          <h3>{{ t(step.title) }}</h3>
          <p>{{ t(step.text) }}</p>
          <span v-if="index < steps.length - 1" class="step-link" aria-hidden="true"><i /></span>
        </li>
      </ol>

      <div class="platforms" v-reveal style="--delay: .2s">
        <span class="platforms-label">{{ t('connect.platformsLabel') }}</span>
        <ul>
          <li v-for="platform in platforms" :key="platform">{{ t(platform) }}</li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.connect-action {
  justify-self: end;
}

.steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.step {
  display: grid;
  align-content: start;
  gap: 12px;
  min-height: 250px;
  padding: 24px;
  overflow: visible;
}

.step-number {
  display: inline-grid;
  place-items: center;
  justify-self: start;
  min-width: 1.4em;
  margin-bottom: 18px;
  padding: .04em .2em .1em;
  color: var(--plate-ink);
  font-family: var(--font-display);
  font-size: 64px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -.05em;
  background: var(--plate);
  border-radius: 16px;
  transform: rotate(-4deg);
  transition: transform 520ms var(--ease-out);
}

.step:nth-child(2) .step-number {
  transform: rotate(3deg);
}

.step h3 {
  font-size: 20px;
  letter-spacing: -.03em;
}

.step p {
  color: var(--fg-secondary);
  font-size: 14px;
  text-wrap: pretty;
}

.step-link {
  position: absolute;
  z-index: 2;
  top: 58px;
  right: -19px;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  background: var(--bg);
  border: 1px dashed var(--line-dash);
  border-radius: 50%;
}

.step-link i {
  width: 6px;
  height: 6px;
  background: var(--plate);
  border-radius: 50%;
  animation: step-link 1.6s var(--ease) infinite;
}

.platforms {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 18px;
  margin-top: 18px;
}

.platforms-label {
  color: var(--fg-secondary);
  font-size: 14px;
  font-weight: 650;
}

.platforms ul {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.platforms li {
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 700;
  border: 1px dashed var(--line-dash);
  border-radius: var(--radius-pill);
  transition: color 220ms var(--ease), background-color 220ms var(--ease), border-color 220ms var(--ease), transform 420ms var(--ease-out);
}

@keyframes step-link {
  0%, 100% { transform: translateX(-4px); opacity: .4; }
  50% { transform: translateX(4px); opacity: 1; }
}

@media (hover: hover) and (pointer: fine) {
  .step:hover .step-number {
    transform: rotate(0) scale(1.06);
  }

  .platforms li:hover {
    color: var(--plate-ink);
    background: var(--plate);
    border-color: var(--plate);
    transform: translateY(-3px) rotate(-3deg);
  }
}

@media (max-width: 860px) {
  .connect-action {
    justify-self: start;
  }

  .steps {
    grid-template-columns: minmax(0, 1fr);
  }

  .step {
    min-height: 0;
  }

  .step-number {
    font-size: 48px;
    margin-bottom: 6px;
  }

  .step-link {
    top: auto;
    right: auto;
    bottom: -19px;
    left: 34px;
  }

  .step-link i {
    animation-name: step-link-down;
  }

  @keyframes step-link-down {
    0%, 100% { transform: translateY(-4px); opacity: .4; }
    50% { transform: translateY(4px); opacity: 1; }
  }
}
</style>
