<script setup lang="ts">
import SupportMessageItem from './SupportMessageItem.vue'

// Тред тикета поддержки: переписка, ответ/внутренняя заметка, статус и мета.
// Эндпоинты (minishop admin API через BFF /api/admin/*):
//   GET   support/tickets/{id}          -> { ticket, messages, user_snapshot, peer_typing }
//   POST  support/tickets/{id}/messages { body, is_internal_note }
//   POST  support/tickets/{id}/read     {}
//   POST  support/tickets/{id}/typing   { typing }
//   PATCH support/tickets/{id}          { status|priority|category }
interface SupportTicketUser {
  user_id?: number | null
  telegram_id?: number | null
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  email?: string | null
}

interface SupportTicket {
  ticket_id: number
  user_id: number
  subject: string
  category: string
  priority: string
  status: string
  last_message_at: string | null
  unread_admin_count: number
  created_at: string | null
  closed_at: string | null
  user?: SupportTicketUser | Record<string, never>
}

interface SupportMessage {
  message_id: number
  author_role: string
  author_name?: string | null
  author_label?: string | null
  body: string
  body_format?: string
  buttons?: { label: string; url: string }[]
  image_id?: string | null
  is_internal_note: boolean
  created_at: string | null
  read_by_user_at?: string | null
  connector_source?: string | null
}

interface TicketDetail {
  ticket: SupportTicket
  messages: SupportMessage[]
  user_snapshot: Record<string, unknown>
  peer_typing: boolean
}

const props = defineProps<{ ticketId: number }>()
const emit = defineEmits<{ updated: []; close: [] }>()

const { call } = useAdminApi()

const detail = ref<TicketDetail | null>(null)
const loading = ref(false)
const loadError = ref('')
const busy = ref(false)

const replyBody = ref('')
const isNote = ref(false)
const sending = ref(false)
const sendError = ref('')
const msgBox = ref<HTMLElement>()

const editPriority = ref('')
const editCategory = ref('')

interface ConfirmState {
  status: string
  title: string
  text: string
}
const confirmAction = ref<ConfirmState | null>(null)

const statusLabels: Record<string, string> = {
  open: 'Открыт',
  awaiting_admin: 'Ждёт ответа',
  awaiting_user: 'Ждёт клиента',
  resolved: 'Решён',
  closed: 'Закрыт',
}

const priorityItems = [
  { value: 'low', label: 'Низкий' },
  { value: 'normal', label: 'Обычный' },
  { value: 'high', label: 'Высокий' },
  { value: 'urgent', label: 'Срочный' },
]

const categoryItems = [
  { value: 'billing', label: 'Оплата' },
  { value: 'technical', label: 'Техническая' },
  { value: 'account', label: 'Аккаунт' },
  { value: 'other', label: 'Другое' },
]

const isClosed = computed(() => ['resolved', 'closed'].includes(detail.value?.ticket.status || ''))

const metaDirty = computed(
  () =>
    !!detail.value &&
    (editPriority.value !== detail.value.ticket.priority ||
      editCategory.value !== detail.value.ticket.category),
)

const userLabel = computed(() => {
  const u = detail.value?.ticket.user
  if (!u) return `user #${detail.value?.ticket.user_id ?? ''}`
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ').trim()
  if (name) return u.username ? `${name} (@${u.username})` : name
  if (u.username) return `@${u.username}`
  if (u.email) return u.email
  return `user #${u.user_id || detail.value?.ticket.user_id || ''}`
})

function bytesToGb(v: unknown): string {
  const n = Number(v)
  if (!Number.isFinite(n) || n <= 0) return '0'
  return (Math.round((n / 2 ** 30) * 10) / 10).toString()
}

const snapshotRows = computed(() => {
  const s = detail.value?.user_snapshot
  if (!s || typeof s !== 'object' || !Object.keys(s).length) return [] as { k: string; v: string }[]
  const rows: { k: string; v: string }[] = []
  const push = (k: string, v: unknown) => {
    if (v !== null && v !== undefined && v !== '') rows.push({ k, v: String(v) })
  }
  push('Имя', s.name)
  push('Username', s.username ? `@${s.username}` : null)
  push('Email', s.email)
  push('Telegram ID', s.telegram_id)
  push('Язык', s.language)
  push('Регистрация', s.registration_date)
  if (s.subscription_active !== null && s.subscription_active !== undefined) {
    push('Подписка', s.subscription_active ? 'активна' : 'не активна')
  }
  push('Статус панели', s.panel_status)
  push('До', s.end_date)
  push('Осталось', s.remaining)
  push('Тариф', s.tariff)
  const tr = s.traffic_regular as { used_bytes?: number; limit_bytes?: number } | null | undefined
  if (tr && (tr.used_bytes || tr.limit_bytes)) {
    push('Трафик', `${bytesToGb(tr.used_bytes)} / ${bytesToGb(tr.limit_bytes)} ГБ`)
  }
  if (s.is_throttled) push('Троттлинг', 'да')
  return rows
})

