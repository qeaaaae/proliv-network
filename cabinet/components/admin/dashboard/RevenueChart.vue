<script setup lang="ts">
interface RevenuePoint {
  date: string
  amount: number
}

const props = defineProps<{
  points: RevenuePoint[]
  currency: string
}>()

const period = ref('30')
const periodItems = [
  { value: '7', label: '7 дней' },
  { value: '14', label: '14 дней' },
  { value: '30', label: '30 дней' },
  { value: '90', label: '90 дней' },
  { value: 'all', label: 'Всё время' },
]

const filtered = computed<RevenuePoint[]>(() => {
  if (period.value === 'all') return props.points
  return props.points.slice(-Number(period.value))
})

const total = computed(() =>
  filtered.value.reduce((sum, p) => sum + (Number(p.amount) || 0), 0),
)
const perDay = computed(() => (filtered.value.length ? total.value / filtered.value.length : 0))

const growth = computed<number | null>(() => {
  if (period.value === 'all') return null
  const n = Number(period.value)
  if (props.points.length < n * 2) return null
  const prev = props.points
    .slice(-n * 2, -n)
    .reduce((sum, p) => sum + (Number(p.amount) || 0), 0)
  if (prev <= 0) return null
  return ((total.value - prev) / prev) * 100
})

const maxY = computed(() =>
  filtered.value.reduce((max, p) => Math.max(max, Number(p.amount) || 0), 0),
)

const W = 600
const H = 150

const bars = computed(() => {
  const pts = filtered.value
  if (!pts.length) return []
  const step = W / pts.length
  const barW = Math.max(1, Math.min(24, step * 0.7))
  const max = maxY.value || 1
  return pts.map((p, index) => {
    const value = Number(p.amount) || 0
    const h = value > 0 ? Math.max(3, (value / max) * (H - 14)) : 0
    return {
      x: index * step + (step - barW) / 2,
      y: H - h,
      w: barW,
      h,
      value,
      date: p.date,
    }
  })
})

function fmtMoney(value: number): string {
  const code = (props.currency || 'RUB').toUpperCase()
  try {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: code,
      maximumFractionDigits: value % 1 ? 2 : 0,
    }).format(value)
  } catch {
    return `${new Intl.NumberFormat('ru-RU').format(value)} ${code}`
  }
}

function fmtShortDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
}

const firstDate = computed(() => {
  const first = filtered.value[0]
  return first ? fmtShortDate(first.date) : ''
})
const lastDate = computed(() => {
  const last = filtered.value[filtered.value.length - 1]
  return last ? fmtShortDate(last.date) : ''
})
</script>

<template>
  <section class="admin-card">
    <div class="chart-head">
      <div class="chart-title">
        <h2>Выручка</h2>
        <p class="admin-note">
          {{ fmtMoney(total) }} за период · в среднем {{ fmtMoney(perDay) }} в день
        </p>
      </div>
      <div class="chart-controls">
        <AdminBadge v-if="growth !== null" :tone="growth >= 0 ? 'success' : 'danger'">
          {{ growth >= 0 ? '+' : '' }}{{ growth.toFixed(1) }}%
        </AdminBadge>
        <AdminSelect v-model="period" :items="periodItems" style="width: 150px" />
      </div>
    </div>

    <p v-if="!filtered.length" class="admin-note">Нет данных о выручке за выбранный период.</p>
    <template v-else>
      <svg
        class="chart"
        :viewBox="`0 0 ${W} ${H}`"
        preserveAspectRatio="none"
        role="img"
        aria-label="График выручки по дням"
      >
        <line x1="0" :y1="H - 0.5" :x2="W" :y2="H - 0.5" class="grid" />
        <line x1="0" :y1="H * 0.5" :x2="W" :y2="H * 0.5" class="grid" />
        <line x1="0" y1="4.5" :x2="W" y2="4.5" class="grid" />
        <rect
          v-for="(bar, i) in bars"
          :key="i"
          :x="bar.x"
          :y="bar.y"
          :width="bar.w"
          :height="bar.h"
          rx="1.5"
          class="bar"
        >
          <title>{{ fmtShortDate(bar.date) }}: {{ fmtMoney(bar.value) }}</title>
        </rect>
      </svg>
      <div class="chart-axis">
        <span>{{ firstDate }}</span>
        <span>макс {{ fmtMoney(maxY) }}</span>
        <span>{{ lastDate }}</span>
      </div>
    </template>
  </section>
</template>

<style scoped>
.chart-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.chart-title {
  display: grid;
  gap: 4px;
}
.chart-title h2 {
  margin: 0;
}
.chart-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}
.chart {
  display: block;
  width: 100%;
  height: 150px;
}
.grid {
  stroke: var(--adm-border, #232c3d);
  stroke-width: 1;
  stroke-dasharray: 3 4;
}
.bar {
  fill: var(--adm-accent, #3b82f6);
  opacity: 0.85;
}
.bar:hover {
  opacity: 1;
}
.chart-axis {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--adm-muted, #8b95a8);
}
</style>
