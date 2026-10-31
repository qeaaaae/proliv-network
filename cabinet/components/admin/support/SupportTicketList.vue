<script setup lang="ts">
// Строка списка тикетов поддержки: статус, приоритет, непрочитанные, юзер.
interface SupportTicketUser {
  user_id?: number | null
  telegram_id?: number | null
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  email?: string | null
}

interface SupportTicketRow {
  ticket_id: number
  user_id: number
  subject: string
  category: string
  priority: string
  status: string
  last_message_at: string | null
  last_message_role: string | null
  unread_admin_count: number
  created_at: string | null
  closed_at: string | null
  user?: SupportTicketUser | Record<string, never>
}

defineProps<{
  tickets: SupportTicketRow[]
  selectedId: number | null
  loading: boolean
  error: string
}>()

const emit = defineEmits<{ select: [id: number] }>()

const statusLabels: Record<string, string> = {
  open: 'Открыт',
  awaiting_admin: 'Ждёт ответа',
  awaiting_user: 'Ждёт клиента',
  resolved: 'Решён',
  closed: 'Закрыт',
}

const priorityLabels: Record<string, string> = {
  low: 'Низкий',
  normal: 'Обычный',
  high: 'Высокий',
  urgent: 'Срочный',
}

function statusTone(status: string): 'default' | 'success' | 'warning' | 'danger' | 'muted' {
  switch (status) {
    case 'open': return 'warning'
    case 'awaiting_admin': return 'danger'
    case 'resolved': return 'success'
    case 'closed': return 'muted'
    default: return 'default'
  }
}

function statusLabel(status: string): string {
  return statusLabels[status] || status
}

function userLabel(user: SupportTicketRow['user'], userId: number): string {
  if (!user) return `user #${userId}`
  const name = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  if (name) return name
  if (user.username) return `@${user.username}`
  if (user.email) return user.email
  return `user #${user.user_id || userId}`
}

function fmtTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <ul class="admin-list">
    <li v-for="t in tickets" :key="t.ticket_id">
      <button
        type="button"
        class="admin-list-item ticket-item"
        :class="{ active: t.ticket_id === selectedId }"
        @click="emit('select', t.ticket_id)"
      >
        <span class="ticket-head">
          <strong class="ticket-subject">#{{ t.ticket_id }} {{ t.subject }}</strong>
          <AdminBadge :tone="statusTone(t.status)">{{ statusLabel(t.status) }}</AdminBadge>
        </span>
        <span class="ticket-meta">
          <span>{{ userLabel(t.user, t.user_id) }}</span>
          <span v-if="t.priority === 'urgent' || t.priority === 'high'" class="ticket-prio">
            {{ priorityLabels[t.priority] || t.priority }}
          </span>
          <span>{{ fmtTime(t.last_message_at || t.created_at) }}</span>
        </span>
        <span v-if="t.unread_admin_count > 0" class="ticket-unread">
          <AdminBadge tone="danger">{{ t.unread_admin_count }} нов.</AdminBadge>
        </span>
      </button>
    </li>
    <li v-if="loading" class="admin-note">Загрузка...</li>
    <li v-else-if="error" class="admin-note admin-error">{{ error }}</li>
    <li v-else-if="!tickets.length" class="admin-note">Тикетов нет</li>
  </ul>
</template>

<style scoped>
.ticket-item {
  position: relative;
}
.ticket-item.active {
  border-color: var(--adm-accent);
  background: var(--adm-accent-soft);
}
.ticket-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.ticket-subject {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ticket-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: var(--adm-muted);
}
.ticket-prio {
  color: var(--adm-warning);
}
.ticket-unread {
  position: absolute;
  right: 10px;
  bottom: 10px;
}
</style>
