<script setup lang="ts">
interface PartnerBalance {
  currency: string
  currency_scale: number
  available_minor: number
  pending_minor: number
  reserved_minor: number
  lifetime_earned_minor: number
}

interface PartnerLinks {
  telegram: string | null
  web: string | null
  telegram_enabled: boolean
  web_enabled: boolean
}

interface PartnerProfile {
  partner_id: number
  user_id: number | null
  display_label: string
  username: string | null
  avatar_url: string | null
  status: string
  commission_bps: number
  welcome_message: string | null
  pause_reason: string | null
  kind: string
  banner_below_stream: boolean
  banner_on_stream: boolean
  activated_at: string
  created_at: string
  balances?: PartnerBalance[]
  clients_count?: number
  latest_client?: string | null
  payments_count?: number
  gross_minor?: number
  earned_minor?: number
  currency?: string
  links?: PartnerLinks
}

interface PartnerClient {
  partner_client_id: number
  client_user_id: number | null
  public_client_id: string
  label: string
  source: string
  attributed_at: string
  payments_count: number
  gross_minor: number
  currency: string
  currency_scale: number
}

interface PartnerCommission {
  commission_id: number
  payment_id: number | null
  client_public_id: string
  client_label: string
  gross_amount_minor: number
  commission_amount_minor: number
  currency: string
  currency_scale: number
  commission_bps: number
  sale_mode: string | null
  provider: string | null
  status: string
  exclusion_reason: string | null
  source_paid_at: string
  available_at: string
  created_at: string
  reversed_at: string | null
}

interface PartnerWithdrawal {
  withdrawal_id: number
  partner_id: number
  method_id: string
  method_type: string
  amount_minor: number
  currency: string
  currency_scale: number
  settlement_asset: string | null
  network: string | null
  status: string
  status_version: number
  status_message: string | null
  external_reference: string | null
  settlement_amount: string | null
  masked_requisites: string
  requested_at: string
  processing_at: string | null
  paid_at: string | null
  decided_at: string | null
}

interface LedgerEntry {
  ledger_entry_id: number
  kind: string
  state: string
  amount_minor: number
  balance_after_minor: number
  currency: string
  currency_scale: number
  created_at: string
  internal_reference: string
}

interface AuditEvent {
  audit_event_id: number
  event_type: string
  actor_type: string
  actor_user_id: number | null
  reason: string | null
  created_at: string
}

interface ImportPreview {
  found: number
  importable: number
  already_this_partner: number
  other_partner: number
  self_conflict: number
  historical_payments: number
}

interface DetailResponse {
  partner: PartnerProfile
  has_relationships: boolean
  clients: PartnerClient[]
  clients_total: number
  commissions: PartnerCommission[]
  commissions_total: number
  withdrawals: PartnerWithdrawal[]
  withdrawals_total: number
  ledger: LedgerEntry[]
  audit: AuditEvent[]
}

const props = defineProps<{ partnerId: number }>()
const emit = defineEmits<{
  notice: [text: string, isError: boolean]
  changed: []
}>()

const { call } = useAdminApi()

const detail = ref<DetailResponse | null>(null)
const loading = ref(false)
const busy = ref(false)

const kindItems = [
  { value: 'standard', label: 'Партнёр' },
  { value: 'streamer', label: 'Стример' },
  { value: 'clipper', label: 'Нарезчик' },
]

const kindLabels: Record<string, string> = {
  standard: 'Партнёр',
  streamer: 'Стример',
  clipper: 'Нарезчик',
}

const statusLabels: Record<string, string> = {
  active: 'Активен',
  paused: 'На паузе',
  closed: 'Закрыт',
}

const statusTones: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'muted'> = {
  active: 'success',
  paused: 'warning',
  closed: 'muted',
}

const commissionLabels: Record<string, string> = {
  pending: 'Ожидает',
  available: 'Доступна',
  paid: 'Выплачена',
  reversed: 'Сторнирована',
  excluded: 'Исключена',
}

