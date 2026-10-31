<script setup lang="ts">
interface PartnerBalance {
  currency: string
  currency_scale: number
  available_minor: number
  pending_minor: number
  reserved_minor: number
  lifetime_earned_minor: number
}

interface PartnerListItem {
  partner_id: number
  user_id: number | null
  display_label: string
  username: string | null
  avatar_url: string | null
  status: string
  commission_bps: number
  kind: string
  banner_below_stream: boolean
  banner_on_stream: boolean
  created_at: string
  balances?: PartnerBalance[]
  clients_count?: number
  latest_client?: string | null
  payments_count?: number
  gross_minor?: number
  earned_minor?: number
}

interface PartnersListResponse {
  partners: PartnerListItem[]
  total: number
  limit: number
  offset: number
}

interface OverviewMetrics {
  active_partners: number
  paused_partners: number
  clients: number
  gross_minor: number
  commissions_minor: number
  pending_minor: number
  available_minor: number
  paid_minor: number
  requested_minor: number
}

interface OverviewResponse {
  currency: string
  currency_scale: number
  metrics: OverviewMetrics
  series: { date: string; gross_minor: number; commission_minor: number; paid_minor: number }[]
}

interface AttentionCounts {
  pending_applications: number
  requested_withdrawals: number
  total: number
}

interface BulkImportPreview {
  found: number
  importable: number
  already_this_partner: number
  other_partner: number
  self_conflict: number
  historical_payments: number
  partners: number
}

const { call } = useAdminApi()

const tab = ref<'partners' | 'applications' | 'withdrawals'>('partners')
const notice = ref('')
const noticeError = ref(false)

const attention = ref<AttentionCounts | null>(null)
const overview = ref<OverviewResponse | null>(null)
const overviewDays = ref('30')
const overviewItems = [
  { value: '30', label: '30 дней' },
  { value: '90', label: '90 дней' },
  { value: 'all', label: 'Всё время' },
]

const partners = ref<PartnerListItem[]>([])
const partnersTotal = ref(0)
const search = ref('')
const statusFilter = ref('all')
const kindFilter = ref('all')
const sort = ref('clients_desc')
const listLoading = ref(false)
const listError = ref('')

const selectedPartnerId = ref<number | null>(null)
const createOpen = ref(false)

const bulkOpen = ref(false)
const bulkPreview = ref<BulkImportPreview | null>(null)
const bulkLoading = ref(false)
const busy = ref(false)

const PAGE = 25

const statusItems = [
  { value: 'all', label: 'Все статусы' },
  { value: 'active', label: 'Активные' },
  { value: 'paused', label: 'На паузе' },
  { value: 'closed', label: 'Закрытые' },
]

const kindItems = [
  { value: 'all', label: 'Все типы' },
  { value: 'standard', label: 'Партнёр' },
  { value: 'streamer', label: 'Стример' },
  { value: 'clipper', label: 'Нарезчик' },
]

