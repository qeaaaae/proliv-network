<script setup lang="ts">
interface Squad {
  uuid: string
  name: string
  members_count?: number | string | null
  active_inbounds_count?: number | string | null
}
interface NodeRow {
  key: string
  label: string
  countryCode: string | null
  online: number | null
  bytes: number
}

const props = defineProps<{
  squads: Squad[] | null
  squadsError: string
  panel: Record<string, unknown> | null
  loading: boolean
}>()
const emit = defineEmits<{ refresh: [] }>()

function isRec(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}
function rows(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter(isRec) : []
}
function str(...values: unknown[]): string {
  for (const v of values) {
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  return ''
}
function toNum(value: unknown): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}
function usersOnline(node: Record<string, unknown>): number | null {
  const raw =
    node.usersOnline ??
    node.users_online ??
    node.onlineUsers ??
    node.online_users ??
    node.onlineUserCount ??
    node.connectedUsers ??
    node.onlineNow
  const n = Number(raw)
  if (Number.isFinite(n)) return n
  const groups = node.metricGroups
  if (isRec(groups)) {
    const g = Number(groups.onlineUsers ?? groups.online_users)
    if (Number.isFinite(g)) return g
  }
  return null
}
function nodeUuid(node: Record<string, unknown>): string {
  const raw = node.uuid ?? node.nodeUuid ?? node.node_uuid ?? node.id
  return raw != null ? String(raw) : ''
}
function trafficBytes(node: Record<string, unknown>): number {
  const total = Number(node.total ?? node.bytes ?? node.value)
  if (Number.isFinite(total) && total > 0) return total
  let bytes = 0
  for (const key of ['inboundsStats', 'outboundsStats', 'inbounds_stats', 'outbounds_stats']) {
    for (const item of rows(node[key])) {
      const combined = Number(item.total ?? item.bytes ?? item.value)
      if (Number.isFinite(combined) && combined > 0) {
        bytes += combined
        continue
      }
      const up = Number(item.uplink ?? item.upload ?? item.uploadBytes ?? item.up ?? item.tx)
      const down = Number(item.downlink ?? item.download ?? item.downloadBytes ?? item.down ?? item.rx)
      bytes += (Number.isFinite(up) ? up : 0) + (Number.isFinite(down) ? down : 0)
    }
  }
  if (bytes <= 0) {
    const up = Number(node.uplink ?? node.uploadBytes ?? node.upload ?? node.up)
    const down = Number(node.downlink ?? node.downloadBytes ?? node.download ?? node.down)
    bytes = (Number.isFinite(up) ? up : 0) + (Number.isFinite(down) ? down : 0)
  }
  if (bytes <= 0) {
    const life = Number(node.totalBytesLifetime ?? node.totalBytes ?? node.bytesLifetime)
    if (Number.isFinite(life) && life > 0) bytes = life
  }
  return bytes
}
function extractNodes(raw: unknown): Record<string, unknown>[] {
  if (Array.isArray(raw)) return rows(raw)
  if (!isRec(raw)) return []
  for (const key of ['nodes', 'items', 'data', 'response', 'lastSevenDays']) {
    if (Array.isArray(raw[key])) return rows(raw[key])
  }
  return []
}

// Приоритет - nodes_bandwidth.topNodes (имя + трафик + онлайн), затем panel.nodes.
const nodeRows = computed<NodeRow[]>(() => {
  const panel = props.panel
  if (!isRec(panel)) return []
  const bw = isRec(panel.nodes_bandwidth) ? panel.nodes_bandwidth : null
  const source = rows(bw?.topNodes).length
    ? rows(bw?.topNodes)
    : rows(bw?.series).length
      ? rows(bw?.series)
      : extractNodes(panel.nodes)
  return source
    .map((node) => {
      const uuid = nodeUuid(node)
      const label =
        str(node.name, node.nodeName, node.node_name, node.label, node.title, node.hostname) ||
        (uuid ? `${uuid.slice(0, 8)}...` : '-')
      return {
        key: uuid || label,
        label,
        countryCode: str(node.countryCode, node.country_code) || null,
        online: usersOnline(node),
        bytes: trafficBytes(node),
      }
    })
    .sort((a, b) => b.bytes - a.bytes)
})

function flag(cc: string | null): string {
  const code = (cc || '').toUpperCase()
  if (code.length !== 2 || !/^[A-Z]{2}$/.test(code)) return ''
  return String.fromCodePoint(...[...code].map((c) => 0x1f1e6 + c.charCodeAt(0) - 65))
}
function fmtBytes(bytes: number): string {
  if (!bytes || bytes <= 0) return '0 GB'
  const gb = bytes / 1073741824
  const formatted = gb >= 10 ? gb.toFixed(1) : gb.toFixed(2)
  return `${formatted.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1')} GB`
}
function fmtCount(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '-'
  const n = Number(value)
  return Number.isFinite(n) ? n.toLocaleString('ru-RU') : String(value)
}
</script>

<template>
  <section class="admin-card">
    <div class="admin-row card-head">
      <h2>Ноды и сквады</h2>
      <button class="admin-btn ghost" :disabled="loading" @click="emit('refresh')">
        {{ loading ? 'Обновление...' : 'Обновить' }}
      </button>
    </div>

    <h3 class="sys-sub">Ноды панели (трафик за 7 дней)</h3>
    <p v-if="!nodeRows.length" class="admin-note">
      {{ loading ? 'Загрузка...' : 'Нет данных - панель не вернула статистику нод.' }}
    </p>
    <table v-else class="admin-table">
      <thead>
        <tr>
          <th>Нода</th>
          <th>Онлайн</th>
          <th>Трафик</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="node in nodeRows" :key="node.key">
          <td>
            {{ flag(node.countryCode) }} {{ node.label }}
            <AdminBadge v-if="node.countryCode" tone="muted">{{ node.countryCode }}</AdminBadge>
          </td>
          <td>
            <AdminBadge v-if="node.online !== null" :tone="node.online > 0 ? 'success' : 'muted'">
              {{ node.online }}
            </AdminBadge>
            <span v-else class="admin-note">-</span>
          </td>
          <td>{{ fmtBytes(node.bytes) }}</td>
        </tr>
      </tbody>
    </table>

    <h3 class="sys-sub">Внутренние сквады</h3>
    <p v-if="squadsError" class="admin-note admin-error">{{ squadsError }}</p>
    <p v-else-if="!squads || !squads.length" class="admin-note">
      {{ loading ? 'Загрузка...' : 'Нет данных - панель не вернула сквады.' }}
    </p>
    <table v-else class="admin-table">
      <thead>
        <tr>
          <th>Сквад</th>
          <th>Участников</th>
          <th>Активных инбаундов</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="squad in squads" :key="squad.uuid">
          <td>{{ squad.name }}</td>
          <td>{{ fmtCount(squad.members_count) }}</td>
          <td>{{ fmtCount(squad.active_inbounds_count) }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.card-head {
  justify-content: space-between;
}
.sys-sub {
  margin: 4px 0 0;
  font-size: 14px;
}
</style>
