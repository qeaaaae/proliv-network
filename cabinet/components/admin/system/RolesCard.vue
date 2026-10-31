<script setup lang="ts">
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
interface RoleCandidate {
  minishop_id: string
  email: string | null
  username: string | null
  first_name: string | null
}

defineProps<{
  roles: RoleRow[] | null
  adminUsers: AdminUserLite[]
  meId: number | null
  loading: boolean
  busy: boolean
  error: string
  notice: string
  noticeError: boolean
}>()
const emit = defineEmits<{
  grant: [payload: { identifier: string; role: string }]
  revoke: [payload: { user_id: number; role: string }]
  refresh: []
}>()

const { call } = useAdminApi()

const identifier = ref('')
const grantRole = ref('admin')
const candidates = ref<RoleCandidate[]>([])
const candidatesLoading = ref(false)

const roleItems = [
  { value: 'admin', label: 'Админ' },
  { value: 'owner', label: 'Владелец' },
]
const ROLE_LABELS: Record<string, string> = {
  owner: 'Владелец',
  admin: 'Админ',
}

function roleLabel(role: string): string {
  return ROLE_LABELS[role] || role
}
function roleTone(role: string): 'warning' | 'default' | 'muted' {
  if (role === 'owner') return 'warning'
  if (role === 'admin') return 'default'
  return 'muted'
}
function submitGrant() {
  const id = identifier.value.trim()
  if (!id) return
  emit('grant', { identifier: id, role: grantRole.value })
}

async function findCandidates() {
  candidatesLoading.value = true
  try {
    const res = await call<{ users: RoleCandidate[] }>('roles/candidates', {
      query: { q: identifier.value.trim() },
    })
    candidates.value = res.users || []
  } catch {
    candidates.value = []
  } finally {
    candidatesLoading.value = false
  }
}
function pickCandidate(user: RoleCandidate) {
  identifier.value = user.minishop_id || user.email || ''
  candidates.value = []
}
function candidateLabel(user: RoleCandidate): string {
  const parts = [user.first_name, user.username ? `@${user.username}` : '']
    .filter(Boolean)
    .join(' ')
  return `${parts || user.minishop_id} · ${user.minishop_id}${user.email ? ` · ${user.email}` : ''}`
}
</script>

<template>
  <section class="admin-card">
    <div class="admin-row card-head">
      <h2>Администраторы</h2>
      <button class="admin-btn ghost" :disabled="loading" @click="emit('refresh')">
        {{ loading ? 'Обновление...' : 'Обновить' }}
      </button>
    </div>
    <p v-if="notice" class="admin-note" :class="{ 'admin-error': noticeError }">{{ notice }}</p>

    <template v-if="roles">
      <p v-if="!roles.length" class="admin-note">Ролей нет.</p>
      <table v-else class="admin-table">
        <thead>
          <tr>
            <th>Пользователь</th>
            <th>Роль</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in roles" :key="`${row.user_id}:${row.role}`">
            <td>
              <div class="sys-role-user">
                <span>{{ row.email || row.minishop_id || `#${row.user_id}` }}</span>
                <span class="admin-note">id {{ row.user_id }}{{ row.minishop_id && row.email ? ` · ${row.minishop_id}` : '' }}</span>
              </div>
            </td>
            <td>
              <AdminBadge :tone="roleTone(row.role)">{{ roleLabel(row.role) }}</AdminBadge>
            </td>
            <td class="sys-role-actions">
              <button
                class="admin-btn ghost"
                :disabled="busy || row.user_id === meId"
                :title="row.user_id === meId ? 'Нельзя снять роль с себя' : 'Снять роль'"
                @click="emit('revoke', { user_id: row.user_id, role: row.role })"
              >
                Снять
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <h3 class="sys-sub">Выдать роль</h3>
      <div class="sys-grant">
        <input
          v-model="identifier"
          class="admin-input"
          placeholder="ms_ id или email"
          aria-label="Идентификатор пользователя"
        />
        <AdminSelect v-model="grantRole" :items="roleItems" />
        <button class="admin-btn" :disabled="busy || !identifier.trim()" @click="submitGrant">
          Выдать
        </button>
        <button class="admin-btn ghost" :disabled="candidatesLoading" @click="findCandidates">
          {{ candidatesLoading ? 'Поиск...' : 'Найти' }}
        </button>
      </div>
      <ul v-if="candidates.length" class="admin-list">
        <li v-for="user in candidates" :key="user.minishop_id">
          <button type="button" class="admin-list-item" @click="pickCandidate(user)">
            <strong>{{ candidateLabel(user) }}</strong>
          </button>
        </li>
      </ul>
    </template>

    <template v-else>
      <p class="admin-note">
        Список ролей доступен только владельцу. Администраторы (по данным сессии):
      </p>
      <ul v-if="adminUsers.length" class="admin-list">
        <li v-for="user in adminUsers" :key="user.user_id" class="sys-admin-item">
          <span>
            {{ user.label }}
            <span class="admin-note">id {{ user.user_id }}{{ user.minishop_id ? ` · ${user.minishop_id}` : '' }}</span>
          </span>
          <AdminBadge tone="default">Админ</AdminBadge>
        </li>
      </ul>
      <p v-else class="admin-note">{{ loading ? 'Загрузка...' : 'Нет данных' }}</p>
      <p v-if="error && !adminUsers.length" class="admin-note admin-error">{{ error }}</p>
    </template>
  </section>
</template>

<style scoped>
.card-head {
  justify-content: space-between;
}
.sys-sub {
  margin: 4px 0 0;
  font-size: 14px;
}
.sys-role-user {
  display: grid;
  gap: 2px;
}
.sys-role-actions {
  text-align: right;
}
.sys-role-actions .admin-btn {
  padding: 6px 12px;
}
.sys-grant {
  display: grid;
  grid-template-columns: minmax(160px, 1fr) minmax(120px, auto) auto auto;
  gap: 8px;
  align-items: center;
}
.sys-admin-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--adm-border);
}
@media (max-width: 620px) {
  .sys-grant {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
