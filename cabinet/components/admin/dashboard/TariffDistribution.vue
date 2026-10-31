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
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, 'ru')),
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
    <div v-else class="td-list">
      <div v-for="row in rows" :key="row.key" class="td-row">
        <div class="td-row-top">
          <span class="td-label">
            {{ row.label }}
            <span v-if="row.inactive" class="td-off">выкл</span>
          </span>
          <span class="td-count">
            <strong>{{ row.count }}</strong>
            <span class="td-pct">{{ pct(row.count).toFixed(0) }}%</span>
          </span>
        </div>
        <div class="td-track" aria-hidden="true">
          <div class="td-fill" :style="{ width: `${pct(row.count)}%` }" />
        </div>
      </div>
    </div>
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
.td-list {
  display: grid;
  gap: 8px;
}
.td-row {
  display: grid;
  gap: 6px;
}
.td-row-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.td-label {
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
.td-track {
  height: 4px;
  border-radius: 999px;
  background: var(--adm-card-2, #1a2231);
  overflow: hidden;
}
.td-fill {
  height: 100%;
  border-radius: inherit;
  background: var(--adm-accent, #3b82f6);
}
</style>
