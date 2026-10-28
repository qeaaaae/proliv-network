<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import AccentMark from '~/components/ui/AccentMark.vue'
import BaseButton from '~/components/ui/BaseButton.vue'

const { t } = useI18n()
const connected = ref(true)
let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  connected.value = false
  timer = setInterval(() => {
    connected.value = !connected.value
  }, 2800)
})

onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <section id="lte" class="landing-block" aria-labelledby="lte-title">
    <div class="content-frame lte">
      <div class="lte-copy" v-reveal>
        <h2 id="lte-title" class="two-tone lte-title">
          <span><AccentMark>{{ t('lte.titleAccent') }}</AccentMark></span>
          <span>{{ t('lte.titleAfter') }}</span>
        </h2>
        <p class="lte-lead">{{ t('lte.lead') }}</p>
        <ul class="lte-points">
          <li>{{ t('lte.points.servers') }}</li>
          <li>{{ t('lte.points.switch') }}</li>
        </ul>
        <BaseButton href="#pricing" variant="secondary" trail="arrow-down">{{ t('actions.viewPricing') }}</BaseButton>
      </div>

      <div class="lte-scene card" :class="{ 'is-on': connected }" v-reveal style="--delay: .1s" aria-hidden="true">
        <svg class="lte-tower" viewBox="0 0 220 380">
          <path d="M60 350 95 40M150 350 115 40M40 350H170" />
          <path d="M60 350 144.4 300 71.3 250 133.1 200 82.6 150 121.8 100 92.7 60M150 350 65.6 300 138.7 250 76.9 200 127.4 150 88.2 100 117.3 60" />
          <path d="M65.6 300H144.4M71.3 250H138.7M76.9 200H133.1M82.6 150H127.4M88.2 100H121.8M92.7 60H117.3" />
          <path d="M105 40V6M101 6H109" />
          <path class="lte-wave" style="--wave: 0" d="M160 38a32 32 0 0 1 0 52" />
          <path class="lte-wave" style="--wave: 1" d="M172 26a50 50 0 0 1 0 76" />
          <path class="lte-wave" style="--wave: 2" d="M184 14a68 68 0 0 1 0 100" />
          <path class="lte-ground" d="M10 372H210" />
        </svg>

        <div class="lte-beam">
          <span v-for="packet in 4" :key="packet" :style="{ '--packet': packet - 1 }" />
        </div>

        <div class="lte-phone">
          <div class="lte-bar">
            <span class="lte-signal"><i v-for="bar in 4" :key="bar" :style="{ '--bar': bar }" /></span>
            <span class="lte-badge">LTE</span>
          </div>
          <div class="lte-row lte-row--mobile">
            <span>{{ t('lte.status.mobile') }}</span>
            <small>{{ t('lte.status.off') }}</small>
          </div>
          <div class="lte-row lte-row--network">
            <span>{{ t('lte.status.network') }}</span>
            <span class="lte-switch"><i /></span>
            <small class="lte-state">{{ t('lte.status.on') }}</small>
          </div>
          <div class="lte-feed">
            <i v-for="line in 5" :key="line" :style="{ '--line': line }" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.lte {
  display: grid;
  grid-template-columns: minmax(0, .95fr) minmax(0, 1.05fr);
  align-items: center;
  gap: clamp(28px, 5vw, 72px);
}

.lte-copy {
  display: grid;
  justify-items: start;
  gap: 22px;
}

.lte-title {
  justify-items: start;
}

.lte-lead {
  max-width: 40ch;
  color: var(--fg-secondary);
  font-size: 17px;
  text-wrap: pretty;
}

.lte-points {
  display: grid;
  width: 100%;
  margin: 0;
  padding: 0;
  list-style: none;
}

.lte-points li {
  padding-block: 14px;
  font-size: 15px;
  font-weight: 650;
  border-top: 1px dashed var(--line-strong);
}

.lte-points li:last-child {
  border-bottom: 1px dashed var(--line-strong);
}

.lte-scene {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(40px, .6fr) auto;
  align-items: center;
  min-height: 440px;
  padding: clamp(24px, 3vw, 40px);
}

