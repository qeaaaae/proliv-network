<script setup lang="ts">
import AdminModal from '~/components/admin/AdminModal.vue'
import AdminSelect from '~/components/admin/AdminSelect.vue'

interface AudienceCountsResponse {
  ok: boolean
  counts: Record<string, number | null>
  audiences: { target: string; fallback_label: string; available?: boolean }[]
  email_enabled: boolean
}

interface PreviewResponse {
  ok: boolean
  rendered_text: string
  rendered_subject: string | null
  unknown_shortcodes: string[]
  length: number
  sent: boolean
}

interface ShortcodesResponse {
  ok: boolean
  shortcodes: { name: string; description: string }[]
  allowed_tags: string[]
}

interface BroadcastCreateResponse {
  ok: boolean
  broadcast: { broadcast_id: number; status: string }
  target: string
  channels: string[]
}

const TELEGRAM_MAX = 4096

// Порядок совпадает с аудиториями бэкенда (bot/services/audience_segmentation.py).
const CORE_AUDIENCES: { value: string; label: string }[] = [
  { value: 'all', label: 'Все пользователи' },
  { value: 'active', label: 'С активной подпиской' },
  { value: 'inactive', label: 'Без активной подписки' },
  { value: 'expired', label: 'Подписка истекла' },
  { value: 'active_never_connected', label: 'Подписка есть, не подключались' },
  { value: 'never', label: 'Никогда не было подписки' },
  { value: 'admins', label: 'Администраторы (тест)' },
]

const ERROR_LABELS: Record<string, string> = {
  empty_text: 'Введите текст сообщения',
  invalid_audience: 'Неизвестная аудитория',
  audience_unavailable: 'Эта аудитория сейчас недоступна',
  unknown_shortcode: 'Неизвестный шорткод в тексте',
  invalid_telegram_html: 'Ошибка HTML-разметки для Telegram',
  queue_unavailable: 'Очередь отправки недоступна',
  email_not_configured: 'Email-канал не настроен на бэкенде',
  preview_failed: 'Не удалось отправить предпросмотр',
  admin_telegram_unavailable: 'У вашего аккаунта не привязан Telegram',
  broadcast_schedule_future: 'Время отправки должно быть в будущем',
}

const emit = defineEmits<{ sent: [] }>()

const { call } = useAdminApi()
const toast = useToast()

const target = ref('all')
const text = ref('')
const counts = ref<Record<string, number | null>>({})
const extraAudiences = ref<{ value: string; label: string }[]>([])
const scheduleEnabled = ref(false)
const scheduledAt = ref('')

const preview = ref<PreviewResponse | null>(null)
const previewBusy = ref(false)
const sendBusy = ref(false)
const confirmOpen = ref(false)

const shortcodes = ref<{ name: string; description: string }[]>([])
const shortcodesOpen = ref(false)

function errText(e: unknown): string {
  const err = e as { code?: string; message?: string }
  return ERROR_LABELS[err.code || ''] || err.message || 'Ошибка запроса'
}

const audienceItems = computed(() => {
  const coreValues = new Set(CORE_AUDIENCES.map((a) => a.value))
  const core = CORE_AUDIENCES.map((a) => ({
    value: a.value,
    label: `${a.label} (${countLabel(a.value)})`,
  }))
  const extra = extraAudiences.value
    .filter((a) => !coreValues.has(a.value))
    .map((a) => ({ value: a.value, label: `${a.label} (${countLabel(a.value)})` }))
  return [...core, ...extra]
})

const audienceLabel = computed(
  () => audienceItems.value.find((i) => i.value === target.value)?.label || target.value,
)

function countLabel(key: string): string {
  const value = counts.value[key]
  return value === null || value === undefined ? '—' : String(value)
}

const canSubmit = computed(() => {
  if (!text.value.trim()) return false
  if (!scheduleEnabled.value) return true
  if (!scheduledAt.value) return false
  const at = new Date(scheduledAt.value)
  return !Number.isNaN(at.getTime()) && at.getTime() > Date.now()
})

async function loadCounts() {
  try {
    const res = await call<AudienceCountsResponse>('broadcast/audience-counts')
    counts.value = res.counts || {}
    extraAudiences.value = (res.audiences || [])
      .filter((a) => a.available !== false)
      .map((a) => ({ value: a.target, label: a.fallback_label || a.target }))
  } catch {
    // Счётчики аудиторий вспомогательные - без них форма работает.
  }
}

async function loadShortcodes() {
  try {
    const res = await call<ShortcodesResponse>('broadcast/shortcodes')
    shortcodes.value = res.shortcodes || []
  } catch {
    // Подсказка по шорткодам вспомогательная.
  }
}

async function runPreview(mode: 'render' | 'send_telegram') {
  if (!text.value.trim()) return toast.push('Введите текст сообщения', 'error')
  previewBusy.value = true
  try {
    const res = await call<PreviewResponse>('broadcast/preview', {
      method: 'POST',
      body: { text: text.value.trim(), mode },
    })
    preview.value = res
    if (mode === 'send_telegram') toast.push('Предпросмотр отправлен вам в Telegram')
    else if (res.unknown_shortcodes?.length) {
      toast.push(`Неизвестные шорткоды: ${res.unknown_shortcodes.join(', ')}`, 'error')
    }
  } catch (e) {
    toast.push(errText(e), 'error')
  } finally {
    previewBusy.value = false
  }
}

