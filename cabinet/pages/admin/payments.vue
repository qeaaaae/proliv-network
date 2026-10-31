<script setup lang="ts">
// Платежи: GET /api/admin/payments (?page&page_size&sort&search),
// GET /api/admin/payments/{id}, POST /api/admin/payments/{id}/finalize|reverse,
// GET /api/admin/payments/export.csv. Админ-гейт - в pages/admin.vue.
// Серверных фильтров по статусу/провайдеру/валюте и датам в API нет -
// селекты ниже фильтруют уже загруженную страницу.
import { Download, RefreshCw } from '@lucide/vue'
import AdminPaymentsDetailModal from '~/components/admin/payments/DetailModal.vue'
import AdminPaymentsTable from '~/components/admin/payments/Table.vue'
import { paymentErrorText } from '~/components/admin/payments/types'
import type {
  AdminPayment,
  AdminPaymentActionSubmit,
  AdminPaymentDetail,
  AdminPaymentsListResponse,
} from '~/components/admin/payments/types'
import type { AdminApiError } from '~/composables/useAdminApi'

const { call } = useAdminApi()
const { push } = useToast()

const payments = ref<AdminPayment[]>([])
const total = ref(0)
const page = ref(0)
// AdminSelect работает со строками - в query уходит Number(pageSize).
const pageSize = ref('25')
const loading = ref(false)
const errorText = ref('')

const search = ref('')
const statusFilter = ref('')
const providerFilter = ref('')
const currencyFilter = ref('')
const sort = ref('date_desc')

const detailOpen = ref(false)
const detail = ref<AdminPaymentDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
const actionBusy = ref(false)

const statusItems = [
  { value: '', label: 'Все статусы' },
  { value: 'succeeded', label: 'Оплачен' },
  { value: 'succeeded_pending_finalization', label: 'Оплачен · применяем покупку' },
  { value: 'succeeded_pending_review', label: 'Оплачен · нужна проверка' },
  { value: 'pending', label: 'Ожидает оплаты' },
  { value: 'refunded', label: 'Возвращён' },
  { value: 'failed', label: 'Ошибка / отменён' },
]
const sortItems = [
  { value: 'date_desc', label: 'Сначала новые' },
  { value: 'date_asc', label: 'Сначала старые' },
  { value: 'amount_desc', label: 'Сумма по убыванию' },
  { value: 'amount_asc', label: 'Сумма по возрастанию' },
  { value: 'status_asc', label: 'По статусу' },
  { value: 'provider_asc', label: 'По провайдеру' },
  { value: 'user_asc', label: 'По пользователю' },
  { value: 'id_desc', label: 'По ID' },
]
const pageSizeItems = [
  { value: '25', label: '25 на странице' },
  { value: '50', label: '50 на странице' },
  { value: '100', label: '100 на странице' },
]

const pageCount = computed(() =>
  Math.max(1, Math.ceil(total.value / Number(pageSize.value) || 25)),
)

const providerItems = computed(() => [
  { value: '', label: 'Все провайдеры' },
  ...[...new Set(payments.value.map((p) => (p.provider || '').trim()).filter(Boolean))]
    .sort()
    .map((value) => ({ value, label: value })),
])
const currencyItems = computed(() => [
  { value: '', label: 'Все валюты' },
  ...[...new Set(payments.value.map((p) => (p.currency || '').trim()).filter(Boolean))]
    .sort()
    .map((value) => ({ value, label: value })),
])

const filtersActive = computed(
  () => Boolean(statusFilter.value || providerFilter.value || currencyFilter.value),
)

function statusMatches(status: string | null, filter: string): boolean {
  if (!filter) return true
  const s = (status || '').trim().toLowerCase()
  if (filter === 'pending') return s.startsWith('pending')
  if (filter === 'failed') {
    return (
      s === 'failed' ||
      s.startsWith('failed_') ||
      s === 'canceled' ||
      s === 'cancelled' ||
      s === 'creation_unknown'
    )
  }
  return s === filter
}

// Клиентская фильтрация текущей страницы: API отдаёт только page/page_size/sort/search.
const visible = computed(() =>
  payments.value.filter(
    (p) =>
      statusMatches(p.status, statusFilter.value) &&
      (!providerFilter.value || (p.provider || '').trim() === providerFilter.value) &&
      (!currencyFilter.value || (p.currency || '').trim() === currencyFilter.value),
  ),
)

