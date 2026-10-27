import { createError, type H3Event } from 'h3'
import { ofetch } from 'ofetch'
import { getCabinetSession } from './session'

// Доступ к общему бэкенду (minishop WebApp API): Bearer-токен юзера
// выдаётся через POST /api/auth/token (initData Telegram Mini App) и
// хранится внутри нашей подписанной сессионной куки.

export interface ShopMeSubscription {
  active?: boolean
  end_date?: string | null
  traffic_used_bytes?: number | null
  traffic_limit_bytes?: number | null
  traffic_next_reset_at?: string | null
  config_link?: string | null
  connect_url?: string | null
  max_devices?: number | null
  tariff_key?: string | null
  tariff_name?: string | null
  status?: string
  days_left?: number
}

export interface ShopMe {
  user?: {
    id?: number
    telegram_id?: number | null
    username?: string | null
    first_name?: string | null
    telegram_photo_url?: string
    email?: string | null
    password_auth_enabled?: boolean
    notification_preferences?: Record<string, boolean>
  }
  subscription?: ShopMeSubscription
  referral?: {
    invited_count?: number
    purchased_count?: number
    bot_link?: string | null
    webapp_link?: string | null
    code?: string | null
  }
  plans?: ShopPlan[]
  balance?: { amount?: string; amount_minor?: number; currency?: string; history?: unknown[] }
  settings?: Record<string, unknown>
  payment_methods?: { id?: string; name?: string; icon?: string; currency?: string }[]
  pending_payment?: { payment_id?: number; payment_url?: string; status?: string } | null
  support_unread_count?: number
}

export interface ShopPlan {
  id?: string
  tariff_key?: string
  tariff_name?: string
  title?: string
  subtitle?: string
  price?: number
  stars_price?: number
  months?: number
  duration_days?: number
  period_key?: number
  traffic_gb?: number
  monthly_gb?: number | null
  device_count?: number
  hwid_device_limit?: number | null
  sale_mode?: string
  billing_model?: string
  is_default_tariff?: boolean
  currency?: string
  description?: string
  available_payment_method_ids?: string[]
  hwid_device_packages?: { id?: string; title?: string; price?: number; device_count?: number }[]
}

// Элемент 'plans' из GET /api/tariffs/topup-options и /api/devices/topup-options:
// sale_mode: 'topup' | 'premium_topup' | 'hwid_devices'
export interface ShopTopupPlan {
  id?: string
  tariff_key?: string
  tariff_name?: string
  sale_mode?: string
  title?: string
  subtitle?: string
  price?: number
  stars_price?: number
  currency?: string
  months?: number
  duration_days?: number
  traffic_gb?: number
  device_count?: number
  valid_until?: string | null
  valid_until_text?: string | null
}

export interface ShopTopupOptions {
  ok?: boolean
  tariff_key?: string
  tariff_name?: string
  plans?: ShopTopupPlan[]
}

export interface ShopDevice {
  token: string
  display_name: string
  default_name: string
  platform: string
  hwid_short: string
  last_connected_at: string | null
  can_disconnect: boolean
}

// Партнёрская программа: GET /api/partner/overview
export interface ShopPartnerMethodField {
  id?: string
  label?: string
  required?: boolean
  placeholder?: string
}

export interface ShopPartnerMethod {
  id?: string
  type?: 'bank_card' | 'sbp' | 'crypto' | string
  enabled?: boolean
  label?: string
  debit_currency?: string
  currency_scale?: number
  min_amount_minor?: number
  max_amount_minor?: number | null
  fields?: ShopPartnerMethodField[]
  networks?: { id?: string; label?: string }[]
  help_text?: string
}

export interface ShopPartnerOverview {
  program_enabled?: boolean
  withdrawals_enabled?: boolean
  balance_payment_enabled?: boolean
  balances?: {
    currency?: string
    currency_scale?: number
    available_minor?: number
    pending_minor?: number
    reserved_minor?: number
    lifetime_earned_minor?: number
  }[]
  withdrawal_methods?: ShopPartnerMethod[]
}

export interface ShopPaymentItem {
  payment_id: number
  description: string | null
  amount: number
  currency: string | null
  provider: string | null
  // upstream: awaiting_payment | processing | crediting | review | completed | refunded | failed
  history_state: string
  created_at: string | null
  checkout_url: string | null
}

// Ответ POST /api/payments и /api/tariffs/change-payment
export interface ShopPaymentResult {
  ok?: boolean
  payment_id?: number
  payment_url?: string | null
  confirmation_url?: string | null
  action?: string
  status?: string
  paid?: boolean
}

export function shopApiUrl(event: H3Event): string {
  const config = useRuntimeConfig(event)
  return (config.shopApiUrl || '').replace(/\/$/, '')
}

