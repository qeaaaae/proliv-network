// Общие форматтеры и тексты ошибок веб-админки.
// Доменные хелперы (статусы подписок, платежей и т.п.) лежат рядом с
// компонентами - сюда выносим только то, что повторялось на ~15 файлах.
export type BadgeTone = 'default' | 'success' | 'warning' | 'danger' | 'muted'

export function fmtNum(v: unknown, empty = '—'): string {
  const n = Number(v)
  return Number.isFinite(n) ? n.toLocaleString('ru-RU') : empty
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

// Сумма в основных единицах + символ валюты.
export function fmtMoney(amount: number | null | undefined, currency?: string | null): string {
  if (amount === null || amount === undefined) return '—'
  const n = Number(amount)
  if (!Number.isFinite(n)) return '—'
  const formatted = n.toLocaleString('ru-RU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })
  return `${formatted} ${currencySymbol(currency)}`
}

// Минорные единицы -> "1 234,5 ₽" (до scale знаков, без хвостовых нулей).
export function fmtMinor(minor: number | null | undefined, scale: number, currency?: string | null): string {
  if (minor === null || minor === undefined) return '—'
  return fmtMoney(minor / 10 ** (scale || 2), currency)
}

// Минорные единицы -> ровно scale знаков ("1 234,00 ₽"), как в партнёрских таблицах.
export function fmtMinorFixed(minor: number | null | undefined, scale = 2, currency = 'RUB'): string {
  const value = (minor ?? 0) / 10 ** (scale || 0)
  return `${value.toLocaleString('ru-RU', {
    minimumFractionDigits: scale,
    maximumFractionDigits: scale,
  })} ${currencySymbol(currency)}`
}

// Базисные пункты -> процент ("1250" -> "12,5%").
export function fmtBps(bps?: number | null): string {
  return bps === null || bps === undefined ? '—' : `${(bps / 100).toLocaleString('ru-RU')}%`
}

// Число с обрезанными нулями: 10 -> "10", 2.5 -> "2,5", 2.125 -> "2,125".
export function fmtTrim(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return Number.isInteger(v) ? String(v) : v.toFixed(3).replace(/0+$/, '').replace(/[.,]$/, '')
}

export function fmtBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return '—'
  const gb = bytes / 1024 ** 3
  if (Math.abs(gb) >= 1) return `${gb.toFixed(2).replace(/\.?0+$/, '')} ГБ`
  const mb = bytes / 1024 ** 2
  if (Math.abs(mb) >= 1) return `${mb.toFixed(0)} МБ`
  return `${bytes} Б`
}

function toDate(iso: string | null | undefined): Date | null {
  if (!iso) return null
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? null : d
}

// "5 ноября 2026 г."
export function fmtDate(iso: string | null | undefined): string {
  const d = toDate(iso)
  return d ? d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'
}

// "5 ноября, 14:32"
export function fmtDateTime(iso: string | null | undefined): string {
  const d = toDate(iso)
  return d
    ? d.toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
    : '—'
}

// "05.11.2026, 14:32" - компактный числовой формат для таблиц.
export function fmtDateTimeFull(iso: string | null | undefined): string {
  const d = toDate(iso)
  return d
    ? d.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—'
}

// "05.11, 14:32" - без года.
export function fmtDateTimeShort(iso: string | null | undefined): string {
  const d = toDate(iso)
  return d
    ? d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
    : '—'
}

// "05.11"
export function fmtDateShort(iso: string | null | undefined): string {
  const d = toDate(iso)
  return d ? d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }) : '—'
}

export function daysLeft(iso: string | null | undefined): number | null {
  const d = toDate(iso)
  return d ? Math.ceil((d.getTime() - Date.now()) / 86400_000) : null
}

const ERROR_LABELS: Record<string, string> = {
  not_found: 'Пользователь не найден',
  user_not_found: 'Пользователь не найден',
  forbidden: 'Недостаточно прав',
  unauthorized: 'Недостаточно прав',
  no_active_subscription: 'Нет активной подписки',
  no_panel_user: 'Пользователь не привязан к панели',
  panel_user_missing: 'Подписка не привязана к панели',
  panel_service_unavailable: 'Сервис панели недоступен',
  panel_unavailable: 'Панель недоступна',
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
  queue_unavailable: 'Очередь фоновых задач недоступна',
  no_telegram_account: 'У пользователя не привязан Telegram',
  send_failed: 'Не удалось отправить сообщение',
  preview_failed: 'Не удалось отправить предпросмотр',
  admin_telegram_unavailable: 'У вас не привязан Telegram-аккаунт',
  subscription_reissue_in_progress: 'Перевыпуск ссылки уже выполняется',
  subscription_reissue_failed: 'Не удалось перевыпустить ссылку',
  invalid_payload: 'Некорректные данные запроса',
  invalid_request: 'Некорректный запрос',
  invalid_tariff_filter: 'Некорректный фильтр тарифа',
  invalid_user_id: 'Некорректный user_id',
  invalid_role_request: 'Некорректный запрос роли',
  invalid_telegram_html: 'Ошибка HTML-разметки',
  invalid_audience: 'Неизвестная аудитория',
  audience_unavailable: 'Эта аудитория сейчас недоступна',
  unknown_shortcode: 'Неизвестный шорткод в тексте',
  email_not_configured: 'Email-канал не настроен на бэкенде',
  broadcast_schedule_future: 'Время отправки должно быть в будущем',
  account_merge_not_required: 'Укажите другой аккаунт для объединения',
  account_merge_confirmation_required: 'Подтвердите объединение',
  account_merge_privileged_source: 'Нельзя объединять аккаунты с правами администратора',
  account_merge_current_admin: 'Нельзя объединить свой текущий аккаунт',
  account_merge_banned: 'Заблокированный аккаунт нельзя объединять',
  account_merge_failed: 'Не удалось объединить аккаунты',
  account_not_found: 'Аккаунт не найден',
  account_identifier_required: 'Укажите ms_ id или email',
  role_revoke_failed: 'Не удалось снять роль',
  balance_disabled: 'Баланс отключён',
  insufficient_funds: 'Недостаточно средств на балансе',
  partner_not_found: 'Партнёрский профиль не найден',
  request_failed: 'Ошибка запроса',
}

// Человекочитаемый текст ошибки админ-API.
// fallback - контекст операции ('Не удалось загрузить'): неизвестный код ->
// '<fallback>: code', совсем пустая ошибка -> fallback.
// extra - доменные подписи поверх общего словаря (например not_found для тикетов).
export function adminErrorMessage(
  err: unknown,
  fallback = 'Ошибка запроса',
  extra?: Record<string, string>,
): string {
  const e = (err as { message?: string; code?: string; data?: { error?: string; message?: string } }) || {}
  const code = e.code || e.data?.error || ''
  if (code) {
    const label = extra?.[code] || ERROR_LABELS[code]
    if (label) return label
    if (code.startsWith('unknown_shortcode')) return ERROR_LABELS.unknown_shortcode as string
  }
  const msg = e.data?.message || (e.message && e.message !== code ? e.message : '')
  if (msg && msg !== 'request_failed' && msg !== 'Backend request failed') return msg
  return code && code !== 'request_failed' ? `${fallback}: ${code}` : fallback
}
