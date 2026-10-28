<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { experienceItems } from '~/data/product'
import AccentMark from '~/components/ui/AccentMark.vue'

const { t } = useI18n()
const routeKeys = {
  europe: 'experience.routes.europe',
  direct: 'experience.routes.direct'
} as const
const prefix = useId()
const flow = ref<HTMLElement | null>(null)
const device = ref<HTMLElement | null>(null)
const hub = ref<HTMLElement | null>(null)
const targets = ref<HTMLElement[]>([])
const hovered = ref(-1)
const size = ref({ width: 0, height: 0 })
const trunk = ref('')
const branches = ref<string[]>([])

function measure() {
  const root = flow.value?.getBoundingClientRect()
  const from = device.value?.getBoundingClientRect()
  const middle = hub.value?.getBoundingClientRect()
  if (!root || !from || !middle) return
  const local = (rect: DOMRect) => ({
    left: rect.left - root.left,
    right: rect.right - root.left,
    top: rect.top - root.top,
    bottom: rect.bottom - root.top,
    x: rect.left - root.left + rect.width / 2,
    y: rect.top - root.top + rect.height / 2
  })
  const a = local(from)
  const b = local(middle)
  const ends = targets.value.map(element => local(element.getBoundingClientRect()))
  size.value = { width: root.width, height: root.height }

  if (a.bottom <= b.top) {
    trunk.value = `M${a.x} ${a.bottom}V${b.top}`
    branches.value = ends.map((end) => {
      const rail = end.left - 11
      return `M${b.x} ${b.bottom}C${b.x} ${b.bottom + 24} ${rail} ${b.bottom + 4} ${rail} ${b.bottom + 36}V${end.y}H${end.left}`
    })
    return
  }
  const bend = (a.right + b.left) / 2
  trunk.value = `M${a.right} ${a.y}C${bend} ${a.y} ${bend} ${b.y} ${b.left} ${b.y}`
  branches.value = ends.map((end) => {
    const curve = (b.right + end.left) / 2
    return `M${b.right} ${b.y}C${curve} ${b.y} ${curve} ${end.y} ${end.left} ${end.y}`
  })
}

let observer: ResizeObserver | undefined