const sortItems = [
  { value: 'clients_desc', label: 'Клиенты ↓' },
  { value: 'earned_desc', label: 'Заработок ↓' },
  { value: 'gross_desc', label: 'Оборот ↓' },
  { value: 'available_desc', label: 'Доступно ↓' },
  { value: 'rate_desc', label: 'Ставка ↓' },
  { value: 'created_desc', label: 'Новые' },
  { value: 'user_asc', label: 'Имя А-Я' },
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

// kind-фильтра нет в API списка - фильтруем внутри загруженной страницы
const filteredPartners = computed(() =>
  kindFilter.value === 'all'
    ? partners.value
    : partners.value.filter((item) => (item.kind || 'standard') === kindFilter.value),
)

function fmtMoney(minor: number | null | undefined, scale = 2, currency = 'RUB'): string {
  const value = (minor ?? 0) / Math.pow(10, scale)
  const cur = currency === 'RUB' ? '₽' : currency
  return `${value.toLocaleString('ru-RU', { minimumFractionDigits: scale, maximumFractionDigits: scale })} ${cur}`
}

function pct(bps?: number | null): string {
  return `${((bps ?? 0) / 100).toLocaleString('ru-RU')}%`
}

function errorText(err: unknown): string {
  const data = (err as { data?: { error?: string; message?: string } }).data || {}
  return data.message || data.error || (err as Error).message || 'request_failed'
}

function onNotice(text: string, isError: boolean) {
  notice.value = text
  noticeError.value = isError
}

function primaryBalance(p: PartnerListItem): PartnerBalance | null {
  return p.balances?.[0] || null
}

async function loadAttention() {
  try {
    attention.value = await call<AttentionCounts>('partners/attention')
  } catch {
    attention.value = null
  }
}

async function loadOverview() {
  try {
    overview.value = await call<OverviewResponse>('partners/overview', {
      query: { currency: 'RUB', days: overviewDays.value },
    })
  } catch {
    overview.value = null
  }
}

async function loadPartners(reset = true) {
  listLoading.value = true
  listError.value = ''
  try {
    const res = await call<PartnersListResponse>('partners', {
      query: {
        status: statusFilter.value === 'all' ? '' : statusFilter.value,
        search: search.value.trim(),
        sort: sort.value,
        currency: 'RUB',
        limit: PAGE,
        offset: reset ? 0 : partners.value.length,
      },
    })
    partners.value = reset ? res.partners : [...partners.value, ...res.partners]
    partnersTotal.value = res.total
  } catch (err) {
    listError.value = errorText(err)
  } finally {
    listLoading.value = false
  }
}

function onChanged() {
  loadPartners()
  loadAttention()
}

async function openBulkImport() {
  bulkOpen.value = true
  bulkPreview.value = null
  bulkLoading.value = true
  try {
    const res = await call<{ preview: BulkImportPreview }>('partners/referral-import')
    bulkPreview.value = res.preview
  } catch (err) {
    onNotice(`Ошибка предпросмотра импорта: ${errorText(err)}`, true)
    bulkOpen.value = false
  } finally {
    bulkLoading.value = false
  }
}

async function submitBulkImport() {
  busy.value = true
  try {
    const res = await call<{
      result: { imported: number; existing: number; conflicts: number; partners_updated: number }
    }>('partners/referral-import', {
      method: 'POST',
      body: { confirm_without_retroactive_commission: true },
    })
    onNotice(
      `Массовый импорт: ${res.result.imported} клиентов у ${res.result.partners_updated} партнёров (конфликтов: ${res.result.conflicts})`,
      false,
    )
    bulkOpen.value = false
    await loadPartners()
  } catch (err) {
    onNotice(`Ошибка импорта: ${errorText(err)}`, true)
  } finally {
    busy.value = false
  }
}

watch([statusFilter, sort], () => loadPartners())
watch(overviewDays, loadOverview)

onMounted(() => {
  loadAttention()
  loadOverview()
  loadPartners()
})
</script>

<template>
  <main class="admin-page partners-page">
    <div class="admin-row partners-head">
      <h1>Партнёры</h1>
      <div class="admin-row">
        <button type="button" class="admin-btn ghost" :disabled="busy" @click="openBulkImport">
          Массовый импорт рефералов
        </button>
        <button type="button" class="admin-btn" @click="createOpen = true">Новый партнёр</button>
      </div>
    </div>

    <p v-if="notice" class="admin-note" :class="{ 'admin-error': noticeError }">{{ notice }}</p>

    <div class="admin-tabs">
      <button
        type="button"
        class="admin-tab"
        :class="{ active: tab === 'partners' }"
        @click="tab = 'partners'"
      >
        Партнёры
      </button>
      <button
        type="button"
        class="admin-tab"
        :class="{ active: tab === 'applications' }"
        @click="tab = 'applications'"
      >
        Заявки
        <AdminBadge v-if="attention?.pending_applications" tone="warning">
          {{ attention.pending_applications }}
        </AdminBadge>
      </button>
      <button
        type="button"
        class="admin-tab"
        :class="{ active: tab === 'withdrawals' }"
        @click="tab = 'withdrawals'"
      >
        Выплаты
        <AdminBadge v-if="attention?.requested_withdrawals" tone="warning">
          {{ attention.requested_withdrawals }}
        </AdminBadge>
      </button>
    </div>

    <template v-if="tab === 'partners'">
      <div class="admin-card">
        <div class="admin-row">
          <h2>Сводка</h2>
          <div class="range-select">
            <AdminSelect v-model="overviewDays" :items="overviewItems" />
          </div>
        </div>
        <div v-if="overview" class="admin-grid cols-3">
          <div class="admin-kpi">
            <small>Активные / на паузе</small>
            <strong>{{ overview.metrics.active_partners }} / {{ overview.metrics.paused_partners }}</strong>
          </div>
          <div class="admin-kpi">
            <small>Клиентов всего</small>
            <strong>{{ overview.metrics.clients }}</strong>
          </div>
          <div class="admin-kpi">
            <small>Оборот</small>
            <strong>{{ fmtMoney(overview.metrics.gross_minor, overview.currency_scale, overview.currency) }}</strong>
          </div>
          <div class="admin-kpi">
            <small>Комиссии начислено</small>
            <strong>{{ fmtMoney(overview.metrics.commissions_minor, overview.currency_scale, overview.currency) }}</strong>
          </div>
          <div class="admin-kpi">
            <small>Доступно / ожидает</small>
            <strong>
              {{ fmtMoney(overview.metrics.available_minor, overview.currency_scale, overview.currency) }}
              / {{ fmtMoney(overview.metrics.pending_minor, overview.currency_scale, overview.currency) }}
            </strong>
          </div>
          <div class="admin-kpi">
            <small>Выплачено / запрошено</small>
            <strong>
              {{ fmtMoney(overview.metrics.paid_minor, overview.currency_scale, overview.currency) }}
              / {{ fmtMoney(overview.metrics.requested_minor, overview.currency_scale, overview.currency) }}
            </strong>
          </div>
        </div>
        <p v-else class="admin-note">Сводка недоступна</p>
      </div>

      <div class="admin-card">
        <h2>Список партнёров</h2>
        <div class="admin-row">
          <input
            v-model="search"
            class="admin-input list-search"
            placeholder="Имя, код, partner_id или user_id"
            @keyup.enter="loadPartners()"
          />
          <button type="button" class="admin-btn" :disabled="listLoading" @click="loadPartners()">
            Найти
          </button>
        </div>
        <div class="admin-row">
          <div class="filter-select">
            <AdminSelect v-model="statusFilter" :items="statusItems" placeholder="Статус" />
          </div>
          <div class="filter-select">
            <AdminSelect v-model="kindFilter" :items="kindItems" placeholder="Тип" />
          </div>
          <div class="filter-select">
            <AdminSelect v-model="sort" :items="sortItems" placeholder="Сортировка" />
          </div>
        </div>
        <p v-if="kindFilter !== 'all'" class="admin-note">
          Фильтр по типу работает внутри загруженной страницы (в API фильтра по типу нет).
        </p>

        <p v-if="listError" class="admin-note admin-error">Ошибка загрузки: {{ listError }}</p>
        <p v-if="listLoading && !partners.length" class="admin-note">Загрузка...</p>

        <ul v-if="filteredPartners.length" class="admin-list">
          <li v-for="p in filteredPartners" :key="p.partner_id">
            <button
              type="button"
              class="admin-list-item"
              :class="{ selected: selectedPartnerId === p.partner_id }"
              @click="selectedPartnerId = p.partner_id"
            >
              <div class="admin-row row-head">
                <strong>{{ p.display_label }}</strong>
                <AdminBadge :tone="statusTones[p.status] || 'default'">
                  {{ statusLabels[p.status] || p.status }}
                </AdminBadge>
                <AdminBadge>{{ kindLabels[p.kind] || p.kind }}</AdminBadge>
                <AdminBadge v-if="p.banner_below_stream" tone="warning">Баннер под стримом</AdminBadge>
                <AdminBadge v-if="p.banner_on_stream" tone="warning">Баннер на стриме</AdminBadge>
              </div>
              <span>
                {{ p.username ? '@' + p.username : p.user_id ? 'user_id ' + p.user_id : 'без юзера' }}
                · ставка {{ pct(p.commission_bps) }}
                · клиентов {{ p.clients_count ?? 0 }}
                <template v-if="primaryBalance(p)">
                  · доступно
                  {{ fmtMoney(primaryBalance(p)!.available_minor, primaryBalance(p)!.currency_scale, primaryBalance(p)!.currency) }}
                </template>
              </span>
            </button>
          </li>
        </ul>
        <p v-else-if="!listLoading" class="admin-note">Партнёров не найдено</p>

        <div v-if="partners.length < partnersTotal" class="admin-row">
          <button type="button" class="admin-btn ghost" :disabled="listLoading" @click="loadPartners(false)">
            Показать ещё ({{ partners.length }} из {{ partnersTotal }})
          </button>
        </div>
      </div>

      <AdminPartnersPartnerDetail
        v-if="selectedPartnerId"
        :key="selectedPartnerId"
        :partner-id="selectedPartnerId"
        @notice="onNotice"
        @changed="onChanged"
      />
    </template>

    <section v-else-if="tab === 'applications'" class="admin-card">
      <h2>Заявки в партнёрскую программу</h2>
      <AdminPartnersApplicationsPanel @notice="onNotice" @changed="loadAttention" />
    </section>

    <section v-else class="admin-card">
      <h2>Заявки на выплату</h2>
      <AdminPartnersWithdrawalsPanel @notice="onNotice" @changed="loadAttention" />
    </section>

    <AdminPartnersPartnerCreateModal
      :open="createOpen"
      @close="createOpen = false"
      @notice="onNotice"
      @created="
        (partner) => {
          loadPartners()
          loadAttention()
          selectedPartnerId = partner.partner_id
        }
      "
    />

    <AdminPartnersConfirmModal
      :open="bulkOpen"
      title="Массовый импорт рефералов"
      :busy="busy || bulkLoading"
      confirm-label="Импортировать"
      :disabled="bulkLoading || !bulkPreview || bulkPreview.importable === 0"
      @close="bulkOpen = false"
      @confirm="submitBulkImport"
    >
      <p v-if="bulkLoading" class="admin-note">Считаем кандидатов...</p>
      <template v-else-if="bulkPreview">
        <p class="admin-note">
          Партнёров с необработанными рефералами: {{ bulkPreview.partners }} · рефералов найдено:
          {{ bulkPreview.found }} · можно импортировать: {{ bulkPreview.importable }} · уже
          привязаны: {{ bulkPreview.already_this_partner }} · у других партнёров:
          {{ bulkPreview.other_partner }} · конфликтов с самим партнёром:
          {{ bulkPreview.self_conflict }}
        </p>
        <p class="admin-note">
          Исторических платежей у импортируемых: {{ bulkPreview.historical_payments }}. Комиссия за
          уже оплаченные платежи начислена не будет.
        </p>
        <p v-if="!bulkPreview.importable" class="admin-note">Импортировать некого.</p>
      </template>
    </AdminPartnersConfirmModal>
  </main>
</template>

<style scoped>
.partners-page h1 {
  margin: 0;
  font-size: 20px;
}
.partners-head {
  justify-content: space-between;
}
.admin-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--adm-border, #232c3d);
  padding-bottom: 8px;
}
.admin-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--adm-muted, #8b95a8);
  font-size: 13px;
  cursor: pointer;
}
.admin-tab:hover {
  color: var(--adm-text, #e8ecf4);
}
.admin-tab.active {
  color: var(--adm-accent, #3b82f6);
  background: var(--adm-accent-soft, rgba(59, 130, 246, 0.14));
}
.range-select {
  width: 140px;
}
.list-search {
  flex: 1;
  min-width: 160px;
}
.filter-select {
  flex: 1;
  min-width: 150px;
}
.row-head {
  gap: 6px;
}
.admin-list-item.selected {
  border-color: var(--adm-accent, #3b82f6);
}
</style>