function errText(e: unknown): string {
  const err = e as { code?: string; message?: string }
  const code = err.code || err.message || ''
  const map: Record<string, string> = {
    not_found: 'Тикет не найден',
    empty_text: 'Пустое сообщение',
    invalid_request: 'Некорректный запрос',
    invalid_telegram_html: 'Ошибка HTML-разметки',
    request_failed: 'Ошибка запроса',
  }
  if (code.startsWith('unknown_shortcode')) return 'Неизвестный шорткод в тексте'
  return map[code] || code || 'Ошибка'
}

async function scrollBottom() {
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

async function load() {
  loading.value = true
  loadError.value = ''
  detail.value = null
  try {
    const res = await call<TicketDetail>(`support/tickets/${props.ticketId}`)
    detail.value = res
    editPriority.value = res.ticket.priority || 'normal'
    editCategory.value = res.ticket.category || 'other'
    await scrollBottom()
    if (res.ticket.unread_admin_count > 0) {
      await call(`support/tickets/${props.ticketId}/read`, { method: 'POST', body: {} })
      emit('updated')
    }
  } catch (e) {
    loadError.value = errText(e)
  } finally {
    loading.value = false
  }
}

async function send() {
  const body = replyBody.value.trim()
  if (!body || sending.value) return
  sending.value = true
  sendError.value = ''
  try {
    const res = await call<{ ticket: SupportTicket; message: SupportMessage }>(
      `support/tickets/${props.ticketId}/messages`,
      { method: 'POST', body: { body, body_format: 'text', is_internal_note: isNote.value } },
    )
    if (detail.value && res.message) {
      detail.value.messages.push(res.message)
      if (res.ticket) detail.value.ticket = { ...detail.value.ticket, ...res.ticket }
    }
    replyBody.value = ''
    await scrollBottom()
    emit('updated')
  } catch (e) {
    sendError.value = errText(e)
  } finally {
    sending.value = false
  }
}

// Индикатор 'печатает' для клиента - шлём не чаще раза в 3 секунды.
let lastTypingAt = 0
function onComposerInput() {
  const now = Date.now()
  if (now - lastTypingAt < 3000 || !replyBody.value.trim()) return
  lastTypingAt = now
  call(`support/tickets/${props.ticketId}/typing`, {
    method: 'POST',
    body: { typing: true },
  }).catch(() => {})
}

function askStatus(status: string) {
  const variants: Record<string, ConfirmState> = {
    resolved: { status, title: 'Отметить решённым', text: 'Клиент увидит, что тикет решён.' },
    closed: { status, title: 'Закрыть тикет', text: 'Тикет будет закрыт. Открыть его можно будет переоткрытием.' },
    open: { status, title: 'Переоткрыть тикет', text: 'Тикет вернётся в активные.' },
  }
  confirmAction.value = variants[status] || null
}

async function doStatus() {
  const action = confirmAction.value
  if (!action || busy.value) return
  busy.value = true
  try {
    const res = await call<{ ticket: SupportTicket }>(`support/tickets/${props.ticketId}`, {
      method: 'PATCH',
      body: { status: action.status },
    })
    if (detail.value && res.ticket) detail.value.ticket = { ...detail.value.ticket, ...res.ticket }
    confirmAction.value = null
    emit('updated')
  } catch (e) {
    sendError.value = errText(e)
    confirmAction.value = null
  } finally {
    busy.value = false
  }
}

async function saveMeta() {
  if (!detail.value || !metaDirty.value || busy.value) return
  busy.value = true
  try {
    const res = await call<{ ticket: SupportTicket }>(`support/tickets/${props.ticketId}`, {
      method: 'PATCH',
      body: { priority: editPriority.value, category: editCategory.value },
    })
    if (res.ticket) detail.value.ticket = { ...detail.value.ticket, ...res.ticket }
    emit('updated')
  } catch (e) {
    sendError.value = errText(e)
  } finally {
    busy.value = false
  }
}

watch(() => props.ticketId, () => {
  replyBody.value = ''
  sendError.value = ''
  isNote.value = false
  load()
}, { immediate: true })
</script>

<template>
  <div class="thread">
    <p v-if="loading" class="admin-note">Загрузка тикета...</p>
    <p v-else-if="loadError" class="admin-note admin-error">{{ loadError }}</p>

    <template v-else-if="detail">
      <header class="thread-head">
        <div class="thread-title">
          <strong>#{{ detail.ticket.ticket_id }} · {{ detail.ticket.subject }}</strong>
          <div class="admin-row">
            <AdminBadge :tone="isClosed ? 'muted' : detail.ticket.status === 'awaiting_admin' ? 'danger' : 'warning'">
              {{ statusLabels[detail.ticket.status] || detail.ticket.status }}
            </AdminBadge>
            <span class="admin-note">{{ userLabel }}</span>
          </div>
        </div>
        <button type="button" class="admin-btn ghost thread-close" aria-label="Скрыть" @click="emit('close')">✕</button>
      </header>

      <details v-if="snapshotRows.length" class="snapshot">
        <summary>Карточка клиента</summary>
        <dl class="snapshot-grid">
          <template v-for="row in snapshotRows" :key="row.k">
            <dt>{{ row.k }}</dt>
            <dd>{{ row.v }}</dd>
          </template>
        </dl>
      </details>

      <div class="admin-row meta-row">
        <label class="meta-field">
          <span class="admin-note">Приоритет</span>
          <AdminSelect v-model="editPriority" :items="priorityItems" />
        </label>
        <label class="meta-field">
          <span class="admin-note">Категория</span>
          <AdminSelect v-model="editCategory" :items="categoryItems" />
        </label>
        <button type="button" class="admin-btn ghost" :disabled="!metaDirty || busy" @click="saveMeta">
          Сохранить
        </button>
      </div>

      <div ref="msgBox" class="msgs">
        <SupportMessageItem v-for="m in detail.messages" :key="m.message_id" :message="m" />
        <p v-if="!detail.messages.length" class="admin-note">Сообщений пока нет</p>
        <p v-if="detail.peer_typing" class="admin-note">Клиент печатает...</p>
      </div>

      <div class="composer">
        <textarea
          v-model="replyBody"
          class="admin-input"
          rows="3"
          :placeholder="isNote ? 'Внутренняя заметка для команды...' : 'Ответ клиенту...'"
          :disabled="sending"
          @input="onComposerInput"
          @keydown.ctrl.enter="send"
        />
        <label class="admin-check">
          <input v-model="isNote" type="checkbox" />
          Внутренняя заметка (клиент не увидит)
        </label>
        <div class="admin-row">
          <button type="button" class="admin-btn" :disabled="sending || !replyBody.trim()" @click="send">
            {{ sending ? 'Отправка...' : isNote ? 'Добавить заметку' : 'Ответить' }}
          </button>
          <template v-if="isClosed">
            <button type="button" class="admin-btn ghost" :disabled="busy" @click="askStatus('open')">
              Переоткрыть
            </button>
          </template>
          <template v-else>
            <button type="button" class="admin-btn ghost" :disabled="busy" @click="askStatus('resolved')">
              Решён
            </button>
            <button type="button" class="admin-btn danger" :disabled="busy" @click="askStatus('closed')">
              Закрыть
            </button>
          </template>
        </div>
        <p v-if="sendError" class="admin-note admin-error">{{ sendError }}</p>
      </div>
    </template>

    <AdminModal
      :open="!!confirmAction"
      :title="confirmAction?.title || ''"
      @close="confirmAction = null"
    >
      <p class="admin-note">{{ confirmAction?.text }}</p>
      <template #footer>
        <button type="button" class="admin-btn ghost" @click="confirmAction = null">Отмена</button>
        <button type="button" class="admin-btn" :disabled="busy" @click="doStatus">Подтвердить</button>
      </template>
    </AdminModal>
  </div>
</template>

<style scoped>
.thread {
  display: grid;
  gap: 12px;
}
.thread-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}
.thread-title {
  display: grid;
  gap: 6px;
  min-width: 0;
}
.thread-close {
  padding: 6px 10px;
}
.snapshot {
  border: 1px solid var(--adm-border);
  border-radius: 10px;
  padding: 10px 12px;
}
.snapshot summary {
  cursor: pointer;
  color: var(--adm-muted);
  font-size: 13px;
}
.snapshot-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 14px;
  margin: 10px 0 0;
  font-size: 13px;
}
.snapshot-grid dt {
  color: var(--adm-muted);
}
.snapshot-grid dd {
  margin: 0;
}
.meta-row {
  align-items: flex-end;
}
.meta-field {
  display: grid;
  gap: 4px;
  width: 160px;
}
.msgs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 480px;
  overflow-y: auto;
  padding: 4px;
}
.composer {
  display: grid;
  gap: 8px;
}
.composer textarea {
  resize: vertical;
}
</style>