const withdrawalLabels: Record<string, string> = {
  requested: 'Запрошена',
  processing: 'В обработке',
  paid: 'Выплачена',
  rejected: 'Отклонена',
  failed: 'Ошибка',
}

const withdrawalTones: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'muted'> = {
  requested: 'warning',
  processing: 'default',
  paid: 'success',
  rejected: 'muted',
  failed: 'danger',
}

const auditLabels: Record<string, string> = {
  created: 'Создание',
  status_changed: 'Смена статуса',
  commission_rate_changed: 'Смена ставки',
  kind_changed: 'Смена типа',
  balance_adjusted: 'Корректировка баланса',
  referral_import: 'Импорт рефералов',
  link_rotated: 'Ротация ссылки',
  application_reopened: 'Переоткрытие заявки',
}

const ledgerKindLabels: Record<string, string> = {
  commission: 'Комиссия',
  withdrawal: 'Выплата',
  adjustment: 'Корректировка',
  reversal: 'Сторно',
}

const partner = computed(() => detail.value?.partner || null)
const primaryBalance = computed(() => partner.value?.balances?.[0] || null)

const modal = ref<'status' | 'rate' | 'kind' | 'balance' | 'import' | 'rotate' | null>(null)

const statusAction = ref<'pause' | 'resume' | 'close'>('pause')
const statusReason = ref('')

const ratePct = ref('')
const rateReason = ref('')

const kindDraft = ref('standard')
const belowDraft = ref(false)
const onDraft = ref(false)
const kindReason = ref('')

const balMode = ref('add')
const balAmount = ref('')
const balReason = ref('')
const balAllowNegative = ref(false)
const balModeItems = [
  { value: 'add', label: 'Начислить' },
  { value: 'subtract', label: 'Списать' },
  { value: 'set', label: 'Установить точно' },
]

const importPreview = ref<ImportPreview | null>(null)
const importLoading = ref(false)

const TABLE_LIMIT = 15

function fmtMoney(minor: number | null | undefined, scale = 2, currency = 'RUB'): string {
  const value = (minor ?? 0) / Math.pow(10, scale)
  const cur = currency === 'RUB' ? '₽' : currency
  return `${value.toLocaleString('ru-RU', { minimumFractionDigits: scale, maximumFractionDigits: scale })} ${cur}`
}

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
  return `${((bps ?? 0) / 100).toLocaleString('ru-RU')}%`
}

function errorText(err: unknown): string {
  const data = (err as { data?: { error?: string; message?: string } }).data || {}
  return data.message || data.error || (err as Error).message || 'request_failed'
}

async function run(fn: () => Promise<string>, closeModal = true) {
  busy.value = true
  try {
    const text = await fn()
    emit('notice', text, false)
    if (closeModal) modal.value = null
    await load()
    emit('changed')
  } catch (err) {
    emit('notice', `Ошибка: ${errorText(err)}`, true)
  } finally {
    busy.value = false
  }
}

async function load() {
  loading.value = true
  try {
    detail.value = await call<DetailResponse>(`partners/${props.partnerId}`, {
      query: { currency: 'RUB' },
    })
  } catch (err) {
    emit('notice', `Ошибка загрузки партнёра: ${errorText(err)}`, true)
    detail.value = null
  } finally {
    loading.value = false
  }
}

function openStatus(action: 'pause' | 'resume' | 'close') {
  statusAction.value = action
  statusReason.value = ''
  modal.value = 'status'
}

const statusActionLabel = computed(() => {
  if (statusAction.value === 'pause') return 'поставить на паузу'
  if (statusAction.value === 'resume') return 'возобновить'
  return 'закрыть'
})

async function submitStatus() {
  await run(async () => {
    const res = await call<{ partner: PartnerProfile }>(
      `partners/${props.partnerId}/${statusAction.value}`,
      { method: 'POST', body: { reason: statusReason.value.trim() || null } },
    )
    return `Статус изменён: ${statusLabels[res.partner.status] || res.partner.status}`
  })
}

