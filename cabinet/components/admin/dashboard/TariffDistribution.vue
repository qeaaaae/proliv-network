<script setup lang="ts">
interface TariffRow {
  kind: string
  tariff_key?: string | null
  tariff_names?: Record<string, string>
  is_configured?: boolean
  is_enabled?: boolean | null
  active_users: number
}

const props = defineProps<{
  tariffs: TariffRow[]
}>()

/* Семантические цвета: платный тариф - акцент/палитра, триал - янтарный,
   отключённый/без тарифа - приглушённый серый. */
const PAID_PALETTE = ['#7dd3fc', '#6ee7b7', '#a78bfa', '#38bdf8', '#f472b6']
const TRIAL_COLOR = '#fbbf24'
const OFF_COLOR = '#3d4553'

function tariffLabel(t: TariffRow): string {
  if (t.kind === 'trial') return 'Триал'
  if (t.kind === 'unassigned' || !t.tariff_key) return 'Без тарифа'
  const names = t.tariff_names || {}
  return names.ru || names.en || Object.values(names).find(Boolean) || t.tariff_key
}

const total = computed(() =>
  props.tariffs.reduce((sum, t) => sum + (Number(t.active_users) || 0), 0),
)

const paidTotal = computed(() =>
  rows.value
    .filter((row) => row.paid)
    .reduce((sum, row) => sum + row.count, 0),
)

const rows = computed(() => {
  let paidIndex = 0
  return [...props.tariffs]
    .map((t) => {
      const inactive = t.is_enabled === false || t.is_configured === false
      const trial = t.kind === 'trial'
      const unassigned = t.kind === 'unassigned' || !t.tariff_key
      const paid = !inactive && !trial && !unassigned
      const color = inactive || unassigned
        ? OFF_COLOR
        : trial
          ? TRIAL_COLOR
          : PAID_PALETTE[paidIndex++ % PAID_PALETTE.length]
      return {
        key: `${t.kind}:${t.tariff_key || ''}`,
        label: tariffLabel(t),
        count: Number(t.active_users) || 0,
        inactive,
        trial,
        paid,
        color,
      }
    })
    .sort((a, b) => Number(b.paid) - Number(a.paid) || b.count - a.count)
})

function pct(count: number): number {
  return total.value > 0 ? (count / total.value) * 100 : 0
}
</script>

<template>
  <section class="admin-card">
    <div class="td-head">
      <h2>Подписки по тарифам</h2>
      <AdminBadge>{{ total }}</AdminBadge>
    </div>
    <p v-if="!rows.length || !total" class="admin-note">Нет активных подписок.</p>
    <template v-else>
      <div class="td-stack" aria-hidden="true">
        <div
          v-for="row in rows"
          :key="row.key"
          class="td-seg"
          :style="{ width: `${pct(row.count)}%`, background: row.color }"
          :title="`${row.label}: ${row.count} (${pct(row.count).toFixed(0)}%)`"
        >
          <span v-if="pct(row.count) >= 14" class="td-seg-num">{{ row.count }}</span>
        </div>
      </div>
      <div class="td-legend">
        <div v-for="row in rows" :key="row.key" class="td-legend-row">
          <span class="td-dot" :style="{ background: row.color }" />
          <span class="td-label">
            {{ row.label }}
            <span v-if="row.inactive" class="td-off">выкл</span>
          </span>
          <span class="td-count">
            <strong>{{ row.count }}</strong>
            <span class="td-pct">{{ pct(row.count).toFixed(0) }}%</span>
          </span>
        </div>
      </div>
      <p class="td-summary">
        Платят {{ paidTotal }} из {{ total }} ({{ pct(paidTotal).toFixed(0) }}%)
      </p>
    </template>
  </section>
</template>

<style scoped>
.td-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.td-head h2 {
  margin: 0;
}
.td-stack {
  display: flex;
  gap: 3px;
  height: 26px;
  border-radius: var(--radius-pill, 999px);
  overflow: hidden;
  background: var(--adm-card-2, #1a1e24);
  padding: 4px;
}
.td-seg {
  position: relative;
  display: grid;
  place-items: center;
  border-radius: var(--radius-pill, 999px);
  min-width: 0;
  transition: width 0.3s var(--ease, ease);
}
.td-seg-num {
  font-size: 12px;
  font-weight: 700;
  color: rgba(6, 20, 30, 0.85);
  font-variant-numeric: tabular-nums;
}
.td-legend {
  display: grid;
  gap: 2px;
}
.td-legend-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
}
.td-legend-row:hover {
  background: var(--adm-card-2, #1a1e24);
}
.td-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.td-label {
  flex: 1;
  font-size: 13px;
  overflow-wrap: anywhere;
}
.td-off {
  margin-left: 6px;
  font-size: 11px;
  color: var(--adm-muted, #8b95a8);
}
.td-count {
  display: flex;
  align-items: baseline;
  gap: 8px;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.td-pct {
  min-width: 4ch;
  text-align: right;
  font-size: 11px;
  color: var(--adm-muted, #8b95a8);
}
.td-summary {
  margin: 0;
  padding-top: 10px;
  border-top: 1px solid var(--adm-border);
  font-size: 12px;
  color: var(--adm-muted);
}
</style>
