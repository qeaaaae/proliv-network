<script setup lang="ts">
// Промокоды: GET/POST /api/admin/promos, PATCH/DELETE /api/admin/promos/{id},
// GET /api/admin/promos/{id}/activations. Админ-гейт - в pages/admin.vue.
import { Check, Copy, History, Pencil, Plus, Power, RefreshCw, Trash2 } from '@lucide/vue'

interface AdminPromo {
  id: number
  code: string
  bot_link: string | null
  webapp_link: string | null
  app_link: string | null
  bonus_days: number
  regular_traffic_gb: number
  premium_traffic_gb: number
  discount_percent: number | null
  duration_multiplier: number | null
  traffic_multiplier: number | null
  bonus_requires_payment: boolean
  applies_to: string
  min_subscription_months: number | null
  min_subscription_days: number | null
  min_traffic_gb: number | null
  origin: string
  effect_summary: string
  max_activations: number
  current_activations: number
  is_active: boolean
  valid_until: string | null
  created_at: string | null
  user_id: number | null
  user_username: string | null
  user_name: string | null
}

const { call } = useAdminApi()
const { push } = useToast()
const { dateTime } = useFormat()

const promos = ref<AdminPromo[]>([])
const total = ref(0)
const ownedTotal = ref(0)
const page = ref(0)
const pageSize = 25
const loading = ref(false)
const errorText = ref('')

const search = ref('')
const statusFilter = ref('')
const scopeFilter = ref('')
const kindFilter = ref('')
const sort = ref('created_desc')

const formOpen = ref(false)
const editing = ref<AdminPromo | null>(null)
const actsOpen = ref(false)
const actsPromo = ref<AdminPromo | null>(null)
const deleting = ref<AdminPromo | null>(null)
const deleteBusy = ref(false)
const copiedId = ref<number | null>(null)

const statusItems = [
  { value: '', label: 'Все статусы' },
  { value: 'active', label: 'Активные' },
  { value: 'disabled', label: 'Выключенные' },
  { value: 'expired', label: 'Истекшие' },
  { value: 'used_up', label: 'Исчерпанные' },
]
const scopeItems = [
  { value: '', label: 'Все области' },
  { value: 'all', label: 'Всё' },
  { value: 'subscription', label: 'Подписка' },
  { value: 'traffic', label: 'Пакеты трафика' },
  { value: 'traffic_topup', label: 'Докупка трафика' },
  { value: 'hwid', label: 'Устройства (HWID)' },
]
const kindItems = [
  { value: '', label: 'Все промокоды' },
  { value: 'personal', label: 'Персональные' },
  { value: 'shared', label: 'Общие' },
]
const sortItems = [
  { value: 'created_desc', label: 'Сначала новые' },
  { value: 'created_asc', label: 'Сначала старые' },
  { value: 'code_asc', label: 'Код А-Я' },
  { value: 'code_desc', label: 'Код Я-А' },
  { value: 'activations_desc', label: 'Больше активаций' },
  { value: 'activations_asc', label: 'Меньше активаций' },
  { value: 'valid_until_asc', label: 'Скоро истекают' },
]

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const hasOwnerColumn = computed(
  () => kindFilter.value === 'personal' || promos.value.some((p) => p.user_id !== null),
)

const scopeLabels: Record<string, string> = {
  all: 'Всё',
  subscription: 'Подписка',
  traffic: 'Трафик',
  traffic_topup: 'Докупка',
  hwid: 'HWID',
}

