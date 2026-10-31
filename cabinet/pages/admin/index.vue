<script setup lang="ts">
interface StatsUsers {
  total_users?: number
  banned_users?: number
  active_today?: number
  active_subscriptions?: number
  paid_subscriptions?: number
  trial_users?: number
  free_subscription_users?: number
  inactive_users?: number
  expired_subscription_users?: number
  referral_users?: number
}

interface RevenuePoint {
  date: string
  amount: number
}

interface StatsFinancial {
  today_revenue?: number
  week_revenue?: number
  month_revenue?: number
  all_time_revenue?: number
  today_payments_count?: number
  admin_gifts_count?: number
  admin_gifts_activated_count?: number
  daily_series?: RevenuePoint[]
}

interface StatsPayment {
  payment_id: number
  user_id: number
  user_label?: string
  amount: number
  currency?: string | null
  provider?: string | null
  status?: string | null
  description?: string | null
  created_at?: string | null
}

interface StatsTariff {
  kind: string
  tariff_key?: string | null
  tariff_names?: Record<string, string>
  is_configured?: boolean
  is_enabled?: boolean | null
  active_users: number
}

interface PanelSync {
  status: string
  last_sync_time?: string | null
  users_processed?: number
  subscriptions_synced?: number
}

interface AdminStatsResponse {
  ok?: boolean
  users?: StatsUsers
  financial?: StatsFinancial
  panel_sync?: PanelSync | null
  recent_payments?: StatsPayment[]
  currency_symbol?: string
  active_tariffs?: StatsTariff[]
  panel?: Record<string, unknown> | null
  queue?: Record<string, unknown> | null
}

interface PartnerAttention {
  pending_applications?: number
  requested_withdrawals?: number
  total?: number
}

interface PartnerRow {
  partner_id: number
  user_id?: number | null
  display_label: string
  username?: string | null
  status: string
  kind?: string
  commission_bps?: number
  clients_count?: number
}

useHead({ title: 'Админка · Дашборд - Proliv Network' })

const { call } = useAdminApi()
const { plural } = useFormat()

const stats = ref<AdminStatsResponse | null>(null)
const attention = ref<PartnerAttention | null>(null)
const partners = ref<PartnerRow[]>([])
const partnersTotal = ref<number | null>(null)
const partnersFailed = ref(false)
const loading = ref(false)
const error = ref('')
const loadedAt = ref('')

const currency = computed(() => stats.value?.currency_symbol || 'RUB')
const users = computed<StatsUsers>(() => stats.value?.users || {})
const fin = computed<StatsFinancial>(() => stats.value?.financial || {})
const dailySeries = computed<RevenuePoint[]>(() =>
  Array.isArray(fin.value.daily_series) ? fin.value.daily_series : [],
)
const todayPayments = computed(() => Number(fin.value.today_payments_count) || 0)
const pendingApplications = computed(() => Number(attention.value?.pending_applications) || 0)
const requestedWithdrawals = computed(() => Number(attention.value?.requested_withdrawals) || 0)

function fmtNum(v: unknown): string {
  const n = Number(v)
  return Number.isFinite(n) ? new Intl.NumberFormat('ru-RU').format(n) : '—'
}

function fmtMoney(v: unknown): string {
  const n = Number(v)
  if (!Number.isFinite(n)) return '—'
  const code = (currency.value || 'RUB').toUpperCase()
  try {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: code,
      maximumFractionDigits: n % 1 ? 2 : 0,
    }).format(n)
  } catch {
    return `${fmtNum(n)} ${code}`
  }
}