function openKind() {
  if (!partner.value) return
  kindDraft.value = partner.value.kind || 'standard'
  belowDraft.value = Boolean(partner.value.banner_below_stream)
  onDraft.value = Boolean(partner.value.banner_on_stream)
  kindReason.value = ''
  modal.value = 'kind'
}

async function submitKind() {
  await run(async () => {
    const res = await call<{ partner: PartnerProfile }>(`partners/${props.partnerId}/kind`, {
      method: 'POST',
      body: {
        kind: kindDraft.value,
        banner_below_stream: kindDraft.value === 'streamer' ? belowDraft.value : false,
        banner_on_stream: kindDraft.value === 'streamer' ? onDraft.value : false,
        reason: kindReason.value.trim() || null,
      },
    })
    return `Тип обновлён: ${kindLabels[res.partner.kind] || res.partner.kind}, ставка ${pct(res.partner.commission_bps)}`
  })
}

function openRate() {
  if (!partner.value) return
  ratePct.value = String(partner.value.commission_bps / 100)
  rateReason.value = ''
  modal.value = 'rate'
}

async function submitRate() {
  const pctValue = Number(ratePct.value)
  if (!Number.isFinite(pctValue) || pctValue < 0 || pctValue > 100) {
    emit('notice', 'Ставка должна быть от 0 до 100%', true)
    return
  }
  if (!rateReason.value.trim()) {
    emit('notice', 'Укажите причину смены ставки', true)
    return
  }
  await run(async () => {
    const res = await call<{ partner: PartnerProfile }>(
      `partners/${props.partnerId}/commission-rate`,
      {
        method: 'POST',
        body: { commission_bps: Math.round(pctValue * 100), reason: rateReason.value.trim() },
      },
    )
    return `Ставка обновлена: ${pct(res.partner.commission_bps)}`
  })
}

function openBalance() {
  balMode.value = 'add'
  balAmount.value = ''
  balReason.value = ''
  balAllowNegative.value = false
  modal.value = 'balance'
}

const balModeLabel = computed(
  () => balModeItems.find((item) => item.value === balMode.value)?.label || balMode.value,
)

