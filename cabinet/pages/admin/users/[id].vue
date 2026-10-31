<script setup lang="ts">
import { adminErrorMessage, userDisplayName } from '~/components/admin/users/format'
import type {
  AdminTariffOption,
  AdminUserDetail,
  AdminUsersListResponse,
} from '~/components/admin/users/types'

const route = useRoute()
const { call } = useAdminApi()

const detail = ref<AdminUserDetail | null>(null)
const tariffOptions = ref<AdminTariffOption[]>([])
const busy = ref(false)
const notFound = ref(false)
const error = ref('')
const notice = ref('')
const noticeError = ref(false)

const routeId = computed(() => String(route.params.id || ''))
const canonicalId = computed(() => detail.value?.user.user_id || 0)

function msg(text: string, isError = false) {
  notice.value = text
  noticeError.value = isError
}

async function load() {
  if (!routeId.value) return
  busy.value = true
  error.value = ''
  try {
    detail.value = await call<AdminUserDetail>(`users/${routeId.value}`)
    notFound.value = false
  } catch (e) {
    const code = (e as { code?: string; message?: string }).code || (e as Error).message || ''
    if (code === 'not_found' || code === 'user_not_found') {
      notFound.value = true
      detail.value = null
    } else {
      error.value = adminErrorMessage(e)
    }
  } finally {
    busy.value = false
  }
}

// Тарифы для модалок продления/смены - список опций отдаёт endpoint списка юзеров
async function loadTariffs() {
  try {
    const res = await call<AdminUsersListResponse>('users', { query: { page_size: 1 } })
    tariffOptions.value = res.tariff_options || []
  } catch {
    tariffOptions.value = []
  }
}

async function reload() {
  await load()
}

watch(routeId, () => {
  notice.value = ''
  load()
})

onMounted(() => {
  load()
  loadTariffs()
})
</script>

<template>
  <main class="admin-page">
    <div class="admin-row">
      <NuxtLink to="/admin/users" class="adm-users-back">&larr; Все пользователи</NuxtLink>
      <button v-if="detail" class="admin-btn ghost" :disabled="busy" @click="reload">Обновить</button>
    </div>

    <p v-if="notice" class="admin-note" :class="{ 'admin-error': noticeError }">{{ notice }}</p>
    <p v-if="busy && !detail" class="admin-note">Загрузка...</p>
    <p v-else-if="error" class="admin-note admin-error">{{ error }}</p>

    <section v-else-if="notFound" class="admin-card">
      <h2>Пользователь не найден</h2>
      <p class="admin-note">Аккаунт с идентификатором '{{ routeId }}' не существует или был удалён.</p>
      <NuxtLink to="/admin/users" class="admin-btn ghost adm-users-back-btn">К списку пользователей</NuxtLink>
    </section>

    <template v-else-if="detail">
      <h1>{{ userDisplayName(detail.user) }}</h1>

      <AdminUsersIdentityCard :detail="detail" />
      <AdminUsersSubscriptionCard :detail="detail" />
      <AdminUsersActionsCard
        :user-id="canonicalId"
        :detail="detail"
        :tariff-options="tariffOptions"
        @updated="reload"
        @notice="msg"
      />
      <AdminUsersSquadsCard
        :user-id="canonicalId"
        :overrides="detail.panel_squad_overrides"
        @updated="reload"
        @notice="msg"
      />
      <AdminUsersBalanceCard :balance="detail.balance" />
      <AdminUsersReferralsCard :user-id="canonicalId" :referral="detail.referral" />
      <AdminUsersPaymentsCard
        :payments="detail.recent_payments"
        :total-paid="detail.total_paid"
        :currency="detail.recent_payments[0]?.currency || detail.balance?.currency"
      />
      <AdminUsersLogsCard :user-id="canonicalId" />
    </template>
  </main>
</template>

<style scoped>
h1 {
  margin: 0;
  font-size: 20px;
}
.adm-users-back {
  color: var(--adm-muted, #8b95a8);
  text-decoration: none;
  font-size: 13px;
}
.adm-users-back:hover {
  color: var(--adm-text, #e8ecf4);
}
.adm-users-back-btn {
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
