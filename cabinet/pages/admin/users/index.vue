<script setup lang="ts">
import {
  adminErrorMessage,
  fmtDateTime,
  fmtMinor,
  fmtMoney,
  planLabel,
  premiumTrafficLabel,
  premiumTrafficTone,
  tariffName,
  userDisplayName,
  userSecondaryLine,
} from '~/components/admin/users/format'
import type { AdminUsersListResponse } from '~/components/admin/users/types'

const { call } = useAdminApi()

const search = ref('')
const filterValue = ref('all')
const panelStatus = ref('all')
const premiumTraffic = ref('all')
const tariffFilter = ref('all')
const sortValue = ref('registered_desc')
const page = ref(0)
const pageSize = 25

const users = ref<AdminUsersListResponse['users']>([])
const total = ref(0)
const tariffOptions = ref<AdminUsersListResponse['tariff_options']>([])
const balanceEnabled = ref(false)
const partnerBalanceEnabled = ref(false)
const balanceCurrency = ref('RUB')
const balanceScale = ref(2)
const busy = ref(false)
const error = ref('')
const loaded = ref(false)

const filterItems = [
  { value: 'all', label: 'Все' },
  { value: 'active', label: 'Активные' },
  { value: 'banned', label: 'Заблокированные' },
  { value: 'paid', label: 'Платящие' },
  { value: 'trial', label: 'Триал' },
  { value: 'free', label: 'Бесплатные' },
  { value: 'active_today', label: 'Новые сегодня' },
  { value: 'referred', label: 'По приглашению' },
  { value: 'active_subscription', label: 'С активной подпиской' },
  { value: 'inactive_subscription', label: 'Без активной подписки' },
  { value: 'expired_subscription', label: 'Подписка истекла' },
  { value: 'unmapped_tariff', label: 'Тариф не распознан' },
  { value: 'tg_linked', label: 'С Telegram' },
  { value: 'no_tg', label: 'Без Telegram' },
  { value: 'email_linked', label: 'С email' },
  { value: 'no_email', label: 'Без email' },
  { value: 'panel_linked', label: 'Привязаны к панели' },
]

const panelStatusItems = [
  { value: 'all', label: 'Любой' },
  { value: 'active', label: 'Активна' },
  { value: 'expired', label: 'Истекла' },
  { value: 'limited', label: 'Лимит трафика' },
]

const premiumItems = [
  { value: 'all', label: 'Любой' },
  { value: 'unlimited', label: 'Безлимит' },
  { value: 'good', label: 'В норме' },
  { value: 'warn', label: 'Почти исчерпан' },
  { value: 'critical', label: 'Исчерпан' },
  { value: 'none', label: 'Нет премиума' },
]

const sortItems = [
  { value: 'registered_desc', label: 'Сначала новые' },
  { value: 'registered_asc', label: 'Сначала старые' },
  { value: 'name_asc', label: 'Имя А-Я' },
  { value: 'name_desc', label: 'Имя Я-А' },
  { value: 'id_asc', label: 'ID по возрастанию' },
  { value: 'id_desc', label: 'ID по убыванию' },
  { value: 'subscription_expires_at_asc', label: 'Подписка истекает раньше' },
  { value: 'subscription_expires_at_desc', label: 'Подписка истекает позже' },
  { value: 'status_asc', label: 'Статус А-Я' },
  { value: 'status_desc', label: 'Статус Я-А' },
  { value: 'payments_total_desc', label: 'Сумма платежей (убыв.)' },
  { value: 'payments_total_asc', label: 'Сумма платежей (возр.)' },
  { value: 'payments_count_desc', label: 'Число платежей (убыв.)' },
  { value: 'invited_users_count_desc', label: 'Приглашено (убыв.)' },
  { value: 'premium_ratio_desc', label: 'Премиум-трафик (убыв.)' },
  { value: 'premium_ratio_asc', label: 'Премиум-трафик (возр.)' },
]

const tariffItems = computed(() => [
  { value: 'all', label: 'Все тарифы' },
  { value: 'trial', label: 'Триал' },
  { value: 'no_subscription', label: 'Без подписки' },
  { value: 'no_tariff', label: 'Без тарифа' },
  ...tariffOptions.value.map((t) => ({
    value: `tariff:${t.tariff_key}`,
    label: tariffName(t) + (t.is_enabled === false ? ' (выкл.)' : ''),
  })),
])

async function load(p = page.value) {
  busy.value = true
  error.value = ''
  try {
    const res = await call<AdminUsersListResponse>('users', {
      query: {
        q: search.value.trim(),
        filter: filterValue.value,
        panel_status: panelStatus.value,
        premium_traffic: premiumTraffic.value,
        sort: sortValue.value,
        tariff_filter: tariffFilter.value,
        page: p,
        page_size: pageSize,
      },
    })
    users.value = res.users || []
    total.value = res.total || 0
    page.value = res.page || 0
    tariffOptions.value = res.tariff_options || []
    balanceEnabled.value = Boolean(res.user_balance_enabled)
    partnerBalanceEnabled.value = Boolean(res.partner_balance_enabled)
    balanceCurrency.value = res.balance_currency || 'RUB'
    balanceScale.value = res.balance_currency_scale ?? 2
    loaded.value = true
  } catch (e) {
    error.value = adminErrorMessage(e)
    users.value = []
    total.value = 0
  } finally {
    busy.value = false
  }
}