async function submitBalance() {
  const amount = Number(balAmount.value)
  if (!Number.isFinite(amount)) {
    emit('notice', 'Укажите сумму', true)
    return
  }
  const amountMinor = Math.round(amount * 100)
  if (amountMinor < 0) {
    emit('notice', 'Сумма не может быть отрицательной', true)
    return
  }
  await run(async () => {
    const res = await call<{ entry_id: number; amount_minor: number; balance_minor: number }>(
      `partners/${props.partnerId}/balance-adjustments`,
      {
        method: 'POST',
        body: {
          currency: 'RUB',
          currency_scale: 2,
          mode: balMode.value,
          amount_minor: amountMinor,
          reason: balReason.value.trim() || null,
          idempotency_key: `adm-${props.partnerId}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
          allow_negative: balAllowNegative.value,
          internal_reference: null,
        },
      },
    )
    return `Баланс скорректирован, новый доступный остаток: ${fmtMoney(res.balance_minor, 2, 'RUB')}`
  })
}

async function openImport() {
  modal.value = 'import'
  importPreview.value = null
  importLoading.value = true
  try {
    const res = await call<{ preview: ImportPreview }>(
      `partners/${props.partnerId}/referral-import`,
    )
    importPreview.value = res.preview
  } catch (err) {
    emit('notice', `Ошибка предпросмотра импорта: ${errorText(err)}`, true)
    modal.value = null
  } finally {
    importLoading.value = false
  }
}

async function submitImport() {
  await run(async () => {
    const res = await call<{ result: { imported: number; existing: number; conflicts: number } }>(
      `partners/${props.partnerId}/referral-import`,
      { method: 'POST', body: { confirm_without_retroactive_commission: true } },
    )
    return `Импортировано клиентов: ${res.result.imported} (конфликтов: ${res.result.conflicts})`
  })
}

async function submitRotate() {
  await run(async () => {
    await call(`partners/${props.partnerId}/link/rotate`, { method: 'POST', body: {} })
    return 'Реферальная ссылка обновлена'
  })
}

watch(() => props.partnerId, load, { immediate: true })
</script>

<template>
  <section v-if="loading && !detail" class="admin-card">
    <p class="admin-note">Загрузка партнёра...</p>
  </section>

  <section v-else-if="partner" class="admin-card partner-detail">
    <div class="admin-row partner-head">
      <img v-if="partner.avatar_url" :src="partner.avatar_url" class="partner-ava" alt="" />
      <div class="partner-title">
        <h2>
          {{ partner.display_label }}
          <small>#{{ partner.partner_id }}</small>
        </h2>
        <p class="admin-note">
          {{ partner.username ? '@' + partner.username : partner.user_id ? 'user_id ' + partner.user_id : 'без юзера' }}
          · с {{ fmtDate(partner.created_at) }}
        </p>
      </div>
      <div class="admin-row">
        <AdminBadge :tone="statusTones[partner.status] || 'default'">
          {{ statusLabels[partner.status] || partner.status }}
        </AdminBadge>
        <AdminBadge>{{ kindLabels[partner.kind] || partner.kind }}</AdminBadge>
        <AdminBadge v-if="partner.banner_below_stream" tone="warning">Баннер под стримом</AdminBadge>
        <AdminBadge v-if="partner.banner_on_stream" tone="warning">Баннер на стриме</AdminBadge>
      </div>
    </div>
    <p v-if="partner.pause_reason" class="admin-note">Причина паузы: {{ partner.pause_reason }}</p>

    <div class="admin-grid cols-3">
      <div class="admin-kpi">
        <small>Ставка</small>
        <strong>{{ pct(partner.commission_bps) }}</strong>
      </div>
      <div class="admin-kpi">
        <small>Клиентов</small>
        <strong>{{ partner.clients_count ?? '—' }}</strong>
      </div>
      <div class="admin-kpi">
        <small>Заработано ({{ partner.currency || 'RUB' }})</small>
        <strong>{{ fmtMoney(partner.earned_minor, 2, partner.currency || 'RUB') }}</strong>
      </div>
      <div v-if="primaryBalance" class="admin-kpi">
        <small>Доступно к выплате</small>
        <strong>{{ fmtMoney(primaryBalance.available_minor, primaryBalance.currency_scale, primaryBalance.currency) }}</strong>
      </div>
      <div v-if="primaryBalance" class="admin-kpi">
        <small>В ожидании / зарезервировано</small>
        <strong>
          {{ fmtMoney(primaryBalance.pending_minor, primaryBalance.currency_scale, primaryBalance.currency) }}
          / {{ fmtMoney(primaryBalance.reserved_minor, primaryBalance.currency_scale, primaryBalance.currency) }}
        </strong>
      </div>
      <div class="admin-kpi">
        <small>Оборот клиентов</small>
        <strong>{{ fmtMoney(partner.gross_minor, 2, partner.currency || 'RUB') }}</strong>
      </div>
    </div>

    <div v-if="partner.balances && partner.balances.length" class="admin-card-lite">
      <h3>Балансы</h3>
      <table class="admin-table">
        <thead>
          <tr><th>Валюта</th><th>Доступно</th><th>Ожидает</th><th>Резерв</th><th>Всего заработано</th></tr>
        </thead>
        <tbody>
          <tr v-for="b in partner.balances" :key="b.currency">
            <td>{{ b.currency }}</td>
            <td>{{ fmtMoney(b.available_minor, b.currency_scale, b.currency) }}</td>
            <td>{{ fmtMoney(b.pending_minor, b.currency_scale, b.currency) }}</td>
            <td>{{ fmtMoney(b.reserved_minor, b.currency_scale, b.currency) }}</td>
            <td>{{ fmtMoney(b.lifetime_earned_minor, b.currency_scale, b.currency) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="partner.links && (partner.links.telegram || partner.links.web)" class="admin-card-lite">
      <h3>Ссылки</h3>
      <p v-if="partner.links.telegram" class="admin-note link-line">
        Telegram: <code>{{ partner.links.telegram }}</code>
      </p>
      <p v-if="partner.links.web" class="admin-note link-line">
        Web: <code>{{ partner.links.web }}</code>
      </p>
    </div>

    <div class="admin-row">
      <button
        v-if="partner.status === 'active'"
        type="button"
        class="admin-btn ghost"
        :disabled="busy"
        @click="openStatus('pause')"
      >
        Пауза
      </button>
      <button
        v-if="partner.status === 'paused'"
        type="button"
        class="admin-btn"
        :disabled="busy"
        @click="openStatus('resume')"
      >
        Возобновить
      </button>
      <button
        v-if="partner.status !== 'closed'"
        type="button"
        class="admin-btn ghost"
        :disabled="busy"
        @click="openStatus('close')"
      >
        Закрыть
      </button>
      <button type="button" class="admin-btn ghost" :disabled="busy" @click="openKind">
        Тип и баннеры
      </button>
      <button type="button" class="admin-btn ghost" :disabled="busy" @click="openRate">
        Ставка
      </button>
      <button type="button" class="admin-btn ghost" :disabled="busy" @click="openBalance">
        Корректировка баланса
      </button>
      <button
        type="button"
        class="admin-btn ghost"
        :disabled="busy || !detail?.has_relationships"
        @click="openImport"
      >
        Импорт рефералов
      </button>
      <button type="button" class="admin-btn ghost" :disabled="busy" @click="modal = 'rotate'">
        Новая ссылка
      </button>
    </div>

    <div class="admin-card-lite">
      <h3>Клиенты <small v-if="detail">({{ detail.clients_total }})</small></h3>
      <table v-if="detail?.clients.length" class="admin-table">
        <thead>
          <tr><th>Клиент</th><th>Источник</th><th>Дата</th><th>Платежей</th><th>Оборот</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in detail.clients.slice(0, TABLE_LIMIT)" :key="c.partner_client_id">
            <td>{{ c.label }} <small class="admin-note">({{ c.public_client_id }})</small></td>
            <td>{{ c.source }}</td>
            <td>{{ fmtDate(c.attributed_at) }}</td>
            <td>{{ c.payments_count }}</td>
            <td>{{ fmtMoney(c.gross_minor, c.currency_scale, c.currency || 'RUB') }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="admin-note">Клиентов пока нет</p>
    </div>

    <div class="admin-card-lite">
      <h3>Комиссии <small v-if="detail">({{ detail.commissions_total }})</small></h3>
      <table v-if="detail?.commissions.length" class="admin-table">
        <thead>
          <tr><th>Клиент</th><th>Сумма</th><th>Комиссия</th><th>Ставка</th><th>Статус</th><th>Оплата</th></tr>
        </thead>
        <tbody>
          <tr v-for="cm in detail.commissions.slice(0, TABLE_LIMIT)" :key="cm.commission_id">
            <td>{{ cm.client_label }}</td>
            <td>{{ fmtMoney(cm.gross_amount_minor, cm.currency_scale, cm.currency) }}</td>
            <td>{{ fmtMoney(cm.commission_amount_minor, cm.currency_scale, cm.currency) }}</td>
            <td>{{ pct(cm.commission_bps) }}</td>
            <td>{{ commissionLabels[cm.status] || cm.status }}</td>
            <td>{{ fmtDate(cm.source_paid_at) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="admin-note">Комиссий пока нет</p>
    </div>

    <div class="admin-card-lite">
      <h3>Выплаты <small v-if="detail">({{ detail.withdrawals_total }})</small></h3>
      <table v-if="detail?.withdrawals.length" class="admin-table">
        <thead>
          <tr><th>Сумма</th><th>Метод</th><th>Реквизиты</th><th>Статус</th><th>Запрошена</th></tr>
        </thead>
        <tbody>
          <tr v-for="w in detail.withdrawals.slice(0, TABLE_LIMIT)" :key="w.withdrawal_id">
            <td>{{ fmtMoney(w.amount_minor, w.currency_scale, w.currency) }}</td>
            <td>{{ w.method_id }}</td>
            <td>{{ w.masked_requisites }}</td>
            <td>
              <AdminBadge :tone="withdrawalTones[w.status] || 'default'">
                {{ withdrawalLabels[w.status] || w.status }}
              </AdminBadge>
            </td>
            <td>{{ fmtDate(w.requested_at) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="admin-note">Выплат пока нет</p>
    </div>

    <div class="admin-card-lite">
      <h3>Журнал баланса</h3>
      <table v-if="detail?.ledger.length" class="admin-table">
        <thead>
          <tr><th>Дата</th><th>Тип</th><th>Сумма</th><th>Остаток</th></tr>
        </thead>
        <tbody>
          <tr v-for="e in detail.ledger.slice(0, TABLE_LIMIT)" :key="e.ledger_entry_id">
            <td>{{ fmtDate(e.created_at) }}</td>
            <td>{{ ledgerKindLabels[e.kind] || e.kind }}<template v-if="e.state !== 'posted'"> ({{ e.state }})</template></td>
            <td>{{ fmtMoney(e.amount_minor, e.currency_scale, e.currency) }}</td>
            <td>{{ fmtMoney(e.balance_after_minor, e.currency_scale, e.currency) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="admin-note">Записей нет</p>
    </div>

    <div class="admin-card-lite">
      <h3>Аудит</h3>
      <table v-if="detail?.audit.length" class="admin-table">
        <thead>
          <tr><th>Дата</th><th>Событие</th><th>Актор</th><th>Причина</th></tr>
        </thead>
        <tbody>
          <tr v-for="a in detail.audit.slice(0, TABLE_LIMIT)" :key="a.audit_event_id">
            <td>{{ fmtDate(a.created_at) }}</td>
            <td>{{ auditLabels[a.event_type] || a.event_type }}</td>
            <td>{{ a.actor_type }}{{ a.actor_user_id ? ` #${a.actor_user_id}` : '' }}</td>
            <td>{{ a.reason || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="admin-note">Событий нет</p>
    </div>
  </section>

  <AdminPartnersConfirmModal
    :open="modal === 'status'"
    :title="`Подтверждение: ${statusActionLabel}`"
    :busy="busy"
    :danger="statusAction === 'close'"
    confirm-label="Применить"
    @close="modal = null"
    @confirm="submitStatus"
  >
    <p class="admin-note">
      Партнёр: {{ partner?.display_label }} (#{{ partnerId }}). Действие: {{ statusActionLabel }}.
    </p>
    <label class="admin-field">
      <span>Причина (для аудита, необязательно)</span>
      <input v-model="statusReason" class="admin-input" placeholder="Например: нарушение условий" />
    </label>
  </AdminPartnersConfirmModal>

  <AdminPartnersConfirmModal
    :open="modal === 'rate'"
    title="Смена ставки"
    :busy="busy"
    confirm-label="Сменить ставку"
    :disabled="!rateReason.trim()"
    @close="modal = null"
    @confirm="submitRate"
  >
    <p class="admin-note">Текущая ставка: {{ pct(partner?.commission_bps) }}</p>
    <label class="admin-field">
      <span>Новая ставка, %</span>
      <input v-model="ratePct" class="admin-input" type="number" min="0" max="100" step="0.01" />
    </label>
    <label class="admin-field">
      <span>Причина (обязательно)</span>
      <input v-model="rateReason" class="admin-input" placeholder="Например: договорились в лс" />
    </label>
    <p class="admin-note">Ставка применяется только к новым платежам.</p>
  </AdminPartnersConfirmModal>

  <AdminPartnersConfirmModal
    :open="modal === 'kind'"
    title="Тип и размещения баннеров"
    :busy="busy"
    confirm-label="Сохранить"
    @close="modal = null"
    @confirm="submitKind"
  >
    <label class="admin-field">
      <span>Тип</span>
      <AdminSelect v-model="kindDraft" :items="kindItems" />
    </label>
    <template v-if="kindDraft === 'streamer'">
      <label class="admin-check">
        <input v-model="belowDraft" type="checkbox" />
        Баннер под стримом
      </label>
      <label class="admin-check">
        <input v-model="onDraft" type="checkbox" />
        Баннер на стриме
      </label>
      <p class="admin-note">Ставка стримера пересчитается по размещениям автоматически.</p>
    </template>
    <label class="admin-field">
      <span>Причина (для аудита, необязательно)</span>
      <input v-model="kindReason" class="admin-input" />
    </label>
  </AdminPartnersConfirmModal>

  <AdminPartnersConfirmModal
    :open="modal === 'balance'"
    title="Корректировка баланса"
    :busy="busy"
    confirm-label="Применить"
    @close="modal = null"
    @confirm="submitBalance"
  >
    <p v-if="primaryBalance" class="admin-note">
      Сейчас доступно: {{ fmtMoney(primaryBalance.available_minor, primaryBalance.currency_scale, primaryBalance.currency) }}
    </p>
    <label class="admin-field">
      <span>Операция</span>
      <AdminSelect v-model="balMode" :items="balModeItems" />
    </label>
    <label class="admin-field">
      <span>Сумма, ₽</span>
      <input v-model="balAmount" class="admin-input" type="number" min="0" step="0.01" />
    </label>
    <label class="admin-field">
      <span>Причина (для аудита)</span>
      <input v-model="balReason" class="admin-input" placeholder="Например: выплата за просмотры" />
    </label>
    <label v-if="balMode === 'subtract'" class="admin-check">
      <input v-model="balAllowNegative" type="checkbox" />
      Разрешить уход в минус
    </label>
    <p class="admin-note">Операция: {{ balModeLabel }}. Валюта RUB.</p>
  </AdminPartnersConfirmModal>

  <AdminPartnersConfirmModal
    :open="modal === 'import'"
    title="Импорт рефералов в клиенты"
    :busy="busy"
    confirm-label="Импортировать"
    :disabled="importLoading || !importPreview || importPreview.importable === 0"
    @close="modal = null"
    @confirm="submitImport"
  >
    <p v-if="importLoading" class="admin-note">Считаем рефералов...</p>
    <template v-else-if="importPreview">
      <p class="admin-note">
        Рефералов у юзера: {{ importPreview.found }} · можно импортировать: {{ importPreview.importable }}
        · уже у этого партнёра: {{ importPreview.already_this_partner }}
        · у других партнёров: {{ importPreview.other_partner }}
        · конфликт с самим партнёром: {{ importPreview.self_conflict }}
      </p>
      <p class="admin-note">
        У импортируемых - исторических платежей: {{ importPreview.historical_payments }}.
        Комиссия за уже оплаченные платежи начислена не будет.
      </p>
      <p v-if="!importPreview.importable" class="admin-note">Импортировать некого.</p>
    </template>
  </AdminPartnersConfirmModal>

  <AdminPartnersConfirmModal
    :open="modal === 'rotate'"
    title="Новая реферальная ссылка"
    :busy="busy"
    confirm-label="Обновить ссылку"
    @close="modal = null"
    @confirm="submitRotate"
  >
    <p class="admin-note">
      Старая ссылка партнёра перестанет работать. Новые клиенты пойдут по новой ссылке.
    </p>
  </AdminPartnersConfirmModal>
</template>

<style scoped>
.partner-detail {
  gap: 16px;
}
.partner-head {
  align-items: flex-start;
  justify-content: space-between;
}
.partner-title h2 {
  margin: 0;
  font-size: 17px;
}
.partner-title h2 small {
  color: var(--adm-muted, #8b95a8);
  font-weight: 400;
}
.partner-ava {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  object-fit: cover;
}
.admin-card-lite {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--adm-border, #232c3d);
  background: var(--adm-card-2, #1a2231);
}
.admin-card-lite h3 {
  margin: 0;
  font-size: 14px;
}
.admin-card-lite h3 small {
  color: var(--adm-muted, #8b95a8);
  font-weight: 400;
}
.admin-field {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
}
.link-line code {
  user-select: all;
  font-size: 12px;
}
.admin-table {
  font-size: 12px;
}
</style>
