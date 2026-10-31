<script setup lang="ts">
type BadgeTone = 'default' | 'success' | 'warning' | 'danger' | 'muted'

interface PanelSyncInfo {
  status: string
  last_sync_time?: string | null
  users_processed?: number
  subscriptions_synced?: number
}

const props = defineProps<{
  panel: Record<string, unknown> | null
  sync: PanelSyncInfo | null
}>()

function rec(v: unknown): Record<string, unknown> | null {
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null
}

function num(v: unknown): number | null {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function fmt(v: unknown): string {
  const n = num(v)
  return n === null ? '—' : new Intl.NumberFormat('ru-RU').format(n)
}

const failed = computed(() => !props.panel || Boolean(rec(props.panel)?.error))
const system = computed(() => (props.panel ? rec(props.panel.system) : null))
const panelUsers = computed(() => (system.value ? rec(system.value.users) : null))
const statusCounts = computed(() => (panelUsers.value ? rec(panelUsers.value.statusCounts) : null))
const onlineStats = computed(() => (system.value ? rec(system.value.onlineStats) : null))
const memory = computed(() => (system.value ? rec(system.value.memory) : null))

const memPct = computed(() => {
  const total = num(memory.value?.total)
  const used = num(memory.value?.used)
  if (!total || total <= 0 || used === null) return null
  return Math.round((used / total) * 1000) / 10
})

const cpuPct = computed(() => {
  const cpu = system.value ? rec(system.value.cpu) : null
  const raw =
    cpu?.usage ??
    cpu?.usedPercent ??
    cpu?.percent ??
    system.value?.cpuUsage ??
    system.value?.cpuLoad
  return num(raw)
})

const bwWeek = computed(() => {
  const bw = props.panel ? rec(props.panel.bandwidth) : null
  const v = bw ? rec(bw.bandwidthLastSevenDays)?.current : null
  return v === null || v === undefined ? null : String(v)
})

const bwMonth = computed(() => {
  const bw = props.panel ? rec(props.panel.bandwidth) : null
  if (!bw) return null
  const v =
    rec(bw.bandwidthLast30Days)?.current ?? rec(bw.bandwidthLastThirtyDays)?.current ?? null
  return v === null || v === undefined ? null : String(v)
})

const tiles = computed(() => {
  if (failed.value || !system.value) return []
  const counts = statusCounts.value || {}
  const items: { label: string; value: string }[] = [
    { label: 'Онлайн сейчас', value: fmt(onlineStats.value?.onlineNow) },
    { label: 'Активных', value: fmt(counts.ACTIVE) },
    { label: 'Всего в панели', value: fmt(panelUsers.value?.totalUsers) },
    { label: 'Истекло', value: fmt(counts.EXPIRED) },
    { label: 'Отключено', value: fmt(counts.DISABLED) },
    { label: 'Лимит трафика', value: fmt(counts.LIMITED) },
  ]
  if (memPct.value !== null) items.push({ label: 'Память', value: `${memPct.value}%` })
  if (cpuPct.value !== null) items.push({ label: 'CPU', value: `${cpuPct.value}%` })
  if (bwWeek.value !== null) items.push({ label: 'Трафик за 7 дней', value: bwWeek.value })
  if (bwMonth.value !== null) items.push({ label: 'Трафик за 30 дней', value: bwMonth.value })
  return items.filter((item) => item.value !== '—')
})

const syncMeta = computed(() => {
  const s = props.sync
  if (!s) return null
  const map: Record<string, { tone: BadgeTone; label: string }> = {
    success: { tone: 'success', label: 'Успешно' },
    failed: { tone: 'danger', label: 'Ошибка' },
    never_run: { tone: 'muted', label: 'Не запускалась' },
    running: { tone: 'warning', label: 'Выполняется' },
  }
  const meta = map[s.status] || { tone: 'muted' as BadgeTone, label: s.status }
  return {
    ...meta,
    time: s.last_sync_time,
    processed: num(s.users_processed),
    subs: num(s.subscriptions_synced),
  }
})

function fmtDateTime(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <section class="admin-card">
    <div class="panel-head">
      <h2>Панель Remnawave</h2>
      <AdminBadge v-if="syncMeta" :tone="syncMeta.tone">
        синхронизация: {{ syncMeta.label }}
      </AdminBadge>
    </div>
    <p v-if="failed" class="admin-note">Данные панели недоступны.</p>
    <div v-else class="tiles">
      <div v-for="t in tiles" :key="t.label" class="tile">
        <span class="tile-label">{{ t.label }}</span>
        <strong class="tile-value">{{ t.value }}</strong>
      </div>
      <p v-if="!tiles.length" class="admin-note">Нет метрик панели.</p>
    </div>
    <p v-if="syncMeta" class="admin-note">
      Последняя синхронизация: {{ fmtDateTime(syncMeta.time) }}
      <template v-if="syncMeta.processed !== null">
        · пользователей: {{ syncMeta.processed }}
      </template>
      <template v-if="syncMeta.subs !== null"> · подписок: {{ syncMeta.subs }} </template>
    </p>
  </section>
</template>

<style scoped>
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.panel-head h2 {
  margin: 0;
}
.tiles {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 8px;
}
.tile {
  display: grid;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--adm-border, #232c3d);
  background: var(--adm-card-2, #1a2231);
}
.tile-label {
  font-size: 11px;
  color: var(--adm-muted, #8b95a8);
}
.tile-value {
  font-size: 16px;
  font-variant-numeric: tabular-nums;
}
</style>
