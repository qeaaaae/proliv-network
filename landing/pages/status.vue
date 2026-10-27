<script setup lang="ts">
useHead({ title: 'Статус - Proliv Network' })

interface Service {
  id: string
  name: string
  flag?: string
  icon?: string
  up: boolean
  state: string
  uptime: string
  // 48 half-hour slots over the last 24h; 0 ok | 1 degraded | 2 down | -1 unknown
  slots: number[]
}

interface StatusPayload {
  updated_at: number
  all_up: boolean
  groups: { locations: Service[]; services: Service[] }
}

const EMPTY_SLOT = -1
const emptySlots = () => Array.from({ length: 48 }, () => EMPTY_SLOT)

const locations = ref<Service[]>([])
const services = ref<Service[]>([])
const allUp = ref(true)
const updatedAt = ref<number | null>(null)
const failed = ref(false)

const updatedLabel = computed(() => {
  if (!updatedAt.value) return ''
  const d = new Date(updatedAt.value * 1000)
  return `Обновлено ${d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`
})

const slotClass = (s: number) =>
  s === 0 ? 'slot--ok' : s === 1 ? 'slot--degraded' : s === 2 ? 'slot--down' : 'slot--unknown'

async function load() {
  try {
    const res = await fetch(`/status/status.json?t=${Date.now()}`)
    if (!res.ok) throw new Error(String(res.status))
    const data = (await res.json()) as StatusPayload & { samples?: unknown }
    locations.value = data.groups?.locations ?? []
    services.value = data.groups?.services ?? []
    allUp.value = Boolean(data.all_up ?? true)
    updatedAt.value = data.updated_at || null
    failed.value = false
  } catch {
    failed.value = true
  }
}

let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  load()
  timer = setInterval(load, 30000)
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <main class="status-page">
    <div class="content-frame status-frame">
      <header class="status-top" data-reveal>
        <NuxtLink to="/" class="status-back">← На главную</NuxtLink>
      </header>

      <div class="status-hero" data-reveal>
        <h1 class="status-title">Статус Proliv Network</h1>
        <span v-if="!failed" class="status-badge" :class="{ 'status-badge--down': !allUp }">
          <i class="badge-dot" aria-hidden="true" />{{ allUp ? 'Всё работает' : 'Есть проблемы' }}
        </span>
      </div>
      <p class="status-lead" data-reveal style="--delay: 0.08s">
        Здесь видно, как сейчас работают наши локации и сервисы
      </p>

      <section class="status-panel card" aria-label="Локации" data-reveal style="--delay: 0.12s">
        <h2 class="panel-title">Локации</h2>
        <ul class="service-list">
          <li v-for="s in locations" :key="s.id" class="service">
            <div class="service-head">
              <img v-if="s.flag" class="service-flag" :src="`/images/flags/${s.flag}.svg`" alt="" width="26" height="18">
              <div class="service-id">
                <h3>{{ s.name }}</h3>
                <span class="service-state">
                  <i class="state-dot" :class="{ 'state-dot--down': !s.up }" aria-hidden="true" />{{ s.state }}
                </span>
              </div>
              <span class="service-uptime">{{ s.uptime }}<small> за 24 часа</small></span>
            </div>
            <div class="uptime-bar" role="img" :aria-label="`Аптайм ${s.uptime} за 24 часа`">
              <i
                v-for="(slot, i) in (s.slots.length ? s.slots : emptySlots())"
                :key="i"
                class="slot"
                :class="slotClass(slot)"
                :style="{ '--i': i }"
              />
            </div>
            <div class="uptime-axis">
              <span>24 часа назад</span>
              <span>Сейчас</span>
            </div>
          </li>
        </ul>
      </section>

      <section class="status-panel card" aria-label="Сервисы" data-reveal style="--delay: 0.16s">
        <h2 class="panel-title">Сервисы</h2>
        <ul class="service-list">
          <li v-for="s in services" :key="s.id" class="service">
            <div class="service-head">
              <span class="service-icon" aria-hidden="true">
                <svg v-if="s.icon === 'tg'" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm4.7 6.7-1.6 7.6c-.1.5-.4.7-.9.4l-2.4-1.8-1.2 1.1c-.1.1-.2.3-.5.3l.2-2.5 4.5-4.1c.2-.2 0-.3-.3-.1l-5.6 3.5-2.4-.8c-.5-.2-.5-.5.1-.8l9.3-3.6c.5-.1.8.2.4.8z"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4" y="6" width="16" height="12" rx="3"/><path d="M9 12h6"/></svg>
              </span>
              <div class="service-id">
                <h3>{{ s.name }}</h3>
                <span class="service-state">
                  <i class="state-dot" :class="{ 'state-dot--down': !s.up }" aria-hidden="true" />{{ s.state }}
                </span>
              </div>
              <span class="service-uptime">{{ s.uptime }}<small v-if="s.uptime !== '—'"> за 24 часа</small></span>
            </div>
            <div class="uptime-bar" role="img" :aria-label="`Аптайм ${s.uptime} за 24 часа`">
              <i
                v-for="(slot, i) in (s.slots.length ? s.slots : emptySlots())"
                :key="i"
                class="slot"
                :class="slotClass(slot)"
                :style="{ '--i': i }"
              />
            </div>
            <div class="uptime-axis">
              <span>24 часа назад</span>
              <span>Сейчас</span>
            </div>
          </li>
        </ul>
      </section>

      <p class="status-note" data-reveal style="--delay: 0.2s">
        <template v-if="failed">Не удалось загрузить метрики - попробуйте обновить страницу.</template>
        <template v-else>Живые метрики с узлов и сервисов. {{ updatedLabel }}</template>
      </p>
    </div>
  </main>
