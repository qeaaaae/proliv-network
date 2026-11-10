<script setup lang="ts">
interface PanelSync {
  status: string
  last_sync_time: string | null
  details: string | null
  users_processed: number
  subscriptions_synced: number
}

const props = defineProps<{
  sync: PanelSync | null
  queue: Record<string, unknown> | null
  busy: boolean
  notice: string
}>()
import { fmtDateTimeFull, fmtNum } from '~/components/admin/format'

const emit = defineEmits<{ sync: [] }>()

const SYNC_LABELS: Record<string, string> = {
  completed: 'Завершена',
  completed_with_errors: 'Завершена с ошибками',
  success: 'Завершена',
  failed: 'Ошибка',
  running: 'Выполняется',
  queued: 'В очереди',
  never_run: 'Не запускалась',
}

function syncTone(status: string): 'success' | 'warning' | 'danger' | 'muted' | 'default' {
  if (status === 'completed' || status === 'success') return 'success'
  if (status === 'completed_with_errors' || status === 'queued' || status === 'running') return 'warning'
  if (status === 'failed') return 'danger'
  return 'muted'
}
function syncLabel(status: string): string {
  return SYNC_LABELS[status] || status || 'Неизвестно'
}
function fmtDateTime(iso: string | null | undefined): string {
  return fmtDateTimeFull(iso)
}
function num(value: unknown): string {
  return fmtNum(value, '-')
}
const queueRows = computed(() => {
  const q = props.queue
  if (!q) return []
  return [
    {
      label: 'Пользовательская очередь',
      size: q.user_queue_size,
      processing: Boolean(q.user_queue_processing),
      recent: q.user_recent_sends,
      sent: q.user_sent_messages,
      failed: q.user_failed_messages,
    },
    {
      label: 'Групповая очередь',
      size: q.group_queue_size,
      processing: Boolean(q.group_queue_processing),
      recent: q.group_recent_sends,
      sent: q.group_sent_messages,
      failed: q.group_failed_messages,
    },
  ]
})
</script>

<template>
  <section class="admin-card">
    <div class="admin-card-head">
      <h2>Синхронизация и очереди</h2>
      <button class="admin-btn" :disabled="busy" @click="emit('sync')">
        {{ busy ? 'Запуск...' : 'Синхронизировать с панелью' }}
      </button>
    </div>
    <p v-if="notice" class="admin-note">{{ notice }}</p>

    <div class="admin-row">
      <span class="admin-note">Последняя синхронизация:</span>
      <AdminBadge :tone="syncTone(sync?.status || 'never_run')">
        {{ syncLabel(sync?.status || 'never_run') }}
      </AdminBadge>
      <span class="admin-note">{{ fmtDateTime(sync?.last_sync_time) }}</span>
    </div>
    <div v-if="sync && sync.status !== 'never_run'" class="admin-row">
      <span class="admin-note">Обработано пользователей: {{ num(sync.users_processed) }}</span>
      <span class="admin-note">Подписок синхронизировано: {{ num(sync.subscriptions_synced) }}</span>
    </div>
    <p v-if="sync?.details" class="admin-note sys-details">{{ sync.details }}</p>

    <h3 class="admin-sub">Очередь сообщений бота</h3>
    <p v-if="!queue" class="admin-note">Данные очереди недоступны.</p>
    <div v-else class="admin-table-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Очередь</th>
            <th>В очереди</th>
            <th>Обработка</th>
            <th>Отправлено</th>
            <th>Ошибок</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in queueRows" :key="row.label">
            <td>{{ row.label }}</td>
            <td>{{ num(row.size) }}</td>
            <td>
              <AdminBadge :tone="row.processing ? 'success' : 'muted'">
                {{ row.processing ? 'Активна' : 'Ожидает' }}
              </AdminBadge>
            </td>
            <td>{{ num(row.sent) }}</td>
            <td>{{ num(row.failed) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.sys-details {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow: auto;
}
</style>
