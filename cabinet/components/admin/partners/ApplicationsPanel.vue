<script setup lang="ts">
interface PartnerApplication {
  application_id: number
  user_id: number | null
  display_label: string
  username: string | null
  avatar_url: string | null
  message: string | null
  status: string
  submitted_at: string
  decided_at: string | null
  decision_message: string | null
  approved_commission_bps: number | null
  welcome_message: string | null
  reapply_allowed_at: string | null
}

interface ApplicationsResponse {
  applications: PartnerApplication[]
  total: number
  limit: number
  offset: number
}

const emit = defineEmits<{
  notice: [text: string, isError: boolean]
  changed: []
}>()

const { call } = useAdminApi()

const PAGE = 25

const applications = ref<PartnerApplication[]>([])
const total = ref(0)
const search = ref('')
const status = ref('pending')
const loading = ref(false)
const busy = ref(false)
const listError = ref('')

const statusItems = [
  { value: 'pending', label: 'Ожидают' },
  { value: 'approved', label: 'Одобренные' },
  { value: 'rejected', label: 'Отклонённые' },
  { value: 'all', label: 'Все' },
]

const statusLabels: Record<string, string> = {
  pending: 'Ожидает',
  approved: 'Одобрена',
  rejected: 'Отклонена',
  canceled: 'Отменена',
}

const statusTones: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'muted'> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'muted',
  canceled: 'muted',
}

const decision = ref<{ app: PartnerApplication; approve: boolean } | null>(null)
const decisionMessage = ref('')
const decisionRate = ref('')
const reopenTarget = ref<PartnerApplication | null>(null)

