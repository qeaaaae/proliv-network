<script setup lang="ts">
import {
  daysLeft,
  fmtBytes,
  fmtDate,
  fmtDateTime,
  subscriptionLabel,
  trafficStrategyLabel,
} from './format'
import type { AdminUserDetail } from './types'

const props = defineProps<{ detail: AdminUserDetail }>()

const sub = computed(() => props.detail.active_subscription)
const remaining = computed(() => daysLeft(sub.value?.end_date))
const history = computed(() => props.detail.subscriptions || [])
</script>

<template>
  <section class="admin-card">
    <h2>Подписка</h2>

    <template v-if="sub">
      <div class="admin-row">
        <strong>{{ subscriptionLabel(sub) }}</strong>
        <AdminUsersStatusBadge :status="sub.status_from_panel || 'active'" />
        <AdminBadge v-if="sub.is_trial" tone="warning">Триал</AdminBadge>
        <AdminBadge v-if="sub.is_throttled" tone="warning">Троттлинг</AdminBadge>
      </div>
      <div class="adm-users-fields">
        <AdminUsersFieldRow label="Действует до">
          {{ fmtDateTime(sub.end_date) }}
          <span v-if="remaining !== null" class="admin-note">
            ({{ remaining > 0 ? `осталось ${remaining} дн.` : 'истекла' }})
          </span>
        </AdminUsersFieldRow>
        <AdminUsersFieldRow label="Трафик">
          {{ fmtBytes(sub.traffic_used_bytes) }} /
          {{ sub.regular_unlimited_override || !sub.traffic_limit_bytes ? 'безлимит' : fmtBytes(sub.traffic_limit_bytes) }}
          <span v-if="sub.regular_bonus_bytes > 0" class="admin-note">
            +бонус {{ fmtBytes(sub.regular_bonus_bytes) }}
          </span>
        </AdminUsersFieldRow>
        <AdminUsersFieldRow label="Премиум-трафик">
          <template v-if="sub.premium_unlimited_override">Безлимит</template>
          <template v-else-if="sub.premium_limit_bytes > 0">
            {{ fmtBytes(sub.premium_used_bytes) }} / {{ fmtBytes(sub.premium_limit_bytes) }}
          </template>
          <template v-else>—</template>
          <span v-if="sub.premium_bonus_bytes > 0" class="admin-note">
            +бонус {{ fmtBytes(sub.premium_bonus_bytes) }}
          </span>
        </AdminUsersFieldRow>
        <AdminUsersFieldRow label="Сброс трафика">
          {{ trafficStrategyLabel(sub.traffic_limit_strategy) }}
          <span v-if="sub.traffic_strategy_lock_reason" class="admin-note">
            (нельзя менять)
          </span>
        </AdminUsersFieldRow>
        <AdminUsersFieldRow label="Устройства">
          <template v-if="detail.hwid_devices.max_devices === 0">Безлимит</template>
          <template v-else>
            {{ detail.hwid_devices.current_devices ?? '—' }} / {{ detail.hwid_devices.max_devices ?? '—' }}
          </template>
          <span v-if="sub.extra_hwid_devices > 0" class="admin-note">
            (+{{ sub.extra_hwid_devices }} докуплено)
          </span>
        </AdminUsersFieldRow>
        <AdminUsersFieldRow label="Автопродление">
          {{ sub.auto_renew_enabled ? 'Включено' : 'Выключено' }}
        </AdminUsersFieldRow>
        <AdminUsersFieldRow v-if="sub.tariff_key" label="Тариф (ключ)">
          {{ sub.tariff_key }}
        </AdminUsersFieldRow>
      </div>
    </template>
    <p v-else class="admin-note">Активной подписки нет.</p>

    <template v-if="detail.trial.used || detail.trial.last_reset_at">
      <h3>Триал</h3>
      <div class="adm-users-fields">
        <AdminUsersFieldRow label="Статус">
          <template v-if="detail.trial.active">Активен до {{ fmtDate(detail.trial.latest_end_date) }}</template>
          <template v-else-if="detail.trial.used">Использован ({{ detail.trial.count }})</template>
          <template v-else>Не использован</template>
        </AdminUsersFieldRow>
        <AdminUsersFieldRow v-if="detail.trial.last_reset_at" label="Сброшен">
          {{ fmtDateTime(detail.trial.last_reset_at) }}
        </AdminUsersFieldRow>
      </div>
    </template>

    <template v-if="history.length > 1">
      <h3>История подписок</h3>
      <div class="adm-users-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Тариф</th>
              <th>Период</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in history" :key="s.subscription_id">
              <td>{{ subscriptionLabel(s) }}</td>
              <td>{{ fmtDate(s.start_date) }} - {{ fmtDate(s.end_date) }}</td>
              <td>
                <AdminUsersStatusBadge :status="s.is_active ? s.status_from_panel || 'active' : 'expired'" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </section>
</template>

<style scoped>
.adm-users-fields {
  display: grid;
  gap: 6px;
}
.adm-users-table-wrap {
  overflow-x: auto;
}
h3 {
  margin: 8px 0 0;
  font-size: 14px;
}
</style>
