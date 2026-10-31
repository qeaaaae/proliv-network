<script setup lang="ts">
type BadgeTone = 'default' | 'success' | 'warning' | 'danger' | 'muted'

interface PaymentRow {
  payment_id: number
  user_id: number
  user_label?: string
  amount: number
  currency?: string | null
  provider?: string | null
  status?: string | null
  description?: string | null
  created_at?: string | null
}

const props = defineProps<{
  payments: PaymentRow[]
  currency: string
}>()

const rows = computed(() => props.payments.slice(0, 10))

const providerLabels: Record<string, string> = {
  yookassa: 'ЮKassa',
  telegram_stars: 'Telegram Stars',
  stars: 'Telegram Stars',
  admin_gift: 'Подарок админа',
  balance: 'Баланс',
  cryptobot: 'CryptoBot',
  platega_sbp: 'Platega СБП',
  platega_card: 'Platega Card',
  platega_crypto: 'Platega Crypto',
}

const statusMeta: Record<string, { tone: BadgeTone; label: string }> = {
  succeeded: { tone: 'success', label: 'Успешно' },
  pending: { tone: 'warning', label: 'Ожидает' },
  created: { tone: 'muted', label: 'Создан' },
  failed: { tone: 'danger', label: 'Ошибка' },
  canceled: { tone: 'danger', label: 'Отменён' },
  cancelled: { tone: 'danger', label: 'Отменён' },
  refunded: { tone: 'muted', label: 'Возврат' },
  reversed: { tone: 'muted', label: 'Отменён админом' },
}

function providerLabel(provider?: string | null): string {
  if (!provider) return '—'
  return providerLabels[provider] || provider
}

function statusOf(p: PaymentRow): { tone: BadgeTone; label: string } {
  const key = String(p.status || '')
  return statusMeta[key] || { tone: 'muted', label: key || '—' }
}

function fmtMoney(value: unknown, paymentCurrency?: string | null): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  const code = String(paymentCurrency || props.currency || 'RUB').toUpperCase()
  try {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: code,
      maximumFractionDigits: n % 1 ? 2 : 0,
    }).format(n)
  } catch {
    return `${new Intl.NumberFormat('ru-RU').format(n)} ${code}`
  }
}

function fmtDateTime(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <section class="admin-card">
    <div class="pay-head">
      <h2>Последние платежи</h2>
      <NuxtLink class="pay-link" to="/admin/payments">Все платежи</NuxtLink>
    </div>
    <p v-if="!rows.length" class="admin-note">Платежей пока нет.</p>
    <div v-else class="pay-table-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Пользователь</th>
            <th>Сумма</th>
            <th>Провайдер</th>
            <th>Статус</th>
            <th>Дата</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in rows" :key="p.payment_id">
            <td>
              <div class="pay-user">{{ p.user_label || `#${p.user_id}` }}</div>
              <div v-if="p.description" class="pay-desc">{{ p.description }}</div>
            </td>
            <td class="pay-amount">{{ fmtMoney(p.amount, p.currency) }}</td>
            <td>{{ providerLabel(p.provider) }}</td>
            <td>
              <AdminBadge :tone="statusOf(p).tone">{{ statusOf(p).label }}</AdminBadge>
            </td>
            <td class="pay-date">{{ fmtDateTime(p.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.pay-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.pay-head h2 {
  margin: 0;
}
.pay-link {
  font-size: 12px;
  color: var(--adm-accent, #3b82f6);
  text-decoration: none;
}
.pay-link:hover {
  text-decoration: underline;
}
.pay-table-wrap {
  overflow-x: auto;
}
.pay-user {
  font-weight: 600;
}
.pay-desc {
  font-size: 11px;
  color: var(--adm-muted, #8b95a8);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pay-amount {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.pay-date {
  color: var(--adm-muted, #8b95a8);
  white-space: nowrap;
}
</style>
