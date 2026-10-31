<script setup lang="ts">
import {
  fmtDateTime,
  telegramNotificationsLabel,
  userDisplayName,
  vpnStatusLabel,
  vpnStatusTone,
} from './format'
import type { AdminUserDetail } from './types'

const props = defineProps<{ detail: AdminUserDetail }>()

const user = computed(() => props.detail.user)

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
</script>

<template>
  <section class="admin-card">
    <div class="adm-users-identity">
      <AdminUsersAvatar :user="user" :size="64" />
      <div class="adm-users-identity-main">
        <h2>
          {{ userDisplayName(user) }}
          <AdminBadge v-if="user.is_banned" tone="danger">Заблокирован</AdminBadge>
        </h2>
        <p class="admin-note">
          <span v-if="user.username">@{{ user.username }} · </span>
          <span v-if="user.minishop_id">{{ user.minishop_id }} · </span>
          ID {{ user.user_id }}
        </p>
      </div>
    </div>

    <div class="adm-users-fields">
      <AdminUsersFieldRow label="Telegram ID">
        {{ user.telegram_id ?? '—' }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="Email">
        {{ user.email || '—' }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="Язык">
        {{ user.language_code || '—' }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="Регистрация">
        {{ fmtDateTime(user.registration_date) }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="Панель (username)">
        {{ user.panel_username || '—' }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="UUID в панели">
        <span class="adm-users-mono">{{ user.panel_user_uuid || '—' }}</span>
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="Устройства">
        {{ detail.hwid_devices.current_devices ?? '—' }} / {{ detail.hwid_devices.max_devices ?? '—' }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="VPN-статус">
        <AdminBadge :tone="vpnStatusTone(detail.vpn_connection_status)">
          {{ vpnStatusLabel(detail.vpn_connection_status) }}
        </AdminBadge>
        <span v-if="detail.last_vpn_connected_at" class="admin-note">
          · {{ fmtDateTime(detail.last_vpn_connected_at) }}
        </span>
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="Уведомления бота">
        {{ telegramNotificationsLabel(detail.telegram_notifications.status) }}
      </AdminUsersFieldRow>
      <AdminUsersFieldRow v-if="detail.partner_attribution" label="Партнёр">
        {{ detail.partner_attribution.display_label }} (#{{ detail.partner_attribution.partner_id }},
        {{ detail.partner_attribution.public_client_id }})
      </AdminUsersFieldRow>
      <AdminUsersFieldRow label="Событий в журнале">
        {{ detail.log_count }}
      </AdminUsersFieldRow>
    </div>

    <div v-if="detail.panel_user_url || detail.install_share_url || detail.subscription_url" class="adm-users-links">
      <a v-if="detail.panel_user_url" :href="detail.panel_user_url" target="_blank" rel="noopener" class="admin-btn ghost">
        Открыть в панели
      </a>
      <button v-if="detail.install_share_url" type="button" class="admin-btn ghost" @click="copy(detail.install_share_url!, 'install')">
        {{ copied === 'install' ? 'Скопировано' : 'Ссылка установки' }}
      </button>
      <button v-if="detail.subscription_url" type="button" class="admin-btn ghost" @click="copy(detail.subscription_url!, 'sub')">
        {{ copied === 'sub' ? 'Скопировано' : 'Ссылка подписки' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.adm-users-identity {
  display: flex;
  gap: 14px;
  align-items: center;
}
.adm-users-identity-main {
  display: grid;
  gap: 4px;
}
.adm-users-identity-main h2 {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.adm-users-fields {
  display: grid;
  gap: 6px;
}
.adm-users-mono {
  font-family: monospace;
  font-size: 12px;
}
.adm-users-links {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.adm-users-links a {
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}
</style>