onMounted(() => {
  observer = new ResizeObserver(measure)
  if (flow.value) observer.observe(flow.value)
  document.fonts?.ready.then(measure)
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <section class="landing-block" aria-labelledby="routes-title">
    <div class="content-frame">
      <header class="split-head" v-reveal>
        <h2 id="routes-title" class="two-tone">
          <span>{{ t('experience.titleBefore') }}</span>
          <span><AccentMark>{{ t('experience.titleAccent') }}</AccentMark></span>
        </h2>
        <p>{{ t('experience.lead') }}</p>
      </header>

      <div ref="flow" class="flow card" v-reveal style="--delay: .08s">
        <svg class="flow-wires" :viewBox="`0 0 ${size.width} ${size.height}`" aria-hidden="true">
          <path :id="`${prefix}-trunk`" class="flow-wire flow-wire--europe" :d="trunk" />
          <path
            v-for="(branch, index) in branches"
            :id="`${prefix}-branch-${index}`"
            :key="index"
            class="flow-wire"
            :class="[`flow-wire--${experienceItems[index]?.route}`, { 'is-hovered': hovered === index }]"
            :d="branch"
          />
          <template v-if="trunk">
            <circle v-for="packet in 3" :key="`trunk-${packet}`" class="flow-packet" r="4">
              <animateMotion dur="1.8s" repeatCount="indefinite" :begin="`${(packet - 1) * .6}s`">
                <mpath :href="`#${prefix}-trunk`" />
              </animateMotion>
            </circle>
            <template v-for="(_, index) in branches" :key="`packets-${index}`">
              <circle
                v-for="packet in 2"
                :key="packet"
                class="flow-packet"
                :class="`flow-packet--${experienceItems[index]?.route}`"
                r="4"
              >
                <animateMotion dur="2.2s" repeatCount="indefinite" :begin="`${index * .35 + (packet - 1) * 1.1}s`">
                  <mpath :href="`#${prefix}-branch-${index}`" />
                </animateMotion>
              </circle>
            </template>
          </template>
        </svg>

        <div ref="device" class="flow-device">
          <svg viewBox="0 0 120 70" aria-hidden="true">
            <rect x="4" y="6" width="74" height="46" rx="4" />
            <path d="M0 58H82M28 52 26 58M54 52 56 58" />
            <rect x="90" y="18" width="26" height="46" rx="5" />
            <path d="M99 23H107" />
          </svg>
          <span>{{ t('experience.device') }}</span>
        </div>

        <div ref="hub" class="flow-hub">
          <span class="flow-orbit" aria-hidden="true" />
          <svg viewBox="6 1 20 30" aria-hidden="true">
            <path d="M16 4c4.2 5.6 8 10.2 8 15a8 8 0 1 1-16 0c0-4.8 3.8-9.4 8-15z" />
          </svg>
        </div>

        <ul class="flow-targets">
          <li
            v-for="(item, index) in experienceItems"
            :key="item.id"
            ref="targets"
            class="flow-target"
            @pointerenter="hovered = index"
            @pointerleave="hovered = -1"
          >
            <div class="flow-target-head">
              <h3>{{ t(item.labelKey) }}</h3>
              <span class="flow-route" :class="{ plate: item.route === 'europe' }">{{ t(routeKeys[item.route]) }}</span>
            </div>
            <p>{{ t(item.descriptionKey) }}</p>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.flow {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  align-items: center;
  column-gap: clamp(56px, 9vw, 140px);
  padding: clamp(24px, 3.4vw, 44px);
}

.flow-wires {
  position: absolute;
  z-index: 0;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.flow-wire {
  fill: none;
  stroke: rgb(255 255 255 / 30%);
  stroke-width: 1.5;
  stroke-dasharray: 3 7;
  transition: stroke 260ms var(--ease);
}

.flow-wire--europe {
  stroke: rgb(125 211 252 / 55%);
  stroke-dasharray: none;
}

.flow-wire.is-hovered {
  stroke: var(--plate);
}

.flow-packet {
  fill: var(--plate);
}

.flow-packet--direct {
  fill: var(--bg);
  stroke: var(--fg-secondary);
  stroke-width: 1.5;
}

.flow-device,
.flow-hub,
.flow-targets {
  position: relative;
  z-index: 1;
}

.flow-device {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 18px 20px 16px;
  font-size: 14px;
  font-weight: 700;
  background: var(--panel);
  border: 1px dashed var(--line-dash);
  border-radius: 18px;
}

.flow-device svg {
  width: 92px;
  height: auto;
  fill: none;
  stroke: var(--fg);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.flow-hub {
  display: grid;
  place-items: center;
  width: 112px;
  height: 112px;
  background: var(--panel-raised);
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  box-shadow: 0 0 0 10px rgb(10 12 14 / 70%);
}

.flow-hub svg {
  width: 34px;
  height: auto;
  fill: var(--plate);
}

.flow-orbit {
  position: absolute;
  inset: -16px;
  border: 1px dashed var(--line-dash);
  border-radius: 50%;
  animation: flow-orbit 22s linear infinite;
}

.flow-orbit::before {
  position: absolute;
  top: 50%;
  left: -4px;
  width: 7px;
  height: 7px;
  content: '';
  background: var(--plate);
  border-radius: 50%;
}

.flow-targets {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.flow-target {
  display: grid;
  gap: 8px;
  padding: 18px 20px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 18px;
  transition: border-color 260ms var(--ease), transform 420ms var(--ease-out);
}

.flow-target-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 14px;
}

.flow-target h3 {
  font-size: clamp(18px, 1.8vw, 24px);
  letter-spacing: -.03em;
}

.flow-target p {
  max-width: 46ch;
  color: var(--fg-secondary);
  font-size: 14px;
}

.flow-route {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 750;
  white-space: nowrap;
  border: 1px dashed var(--line-dash);
  border-radius: var(--radius-pill);
}

.flow-route.plate {
  border-color: transparent;
  border-radius: var(--radius-pill);
}

@keyframes flow-orbit {
  to { transform: rotate(360deg); }
}

@media (hover: hover) and (pointer: fine) {
  .flow-target:hover {
    border-color: var(--line-dash);
    transform: translateX(6px);
  }
}

@media (max-width: 900px) {
  .flow {
    grid-template-columns: minmax(0, 1fr);
    justify-items: center;
    row-gap: 44px;
  }

  .flow-targets {
    justify-self: stretch;
    padding-left: 22px;
  }
}
</style>
