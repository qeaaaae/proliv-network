<script setup lang="ts">
import SupportTicketList from '~/components/admin/support/SupportTicketList.vue'
import SupportTicketThread from '~/components/admin/support/SupportTicketThread.vue'

// Админка 'Поддержка': тикеты поддержки из minishop admin API
// (BFF-прокси /api/admin/* -> shop /api/admin/*, см. useAdminApi).
// Эндпоинты:
//   GET support/stats    -> { stats: { open, awaiting_admin, awaiting_user, active, closed, total, total_unread_admin } }
//   GET support/tickets  ?status&priority&category&search&sort&limit&offset
//   (тред/ответ/статусы - в components/admin/support/SupportTicketThread.vue)
interface SupportTicketUser {
  user_id?: number | null
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

interface SupportStats {
  open: number
  awaiting_admin: number
  awaiting_user: number
  active: number
  closed: number
  total: number
  total_unread_admin: number
}

const { call } = useAdminApi()

const stats = ref<SupportStats | null>(null)
const tickets = ref<SupportTicketRow[]>([])
const loadingList = ref(false)
const listError = ref('')
const hasMore = ref(false)
const selectedId = ref<number | null>(null)

const search = ref('')
const fStatus = ref('active')
const fPriority = ref('')
const fCategory = ref('')
const fSort = ref('updated_desc')

const PAGE_SIZE = 50

const statusItems = [
  { value: 'active', label: 'Активные' },
  { value: 'all', label: 'Все' },
  { value: 'open', label: 'Новые' },
  { value: 'awaiting_admin', label: 'Ждут ответа' },
  { value: 'awaiting_user', label: 'Ждут клиента' },
  { value: 'resolved', label: 'Решённые' },
  { value: 'closed', label: 'Закрытые' },
]

const priorityItems = [
  { value: '', label: 'Все приоритеты' },
  { value: 'urgent', label: 'Срочный' },
  { value: 'high', label: 'Высокий' },
  { value: 'normal', label: 'Обычный' },
  { value: 'low', label: 'Низкий' },
]

const categoryItems = [
  { value: '', label: 'Все категории' },
  { value: 'billing', label: 'Оплата' },
  { value: 'technical', label: 'Техническая' },
  { value: 'account', label: 'Аккаунт' },
  { value: 'other', label: 'Другое' },
]

const sortItems = [
  { value: 'updated_desc', label: 'Сначала активные' },
  { value: 'updated_asc', label: 'Давно без ответа' },
  { value: 'importance_desc', label: 'По важности ↓' },
  { value: 'importance_asc', label: 'По важности ↑' },
  { value: 'created_desc', label: 'Сначала новые' },
  { value: 'created_asc', label: 'Сначала старые' },
]

function errText(e: unknown): string {
  const err = e as { code?: string; message?: string }
  const code = err.code || err.message || ''
  const map: Record<string, string> = {
    request_failed: 'Ошибка запроса',
    not_found: 'Не найдено',
  }
  return map[code] || code || 'Ошибка загрузки'
}

async function loadStats() {
  try {
    const res = await call<{ stats: SupportStats }>('support/stats')
    stats.value = res.stats
  } catch {
    stats.value = null
  }
}

async function loadTickets(reset: boolean) {
  loadingList.value = true
  listError.value = ''
  try {
    const offset = reset ? 0 : tickets.value.length
    const res = await call<{ tickets: SupportTicketRow[] }>('support/tickets', {
      query: {
        status: fStatus.value,
        priority: fPriority.value,
        category: fCategory.value,
        search: search.value.trim(),
        sort: fSort.value,
        limit: PAGE_SIZE,
        offset,
      },
    })
    const batch = res.tickets || []
    tickets.value = reset ? batch : [...tickets.value, ...batch]
    hasMore.value = batch.length >= PAGE_SIZE
  } catch (e) {
    listError.value = errText(e)
    if (reset) tickets.value = []
  } finally {
    loadingList.value = false
  }
}

function reloadAll() {
  loadStats()
  loadTickets(true)
}

function onSelect(id: number) {
  selectedId.value = id
}

function onThreadUpdated() {
  // Непрочитанное сброшено / статус сменился - обновляем список и статистику
  loadStats()
  loadTickets(true)
}

watch([fStatus, fPriority, fCategory, fSort], () => loadTickets(true))

onMounted(reloadAll)
</script>

<template>
  <main class="admin-page support-page">
    <div class="support-head">
      <h1 class="support-title">Поддержка</h1>
      <button type="button" class="admin-btn ghost" @click="reloadAll">Обновить</button>
    </div>

    <div v-if="stats" class="admin-grid cols-3">
      <div class="admin-kpi">
        <small>Активные</small>
        <strong>{{ stats.active }}</strong>
      </div>
      <div class="admin-kpi">
        <small>Ждут ответа</small>
        <strong :class="{ 'admin-error': stats.awaiting_admin > 0 }">{{ stats.awaiting_admin }}</strong>
      </div>
      <div class="admin-kpi">
        <small>Непрочитано</small>
        <strong :class="{ 'admin-error': stats.total_unread_admin > 0 }">{{ stats.total_unread_admin }}</strong>
      </div>
    </div>

    <section class="admin-card">
      <div class="filters">
        <AdminSelect v-model="fStatus" :items="statusItems" />
        <AdminSelect v-model="fPriority" :items="priorityItems" />
        <AdminSelect v-model="fCategory" :items="categoryItems" />
        <AdminSelect v-model="fSort" :items="sortItems" />
      </div>
      <div class="admin-row">
        <input
          v-model="search"
          class="admin-input"
          placeholder="Поиск: тема, @username, имя, email"
          @keyup.enter="loadTickets(true)"
        />
        <button type="button" class="admin-btn ghost" :disabled="loadingList" @click="loadTickets(true)">
          Найти
        </button>
      </div>
    </section>

    <div class="support-split">
      <section class="admin-card list-card">
        <SupportTicketList
          :tickets="tickets"
          :selected-id="selectedId"
          :loading="loadingList"
          :error="listError"
          @select="onSelect"
        />
        <button
          v-if="hasMore"
          type="button"
          class="admin-btn ghost"
          :disabled="loadingList"
          @click="loadTickets(false)"
        >
          Показать ещё
        </button>
      </section>

      <section class="admin-card thread-card">
        <SupportTicketThread
          v-if="selectedId !== null"
          :ticket-id="selectedId"
          @updated="onThreadUpdated"
          @close="selectedId = null"
        />
        <p v-else class="admin-note">Выберите тикет из списка, чтобы открыть переписку.</p>
      </section>
    </div>
  </main>
</template>

<style scoped>
.support-page {
  max-width: 1100px;
}
.support-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.support-title {
  margin: 0;
  font-size: 20px;
}
.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
}
.support-split {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
  align-items: start;
}
.list-card,
.thread-card {
  min-width: 0;
}
.list-card {
  max-height: 70dvh;
  overflow-y: auto;
  overflow-x: hidden;
}
@media (max-width: 860px) {
  .support-split {
    grid-template-columns: 1fr;
  }
  .list-card {
    max-height: none;
  }
}
</style>