</template>

<style scoped>
.status-page {
  flex: 1;
  padding: 28px 0 96px;
}

.status-frame {
  max-width: 900px;
}

.status-back {
  color: var(--muted);
  font-size: 14px;
  transition: color 0.18s ease;
}

.status-back:hover {
  color: var(--accent);
}

.status-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 40px;
}

.status-title {
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text);
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.badge-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #3ddc84;
  box-shadow:
    0 0 6px rgba(61, 220, 132, 0.8),
    0 0 16px rgba(61, 220, 132, 0.4);
  animation: badge-pulse 2.4s ease-in-out infinite;
}

.status-badge--down .badge-dot {
  background: #ff8587;
  box-shadow:
    0 0 6px rgba(255, 133, 135, 0.8),
    0 0 16px rgba(255, 133, 135, 0.4);
}

@keyframes badge-pulse {
  50% {
    opacity: 0.55;
  }
}

.status-lead {
  margin-top: 12px;
  color: var(--fg-secondary);
  font-size: 16px;
}

.status-panel {
  margin-top: 28px;
  padding: clamp(18px, 3vw, 28px);
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}

.service-list {
  display: grid;
}

.service {
  padding: 22px 0 18px;
  border-bottom: 1px solid var(--border);
}

.service:last-child {
  border-bottom: 0;
  padding-bottom: 6px;
}

.service-head {
  display: flex;
  align-items: center;
  gap: 14px;
}

.service-flag {
  flex: none;
  width: 26px;
  height: 18px;
  border-radius: 4px;
  object-fit: cover;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.14);
}

.service-icon {
  display: inline-grid;
  flex: none;
  width: 26px;
  height: 26px;
  place-items: center;
  color: var(--accent);
  background: var(--accent-soft);
  border-radius: 6px;
}

.service-icon svg {
  width: 16px;
  height: 16px;
}

.service-id {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.service-id h3 {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.service-state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--fg-secondary);
  font-size: 13px;
}

.state-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3ddc84;
}

.state-dot--down {
  background: #ff8587;
}

.service-uptime {
  margin-left: auto;
  color: var(--text);
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}

.service-uptime small {
  color: var(--muted);
  font-size: 12px;
  font-weight: 400;
}

.uptime-bar {
  display: flex;
  gap: 3px;
  margin-top: 14px;
}

.slot {
  flex: 1;
  min-width: 4px;
  height: 22px;
  border-radius: 3px;
  background: #3ddc84;
  animation: slot-in 0.5s var(--ease-out) both;
  animation-delay: calc(var(--i) * 14ms);
}

@keyframes slot-in {
  from {
    opacity: 0;
    transform: scaleY(0.3);
  }
  to {
    opacity: 0.85;
    transform: scaleY(1);
  }
}

.slot--degraded {
  background: #f0b429;
}

.slot--down {
  background: #ff8587;
}

.slot--unknown {
  background: var(--border, #2a3240);
  opacity: 0.4;
}

.uptime-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  color: var(--muted);
  font-size: 12px;
}

.status-note {
  margin-top: 20px;
  padding: 12px 16px;
  color: var(--muted);
  font-size: 13px;
  background: var(--accent-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-control);
}

@media (max-width: 640px) {
  .status-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .service-head {
    flex-wrap: wrap;
  }

  .service-uptime {
    width: 100%;
    margin-left: 40px;
  }
}
</style>