async function load() {
  loading.value = true
  errorText.value = ''
  try {
    const res = await call<AdminPaymentsListResponse>('payments', {
      query: {
        page: page.value,
        page_size: Number(pageSize.value) || 25,
        sort: sort.value,
        search: search.value.trim(),
      },
    })
    payments.value = res.payments || []
    total.value = res.total || 0
  } catch (e) {
    errorText.value = `Ошибка загрузки: ${(e as Error).message || 'failed'}`
    payments.value = []
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 0
  load()
}

watch([sort, pageSize], applyFilters)

async function openPayment(p: AdminPayment) {
  // Сначала показываем данные строки, детали подгружаем с detail-эндпоинта.
  detail.value = p as AdminPaymentDetail
  detailError.value = ''
  detailOpen.value = true
  detailLoading.value = true
  try {
    const res = await call<{ payment: AdminPaymentDetail }>(`payments/${p.payment_id}`)
    detail.value = res.payment
  } catch (e) {
    detailError.value = paymentErrorText((e as AdminApiError).code || (e as Error).message)
  } finally {
    detailLoading.value = false
  }
}

async function refreshDetail(paymentId: number) {
  try {
    const res = await call<{ payment: AdminPaymentDetail }>(`payments/${paymentId}`)
    detail.value = res.payment
  } catch {
    // тихо - основная ошибка уже показана
  }
}

async function submitAction(payload: AdminPaymentActionSubmit) {
  const p = detail.value
  if (!p) return
  actionBusy.value = true
  detailError.value = ''
  try {
    const res = await call<{ payment: AdminPaymentDetail }>(
      `payments/${p.payment_id}/${payload.mode === 'finalize' ? 'finalize' : 'reverse'}`,
      {
        method: 'POST',
        body:
          payload.mode === 'finalize'
            ? {
                reason: payload.reason,
                confirm_promo_conflict: payload.confirmPromoConflict,
                confirm_subscription_end_change: payload.confirmSubscriptionEndChange,
              }
            : {
                reason: payload.reason,
                without_reason: payload.withoutReason,
                restore_promo_usage: payload.restorePromoUsage,
                refund_to_balance: payload.refundToBalance,
              },
      },
    )
    detail.value = res.payment
    push(payload.mode === 'finalize' ? 'Платёж проведён' : 'Платёж отменён')
    await load()
  } catch (e) {
    detailError.value = paymentErrorText(
      (e as AdminApiError).code || (e as Error).message,
    )
    // Подтянуть свежие флаги can_*/warnings - например после 409.
    await refreshDetail(p.payment_id)
  } finally {
    actionBusy.value = false
  }
}

function exportCsv() {
  window.open('/api/admin/payments/export.csv', '_blank')
}

onMounted(load)
</script>

<template>
  <main class="admin-page">
    <div class="admin-row page-head">
      <h1 class="page-title">Платежи</h1>
      <div class="admin-row">
        <button type="button" class="admin-btn ghost" :disabled="loading" @click="load">
          <RefreshCw :size="14" />
          Обновить
        </button>
        <button type="button" class="admin-btn ghost" @click="exportCsv">
          <Download :size="14" />
          Экспорт CSV
        </button>
      </div>
    </div>

    <section class="admin-card filters">
      <div class="admin-row">
        <input
          v-model="search"
          class="admin-input search"
          placeholder="ID пользователя, @username, имя или email"
          @keyup.enter="applyFilters"
        />
        <button type="button" class="admin-btn ghost" :disabled="loading" @click="applyFilters">
          Найти
        </button>
      </div>
      <div class="admin-grid cols-3">
        <AdminSelect v-model="statusFilter" :items="statusItems" />
        <AdminSelect v-model="providerFilter" :items="providerItems" />
        <AdminSelect v-model="currencyFilter" :items="currencyItems" />
      </div>
      <div class="admin-grid cols-3">
        <AdminSelect v-model="sort" :items="sortItems" />
        <AdminSelect v-model="pageSize" :items="pageSizeItems" />
      </div>
      <p v-if="filtersActive" class="admin-note">
        Статус, провайдер и валюта фильтруют текущую страницу - API отдаёт фильтр только по
        поиску и сортировке.
      </p>
    </section>

    <section class="admin-card">
      <p v-if="loading && !payments.length" class="admin-note">Загрузка...</p>
      <p v-else-if="errorText" class="admin-note admin-error">{{ errorText }}</p>
      <p v-else-if="!payments.length" class="admin-note">Нет платежей</p>
      <p v-else-if="!visible.length" class="admin-note">
        На этой странице нет платежей под текущие фильтры
      </p>

      <AdminPaymentsTable v-else :payments="visible" @open="openPayment" />

      <div class="admin-row pager">
        <button
          type="button"
          class="admin-btn ghost"
          :disabled="page === 0 || loading"
          @click="page--; load()"
        >
          Назад
        </button>
        <span class="admin-note"
          >Страница {{ page + 1 }} из {{ pageCount }} · всего {{ total
          }}<template v-if="filtersActive"> · на странице: {{ visible.length }}</template></span
        >
        <button
          type="button"
          class="admin-btn ghost"
          :disabled="page + 1 >= pageCount || loading"
          @click="page++; load()"
        >
          Вперёд
        </button>
      </div>
    </section>

    <AdminPaymentsDetailModal
      :open="detailOpen"
      :payment="detail"
      :loading="detailLoading"
      :busy="actionBusy"
      :error-text="detailError"
      @close="detailOpen = false"
      @action="submitAction"
    />
  </main>
</template>

<style scoped>
.page-head {
  justify-content: space-between;
}
.page-title {
  margin: 0;
  font-size: 20px;
}
.filters {
  gap: 10px;
}
.search {
  flex: 1;
}
.pager {
  justify-content: center;
}
.admin-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