async function load() {
  loading.value = true
  errorText.value = ''
  try {
    const res = await call<{
      promos: AdminPromo[]
      total: number
      owned_total: number
    }>('promos', {
      query: {
        page: page.value,
        page_size: pageSize,
        sort: sort.value,
        search: search.value.trim(),
        status: statusFilter.value,
        scope: scopeFilter.value,
        kind: kindFilter.value,
      },
    })
    promos.value = res.promos || []
    total.value = res.total || 0
    ownedTotal.value = res.owned_total || 0
  } catch (e) {
    errorText.value = `Ошибка загрузки: ${(e as Error).message || 'failed'}`
    promos.value = []
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 0
  load()
}

watch([statusFilter, scopeFilter, kindFilter, sort], applyFilters)

function ownerLabel(p: AdminPromo): string {
  if (p.user_username) return `@${p.user_username}`
  if (p.user_name) return p.user_name
  return `#${p.user_id}`
}

function validityLabel(p: AdminPromo): string {
  if (!p.valid_until) return 'Бессрочно'
  return dateTime(p.valid_until)
}

async function copyCode(p: AdminPromo) {
  try {
    await navigator.clipboard.writeText(p.code)
    copiedId.value = p.id
    push(`Код ${p.code} скопирован`)
    setTimeout(() => {
      if (copiedId.value === p.id) copiedId.value = null
    }, 1500)
  } catch {
    push('Не удалось скопировать', 'error')
  }
}

function openCreate() {
  editing.value = null
  formOpen.value = true
}

function openEdit(p: AdminPromo) {
  editing.value = p
  formOpen.value = true
}

function openActivations(p: AdminPromo) {
  actsPromo.value = p
  actsOpen.value = true
}

async function toggleActive(p: AdminPromo) {
  try {
    await call<{ promo: AdminPromo }>(`promos/${p.id}`, {
      method: 'PATCH',
      body: { is_active: !p.is_active },
    })
    push(p.is_active ? `${p.code} выключен` : `${p.code} включён`)
    await load()
  } catch (e) {
    push(`Ошибка: ${(e as Error).message || 'failed'}`, 'error')
  }
}

async function confirmDelete() {
  if (!deleting.value) return
  deleteBusy.value = true
  try {
    await call(`promos/${deleting.value.id}`, { method: 'DELETE', body: {} })
    push(`Промокод ${deleting.value.code} удалён`)
    deleting.value = null
    await load()
  } catch (e) {
    push(`Ошибка удаления: ${(e as Error).message || 'failed'}`, 'error')
  } finally {
    deleteBusy.value = false
  }
}

function onSaved() {
  load()
}

onMounted(load)
</script>

<template>
  <main class="admin-page">
    <div class="admin-row page-head">
      <h1 class="page-title">Промокоды</h1>
      <div class="admin-row">
        <button type="button" class="admin-btn ghost" :disabled="loading" @click="load">
          <RefreshCw :size="14" />
          Обновить
        </button>
        <button type="button" class="admin-btn" @click="openCreate">
          <Plus :size="14" />
          Создать
        </button>
      </div>
    </div>

    <section class="admin-card filters">
      <div class="admin-row">
        <input
          v-model="search"
          class="admin-input search"
          placeholder="Поиск по коду"
          @keyup.enter="applyFilters"
        />
        <button type="button" class="admin-btn ghost" :disabled="loading" @click="applyFilters">
          Найти
        </button>
      </div>
      <div class="admin-grid cols-3">
        <AdminSelect v-model="statusFilter" :items="statusItems" />
        <AdminSelect v-model="scopeFilter" :items="scopeItems" />
        <AdminSelect v-model="sort" :items="sortItems" />
      </div>
      <div v-if="ownedTotal > 0" class="admin-grid cols-3">
        <AdminSelect v-model="kindFilter" :items="kindItems" />
      </div>
    </section>

    <section class="admin-card">
      <p v-if="loading" class="admin-note">Загрузка...</p>
      <p v-else-if="errorText" class="admin-note admin-error">{{ errorText }}</p>
      <p v-else-if="!promos.length" class="admin-note">Промокоды не найдены</p>

      <div v-else class="table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Код</th>
              <th>Эффект</th>
              <th>Область</th>
              <th>Активации</th>
              <th>Действует до</th>
              <th>Статус</th>
              <th v-if="hasOwnerColumn">Владелец</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in promos" :key="p.id">
              <td>
                <div class="code-cell">
                  <code class="code">{{ p.code }}</code>
                  <button
                    type="button"
                    class="icon-btn"
                    title="Скопировать код"
                    :aria-label="`Скопировать ${p.code}`"
                    @click="copyCode(p)"
                  >
                    <Check v-if="copiedId === p.id" :size="14" class="ok" />
                    <Copy v-else :size="14" />
                  </button>
                </div>
              </td>
              <td>{{ p.effect_summary }}</td>
              <td>
                <AdminBadge tone="default">{{ scopeLabels[p.applies_to] || p.applies_to }}</AdminBadge>
              </td>
              <td>{{ p.current_activations }} / {{ p.max_activations }}</td>
              <td>{{ validityLabel(p) }}</td>
              <td><AdminPromosStatusBadge :promo="p" /></td>
              <td v-if="hasOwnerColumn">
                <AdminBadge v-if="p.user_id !== null" tone="muted">{{ ownerLabel(p) }}</AdminBadge>
                <span v-else class="admin-note">—</span>
              </td>
              <td>
                <div class="row-actions">
                  <button
                    type="button"
                    class="icon-btn"
                    title="Активации"
                    @click="openActivations(p)"
                  >
                    <History :size="15" />
                  </button>
                  <button type="button" class="icon-btn" title="Изменить" @click="openEdit(p)">
                    <Pencil :size="15" />
                  </button>
                  <button
                    type="button"
                    class="icon-btn"
                    :title="p.is_active ? 'Выключить' : 'Включить'"
                    @click="toggleActive(p)"
                  >
                    <Power :size="15" :class="{ off: !p.is_active }" />
                  </button>
                  <button
                    type="button"
                    class="icon-btn danger"
                    title="Удалить"
                    @click="deleting = p"
                  >
                    <Trash2 :size="15" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="admin-row pager">
        <button type="button" class="admin-btn ghost" :disabled="page === 0 || loading" @click="page--; load()">
          Назад
        </button>
        <span class="admin-note">Страница {{ page + 1 }} из {{ pageCount }} · всего {{ total }}</span>
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

    <AdminPromosFormModal
      :open="formOpen"
      :promo="editing"
      @close="formOpen = false"
      @saved="onSaved"
    />
    <AdminPromosActivationsModal
      :open="actsOpen"
      :promo-id="actsPromo?.id ?? null"
      :code="actsPromo?.code || ''"
      @close="actsOpen = false"
    />

    <AdminModal :open="deleting !== null" title="Удалить промокод" @close="deleting = null">
      <p class="admin-note">
        Удалить промокод <code class="code">{{ deleting?.code }}</code
        >? Использованных активаций: {{ deleting?.current_activations || 0 }}. Действие
        необратимое.
      </p>
      <template #footer>
        <button type="button" class="admin-btn ghost" :disabled="deleteBusy" @click="deleting = null">
          Отмена
        </button>
        <button type="button" class="admin-btn danger" :disabled="deleteBusy" @click="confirmDelete">
          {{ deleteBusy ? 'Удаление...' : 'Удалить' }}
        </button>
      </template>
    </AdminModal>
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
.table-wrap {
  overflow-x: auto;
}
.code-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}
.code {
  font-family: ui-monospace, monospace;
  font-size: 13px;
  color: var(--adm-accent, #3b82f6);
}
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--adm-muted, #8b95a8);
  cursor: pointer;
}
.icon-btn:hover {
  border-color: var(--adm-border, #232c3d);
  color: var(--adm-text, #e8ecf4);
}
.icon-btn.danger:hover {
  color: var(--adm-danger, #f87171);
  border-color: rgba(248, 113, 113, 0.4);
}
.icon-btn .ok {
  color: var(--adm-success, #34d399);
}
.icon-btn .off {
  color: var(--adm-danger, #f87171);
}
.row-actions {
  display: flex;
  gap: 2px;
  justify-content: flex-end;
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