.lte-tower {
  width: 100%;
  max-width: 240px;
  height: auto;
  fill: none;
  stroke: rgb(255 255 255 / 34%);
  stroke-width: 1.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.lte-ground {
  stroke-dasharray: 2 6;
}

.lte-wave {
  stroke: var(--plate);
  opacity: .12;
  transition: opacity 400ms var(--ease);
}

.is-on .lte-wave {
  animation: lte-wave 1.4s var(--ease) infinite;
  animation-delay: calc(var(--wave) * .18s);
}

.lte-beam {
  position: relative;
  align-self: center;
  height: 2px;
  margin-top: 40px;
  background: repeating-linear-gradient(90deg, rgb(255 255 255 / 26%) 0 4px, transparent 4px 10px);
}

.lte-beam span {
  position: absolute;
  top: -3px;
  left: 0;
  width: 8px;
  height: 8px;
  background: var(--plate);
  border-radius: 50%;
  opacity: 0;
}

.is-on .lte-beam span {
  animation: lte-packet 1.6s linear infinite;
  animation-delay: calc(var(--packet) * .4s);
}

.lte-phone {
  display: grid;
  align-content: start;
  gap: 10px;
  width: clamp(190px, 18vw, 230px);
  aspect-ratio: 9 / 17;
  padding: 18px 14px;
  background: var(--panel-raised);
  border: 1px solid var(--line-strong);
  border-radius: 30px;
  box-shadow: 0 30px 60px rgb(0 0 0 / 45%), inset 0 0 0 5px var(--sheet);
}

.lte-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px 10px;
}

.lte-signal {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 14px;
}

.lte-signal i {
  width: 4px;
  height: calc(var(--bar) * 25%);
  background: var(--fg-tertiary);
  border-radius: 1px;
  transition: background-color 300ms var(--ease);
  transition-delay: calc(var(--bar) * 60ms);
}

.is-on .lte-signal i {
  background: var(--fg);
}

.lte-badge {
  padding: 3px 7px;
  color: var(--fg-tertiary);
  font-size: 10px;
  font-weight: 800;
  border: 1px dashed var(--line-dash);
  border-radius: 6px;
  transition: color 300ms var(--ease), background-color 300ms var(--ease), border-color 300ms var(--ease);
}

.is-on .lte-badge {
  color: var(--plate-ink);
  background: var(--plate);
  border-color: var(--plate);
}

.lte-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 2px 8px;
  padding: 10px 12px;
  font-size: 12px;
  font-weight: 700;
  background: rgb(255 255 255 / 3%);
  border: 1px solid var(--line);
  border-radius: 14px;
}

.lte-row small {
  grid-column: 1 / -1;
  color: var(--fg-tertiary);
  font-size: 11px;
  font-weight: 600;
}

.lte-row--mobile small {
  text-decoration: line-through;
}

.lte-row--network {
  transition: background-color 300ms var(--ease), border-color 300ms var(--ease);
}

.is-on .lte-row--network {
  border-color: var(--line-dash);
  background: rgb(255 255 255 / 6%);
}

.lte-state {
  opacity: 0;
  transform: translateY(4px);
  transition: opacity 300ms var(--ease), transform 300ms var(--ease-out);
}

.is-on .lte-state {
  color: var(--fg-secondary);
  opacity: 1;
  transform: none;
}

.lte-switch {
  position: relative;
  width: 30px;
  height: 18px;
  background: var(--control);
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  transition: background-color 300ms var(--ease);
}

.lte-switch i {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 12px;
  height: 12px;
  background: var(--fg-tertiary);
  border-radius: 50%;
  transition: transform 360ms var(--ease-out), background-color 300ms var(--ease);
}

.is-on .lte-switch {
  background: var(--plate);
}

.is-on .lte-switch i {
  background: var(--plate-ink);
  transform: translateX(12px);
}

.lte-feed {
  display: grid;
  gap: 7px;
  margin-top: 8px;
  padding: 12px;
  border: 1px dashed var(--line);
  border-radius: 14px;
}

.lte-feed i {
  height: 6px;
  width: calc(100% - var(--line) * 11%);
  background: var(--control);
  border-radius: 3px;
  transition: background-color 400ms var(--ease);
  transition-delay: calc(var(--line) * 70ms);
}

.is-on .lte-feed i {
  background: rgb(255 255 255 / 20%);
}

@keyframes lte-wave {
  0%, 100% { opacity: .12; }
  40% { opacity: 1; }
}

@keyframes lte-packet {
  0% { left: 0; opacity: 0; }
  15%, 80% { opacity: 1; }
  100% { left: calc(100% - 8px); opacity: 0; }
}

@media (max-width: 900px) {
  .lte {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 520px) {
  .lte-scene {
    grid-template-columns: minmax(0, .8fr) minmax(16px, .3fr) auto;
    min-height: 0;
    padding: 18px;
  }

  .lte-phone {
    width: 168px;
  }
}
</style>
