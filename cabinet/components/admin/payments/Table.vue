<script setup lang="ts">
// Таблица платежей: клик по строке открывает карточку (emit 'open').
import {
  paymentDescription,
  paymentMoney,
  paymentProviderLabel,
  paymentStatusLabel,
  paymentStatusTone,
} from './types'
import type { AdminPayment } from './types'

defineProps<{ payments: AdminPayment[] }>()
const emit = defineEmits<{ open: [payment: AdminPayment] }>()

const { dateTime } = useFormat()
</script>

<template>
  <div class="table-wrap">
    <table class="admin-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Пользователь</th>
          <th>Покупка</th>
          <th>Сумма</th>
          <th>Провайдер</th>
          <th>Статус</th>
          <th>Дата</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="p in payments"
          :key="p.payment_id"
          class="row"
          @click="emit('open', p)"
        >
          <td><code class="pid">#{{ p.payment_id }}</code></td>
          <td>
            <div class="user-cell">
              <strong>{{ p.user_label || `#${p.user_id}` }}</strong>
              <small v-if="p.user_minishop_id || p.telegram_id">
                {{ p.user_minishop_id || `tg ${p.telegram_id}` }}
              </small>
            </div>
          </td>
          <td class="desc">{{ paymentDescription(p) }}</td>
          <td class="amount">{{ paymentMoney(p.amount, p.currency) }}</td>
          <td>{{ paymentProviderLabel(p.provider) }}</td>
          <td>
            <AdminBadge :tone="paymentStatusTone(p.status)">
              {{ paymentStatusLabel(p.status) }}
            </AdminBadge>
          </td>
          <td class="date">{{ p.created_at ? dateTime(p.created_at) : '—' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-wrap {
  overflow-x: auto;
}
.row {
  cursor: pointer;
}
.row:hover td {
  background: var(--adm-accent-soft, rgba(59, 130, 246, 0.08));
}
.pid {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: var(--adm-accent, #3b82f6);
  white-space: nowrap;
}
.user-cell {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.user-cell strong {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}
.user-cell small {
  color: var(--adm-muted, #8b95a8);
  font-size: 11px;
  font-family: ui-monospace, monospace;
}
.desc {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.amount {
  white-space: nowrap;
}
.date {
  white-space: nowrap;
}
</style>