function askSend() {
  if (!canSubmit.value) {
    if (scheduleEnabled.value) toast.push('Выберите время отправки в будущем', 'error')
    else toast.push('Введите текст сообщения', 'error')
    return
  }
  confirmOpen.value = true
}

async function send() {
  sendBusy.value = true
  try {
    const body: Record<string, unknown> = {
      target: target.value,
      text: text.value.trim(),
      channels: ['telegram'],
      exclude_blocked_telegram: null,
      scheduled_at: scheduleEnabled.value ? new Date(scheduledAt.value).toISOString() : null,
    }
    const res = await call<BroadcastCreateResponse>('broadcast', { method: 'POST', body })
    confirmOpen.value = false
    toast.push(
      res.broadcast?.status === 'scheduled'
        ? `Рассылка #${res.broadcast.broadcast_id} запланирована`
        : `Рассылка #${res.broadcast?.broadcast_id} поставлена в очередь`,
    )
    text.value = ''
    preview.value = null
    scheduleEnabled.value = false
    scheduledAt.value = ''
    emit('sent')
  } catch (e) {
    toast.push(errText(e), 'error')
  } finally {
    sendBusy.value = false
  }
}

onMounted(() => {
  loadCounts()
  loadShortcodes()
})
</script>

<template>
  <section class="admin-card">
    <h2>Новая рассылка</h2>

    <label class="bc-field">
      <span class="bc-label">Аудитория</span>
      <AdminSelect v-model="target" :items="audienceItems" />
    </label>

    <label class="bc-field">
      <span class="bc-label">Текст сообщения (Telegram HTML, до {{ TELEGRAM_MAX }} символов)</span>
      <textarea v-model="text" class="admin-input bc-textarea" rows="6" maxlength="4096" />
      <span class="bc-counter">{{ text.length }} / {{ TELEGRAM_MAX }}</span>
    </label>

    <p class="admin-note">
      Поддерживаются шорткоды персонализации и Telegram HTML-разметка.
      <button type="button" class="bc-link" @click="shortcodesOpen = !shortcodesOpen">
        {{ shortcodesOpen ? 'Скрыть шорткоды' : 'Показать шорткоды' }}
      </button>
    </p>
    <ul v-if="shortcodesOpen && shortcodes.length" class="admin-list bc-shortcodes">
      <li v-for="s in shortcodes" :key="s.name" class="bc-shortcode">
        <code>{{ '{' + s.name + '}' }}</code>
        <span class="admin-note">{{ s.description }}</span>
      </li>
    </ul>

    <label class="admin-check">
      <input v-model="scheduleEnabled" type="checkbox" /> Отправить позже
    </label>
    <label v-if="scheduleEnabled" class="bc-field">
      <span class="bc-label">Дата и время отправки</span>
      <input v-model="scheduledAt" type="datetime-local" class="admin-input" />
    </label>

    <div class="admin-row">
      <button class="admin-btn ghost" :disabled="previewBusy" @click="runPreview('render')">
        Предпросмотр
      </button>
      <button class="admin-btn ghost" :disabled="previewBusy" @click="runPreview('send_telegram')">
        Тест себе в Telegram
      </button>
      <button class="admin-btn" :disabled="sendBusy || !canSubmit" @click="askSend">
        Отправить
      </button>
    </div>

    <div v-if="preview" class="bc-preview">
      <p class="admin-note">
        Предпросмотр · {{ preview.length }} символов
        <template v-if="preview.unknown_shortcodes?.length">
          · <span class="admin-error">неизвестные шорткоды: {{ preview.unknown_shortcodes.join(', ') }}</span>
        </template>
      </p>
      <pre class="bc-preview-text">{{ preview.rendered_text }}</pre>
    </div>

    <AdminModal :open="confirmOpen" title="Подтвердите рассылку" @close="confirmOpen = false">
      <p class="admin-note">Аудитория: <strong>{{ audienceLabel }}</strong></p>
      <p class="admin-note" v-if="scheduleEnabled">
        Время отправки: {{ new Date(scheduledAt).toLocaleString('ru-RU') }}
      </p>
      <pre class="bc-preview-text">{{ text.trim() }}</pre>
      <template #footer>
        <button class="admin-btn ghost" :disabled="sendBusy" @click="confirmOpen = false">
          Отмена
        </button>
        <button class="admin-btn danger" :disabled="sendBusy" @click="send">
          {{ sendBusy ? 'Отправка...' : 'Подтвердить отправку' }}
        </button>
      </template>
    </AdminModal>
  </section>
</template>

<style scoped>
.bc-field {
  display: grid;
  gap: 6px;
}
.bc-label {
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
}
.bc-textarea {
  resize: vertical;
  font-family: inherit;
}
.bc-counter {
  font-size: 11px;
  color: var(--adm-muted, #8b95a8);
  justify-self: end;
}
.bc-link {
  border: 0;
  background: none;
  padding: 0;
  color: var(--adm-accent, #3b82f6);
  font-size: 12px;
  cursor: pointer;
}
.bc-shortcodes {
  max-height: 180px;
  overflow: auto;
}
.bc-shortcode {
  display: flex;
  gap: 8px;
  align-items: baseline;
  padding: 4px 0;
}
.bc-shortcode code {
  color: var(--adm-accent, #3b82f6);
  font-size: 12px;
}
.bc-preview {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--adm-border, #232c3d);
  background: var(--adm-bg, #0b0f17);
}
.bc-preview-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  font-family: inherit;
  max-height: 240px;
  overflow: auto;
}
</style>