// Бэкенд настроен и юзер имеет токен minishop
export function hasShopBackend(event: H3Event): boolean {
  return Boolean(shopApiUrl(event) && getCabinetSession(event)?.apiToken)
}

export async function shopFetch<T = Record<string, unknown>>(
  event: H3Event,
  path: string,
  opts: { method?: string; body?: unknown; auth?: boolean } = {},
): Promise<T> {
  const base = shopApiUrl(event)
  if (!base) throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })

  // Без 'identity' minishop на паре Accept: application/json + gzip/br
  // уходит в ~20-секундный путь сжатия - ломает наш таймаут.
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Accept-Encoding': 'identity',
  }
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json'
  if (opts.auth !== false) {
    const session = getCabinetSession(event)
    if (!session?.apiToken) {
      throw createError({ statusCode: 401, statusMessage: 'No backend session' })
    }
    headers.Authorization = `Bearer ${session.apiToken}`
    const method = (opts.method || 'GET').toUpperCase()
    if (session.apiCsrf && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      headers['X-CSRF-Token'] = session.apiCsrf
    }
  }

  let res: unknown
  try {
    res = await ofetch(`${base}${path}`, {
      method: (opts.method || 'GET') as 'GET',
      headers,
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
      timeout: 15000,
    })
  } catch (err) {
    const e = err as { statusCode?: number; data?: { detail?: string; message?: string }; message?: string }
    const status = e.statusCode ?? 502
    const detail = e.data?.detail || e.data?.message || 'Backend request failed'
    throw createError({ statusCode: status, statusMessage: String(detail) })
  }
  return res as T
}

export function bytesToGb(bytes: number | null | undefined): number {
  if (!bytes || bytes <= 0) return 0
  return Math.round((bytes / 2 ** 30) * 10) / 10
}

const PLATFORMS = new Set(['ios', 'android', 'windows', 'macos', 'tvos', 'linux'])

export interface ShopTicketOut {
  ticket_id: number
  subject: string
  status: string
  created_at: string | null
  updated_at: string | null
  last_message_at: string | null
  last_message_role: string | null
  closed_at: string | null
  unread_user_count?: number
}

export function mapTicketStatus(t: Pick<ShopTicketOut, 'status' | 'closed_at' | 'last_message_role'>): 'open' | 'answered' | 'closed' {
  // upstream: open | awaiting_user | awaiting_admin | resolved | closed
  if (t.closed_at || t.status === 'closed' || t.status === 'resolved') return 'closed'
  if (t.status === 'awaiting_user' || t.status === 'answered') return 'answered'
  if (['admin', 'connector', 'support'].includes(t.last_message_role || '')) return 'answered'
  return 'open'
}

export interface ShopTicketMessage {
  // upstream SupportMessageOut: author_role = user | admin | connector
  author_role?: string
  role?: string
  from?: string
  body?: string
  text?: string
  body_format?: string
  is_internal_note?: boolean
  created_at?: string | null
}

export function mapTicketMessage(m: ShopTicketMessage): { from: 'user' | 'support'; text: string; at: string } {
  const role = m.author_role || m.role || m.from || 'user'
  let text = m.body || m.text || ''
  // body_format='html' - Telegram-разметка; фронт показывает чистый текст
  if (m.body_format === 'html') text = text.replace(/<[^>]+>/g, '')
  return {
    from: ['admin', 'connector', 'support'].includes(role) ? 'support' : 'user',
    text,
    at: m.created_at || '',
  }
}

export function mapTicket(t: ShopTicketOut) {
  return {
    id: `T-${t.ticket_id}`,
    subject: t.subject,
    status: mapTicketStatus(t),
    createdAt: t.created_at || '',
    updatedAt: t.last_message_at || t.updated_at || t.created_at || '',
    lastMessage: '',
  }
}

export function mapSettings(prefs: Record<string, boolean> | undefined): {
  notifyExpiry: boolean
  notifyNews: boolean
  notifySecurity: boolean
} {
  return {
    notifyExpiry: prefs?.system_telegram ?? true,
    notifyNews: prefs?.marketing_telegram ?? true,
    notifySecurity: prefs?.system_email ?? true,
  }
}

export function mapDevice(d: ShopDevice): {
  id: string
  name: string
  platform: 'ios' | 'android' | 'windows' | 'macos' | 'tvos' | 'linux' | 'other'
  hwid: string
  lastSeen: string
} {
  const platform = (d.platform || 'other').toLowerCase()
  return {
    id: d.token,
    name: d.display_name || d.default_name || 'Устройство',
    platform: (PLATFORMS.has(platform) ? platform : 'other') as 'other',
    hwid: d.hwid_short || '',
    lastSeen: d.last_connected_at || '',
  }
}
