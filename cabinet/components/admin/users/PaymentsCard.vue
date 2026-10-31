<script setup lang="ts">
import { fmtDateTime, fmtMoney, paymentStatusLabel, paymentStatusTone } from './format'
import type { AdminPayment } from './types'

defineProps<{ payments: AdminPayment[]; totalPaid: number; currency?: string | null }>()
</script>

<template>
  <section class="admin-card">
    <h2>Платежи</h2>
    <div class="admin-kpi">
      <small>Всего оплачено</small>
      <strong>{{ fmtMoney(totalPaid, currency) }}</strong>
    </div>
    <div v-if="payments.length" class="adm-users-table-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Описание</th>
            <th>Сумма</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in payments" :key="p.payment_id">
            <td>{{ fmtDateTime(p.created_at) }}</td>
            <td>{{ p.description || p.sale_mode || '—' }}</td>
            <td>{{ fmtMoney(p.amount, p.currency) }}</td>
            <td><AdminBadge :tone="paymentStatusTone(p.status)">{{ paymentStatusLabel(p.status) }}</AdminBadge></td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else class="admin-note">Платежей пока не было.</p>
  </section>
</template>

<style scoped>
.adm-users-table-wrap {
  overflow-x: auto;
}
</style>
