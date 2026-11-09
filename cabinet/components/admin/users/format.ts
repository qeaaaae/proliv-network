// Форматирование и подписи для раздела "Пользователи" веб-админки.
// Общие хелперы (даты, деньги, ошибки) - в ../format и реэкспортированы ниже,
// чтобы старые импорты './format' продолжали работать.
import type {
  AdminPremiumTraffic,
  AdminSubscription,
  AdminSubscriptionPlan,
  AdminTariffOption,
  AdminUser,
} from './types'
import { fmtBytes } from '../format'
import type { BadgeTone } from '../format'

export {
  adminErrorMessage,
  currencySymbol,
  daysLeft,
  fmtBytes,
  fmtDate,
  fmtDateTime,
  fmtMinor,
  fmtMoney,
  fmtNum,
} from '../format'
export type { BadgeTone } from '../format'

export function userDisplayName(user: AdminUser | null | undefined): string {
  if (!user) return '—'
  const full = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  if (full) return full
  if (user.username) return `@${user.username}`
  if (user.email) return user.email
  return `Пользователь #${user.user_id}`
}

export function userSecondaryLine(user: AdminUser | null | undefined): string {
  if (!user) return ''
  const parts: string[] = []
  if (user.username) parts.push(`@${user.username}`)
  if (user.minishop_id) parts.push(user.minishop_id)
  else parts.push(`#${user.user_id}`)
  return parts.join(' · ')
}

export function panelStatusLabel(status: string | null | undefined, banned?: boolean): string {
  if (banned) return 'Заблокирован'
  switch ((status || '').toLowerCase()) {
    case 'active':
      return 'Активна'
    case 'expired':
      return 'Истекла'
    case 'limited':
      return 'Лимит трафика'
    case 'disabled':
      return 'Отключена'
    case 'bot_only':
      return 'Без подписки'
    default:
      return status || 'Без подписки'
  }
}

export function panelStatusTone(status: string | null | undefined, banned?: boolean): BadgeTone {
  if (banned) return 'danger'
  switch ((status || '').toLowerCase()) {
    case 'active':
      return 'success'
    case 'expired':
      return 'muted'
    case 'limited':
      return 'warning'
    case 'disabled':
      return 'danger'
    default:
      return 'muted'
  }
}

export function premiumTrafficLabel(t: AdminPremiumTraffic | null | undefined): string {
  if (!t || t.state === 'none') return '—'
  if (t.state === 'unlimited') return 'Безлимит'
  const pct = t.percent ?? 0
  return `${pct}% (${fmtBytes(t.used_bytes ?? null)} / ${fmtBytes(t.limit_bytes ?? null)})`
}

export function premiumTrafficTone(t: AdminPremiumTraffic | null | undefined): BadgeTone {
  if (!t || t.state === 'none') return 'muted'
  switch (t.state) {
    case 'unlimited':
      return 'success'
    case 'warn':
      return 'warning'
    case 'critical':
      return 'danger'
    default:
      return 'default'
  }
}

export function vpnStatusLabel(status: string | null | undefined): string {
  switch ((status || '').toLowerCase()) {
    case 'connected':
      return 'Подключён'
    case 'disconnected':
      return 'Не подключён'
    default:
      return 'Нет данных'
  }
}

export function vpnStatusTone(status: string | null | undefined): BadgeTone {
  return (status || '').toLowerCase() === 'connected' ? 'success' : 'muted'
}

export function telegramNotificationsLabel(status: string | null | undefined): string {
  switch ((status || '').toLowerCase()) {
    case 'enabled':
      return 'Включены'
    case 'blocked':
      return 'Заблокировал бота'
    case 'disabled':
      return 'Выключены'
    default:
      return 'Неизвестно'
  }
}

export function tariffName(option: AdminTariffOption | null | undefined): string {
  if (!option) return '—'
  return option.tariff_names?.ru || option.tariff_names?.en || option.tariff_key
}

export function planLabel(plan: AdminSubscriptionPlan | null | undefined): string {
  if (!plan) return '—'
  if (plan.kind === 'trial') return 'Триал'
  if (plan.kind === 'unassigned') return 'Без тарифа'
  return plan.tariff_names?.ru || plan.tariff_names?.en || plan.tariff_key || 'Тариф'
}

export function subscriptionLabel(sub: AdminSubscription | null | undefined): string {
  if (!sub) return '—'
  return sub.display_label || sub.tariff_key || (sub.is_trial ? 'Триал' : 'Подписка')
}

export function trafficStrategyLabel(strategy: string | null | undefined): string {
  switch ((strategy || '').toUpperCase()) {
    case 'NO_RESET':
      return 'Без сброса'
    case 'DAY':
      return 'Раз в день'
    case 'WEEK':
      return 'Раз в неделю'
    case 'MONTH':
      return 'Раз в месяц'
    case 'MONTH_ROLLING':
      return 'Скользящий месяц'
    default:
      return strategy || '—'
  }
}

export function paymentStatusLabel(status: string | null | undefined): string {
  switch ((status || '').toLowerCase()) {
    case 'succeeded':
    case 'completed':
      return 'Оплачен'
    case 'pending':
    case 'awaiting_payment':
      return 'Ожидает оплаты'
    case 'processing':
      return 'В обработке'
    case 'crediting':
      return 'Зачисляется'
    case 'review':
      return 'На проверке'
    case 'failed':
      return 'Ошибка'
    case 'refunded':
      return 'Возврат'
    case 'cancelled':
    case 'canceled':
      return 'Отменён'
    default:
      return status || '—'
  }
}

export function paymentStatusTone(status: string | null | undefined): BadgeTone {
  switch ((status || '').toLowerCase()) {
    case 'succeeded':
    case 'completed':
      return 'success'
    case 'failed':
    case 'cancelled':
    case 'canceled':
      return 'danger'
    case 'refunded':
    case 'review':
      return 'warning'
    default:
      return 'muted'
  }
}
