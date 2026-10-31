<script setup lang="ts">
// Активации промокода: GET /api/admin/promos/{id}/activations
// (?page&page_size&sort) -> { activations, page, total, revenue_summary }.
interface PromoActivation {
  activation_id: number
  promo_id: number
  user_id: number
  user_minishop_id: string | null
  user_label: string
  telegram_id: number | null
  activated_at: string | null
  payment_id: number | null
  payment_amount: number | null
  payment_currency: string | null
  payment_status: string | null
  payment_provider: string | null
  payment_sale_mode: string | null
  payment_description: string | null
  payment_created_at: string | null
  effect_summary: string | null
  bonus_days: number | null
  discount_percent: number | null
  applies_to: string | null
  base_amount: number | null
  discount_amount: number | null
  charged_months: number | null
  charged_days: number | null
  charged_gb: number | null
  granted_days: number | null
  granted_gb: number | null
  granted_regular_traffic_gb: number | null
  granted_premium_traffic_gb: number | null
}

interface RevenueSummary {
  payments_total: number
  revenue_payments: number
  currencies: { currency: string; amount: number; payments: number }[]
}

const props = defineProps<{ open: boolean; promoId: number | null; code: string }>()
const emit = defineEmits<{ close: [] }>()

const { call } = useAdminApi()
const { dateTime } = useFormat()

const rows = ref<PromoActivation[]>([])
const summary = ref<RevenueSummary | null>(null)
const total = ref(0)
const page = ref(0)
const pageSize = 25
const sort = ref('date_desc')
const loading = ref(false)
const errorText = ref('')

const sortItems = [
  { value: 'date_desc', label: 'Сначала новые' },
  { value: 'date_asc', label: 'Сначала старые' },
  { value: 'user_asc', label: 'По пользователю' },
  { value: 'amount_desc', label: 'По сумме оплаты' },
  { value: 'status_asc', label: 'По статусу оплаты' },
]

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const revenueText = computed(() => {
  const s = summary.value
  if (!s || !s.currencies.length) return ''
  return s.currencies
    .map((c) => `${fmtAmount(c.amount)} ${c.currency} (${c.payments} пл.)`)
    .join(' · ')
})

async function load() {
  if (props.promoId === null) return
  loading.value = true
  errorText.value = ''
  try {
    const res = await call<{
      activations: PromoActivation[]
      total: number
      revenue_summary: RevenueSummary
    }>(`promos/${props.promoId}/activations`, {
      query: { page: page.value, page_size: pageSize, sort: sort.value },
    })
    rows.value = res.activations || []
    total.value = res.total || 0
    summary.value = res.revenue_summary || null
  } catch (e) {
    errorText.value = `Ошибка загрузки: ${(e as Error).message || 'failed'}`
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.open, props.promoId],
  ([open]) => {
    if (open) {
      page.value = 0
      sort.value = 'date_desc'
      load()
    }
  },
)
watch([page, sort], () => {
  if (props.open) load()
})

function fmtAmount(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(v)
}

function fmtNum(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return Number.isInteger(v) ? String(v) : v.toFixed(3).replace(/0+$/, '').replace(/\.$/, '')
}

function paymentText(a: PromoActivation): string {
  if (!a.payment_id) return 'без оплаты'
  const amount =
    a.payment_amount !== null
      ? `${fmtAmount(a.payment_amount)} ${a.payment_currency || ''}`.trim()
      : ''
  return [`#${a.payment_id}`, amount, a.payment_provider || ''].filter(Boolean).join(' · ')
}

function paymentTone(a: PromoActivation): 'success' | 'warning' | 'danger' | 'muted' {
  const s = (a.payment_status || '').toLowerCase()
  if (!a.payment_id) return 'muted'
  if (s === 'succeeded' || s === 'completed') return 'success'
  if (s === 'refunded' || s === 'failed' || s === 'cancelled') return 'danger'
  return 'warning'
}

function grantText(a: PromoActivation): string {
  const parts: string[] = []
  if (a.granted_days) parts.push(`+${a.granted_days} дн.`)
  if (a.granted_gb !== null && a.granted_gb !== undefined) {
    parts.push(
      a.charged_gb !== null && a.charged_gb !== undefined
        ? `${fmtNum(a.charged_gb)} -> ${fmtNum(a.granted_gb)} ГБ`
        : `${fmtNum(a.granted_gb)} ГБ`,
    )
  }
  if (a.granted_regular_traffic_gb) parts.push(`+${fmtNum(a.granted_regular_traffic_gb)} ГБ обычн.`)
  if (a.granted_premium_traffic_gb) parts.push(`+${fmtNum(a.granted_premium_traffic_gb)} ГБ прем.`)
  return parts.join(', ') || '—'
}

function userText(a: PromoActivation): string {
  const parts = [a.user_label || `#${a.user_id}`]
  if (a.telegram_id) parts.push(`tg ${a.telegram_id}`)
  return parts.join(' · ')
}
</script>

<template>
  <AdminModal :open="open" :title="`Активации - ${code}`" @close="emit('close')">
    <div class="acts">
      <div class="admin-row acts-head">
        <AdminSelect v-model="sort" :items="sortItems" class="acts-sort" />
        <span class="admin-note">Всего: {{ total }}</span>
      </div>

      <p v-if="loading" class="admin-note">Загрузка...</p>
      <p v-else-if="errorText" class="admin-note admin-error">{{ errorText }}</p>
      <p v-else-if="!rows.length" class="admin-note">Активаций пока нет</p>

      <div v-else class="acts-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Дата</th>
              <th>Оплата</th>
              <th>Выдано</th>
              <th>Эффект</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in rows" :key="a.activation_id">
              <td>{{ userText(a) }}</td>
              <td>{{ a.activated_at ? dateTime(a.activated_at) : '—' }}</td>
              <td>
                <AdminBadge :tone="paymentTone(a)">{{ paymentText(a) }}</AdminBadge>
              </td>
              <td>{{ grantText(a) }}</td>
              <td>{{ a.effect_summary || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="summary" class="admin-note">
        Платежей по промокоду: {{ summary.payments_total }} · оплачено: {{ summary.revenue_payments
        }}<template v-if="revenueText"> · выручка: {{ revenueText }}</template>
      </p>

      <div v-if="pageCount > 1" class="admin-row acts-pager">
        <button type="button" class="admin-btn ghost" :disabled="page === 0 || loading" @click="page--">
          Назад
        </button>
        <span class="admin-note">{{ page + 1 }} / {{ pageCount }}</span>
        <button
          type="button"
          class="admin-btn ghost"
          :disabled="page + 1 >= pageCount || loading"
          @click="page++"
        >
          Вперёд
        </button>
      </div>
    </div>
    <template #footer>
      <button type="button" class="admin-btn ghost" @click="emit('close')">Закрыть</button>
    </template>
  </AdminModal>
</template>

<style scoped>
.acts {
  display: grid;
  gap: 12px;
}
.acts-head {
  justify-content: space-between;
}
.acts-sort {
  max-width: 220px;
}
.acts-table-wrap {
  overflow-x: auto;
}
.acts-pager {
  justify-content: center;
}
</style>
