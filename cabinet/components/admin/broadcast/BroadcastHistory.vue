<script setup lang="ts">
import AdminBadge from '~/components/admin/AdminBadge.vue'
import AdminModal from '~/components/admin/AdminModal.vue'

interface BroadcastItem {
  broadcast_id: number
  status: string
  target: string
  channels: string[]
  texts: Record<string, string>
  scheduled_at: string
  created_at: string
  finished_at: string | null
  recipient_count: number
  total_deliveries: number
  successful_deliveries: number
  failed_deliveries: number
  telegram_sent: number
  telegram_failed: number
  last_error: string | null
}

interface BroadcastsResponse {
  ok: boolean
  broadcasts: BroadcastItem[]
}

const STATUS_LABELS: Record<string, string> = {
  scheduled: 'Запланирована',
  queued: 'В очереди',
  running: 'Отправляется',
  completed: 'Доставлена',
  completed_with_errors: 'С ошибками',
  failed: 'Ошибка',
  cancelled: 'Отменена',
}

const STATUS_TONES: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'muted'> = {
  scheduled: 'default',
  queued: 'warning',
  running: 'warning',
  completed: 'success',
  completed_with_errors: 'warning',
  failed: 'danger',
  cancelled: 'muted',
}

const TARGET_LABELS: Record<string, string> = {
  all: 'Все',
  active: 'С подпиской',
  inactive: 'Без подписки',
  expired: 'Истекла',
  active_never_connected: 'Не подключались',
  never: 'Без истории подписки',
  admins: 'Админы',
}

const { call } = useAdminApi()
const toast = useToast()

const items = ref<BroadcastItem[]>([])
const loading = ref(true)
const deleting = ref<BroadcastItem | null>(null)
const deleteBusy = ref(false)

async function reload() {
  loading.value = true
  try {
    const res = await call<BroadcastsResponse>('broadcasts')
    items.value = res.broadcasts || []
  } catch {
    toast.push('Не удалось загрузить историю рассылок', 'error')
  } finally {
    loading.value = false
  }
}

defineExpose({ reload })

function previewText(item: BroadcastItem): string {
  const text = Object.values(item.texts || {})[0] || ''
  return text.length > 80 ? `${text.slice(0, 80)}…` : text
}

function targetLabel(target: string): string {
  if (target.startsWith('user:')) return `Юзер ${target.slice(5)}`
  if (target.startsWith('tariff:')) return `Тариф ${target.slice(7)}`
  return TARGET_LABELS[target] || target
}

function fmt(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('ru-RU')
}

function isActive(item: BroadcastItem): boolean {
  return ['scheduled', 'queued', 'running'].includes(item.status)
}

async function confirmDelete() {
  if (!deleting.value) return
  deleteBusy.value = true
  try {
    await call(`broadcasts/${deleting.value.broadcast_id}`, { method: 'DELETE' })
    toast.push(
      isActive(deleting.value)
        ? `Рассылка #${deleting.value.broadcast_id} отменена`
        : `Рассылка #${deleting.value.broadcast_id} удалена`,
    )
    deleting.value = null
    await reload()
  } catch {
    toast.push('Не удалось удалить рассылку', 'error')
  } finally {
    deleteBusy.value = false
  }
}

onMounted(reload)
</script>

<template>
  <section class="admin-card">
    <h2>История рассылок</h2>
    <p v-if="loading" class="admin-note">Загрузка...</p>
    <p v-else-if="!items.length" class="admin-note">Рассылок пока не было.</p>
    <div v-else class="bc-table-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Дата</th>
            <th>Аудитория</th>
            <th>Текст</th>
            <th>Статус</th>
            <th>Доставка</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.broadcast_id">
            <td>{{ item.broadcast_id }}</td>
            <td>{{ fmt(isActive(item) ? item.scheduled_at : item.created_at) }}</td>
            <td>{{ targetLabel(item.target) }}</td>
            <td class="bc-text" :title="previewText(item)">{{ previewText(item) }}</td>
            <td>
              <AdminBadge :tone="STATUS_TONES[item.status] || 'default'">
                {{ STATUS_LABELS[item.status] || item.status }}
              </AdminBadge>
            </td>
            <td>
              {{ item.successful_deliveries }}/{{ item.total_deliveries || item.recipient_count }}
              <span v-if="item.failed_deliveries" class="admin-error">
                (+{{ item.failed_deliveries }} ош.)
              </span>
            </td>
            <td>
              <button class="admin-btn ghost bc-del" @click="deleting = item">
                {{ isActive(item) ? 'Отменить' : 'Удалить' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="items.some((i) => i.last_error)" class="admin-note">
        Последняя ошибка у выбранных рассылок показывается в столбце статуса на бэкенде.
      </p>
    </div>

    <AdminModal
      :open="Boolean(deleting)"
      :title="deleting && isActive(deleting) ? 'Отменить рассылку?' : 'Удалить рассылку?'"
      @close="deleting = null"
    >
      <p v-if="deleting" class="admin-note">
        #{{ deleting.broadcast_id }} · {{ targetLabel(deleting.target) }} · «{{ previewText(deleting) }}»
      </p>
      <template #footer>
        <button class="admin-btn ghost" :disabled="deleteBusy" @click="deleting = null">Назад</button>
        <button class="admin-btn danger" :disabled="deleteBusy" @click="confirmDelete">
          {{ deleteBusy ? 'Удаление...' : 'Подтвердить' }}
        </button>
      </template>
    </AdminModal>
  </section>
</template>

<style scoped>
.bc-table-wrap {
  overflow-x: auto;
}
.bc-text {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bc-del {
  padding: 6px 10px;
  font-size: 12px;
}
</style>
