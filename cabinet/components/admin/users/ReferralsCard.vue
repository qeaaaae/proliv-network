<script setup lang="ts">
import { adminErrorMessage, fmtDateTime, userDisplayName, userSecondaryLine } from './format'
import type { AdminReferralInfo, AdminUserReferralsResponse } from './types'

const props = defineProps<{ userId: number; referral: AdminReferralInfo }>()

const { call } = useAdminApi()

const invitees = ref<AdminUserReferralsResponse['invitees']>([])
const inviter = ref<AdminUserReferralsResponse['inviter']>(props.referral.inviter)
const total = ref(props.referral.invitees_total)
const page = ref(0)
const pageSize = 10
const busy = ref(false)
const error = ref('')
const loaded = ref(false)

const copied = ref('')
async function copy(text: string, tag: string) {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = tag
    setTimeout(() => {
      if (copied.value === tag) copied.value = ''
    }, 1600)
  } catch {
    copied.value = ''
  }
}

async function load(p = 0) {
  busy.value = true
  error.value = ''
  try {
    const res = await call<AdminUserReferralsResponse>(`users/${props.userId}/referrals`, {
      query: { page: p, page_size: pageSize },
    })
    invitees.value = res.invitees || []
    inviter.value = res.inviter
    total.value = res.total
    page.value = res.page
    loaded.value = true
  } catch (e) {
    error.value = adminErrorMessage(e)
  } finally {
    busy.value = false
  }
}

const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

watch(
  () => props.userId,
  () => {
    invitees.value = []
    inviter.value = props.referral.inviter
    total.value = props.referral.invitees_total
    page.value = 0
    loaded.value = false
    error.value = ''
  },
)
</script>

<template>
  <section class="admin-card">
    <h2>Реферальная программа</h2>

    <div class="adm-users-fields">
      <AdminUsersFieldRow label="Реферальный код">
        {{ referral.code || '—' }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="Приглашено">
        {{ referral.invitees_total }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow v-if="referral.inviter || inviter" label="Пригласил">
        <NuxtLink :to="`/admin/users/${(inviter || referral.inviter)!.user_id}`" class="adm-users-link">
          {{ userDisplayName(inviter || referral.inviter) }}
        </NuxtLink>
      </AdminUsersFieldRow>
      <AdminUsersFieldRow v-if="referral.bot_link" label="Ссылка (бот)">
        <button type="button" class="adm-users-copy" @click="copy(referral.bot_link!, 'bot')">
          {{ copied === 'bot' ? 'Скопировано' : 'Копировать' }}
        </button>
      </AdminUsersFieldRow>
      <AdminUsersFieldRow v-if="referral.webapp_link" label="Ссылка (webapp)">
        <button type="button" class="adm-users-copy" @click="copy(referral.webapp_link!, 'web')">
          {{ copied === 'web' ? 'Скопировано' : 'Копировать' }}
        </button>
      </AdminUsersFieldRow>
    </div>

    <div class="admin-row">
      <button class="admin-btn ghost" :disabled="busy" @click="load(0)">
        {{ loaded ? 'Обновить список' : 'Показать приглашённых' }}
      </button>
    </div>
    <p v-if="error" class="admin-note admin-error">{{ error }}</p>

    <template v-if="loaded">
      <ul v-if="invitees.length" class="admin-list">
        <li v-for="u in invitees" :key="u.user_id">
          <NuxtLink :to="`/admin/users/${u.user_id}`" class="admin-list-item adm-users-invitee">
            <AdminUsersAvatar :user="u" :size="32" />
            <span class="adm-users-invitee-main">
              <strong>{{ userDisplayName(u) }}</strong>
              <span>{{ userSecondaryLine(u) }} · {{ fmtDateTime(u.registration_date) }}</span>
            </span>
          </NuxtLink>
        </li>
      </ul>
      <p v-else class="admin-note">Приглашённых нет.</p>

      <div v-if="pages > 1" class="admin-row adm-users-pager">
        <button class="admin-btn ghost" :disabled="busy || page <= 0" @click="load(page - 1)">Назад</button>
        <span class="admin-note">Страница {{ page + 1 }} из {{ pages }}</span>
        <button class="admin-btn ghost" :disabled="busy || page >= pages - 1" @click="load(page + 1)">Вперёд</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.adm-users-fields {
  display: grid;
  gap: 6px;
}
.adm-users-link {
  color: var(--adm-accent, #3b82f6);
  text-decoration: none;
}
.adm-users-copy {
  border: 0;
  background: transparent;
  color: var(--adm-accent, #3b82f6);
  cursor: pointer;
  font-size: 13px;
  padding: 0;
}
.adm-users-invitee {
  display: flex;
  gap: 10px;
  align-items: center;
  text-decoration: none;
}
.adm-users-invitee-main {
  display: grid;
  gap: 2px;
}
.adm-users-pager {
  justify-content: center;
}
</style>