// Дебаунс поиска и сброс страницы при смене фильтров
let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(0), 350)
})
watch([filterValue, panelStatus, premiumTraffic, tariffFilter, sortValue], () => load(0))

const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const rangeStart = computed(() => (total.value === 0 ? 0 : page.value * pageSize + 1))
const rangeEnd = computed(() => Math.min(total.value, (page.value + 1) * pageSize))

function balanceText(item: AdminUsersListResponse['users'][number]): string {
  const parts: string[] = []
  if (balanceEnabled.value) parts.push(fmtMinor(item.user_balance_amount_minor, balanceScale.value, balanceCurrency.value))
  if (partnerBalanceEnabled.value && item.partner_balance_amount_minor) {
    parts.push(`П: ${fmtMinor(item.partner_balance_amount_minor, balanceScale.value, balanceCurrency.value)}`)
  }
  return parts.join(' · ') || '—'
}

onMounted(() => load(0))
</script>

<template>
  <main class="admin-page">
    <h1>Пользователи</h1>

    <section class="admin-card">
      <div class="adm-users-search">
        <input
          v-model="search"
          class="admin-input"
          type="search"
          placeholder="Имя, @username, email, user_id, telegram_id, ms_id"
        />
      </div>
      <div class="adm-users-filters">
        <AdminSelect v-model="filterValue" :items="filterItems" />
        <AdminSelect v-model="panelStatus" :items="panelStatusItems" />
        <AdminSelect v-model="premiumTraffic" :items="premiumItems" />
        <AdminSelect v-model="tariffFilter" :items="tariffItems" />
        <AdminSelect v-model="sortValue" :items="sortItems" />
      </div>
    </section>

    <p v-if="error" class="admin-note admin-error">{{ error }}</p>

    <section class="admin-card">
      <div class="adm-users-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Статус</th>
              <th>Тариф</th>
              <th>Подписка до</th>
              <th>Премиум</th>
              <th>Платежи</th>
              <th>Рефералы</th>
              <th>Баланс</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="u in users"
              :key="u.user_id"
              class="adm-users-row"
              @click="navigateTo(`/admin/users/${u.user_id}`)"
            >
              <td>
                <div class="adm-users-cell-user">
                  <AdminUsersAvatar :user="u" :size="36" />
                  <div class="adm-users-cell-names">
                    <strong>{{ userDisplayName(u) }}</strong>
                    <span>{{ userSecondaryLine(u) }}</span>
                  </div>
                </div>
              </td>
              <td><AdminUsersStatusBadge :status="u.panel_status" :banned="u.is_banned" /></td>
              <td>{{ planLabel(u.subscription_plan) }}</td>
              <td>{{ u.subscription_expires_at ? fmtDateTime(u.subscription_expires_at) : '—' }}</td>
              <td><AdminBadge :tone="premiumTrafficTone(u.premium_traffic)">{{ premiumTrafficLabel(u.premium_traffic) }}</AdminBadge></td>
              <td>
                {{ fmtMoney(u.payments_total_amount, u.payments_currency) }}
                <span v-if="u.payments_count" class="admin-note">({{ u.payments_count }})</span>
              </td>
              <td>{{ u.invited_users_count || '—' }}</td>
              <td>{{ balanceText(u) }}</td>
            </tr>
            <tr v-if="!users.length">
              <td colspan="8" class="admin-note">
                {{ busy ? 'Загрузка...' : loaded ? 'Пользователи не найдены' : '' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="admin-row adm-users-pager">
        <span class="admin-note">
          {{ total ? `Показано ${rangeStart}-${rangeEnd} из ${total}` : '' }}
        </span>
        <button class="admin-btn ghost" :disabled="busy || page <= 0" @click="load(page - 1)">Назад</button>
        <span class="admin-note">Страница {{ page + 1 }} из {{ pages }}</span>
        <button class="admin-btn ghost" :disabled="busy || page >= pages - 1" @click="load(page + 1)">Вперёд</button>
        <button class="admin-btn ghost" :disabled="busy" @click="load(page)">Обновить</button>
      </div>
    </section>
  </main>
</template>

<style scoped>
h1 {
  margin: 0;
  font-size: 20px;
}
.adm-users-search {
  display: grid;
}
.adm-users-filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
}
.adm-users-table-wrap {
  overflow-x: auto;
}
.adm-users-row {
  cursor: pointer;
}
.adm-users-row:hover td {
  background: var(--adm-accent-soft, rgba(59, 130, 246, 0.08));
}
.adm-users-cell-user {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 200px;
}
.adm-users-cell-names {
  display: grid;
  gap: 2px;
}
.adm-users-cell-names span {
  font-size: 12px;
  color: var(--adm-muted, #8b95a8);
}
.adm-users-pager {
  justify-content: center;
  flex-wrap: wrap;
}
</style>
