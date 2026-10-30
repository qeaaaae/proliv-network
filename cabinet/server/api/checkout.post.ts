import { readBody } from 'h3'
import { requireUser } from '../utils/session'
import {
  hasShopBackend,
  shopFetch,
  type ShopMe,
  type ShopPaymentResult,
  type ShopPlan,
  type ShopTopupOptions,
  type ShopTopupPlan,
} from '../utils/backend'

const TRAFFIC_SALE_MODES = new Set(['traffic', 'traffic_package', 'topup', 'premium_topup'])

function planDays(p: ShopPlan | ShopTopupPlan): number {
  return p.duration_days ?? Math.round((p.months ?? 1) * 30)
}

// Создание платежа на бэкенде: подписка (planId или periodDays), докупка
// (extra: traffic-N | premium-N | device-N) или подарок. Бэкенд возвращает
// payment_url/confirmation_url для редиректа на оплату.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{
    planId?: string
    periodDays?: number
    method?: string
    gift?: boolean
    giftTo?: string
    extra?: string
    promo?: string
    balanceSource?: string
    saleMode?: string
  }>(event)

  const me = await shopFetch<ShopMe>(event, '/api/me')
  const plans = me.plans ?? []
  const method = body?.method || 'yookassa'
  const payload: Record<string, unknown> = { method }
  if (body?.promo) payload.promo_code = body.promo
  // Балансная скидка upstream: бэкенд сам списывает сколько хватает
  // (полностью или до минималки провайдера) и выставляет инвойс на остаток.
  if (body?.balanceSource === 'user' || body?.balanceSource === 'partner') {
    payload.balance_source = body.balanceSource
  }

  if (body?.saleMode === 'trial') {
    // Платный триал: цена и срок считаются на бэкенде из TRIAL_* настроек,
    // upstream сам выставит инвойс и активирует триал после оплаты.
    payload.sale_mode = 'trial'
  } else if (body?.extra) {
    // Докупка: traffic-{gb} | premium-{gb} | device-{count}
    const m = /^(traffic|premium|device)-(\d+(?:\.\d+)?)$/i.exec(body.extra)
    if (!m) throw createError({ statusCode: 400, statusMessage: 'Неизвестный пакет' })
    const kind = (m[1] || '').toLowerCase()
    const units = Number(m[2])

    const [trafficOpts, deviceOpts] = await Promise.all([
      kind === 'device'
        ? Promise.resolve(null)
        : shopFetch<ShopTopupOptions>(event, '/api/tariffs/topup-options').catch(() => null),
      kind === 'device'
        ? shopFetch<ShopTopupOptions>(event, '/api/devices/topup-options').catch(() => null)
        : Promise.resolve(null),
    ])

    let topup: ShopTopupPlan | undefined
    if (kind === 'device') {
      topup = (deviceOpts?.plans ?? []).find((p) => p.device_count === units)
      payload.device_count = units
      payload.sale_mode = topup?.sale_mode || 'hwid_devices'
    } else {
      const saleMode = kind === 'premium' ? 'premium_topup' : 'topup'
      topup = (trafficOpts?.plans ?? []).find(
        (p) => (p.sale_mode || 'topup') === saleMode && Number(p.traffic_gb ?? p.months) === units,
      )
      payload.traffic_gb = units
      payload.sale_mode = topup?.sale_mode || saleMode
    }
    const tariffKey = topup?.tariff_key ?? me.subscription?.tariff_key ?? plans.find((p) => p.tariff_key)?.tariff_key
    if (kind === 'device') {
      // Пакет должен прийти из /api/devices/topup-options: если его там нет
      // (эндпоинт отказал или плана нет) - постить на /api/payments бессмысленно,
      // бэкенд вернёт 400 с английским "Device top-up is not available".
      if (!topup) {
        throw createError({ statusCode: 400, statusMessage: 'Докупка устройств недоступна' })
      }
    } else if (!topup && !tariffKey) {
      throw createError({ statusCode: 400, statusMessage: 'Пакет трафика недоступен' })
    }
    if (tariffKey) payload.tariff_key = tariffKey
  } else {
    // Подписка: сначала по точному planId, затем по длительности
    const plan =
      (body?.planId ? plans.find((p) => p.id === body.planId) : undefined) ??
      plans.find((p) => (p.sale_mode ?? 'subscription') === 'subscription' && planDays(p) === (body?.periodDays ?? 30))

    const saleMode = plan?.sale_mode || 'subscription'
    payload.sale_mode = saleMode
    if (plan?.tariff_key) payload.tariff_key = plan.tariff_key
    if (TRAFFIC_SALE_MODES.has(saleMode)) {
      payload.traffic_gb = plan?.traffic_gb ?? plan?.months
    } else {
      const days = plan ? planDays(plan) : (body?.periodDays ?? 30)
      payload.duration_days = days
      if (plan?.months) payload.months = plan.months
      else if (days % 30 === 0) payload.months = Math.round(days / 30)
    }

    if (body?.gift) {
      payload.gift = true
      const giftTo = (body.giftTo || '').trim()
      if (giftTo) payload.gift_recipient_email = giftTo
    }
  }

  // Реферальная скидка друга: бэкенд сам предлагает персональный промокод
  // (suggested_promo_code) приглашённым юзерам - подставляем его на
  // подписочные покупки, если промокод не указан явно. Валидность и
  // привязку к юзеру бэкенд проверяет сам.
  if (!payload.promo_code && payload.sale_mode === 'subscription' && me.suggested_promo_code) {
    payload.promo_code = me.suggested_promo_code
  }

  const res = await shopFetch<ShopPaymentResult>(event, '/api/payments', { method: 'POST', body: payload })

  return {
    ok: Boolean(res.ok),
    demo: false,
    orderId: res.payment_id ? `P-${res.payment_id}` : null,
    periodDays: body?.periodDays ?? 30,
    method,
    gift: body?.gift ?? false,
    paymentUrl: res.payment_url || res.confirmation_url || null,
    status: res.status,
    paid: Boolean(res.paid),
    action: res.action,
  }
})
