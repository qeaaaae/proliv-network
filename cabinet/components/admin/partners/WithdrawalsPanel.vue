<script setup lang="ts">
interface PartnerWithdrawal {
  withdrawal_id: number
  partner_id: number
  user_id: number | null
  display_label: string | null
  username: string | null
  avatar_url: string | null
  method_id: string
  method_type: string
  method_snapshot: Record<string, unknown>
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

interface WithdrawalsResponse {
  withdrawals: PartnerWithdrawal[]
  total: number
  limit: number
  offset: number
}

type WithdrawalAction = 'processing' | 'paid' | 'reject' | 'fail'

const emit = defineEmits<{
  notice: [text: string, isError: boolean]
  changed: []
}>()

const { call } = useAdminApi()

const PAGE = 25

const withdrawals = ref<PartnerWithdrawal[]>([])
const total = ref(0)
const search = ref('')
const status = ref('requested')
const loading = ref(false)
const busy = ref(false)
const listError = ref('')

const statusItems = [
  { value: 'requested', label: 'Запрошенные' },
  { value: 'processing', label: 'В обработке' },
  { value: 'paid', label: 'Выплаченные' },
  { value: 'rejected', label: 'Отклонённые' },
  { value: 'failed', label: 'С ошибкой' },
  { value: 'all', label: 'Все' },
]

const statusLabels: Record<string, string> = {
  requested: 'Запрошена',
  processing: 'В обработке',
  paid: 'Выплачена',
  rejected: 'Отклонена',
  failed: 'Ошибка',
}

const statusTones: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'muted'> = {
  requested: 'warning',
  processing: 'default',
  paid: 'success',
  rejected: 'muted',
  failed: 'danger',
}

const actionLabels: Record<WithdrawalAction, string> = {
  processing: 'В обработку',
  paid: 'Выплачена',
  reject: 'Отклонить',
  fail: 'Отметить ошибкой',
}

const transitions: Record<string, WithdrawalAction[]> = {
  requested: ['processing', 'reject', 'fail'],
  processing: ['paid', 'reject', 'fail'],
  failed: ['processing', 'reject'],
}

const pending = ref<{ w: PartnerWithdrawal; action: WithdrawalAction } | null>(null)
const transitionMessage = ref('')
const transitionReference = ref('')
const transitionSettlement = ref('')

const revealTarget = ref<PartnerWithdrawal | null>(null)
const requisites = ref<Record<string, string> | null>(null)
const revealBusy = ref(false)

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

function errorText(err: unknown): string {
  const data = (err as { data?: { error?: string; message?: string } }).data || {}
  return data.message || data.error || (err as Error).message || 'request_failed'
}

function methodLabel(w: PartnerWithdrawal): string {
  const snapshot = w.method_snapshot || {}
  const label = snapshot.label
  return typeof label === 'string' && label ? label : w.method_id
}

async function load(reset = true) {
  loading.value = true
  listError.value = ''
  try {
    const res = await call<WithdrawalsResponse>('partner-withdrawals', {
      query: {
        status: status.value === 'all' ? '' : status.value,
        search: search.value.trim(),
        limit: PAGE,
        offset: reset ? 0 : withdrawals.value.length,
      },
    })
    withdrawals.value = reset ? res.withdrawals : [...withdrawals.value, ...res.withdrawals]
    total.value = res.total
  } catch (err) {
    listError.value = errorText(err)
  } finally {
    loading.value = false
  }
}

function openTransition(w: PartnerWithdrawal, action: WithdrawalAction) {
  pending.value = { w, action }
  transitionMessage.value = ''
  transitionReference.value = ''
  transitionSettlement.value = ''
}

const messageRequired = computed(() => pending.value?.action === 'reject')
const settlementRequired = computed(
  () => pending.value?.action === 'paid' && pending.value.w.method_type === 'crypto',
)
const confirmDisabled = computed(
  () =>
    (messageRequired.value && !transitionMessage.value.trim()) ||
    (settlementRequired.value && !transitionSettlement.value.trim()),
)

async function submitTransition() {
  if (!pending.value) return
  const { w, action } = pending.value
  busy.value = true
  try {
    await call(`partner-withdrawals/${w.withdrawal_id}/${action}`, {
      method: 'POST',
      body: {
        status_version: w.status_version,
        message: transitionMessage.value.trim() || null,
        external_reference: transitionReference.value.trim() || null,
        settlement_amount: transitionSettlement.value.trim() || null,
      },
    })
    emit(
      'notice',
      `Выплата #${w.withdrawal_id}: статус '${statusLabels[action === 'reject' ? 'rejected' : action === 'fail' ? 'failed' : action] || action}'`,
      false,
    )
    pending.value = null
    await load()
    emit('changed')
  } catch (err) {
    emit('notice', `Ошибка: ${errorText(err)}`, true)
  } finally {
    busy.value = false
  }
}

async function openReveal(w: PartnerWithdrawal) {
  revealTarget.value = w
  requisites.value = null
  revealBusy.value = true
  try {
    const res = await call<{ requisites: Record<string, string> }>(
      `partner-withdrawals/${w.withdrawal_id}/reveal`,
      { method: 'POST', body: {} },
    )
    requisites.value = res.requisites || {}
  } catch (err) {
    emit('notice', `Не удалось показать реквизиты: ${errorText(err)}`, true)
    revealTarget.value = null
  } finally {
    revealBusy.value = false
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
        placeholder="Партнёр или user_id"
        @keyup.enter="load()"
      />
      <div class="panel-select">
        <AdminSelect v-model="status" :items="statusItems" />
      </div>
      <button type="button" class="admin-btn" :disabled="loading" @click="load()">Найти</button>
    </div>

    <p v-if="listError" class="admin-note admin-error">Ошибка загрузки: {{ listError }}</p>
    <p v-if="loading && !withdrawals.length" class="admin-note">Загрузка...</p>

    <ul v-if="withdrawals.length" class="admin-list">
      <li v-for="w in withdrawals" :key="w.withdrawal_id" class="wd-item">
        <div class="admin-row wd-head">
          <strong>{{ fmtMoney(w.amount_minor, w.currency_scale, w.currency) }}</strong>
          <span class="admin-note">
            {{ w.display_label || `партнёр #${w.partner_id}` }}
            <template v-if="w.username"> (@{{ w.username }})</template>
            · {{ methodLabel(w) }} · {{ fmtDate(w.requested_at) }}
          </span>
          <AdminBadge :tone="statusTones[w.status] || 'default'">
            {{ statusLabels[w.status] || w.status }}
          </AdminBadge>
        </div>
        <p class="admin-note">
          Реквизиты: {{ w.masked_requisites }}
          <template v-if="w.settlement_asset"> · {{ w.settlement_asset }}</template>
          <template v-if="w.network"> · {{ w.network }}</template>
        </p>
        <p v-if="w.status_message" class="admin-note">Комментарий: {{ w.status_message }}</p>
        <p v-if="w.external_reference" class="admin-note">Референс: {{ w.external_reference }}</p>
        <p v-if="w.settlement_amount" class="admin-note">
          Выплачено: {{ w.settlement_amount }} {{ w.settlement_asset || '' }}
        </p>
        <div class="admin-row">
          <button type="button" class="admin-btn ghost" :disabled="busy" @click="openReveal(w)">
            Реквизиты
          </button>
          <button
            v-for="action in transitions[w.status] || []"
            :key="action"
            type="button"
            class="admin-btn"
            :class="{ ghost: action !== 'paid' }"
            :disabled="busy"
            @click="openTransition(w, action)"
          >
            {{ actionLabels[action] }}
          </button>
        </div>
      </li>
    </ul>
    <p v-else-if="!loading" class="admin-note">Выплат нет</p>

    <div v-if="withdrawals.length < total" class="admin-row">
      <button type="button" class="admin-btn ghost" :disabled="loading" @click="load(false)">
        Показать ещё ({{ withdrawals.length }} из {{ total }})
      </button>
    </div>
  </div>

  <AdminPartnersConfirmModal
    :open="pending !== null"
    :title="`Выплата #${pending?.w.withdrawal_id} - ${pending ? actionLabels[pending.action] : ''}`"
    :busy="busy"
    :danger="pending?.action === 'reject' || pending?.action === 'fail'"
    :confirm-label="pending ? actionLabels[pending.action] : 'Применить'"
    :disabled="confirmDisabled"
    @close="pending = null"
    @confirm="submitTransition"
  >
    <p class="admin-note">
      {{ pending?.w.display_label || `партнёр #${pending?.w.partner_id}` }} ·
      {{ pending ? fmtMoney(pending.w.amount_minor, pending.w.currency_scale, pending.w.currency) : '' }}
      · {{ pending ? methodLabel(pending.w) : '' }}
    </p>
    <label class="admin-field">
      <span>{{ messageRequired ? 'Причина отклонения (обязательно)' : 'Комментарий (необязательно)' }}</span>
      <input v-model="transitionMessage" class="admin-input" placeholder="Сообщение партнёру" />
    </label>
    <label class="admin-field">
      <span>Внешний референс (необязательно)</span>
      <input v-model="transitionReference" class="admin-input" placeholder="Номер перевода / txid" />
    </label>
    <label v-if="pending?.action === 'paid'" class="admin-field">
      <span>
        Сумма расчёта{{ settlementRequired ? ' (обязательно для crypto)' : ' (необязательно)' }}
      </span>
      <input
        v-model="transitionSettlement"
        class="admin-input"
        :placeholder="pending?.w.settlement_asset || 'USDT'"
      />
    </label>
  </AdminPartnersConfirmModal>

  <AdminModal
    :open="revealTarget !== null"
    :title="`Реквизиты выплаты #${revealTarget?.withdrawal_id}`"
    @close="revealTarget = null"
  >
    <p v-if="revealBusy" class="admin-note">Загрузка...</p>
    <template v-else-if="requisites">
      <p v-if="!Object.keys(requisites).length" class="admin-note">Реквизиты пусты</p>
      <div v-for="(value, key) in requisites" :key="key" class="req-row">
        <span class="admin-note">{{ key }}</span>
        <code>{{ value }}</code>
      </div>
    </template>
    <template #footer>
      <button type="button" class="admin-btn ghost" @click="revealTarget = null">Закрыть</button>
    </template>
  </AdminModal>
</template>

<style scoped>
.panel-search {
  flex: 1;
  min-width: 160px;
}
.panel-select {
  width: 180px;
}
.wd-item {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--adm-border, #232c3d);
}
.req-row {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 8px;
  align-items: baseline;
}
.req-row code {
  user-select: all;
  font-size: 13px;
  word-break: break-all;
}
.admin-field {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
}
</style>