function errText(e: unknown): string {
  return (e as { message?: string })?.message || 'request_failed'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [statsRes, attentionRes, partnersRes] = await Promise.allSettled([
      call<AdminStatsResponse>('stats'),
      call<PartnerAttention>('partners/attention'),
      call<{ partners?: PartnerRow[]; total?: number }>('partners', {
        query: { limit: 5 },
      }),
    ])
    if (statsRes.status === 'fulfilled') {
      stats.value = statsRes.value
    } else {
      error.value = errText(statsRes.reason)
    }
    attention.value = attentionRes.status === 'fulfilled' ? attentionRes.value : null
    if (partnersRes.status === 'fulfilled') {
      partners.value = partnersRes.value.partners || []
      partnersTotal.value = Number(partnersRes.value.total ?? partners.value.length)
      partnersFailed.value = false
    } else {
      partners.value = []
      partnersTotal.value = null
      partnersFailed.value = true
    }
    if (stats.value) {
      loadedAt.value = new Date().toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
      })
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="admin-page dash">
    <div class="dash-head">
      <div>
        <h1>Дашборд</h1>
        <p class="admin-note">Обзор ключевых метрик minishop</p>
      </div>
      <div class="admin-row">
        <span v-if="loadedAt" class="admin-note">Обновлено {{ loadedAt }}</span>
        <button class="admin-btn ghost" :disabled="loading" @click="load">Обновить</button>
      </div>
    </div>

    <p v-if="loading && !stats" class="admin-note">Загрузка...</p>

    <section v-else-if="error && !stats" class="admin-card">
      <h2>Не удалось загрузить данные</h2>
      <p class="admin-note admin-error">{{ error }}</p>
      <div>
        <button class="admin-btn" @click="load">Повторить</button>
      </div>
    </section>

    <template v-else-if="stats">
      <div class="admin-grid cols-3">
        <div class="admin-kpi">
          <small>Пользователи</small>
          <strong>{{ fmtNum(users.total_users) }}</strong>
          <small>+{{ fmtNum(users.active_today) }} сегодня</small>
          <small>
            заблокировано {{ fmtNum(users.banned_users) }} · рефералов
            {{ fmtNum(users.referral_users) }}
          </small>
        </div>
        <div class="admin-kpi">
          <small>Активные подписки</small>
          <strong>{{ fmtNum(users.active_subscriptions) }}</strong>
          <small>
            платных {{ fmtNum(users.paid_subscriptions) }} · триал
            {{ fmtNum(users.trial_users) }}
          </small>
          <small>бесплатных {{ fmtNum(users.free_subscription_users) }}</small>
        </div>
        <div class="admin-kpi">
          <small>Без подписки</small>
          <strong>{{ fmtNum(users.inactive_users) }}</strong>
          <small>истекла у {{ fmtNum(users.expired_subscription_users) }}</small>
        </div>
        <div class="admin-kpi">
          <small>Выручка сегодня</small>
          <strong>{{ fmtMoney(fin.today_revenue) }}</strong>
          <small>
            {{ fmtNum(todayPayments) }}
            {{ plural(todayPayments, 'платёж', 'платежа', 'платежей') }}
          </small>
        </div>
        <div class="admin-kpi">
          <small>Выручка за 30 дней</small>
          <strong>{{ fmtMoney(fin.month_revenue) }}</strong>
          <small>всего {{ fmtMoney(fin.all_time_revenue) }}</small>
        </div>
        <div class="admin-kpi">
          <small>Партнёры</small>
          <strong>{{ partnersTotal === null ? '—' : fmtNum(partnersTotal) }}</strong>
          <small v-if="attention">
            {{ fmtNum(pendingApplications + requestedWithdrawals) }} ожидают решения
          </small>
          <small v-else-if="partnersFailed">данные недоступны</small>
        </div>
      </div>

      <AdminDashboardAttentionCard
        v-if="attention"
        :pending-applications="pendingApplications"
        :requested-withdrawals="requestedWithdrawals"
      />

      <AdminDashboardRevenueChart :points="dailySeries" :currency="currency" />

      <div class="admin-grid cols-2">
        <AdminDashboardTariffDistribution :tariffs="stats.active_tariffs || []" />
        <AdminDashboardTopPartners
          :partners="partners"
          :total="partnersTotal"
          :load-failed="partnersFailed"
        />
      </div>

      <AdminDashboardPanelCard :panel="stats.panel || null" :sync="stats.panel_sync || null" />

      <AdminDashboardRecentPayments
        :payments="stats.recent_payments || []"
        :currency="currency"
      />
    </template>
  </main>
</template>

<style scoped>
.dash-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.dash-head h1 {
  margin: 0;
  font-size: 20px;
}
.dash-head p {
  margin: 4px 0 0;
}
.admin-kpi strong {
  font-variant-numeric: tabular-nums;
}
</style>
