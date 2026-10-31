<script setup lang="ts">
interface LogEntry {
  log_id: number
  user_id: number | null
  user_label: string | null
  telegram_username: string | null
  telegram_first_name: string | null
  email: string | null
  event_type: string | null
  content: string | null
  is_admin_event: boolean
  target_user_id: number | null
  target_user_label: string | null
  timestamp: string | null
}
interface LogsResponse {
  logs: LogEntry[]
  page: number
  page_size: number
  total: number
}

const { call } = useAdminApi()

const PAGE_SIZE = 50
const logs = ref<LogEntry[]>([])
const page = ref(0)
const total = ref(0)
const loading = ref(false)
const error = ref('')

const userFilter = ref('')
const userApplied = ref('')
const sort = ref('date_desc')
const kind = ref('all')
const eventType = ref('all')

const sortItems = [
  { value: 'date_desc', label: 'Сначала новые' },
  { value: 'date_asc', label: 'Сначала старые' },
  { value: 'event_asc', label: 'Событие А-Я' },
  { value: 'event_desc', label: 'Событие Я-А' },
  { value: 'user_asc', label: 'Пользователь А-Я' },
  { value: 'user_desc', label: 'Пользователь Я-А' },
]
const kindItems = [
  { value: 'all', label: 'Все события' },
  { value: 'admin', label: 'Админские' },
  { value: 'user', label: 'Пользовательские' },
]

const eventTypeItems = computed(() => {
  const types = new Set<string>()
  for (const entry of logs.value) {
    if (entry.event_type) types.add(entry.event_type)
  }
  return [{ value: 'all', label: 'Все типы' }, ...[...types].sort().map((t) => ({ value: t, label: t }))]
})

const visibleLogs = computed(() =>
  logs.value.filter((entry) => {
    if (kind.value === 'admin' && !entry.is_admin_event) return false
    if (kind.value === 'user' && entry.is_admin_event) return false
    if (eventType.value !== 'all' && entry.event_type !== eventType.value) return false
    return true
  }),
)
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

function errText(e: unknown): string {
  const code = (e as { code?: string })?.code
  if (code === 'invalid_user_id') return 'Некорректный user_id'
  const msg = (e as Error)?.message
  return msg && msg !== 'request_failed' ? msg : 'Ошибка загрузки'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await call<LogsResponse>('logs', {
      query: {
        page: page.value,
        page_size: PAGE_SIZE,
        sort: sort.value,
        user_id: userApplied.value || undefined,
      },
    })
    logs.value = res.logs || []
    total.value = Number(res.total) || 0
    if (page.value >= pageCount.value) page.value = Math.max(0, pageCount.value - 1)
  } catch (e) {
    error.value = errText(e)
    logs.value = []
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  const raw = userFilter.value.trim()
  if (raw && !/^\d+$/.test(raw)) {
    error.value = 'user_id должен быть числом'
    return
  }
  userApplied.value = raw
  page.value = 0
  load()
}
function setPage(next: number) {
  page.value = Math.min(Math.max(0, next), pageCount.value - 1)
  load()
}
watch([sort], () => {
  page.value = 0
  load()
})

function fmtDateTime(iso: string | null): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
function userDisplay(entry: LogEntry, kindOf: 'user' | 'target'): string {
  const label = kindOf === 'target' ? entry.target_user_label : entry.user_label
  if (label) return label
  if (kindOf === 'user') {
    if (entry.telegram_first_name) return entry.telegram_first_name
    if (entry.telegram_username) {
      const name = String(entry.telegram_username)
      return name.startsWith('@') ? name : `@${name}`
    }
    if (entry.email) return entry.email
  }
  const id = kindOf === 'target' ? entry.target_user_id : entry.user_id
  return id ? `#${id}` : '-'
}

onMounted(load)
</script>

<template>
  <section class="admin-card">
    <div class="admin-row card-head">
      <h2>Логи</h2>
      <span class="admin-note">Всего: {{ total.toLocaleString('ru-RU') }}</span>
      <button class="admin-btn ghost" :disabled="loading" @click="load">
        {{ loading ? 'Обновление...' : 'Обновить' }}
      </button>
    </div>

    <form class="sys-filters" @submit.prevent="applyFilters">
      <input
        v-model="userFilter"
        class="admin-input"
        type="search"
        inputmode="numeric"
        placeholder="user_id"
        aria-label="Фильтр по user_id"
      />
      <AdminSelect v-model="sort" :items="sortItems" />
      <AdminSelect v-model="kind" :items="kindItems" />
      <AdminSelect v-model="eventType" :items="eventTypeItems" placeholder="Тип события" />
      <button class="admin-btn" type="submit" :disabled="loading">Применить</button>
    </form>

    <p v-if="error" class="admin-note admin-error">{{ error }}</p>
    <p v-else-if="loading && !logs.length" class="admin-note">Загрузка...</p>
    <p v-else-if="!visibleLogs.length" class="admin-note">Записей нет</p>

    <div v-else class="sys-logs-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Событие</th>
            <th>Пользователь</th>
            <th>Цель</th>
            <th>Содержимое</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in visibleLogs" :key="entry.log_id">
            <td class="sys-nowrap">{{ fmtDateTime(entry.timestamp) }}</td>
            <td>
              <span class="sys-mono">{{ entry.event_type || '-' }}</span>
              <AdminBadge v-if="entry.is_admin_event" tone="warning">admin</AdminBadge>
            </td>
            <td>{{ userDisplay(entry, 'user') }}</td>
            <td>{{ userDisplay(entry, 'target') }}</td>
            <td class="sys-content">{{ entry.content || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="admin-row">
      <button class="admin-btn ghost" :disabled="loading || page <= 0" @click="setPage(page - 1)">
        Назад
      </button>
      <span class="admin-note">Страница {{ page + 1 }} из {{ pageCount }}</span>
      <button
        class="admin-btn ghost"
        :disabled="loading || page >= pageCount - 1"
        @click="setPage(page + 1)"
      >
        Вперёд
      </button>
    </div>
  </section>
</template>

<style scoped>
.card-head {
  justify-content: space-between;
}
.sys-filters {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) repeat(3, minmax(140px, 1fr)) auto;
  gap: 8px;
  align-items: center;
}
.sys-logs-wrap {
  overflow-x: auto;
}
.sys-nowrap {
  white-space: nowrap;
}
.sys-mono {
  font-family: monospace;
  font-size: 12px;
}
.sys-content {
  max-width: 340px;
  word-break: break-word;
  white-space: pre-wrap;
}
@media (max-width: 720px) {
  .sys-filters {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