function fmtDate(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function pct(bps?: number | null): string {
  return bps === null || bps === undefined ? '—' : `${(bps / 100).toLocaleString('ru-RU')}%`
}

function errorText(err: unknown): string {
  const data = (err as { data?: { error?: string; message?: string } }).data || {}
  return data.message || data.error || (err as Error).message || 'request_failed'
}

async function load(reset = true) {
  loading.value = true
  listError.value = ''
  try {
    const res = await call<ApplicationsResponse>('partner-applications', {
      query: {
        status: status.value === 'all' ? '' : status.value,
        search: search.value.trim(),
        limit: PAGE,
        offset: reset ? 0 : applications.value.length,
      },
    })
    applications.value = reset ? res.applications : [...applications.value, ...res.applications]
    total.value = res.total
  } catch (err) {
    listError.value = errorText(err)
  } finally {
    loading.value = false
  }
}

function openDecision(app: PartnerApplication, approve: boolean) {
  decision.value = { app, approve }
  decisionMessage.value = ''
  decisionRate.value = ''
}

async function submitDecision() {
  if (!decision.value) return
  const { app, approve } = decision.value
  let commissionBps: number | null = null
  if (approve && decisionRate.value.trim()) {
    const value = Number(decisionRate.value)
    if (!Number.isFinite(value) || value < 0 || value > 100) {
      emit('notice', 'Ставка должна быть от 0 до 100%', true)
      return
    }
    commissionBps = Math.round(value * 100)
  }
  busy.value = true
  try {
    await call(`partner-applications/${app.application_id}/${approve ? 'approve' : 'reject'}`, {
      method: 'POST',
      body: {
        decision_message: decisionMessage.value.trim() || null,
        commission_bps: commissionBps,
        welcome_message: null,
      },
    })
    emit('notice', `Заявка #${app.application_id} ${approve ? 'одобрена' : 'отклонена'}`, false)
    decision.value = null
    await load()
    emit('changed')
  } catch (err) {
    emit('notice', `Ошибка: ${errorText(err)}`, true)
  } finally {
    busy.value = false
  }
}

async function submitReopen() {
  if (!reopenTarget.value) return
  const app = reopenTarget.value
  busy.value = true
  try {
    await call(`partner-applications/${app.application_id}/reopen`, { method: 'POST', body: {} })
    emit('notice', `Заявке #${app.application_id} разрешена повторная подача`, false)
    reopenTarget.value = null
    await load()
    emit('changed')
  } catch (err) {
    emit('notice', `Ошибка: ${errorText(err)}`, true)
  } finally {
    busy.value = false
  }
}

watch(status, () => load())
onMounted(() => load())
</script>

<template>
  <div class="admin-grid">
    <div class="admin-row">
      <input
        v-model="search"
        class="admin-input panel-search"
        placeholder="Имя или user_id"
        @keyup.enter="load()"
      />
      <div class="panel-select">
        <AdminSelect v-model="status" :items="statusItems" />
      </div>
      <button type="button" class="admin-btn" :disabled="loading" @click="load()">Найти</button>
    </div>

    <p v-if="listError" class="admin-note admin-error">Ошибка загрузки: {{ listError }}</p>
    <p v-if="loading && !applications.length" class="admin-note">Загрузка...</p>

    <ul v-if="applications.length" class="admin-list">
      <li v-for="app in applications" :key="app.application_id" class="app-item">
        <div class="admin-row app-head">
          <strong>{{ app.display_label }}</strong>
          <span class="admin-note">
            {{ app.username ? '@' + app.username : app.user_id ? 'user_id ' + app.user_id : '—' }}
            · заявка #{{ app.application_id }} · {{ fmtDate(app.submitted_at) }}
          </span>
          <AdminBadge :tone="statusTones[app.status] || 'default'">
            {{ statusLabels[app.status] || app.status }}
          </AdminBadge>
        </div>
        <p v-if="app.message" class="admin-note app-message">{{ app.message }}</p>
        <p v-if="app.decision_message" class="admin-note">
          Решение: {{ app.decision_message }}
          <template v-if="app.approved_commission_bps !== null">
            · ставка {{ pct(app.approved_commission_bps) }}
          </template>
        </p>
        <p v-if="app.status === 'rejected' && app.reapply_allowed_at" class="admin-note">
          Повторная подача разрешена {{ fmtDate(app.reapply_allowed_at) }}
        </p>
        <div v-if="app.status === 'pending'" class="admin-row">
          <button type="button" class="admin-btn" :disabled="busy" @click="openDecision(app, true)">
            Одобрить
          </button>
          <button
            type="button"
            class="admin-btn ghost"
            :disabled="busy"
            @click="openDecision(app, false)"
          >
            Отклонить
          </button>
        </div>
        <div v-else-if="app.status === 'rejected' && !app.reapply_allowed_at" class="admin-row">
          <button type="button" class="admin-btn ghost" :disabled="busy" @click="reopenTarget = app">
            Разрешить повторную подачу
          </button>
        </div>
      </li>
    </ul>
    <p v-else-if="!loading" class="admin-note">Заявок нет</p>

    <div v-if="applications.length < total" class="admin-row">
      <button type="button" class="admin-btn ghost" :disabled="loading" @click="load(false)">
        Показать ещё ({{ applications.length }} из {{ total }})
      </button>
    </div>
  </div>

  <AdminPartnersConfirmModal
    :open="decision !== null"
    :title="decision?.approve ? 'Одобрить заявку' : 'Отклонить заявку'"
    :busy="busy"
    :danger="decision?.approve === false"
    :confirm-label="decision?.approve ? 'Одобрить' : 'Отклонить'"
    @close="decision = null"
    @confirm="submitDecision"
  >
    <p class="admin-note">
      {{ decision?.app.display_label }} · заявка #{{ decision?.app.application_id }}
    </p>
    <label v-if="decision?.approve" class="admin-field">
      <span>Ставка, % (необязательно - по умолчанию стандартная)</span>
      <input v-model="decisionRate" class="admin-input" type="number" min="0" max="100" step="0.01" />
    </label>
    <label class="admin-field">
      <span>Сообщение юзеру (необязательно)</span>
      <input v-model="decisionMessage" class="admin-input" placeholder="Комментарий к решению" />
    </label>
  </AdminPartnersConfirmModal>

  <AdminPartnersConfirmModal
    :open="reopenTarget !== null"
    title="Повторная подача заявки"
    :busy="busy"
    confirm-label="Разрешить"
    @close="reopenTarget = null"
    @confirm="submitReopen"
  >
    <p class="admin-note">
      Юзер {{ reopenTarget?.display_label }} сможет подать заявку в партнёры ещё раз.
    </p>
  </AdminPartnersConfirmModal>
</template>

<style scoped>
.panel-search {
  flex: 1;
  min-width: 160px;
}
.panel-select {
  width: 180px;
}
.app-item {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--adm-border, #232c3d);
}
.app-head {
  justify-content: flex-start;
}
.app-message {
  white-space: pre-wrap;
}
.admin-field {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
}
</style>
