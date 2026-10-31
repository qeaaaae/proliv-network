<script setup lang="ts">
import { currencySymbol, fmtDateTime, fmtMinor } from './format'
import type { AdminBalance } from './types'

const props = defineProps<{ balance: AdminBalance | null | undefined }>()

const sources = computed(() => props.balance?.sources || [])
const history = computed(() => (props.balance?.history || []).slice(0, 15))

const KIND_LABELS: Record<string, string> = {
  credit: 'Начисление',
  debit: 'Списание',
  topup: 'Пополнение',
  payment: 'Оплата',
  refund: 'Возврат',
  conversion_in: 'Перевод (вход)',
  conversion_out: 'Перевод (исход)',
  admin_adjustment: 'Корректировка',
  hold: 'Удержание',
  release: 'Разблокировка',
}

function kindLabel(kind: string): string {
  return KIND_LABELS[kind] || kind
}

function sourceLabel(id: string): string {
  return id === 'partner' ? 'Партнёрский' : 'Основной'
}
</script>

<template>
  <section v-if="balance" class="admin-card">
    <h2>Баланс</h2>
    <p v-if="!balance.enabled" class="admin-note">Баланс отключён в настройках сервиса.</p>
    <template v-else>
      <div class="adm-users-balance-row">
        <div v-for="src in sources" :key="src.id" class="admin-kpi">
          <small>{{ sourceLabel(src.id) }}</small>
          <strong>{{ fmtMinor(src.amount_minor, balance.currency_scale, src.currency) }}</strong>
          <small v-if="src.status">статус: {{ src.status }}</small>
        </div>
      </div>

      <template v-if="history.length">
        <h3>Последние операции</h3>
        <div class="adm-users-table-wrap">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Операция</th>
                <th>Сумма</th>
                <th>Комментарий</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in history" :key="`${entry.source_id}-${entry.entry_id}`">
                <td>{{ fmtDateTime(entry.created_at) }}</td>
                <td>
                  {{ kindLabel(entry.kind) }}
                  <span v-if="entry.source_id === 'partner'" class="admin-note">(партнёр)</span>
                </td>
                <td :class="{ 'adm-users-neg': entry.amount_minor < 0 }">
                  {{ entry.amount_minor > 0 ? '+' : '' }}{{ fmtMinor(entry.amount_minor, balance.currency_scale, currencySymbol(balance.currency)) }}
                </td>
                <td>{{ entry.reason || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </template>
  </section>
</template>

<style scoped>
.adm-users-balance-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.adm-users-balance-row .admin-kpi {
  flex: 1 1 160px;
}
.adm-users-neg {
  color: var(--adm-danger, #f87171);
}
.adm-users-table-wrap {
  overflow-x: auto;
}
h3 {
  margin: 8px 0 0;
  font-size: 14px;
}
</style>
