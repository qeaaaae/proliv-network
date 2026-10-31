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

const PALETTE = ['#7dd3fc', '#6ee7b7', '#fbbf24', '#a78bfa', '#ff8587', '#38bdf8']
const MUTED = '#3d4553'

function tariffLabel(t: TariffRow): string {
  if (t.kind === 'trial') return 'Триал'
  if (t.kind === 'unassigned' || !t.tariff_key) return 'Без тарифа'
  const names = t.tariff_names || {}
  return names.ru || names.en || Object.values(names).find(Boolean) || t.tariff_key
}

const total = computed(() =>
  props.tariffs.reduce((sum, t) => sum + (Number(t.active_users) || 0), 0),
)

const rows = computed(() =>
  [...props.tariffs]
    .map((t) => ({
      key: `${t.kind}:${t.tariff_key || ''}`,
      label: tariffLabel(t),
      count: Number(t.active_users) || 0,
      inactive: t.is_enabled === false || t.is_configured === false,
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, 'ru'))
    .map((row, i) => ({ ...row, color: row.inactive ? MUTED : PALETTE[i % PALETTE.length] })),
)

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
        />
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
  height: 16px;
  border-radius: var(--radius-pill, 999px);
  overflow: hidden;
  background: var(--adm-card-2, #1a1e24);
  padding: 3px;
}
.td-seg {
  border-radius: var(--radius-pill, 999px);
  min-width: 0;
  transition: width 0.3s var(--ease, ease);
}
.td-legend {
  display: grid;
  gap: 4px;
}
.td-legend-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 10px;
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
</style>
