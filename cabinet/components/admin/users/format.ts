// Форматирование и подписи для раздела "Пользователи" веб-админки.
import type {
  AdminPremiumTraffic,
  AdminSubscription,
  AdminSubscriptionPlan,
  AdminTariffOption,
  AdminUser,
} from './types'

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

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const t = new Date(iso).getTime()
  if (!Number.isFinite(t)) return '—'
  return new Date(t).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const t = new Date(iso).getTime()
  if (!Number.isFinite(t)) return '—'
  return new Date(t).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function daysLeft(iso: string | null | undefined): number | null {
  if (!iso) return null
  const t = new Date(iso).getTime()
  if (!Number.isFinite(t)) return null
  return Math.ceil((t - Date.now()) / 86400_000)
}

export function fmtBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return '—'
  const gb = bytes / 1024 ** 3
  if (Math.abs(gb) >= 1) return `${gb.toFixed(2).replace(/\.?0+$/, '')} ГБ`
  const mb = bytes / 1024 ** 2
  if (Math.abs(mb) >= 1) return `${mb.toFixed(0)} МБ`
  return `${bytes} Б`
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  RUB: '₽',
  USD: '$',
  EUR: '€',
  XTR: '★',
}

export function currencySymbol(currency: string | null | undefined): string {
  if (!currency) return '₽'
  return CURRENCY_SYMBOLS[currency.toUpperCase()] || currency.toUpperCase()
}

export function fmtMoney(amount: number | null | undefined, currency?: string | null): string {
  if (amount === null || amount === undefined) return '—'
  const formatted = amount.toLocaleString('ru-RU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })
  return `${formatted} ${currencySymbol(currency)}`
}

export function fmtMinor(minor: number | null | undefined, scale: number, currency?: string): string {
  if (minor === null || minor === undefined) return '—'
  return fmtMoney(minor / 10 ** (scale || 2), currency)
}

export type BadgeTone = 'default' | 'success' | 'warning' | 'danger' | 'muted'

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

const ERROR_LABELS: Record<string, string> = {
  not_found: 'Пользователь не найден',
  user_not_found: 'Пользователь не найден',
  forbidden: 'Недостаточно прав',
  no_active_subscription: 'Нет активной подписки',
  no_panel_user: 'Пользователь не привязан к панели',
  panel_user_missing: 'Подписка не привязана к панели',
  panel_service_unavailable: 'Сервис панели недоступен',
  panel_unavailable: 'Сервис панели недоступен',
  subscription_service_unavailable: 'Сервис подписок недоступен',
  panel_update_failed: 'Не удалось обновить данные в панели',
  panel_status_update_failed: 'Не удалось обновить статус в панели',
  panel_delete_failed: 'Не удалось удалить пользователя в панели',
  panel_request_failed: 'Ошибка запроса к панели',
  tariff_required: 'Выберите тариф',
  invalid_tariff: 'Неизвестный тариф',
  tariffs_not_configured: 'Тарифы не настроены',
  no_period_tariffs: 'Нет тарифов с помесячной оплатой',
  invalid_days: 'Некорректное число дней',
  invalid_end_date: 'Дата окончания должна быть в будущем',
  extend_failed: 'Не удалось изменить подписку',
  tariff_change_failed: 'Не удалось сменить тариф',
  invalid_kind: 'Некорректный тип трафика',
  missing_amount: 'Укажите объём',
  invalid_amount: 'Некорректный объём',
  grant_failed: 'Не удалось начислить трафик',
  invalid_bonus: 'Некорректный бонус',
  invalid_regular_bonus: 'Некорректный бонус',
  invalid_hwid_device_limit: 'Некорректный лимит устройств',
  invalid_traffic_strategy: 'Некорректная стратегия сброса',
  traffic_strategy_locked: 'Стратегия сброса заблокирована для этой подписки',
  empty_text: 'Введите текст сообщения',
  queue_unavailable: 'Очередь сообщений недоступна',
  no_telegram_account: 'У пользователя не привязан Telegram',
  send_failed: 'Не удалось отправить сообщение',
  preview_failed: 'Не удалось отправить предпросмотр',
  admin_telegram_unavailable: 'У вас не привязан Telegram-аккаунт',
  subscription_reissue_in_progress: 'Перевыпуск ссылки уже выполняется',
  subscription_reissue_failed: 'Не удалось перевыпустить ссылку',
  invalid_payload: 'Некорректные данные запроса',
  invalid_tariff_filter: 'Некорректный фильтр тарифа',
  account_merge_not_required: 'Укажите другой аккаунт для объединения',
  account_merge_confirmation_required: 'Подтвердите объединение',
  account_merge_privileged_source: 'Нельзя объединять аккаунты с правами администратора',
  account_merge_current_admin: 'Нельзя объединить свой текущий аккаунт',
  account_merge_banned: 'Заблокированный аккаунт нельзя объединять',
  account_merge_failed: 'Не удалось объединить аккаунты',
  balance_disabled: 'Баланс отключён',
  insufficient_funds: 'Недостаточно средств на балансе',
  partner_not_found: 'Партнёрский профиль не найден',
  request_failed: 'Ошибка запроса',
}

export function adminErrorMessage(err: unknown): string {
  const e = err as { message?: string; code?: string; data?: { error?: string } }
  const code = e?.code || e?.data?.error || e?.message || ''
  return ERROR_LABELS[code] || `Ошибка: ${code || 'request_failed'}`
}
