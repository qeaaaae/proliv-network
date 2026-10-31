<script setup lang="ts">
interface HealthAlert {
  id: string | number
  severity: string
  message_key: string
  params: Record<string, unknown>
  sections: string[]
}
interface PanelCompatibility {
  version: string | null
  generation: string
  support_status: string
  certified_versions: string[]
  capabilities: string[]
  observed_capabilities: Record<string, boolean>
}
interface HealthData {
  alerts: HealthAlert[]
  checked_at: string | null
  panel_compatibility: PanelCompatibility | null
}
interface PanelSync {
  status: string
  last_sync_time: string | null
  details: string | null
  users_processed: number
  subscriptions_synced: number
}
// type-алиас (не interface) - иначе не присваивается к Record<string, unknown>.
type StatsData = {
  users: Record<string, unknown>
  financial: Record<string, unknown>
  panel_sync: PanelSync | null
  currency_symbol: string
  panel: Record<string, unknown> | null
  queue: Record<string, unknown> | null
}
interface Squad {
  uuid: string
  name: string
  members_count?: number | string | null
  active_inbounds_count?: number | string | null
}
interface RoleRow {
  user_id: number
  email: string | null
  minishop_id: string | null
  role: string
}
interface AdminUserLite {
  user_id: number
  label: string
  email: string | null
  minishop_id: string | null
}
interface UsersListResponse {
  users: {
    user_id: number
    username: string | null
    first_name: string | null
    last_name: string | null
    email: string | null
    minishop_id: string | null
  }[]
}

const { call } = useAdminApi()

const health = ref<HealthData | null>(null)
const healthLoading = ref(false)
const healthError = ref('')

const stats = ref<StatsData | null>(null)
const statsLoading = ref(false)
const statsError = ref('')

const squads = ref<Squad[] | null>(null)
const squadsLoading = ref(false)
const squadsError = ref('')

const meId = ref<number | null>(null)
const adminIds = ref<number[]>([])
const roles = ref<RoleRow[] | null>(null)
const adminUsers = ref<AdminUserLite[]>([])
const rolesLoading = ref(false)
const rolesError = ref('')
const rolesBusy = ref(false)
const rolesNotice = ref('')
const rolesNoticeError = ref(false)

const syncBusy = ref(false)
const syncNotice = ref('')

function errText(e: unknown, fallback = 'Ошибка запроса'): string {
  const code = (e as { code?: string })?.code
  const map: Record<string, string> = {
    forbidden: 'Нет доступа',
    unauthorized: 'Нет доступа',
    panel_unavailable: 'Панель недоступна',
    panel_request_failed: 'Ошибка запроса к панели',
    queue_unavailable: 'Очередь фоновых задач недоступна',
    account_not_found: 'Аккаунт не найден',
    account_identifier_required: 'Укажите ms_ id или email',
    invalid_role_request: 'Некорректный запрос роли',
    role_revoke_failed: 'Не удалось снять роль',
    invalid_payload: 'Некорректный запрос',
  }
  if (code && map[code]) return map[code]
  const msg = (e as Error)?.message
  return msg && msg !== 'request_failed' && msg !== 'Backend request failed' ? msg : fallback
}

async function loadHealth(refresh = false) {
  healthLoading.value = true
  healthError.value = ''
  try {
    health.value = await call<HealthData>('health', {
      query: refresh ? { refresh: '1' } : {},
    })
  } catch (e) {
    healthError.value = errText(e, 'Не удалось загрузить состояние')
  } finally {
    healthLoading.value = false
  }
}

async function loadStats() {
  statsLoading.value = true
  statsError.value = ''
  try {
    stats.value = await call<StatsData>('stats')
  } catch (e) {
    statsError.value = errText(e, 'Не удалось загрузить статистику')
  } finally {
    statsLoading.value = false
  }
}

async function refreshAll() {
  await Promise.all([loadHealth(true), loadStats(), loadSquads()])
}

async function loadSquads() {
  squadsLoading.value = true
  squadsError.value = ''
  try {
    const res = await call<{ squads: Squad[] }>('panel/internal-squads')
    squads.value = res.squads || []
  } catch (e) {
    squadsError.value = errText(e, 'Не удалось загрузить сквады')
    squads.value = null
  } finally {
    squadsLoading.value = false
  }
}

async function loadMe() {
  try {
    const res = await call<{ user_id: number; admin_ids: number[] }>('me')
    meId.value = res.user_id
    adminIds.value = res.admin_ids || []
  } catch {
    meId.value = null
    adminIds.value = []
  }
}

