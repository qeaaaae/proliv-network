<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { locations } from '~/data/product'
import { flagUrls } from '~/data/assets'
import AccentMark from '~/components/ui/AccentMark.vue'
import DottedGlobe from '~/components/ui/DottedGlobe.vue'

const { t } = useI18n()
const activeId = ref(locations[1]!.id)
const touring = ref(false)
const markers = computed(() => locations.map(location => ({
  id: location.id,
  lat: location.lat,
  lon: location.lon,
  label: t(location.cityKey)
})))

let timer: ReturnType<typeof setInterval> | undefined

function stopTour() {
  touring.value = false
  clearInterval(timer)
}

function select(id: typeof activeId.value) {
  stopTour()
  activeId.value = id
}

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  touring.value = true
  timer = setInterval(() => {
    const index = locations.findIndex(location => location.id === activeId.value)
    activeId.value = locations[(index + 1) % locations.length]!.id
  }, 3600)
})

onBeforeUnmount(stopTour)
</script>

<template>
  <section id="locations" class="landing-block" aria-labelledby="locations-title">
    <div class="content-frame">
      <header class="split-head" v-reveal>
        <h2 id="locations-title" class="two-tone">
          <span>{{ t('locations.titleBefore') }}</span>
          <span><AccentMark>{{ t('locations.titleAccent') }}</AccentMark> {{ t('locations.titleAfter') }}</span>
        </h2>
        <p>{{ t('locations.lead') }}</p>
      </header>

      <div class="atlas card" v-reveal style="--delay: .08s">
        <ul class="atlas-list" role="group" :aria-label="t('a11y.locationSelector')">
          <li v-for="location in locations" :key="location.id">
            <button
              type="button"
              class="atlas-row"
              :aria-pressed="activeId === location.id"
              @click="select(location.id)"
            >
              <img :src="flagUrls[location.countryCode]" alt="" width="28" height="20">
              <span class="atlas-country">{{ t(location.nameKey) }}</span>
              <span class="atlas-city">{{ t(location.cityKey) }}</span>
              <span class="atlas-port numeric">{{ t('locations.port') }}</span>
              <span v-if="touring && activeId === location.id" :key="activeId" class="atlas-timer" aria-hidden="true" />
            </button>
          </li>
        </ul>
        <div class="atlas-globe">
          <DottedGlobe :markers="markers" :active="activeId" />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.atlas {
  display: grid;
  grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr);
}

.atlas-list {
  display: grid;
  align-content: center;
  margin: 0;
  padding: clamp(14px, 2vw, 24px);
  list-style: none;
}

.atlas-list li + li {
  border-top: 1px dashed var(--line-strong);
}

.atlas-row {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  grid-template-areas:
    'flag country port'
    'flag city port';
  align-items: center;
  gap: 2px 16px;
  width: 100%;
  padding: 14px 14px;
  overflow: hidden;
  text-align: left;
  border-radius: 14px;
  transition: background-color 260ms var(--ease), color 260ms var(--ease);
}

.atlas-row img {
  grid-area: flag;
  width: 28px;
  height: 20px;
  object-fit: cover;
  border-radius: 4px;
  box-shadow: 0 0 0 1px rgb(255 255 255 / 16%);
  transition: transform 420ms var(--ease-out);
}

.atlas-country {
  grid-area: country;
  font-family: var(--font-display);
  font-size: clamp(16px, 1.5vw, 20px);
  font-weight: 700;
  letter-spacing: -.03em;
}

.atlas-city {
  grid-area: city;
  color: var(--fg-secondary);
  font-size: 13px;
  font-weight: 600;
  transition: color 260ms var(--ease);
}

.atlas-port {
  grid-area: port;
  padding: 7px 11px;
  color: var(--fg-secondary);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  border: 1px dashed var(--line-dash);
  border-radius: var(--radius-pill);
  transition: color 260ms var(--ease), border-color 260ms var(--ease), background-color 260ms var(--ease);
}

.atlas-timer {
  position: absolute;
  bottom: 0;
  left: 14px;
  right: 14px;
  height: 2px;
  background: var(--plate-ink);
  border-radius: 2px;
  opacity: .35;
  transform-origin: left;
  animation: atlas-timer 3.6s linear both;
}

.atlas-row[aria-pressed='true'] {
  color: var(--plate-ink);
  background: var(--plate);
}

.atlas-row[aria-pressed='true'] .atlas-city {
  color: var(--plate-ink-soft);
}

.atlas-row[aria-pressed='true'] .atlas-port {
  color: var(--plate);
  background: var(--plate-ink);
  border-color: var(--plate-ink);
}

.atlas-globe {
  position: relative;
  min-height: 460px;
  border-left: 1px dashed var(--line-strong);
}

@keyframes atlas-timer {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}

@media (hover: hover) and (pointer: fine) {
  .atlas-row:not([aria-pressed='true']):hover {
    background: rgb(255 255 255 / 4%);
  }

  .atlas-row:not([aria-pressed='true']):hover .atlas-port {
    color: var(--fg);
    border-color: rgb(255 255 255 / 72%);
  }

  .atlas-row:hover img {
    transform: rotate(-8deg) scale(1.12);
  }
}

@media (max-width: 900px) {
  .atlas {
    grid-template-columns: minmax(0, 1fr);
  }

  .atlas-globe {
    order: -1;
    min-height: 0;
    aspect-ratio: 1 / .78;
    border-bottom: 1px dashed var(--line-strong);
    border-left: 0;
  }
}

@media (max-width: 520px) {
  .atlas-row {
    gap: 2px 12px;
    padding: 12px 10px;
  }
}
</style>
