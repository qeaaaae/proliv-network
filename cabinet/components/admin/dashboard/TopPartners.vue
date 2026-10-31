<script setup lang="ts">
type BadgeTone = 'default' | 'success' | 'warning' | 'danger' | 'muted'

interface PartnerRow {
  partner_id: number
  user_id?: number | null
  display_label: string
  username?: string | null
  status: string
  kind?: string
  clients_count?: number
}

const props = defineProps<{
  partners: PartnerRow[]
  total: number | null
  loadFailed?: boolean
}>()

const { plural } = useFormat()

const kindLabels: Record<string, string> = {
  standard: 'Партнёр',
  streamer: 'Стример',
  clipper: 'Нарезчик',
}

const statusMeta: Record<string, { tone: BadgeTone; label: string }> = {
  active: { tone: 'success', label: 'Активен' },
  paused: { tone: 'warning', label: 'Пауза' },
  closed: { tone: 'muted', label: 'Закрыт' },
  pending: { tone: 'muted', label: 'Ожидает' },
}

function statusOf(p: PartnerRow): { tone: BadgeTone; label: string } {
  return statusMeta[p.status] || { tone: 'muted', label: p.status }
}

function subLabel(p: PartnerRow): string {
  const who = p.username ? `@${p.username}` : p.user_id ? `#${p.user_id}` : `id ${p.partner_id}`
  const kind = kindLabels[p.kind || 'standard'] || p.kind || 'Партнёр'
  const clients = Number(p.clients_count) || 0
  return `${who} · ${kind} · ${clients} ${plural(clients, 'клиент', 'клиента', 'клиентов')}`
}
</script>

<template>
  <section class="admin-card">
    <div class="tp-head">
      <h2>Топ партнёров</h2>
      <AdminBadge v-if="total !== null">{{ total }}</AdminBadge>
    </div>
    <p v-if="props.loadFailed" class="admin-note">Не удалось загрузить список партнёров.</p>
    <p v-else-if="!partners.length" class="admin-note">Партнёров пока нет.</p>
    <ul v-else class="admin-list">
      <li v-for="p in partners" :key="p.partner_id">
        <NuxtLink class="admin-list-item tp-item" to="/admin/partners">
          <div class="tp-main">
            <strong>{{ p.display_label }}</strong>
            <AdminBadge :tone="statusOf(p).tone">{{ statusOf(p).label }}</AdminBadge>
          </div>
          <span>{{ subLabel(p) }}</span>
        </NuxtLink>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.tp-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.tp-head h2 {
  margin: 0;
}
.tp-item {
  text-decoration: none;
}
.tp-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
</style>