function userLabel(u: UsersListResponse['users'][number]): string {
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ').trim()
  if (name) return name
  if (u.username) return `@${u.username}`
  if (u.email) return u.email
  return `#${u.user_id}`
}

async function resolveAdminUsers() {
  const resolved: AdminUserLite[] = []
  for (const id of adminIds.value.slice(0, 15)) {
    try {
      const res = await call<UsersListResponse>('users', {
        query: { q: String(id), page_size: 10 },
      })
      const hit = (res.users || []).find((u) => u.user_id === id)
      resolved.push({
        user_id: id,
        label: hit ? userLabel(hit) : `#${id}`,
        email: hit?.email || null,
        minishop_id: hit?.minishop_id || null,
      })
    } catch {
      resolved.push({ user_id: id, label: `#${id}`, email: null, minishop_id: null })
    }
  }
  adminUsers.value = resolved
}

async function loadRoles() {
  rolesLoading.value = true
  rolesError.value = ''
  try {
    const res = await call<{ roles: RoleRow[] }>('roles')
    roles.value = res.roles || []
  } catch (e) {
    // Список ролей - только для владельца (403): показываем admin_ids из /me.
    roles.value = null
    rolesError.value = errText(e)
    if (!adminUsers.value.length) await resolveAdminUsers()
  } finally {
    rolesLoading.value = false
  }
}

async function grantRole(payload: { identifier: string; role: string }) {
  rolesBusy.value = true
  rolesNotice.value = ''
  try {
    const body = payload.identifier.toLowerCase().startsWith('ms_')
      ? { minishop_id: payload.identifier, role: payload.role }
      : { email: payload.identifier, role: payload.role }
    await call('roles', { method: 'POST', body })
    rolesNotice.value = 'Роль выдана'
    rolesNoticeError.value = false
    await loadRoles()
  } catch (e) {
    rolesNotice.value = errText(e)
    rolesNoticeError.value = true
  } finally {
    rolesBusy.value = false
  }
}

async function revokeRole(payload: { user_id: number; role: string }) {
  rolesBusy.value = true
  rolesNotice.value = ''
  try {
    await call(`roles/${payload.user_id}/${payload.role}`, { method: 'DELETE' })
    rolesNotice.value = 'Роль снята'
    rolesNoticeError.value = false
    await loadRoles()
  } catch (e) {
    rolesNotice.value = errText(e)
    rolesNoticeError.value = true
  } finally {
    rolesBusy.value = false
  }
}

async function runSync() {
  syncBusy.value = true
  syncNotice.value = ''
  try {
    await call('sync', { method: 'POST', body: {} })
    syncNotice.value = 'Синхронизация поставлена в очередь'
    // Воркер подхватывает задачу асинхронно - обновляем статус с задержкой.
    setTimeout(() => {
      loadStats()
    }, 4000)
  } catch (e) {
    syncNotice.value = errText(e, 'Не удалось запустить синхронизацию')
  } finally {
    syncBusy.value = false
  }
}

onMounted(async () => {
  await loadMe()
  await Promise.all([loadHealth(), loadStats(), loadSquads(), loadRoles()])
})
</script>

<template>
  <main class="admin-page">
    <h1 class="sys-title">Система</h1>

    <p v-if="statsError" class="admin-note admin-error">{{ statsError }}</p>

    <AdminSystemHealthCard
      :health="health"
      :stats="stats"
      :loading="healthLoading"
      :error="healthError"
      @refresh="refreshAll"
    />

    <AdminSystemSyncCard
      :sync="stats?.panel_sync || null"
      :queue="stats?.queue || null"
      :busy="syncBusy"
      :notice="syncNotice"
      @sync="runSync"
    />

    <AdminSystemNodesCard
      :squads="squads"
      :squads-error="squadsError"
      :panel="stats?.panel || null"
      :loading="squadsLoading || statsLoading"
      @refresh="refreshAll"
    />

    <AdminSystemLogsCard />

    <AdminSystemRolesCard
      :roles="roles"
      :admin-users="adminUsers"
      :me-id="meId"
      :loading="rolesLoading"
      :busy="rolesBusy"
      :error="rolesError"
      :notice="rolesNotice"
      :notice-error="rolesNoticeError"
      @grant="grantRole"
      @revoke="revokeRole"
      @refresh="loadRoles"
    />
  </main>
</template>

<style scoped>
.sys-title {
  margin: 0;
  font-size: 20px;
}
</style>
