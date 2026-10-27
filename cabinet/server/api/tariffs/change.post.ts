import { readBody } from 'h3'
import { requireUser } from '../../utils/session'
import { hasShopBackend, shopFetch, type ShopPaymentResult } from '../../utils/backend'

// Смена тарифа. Бесплатные режимы (mode: recalc_days | convert_days_to_gb)
// идут в POST /api/tariffs/change; платный апгрейд - в
// POST /api/tariffs/change-payment (возвращает ссылку на оплату).
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{ tariffKey?: string; mode?: string; method?: string }>(event)
  const tariffKey = (body?.tariffKey || '').trim()
  if (!tariffKey) throw createError({ statusCode: 400, statusMessage: 'Не выбран тариф' })

  const mode = (body?.mode || '').trim()
  if (mode) {
    const res = await shopFetch<{ ok?: boolean; subscription_id?: number; tariff_key?: string }>(
      event,
      '/api/tariffs/change',
      { method: 'POST', body: { tariff_key: tariffKey, mode } },
    )
    return { ok: Boolean(res.ok), subscriptionId: res.subscription_id, tariffKey: res.tariff_key }
  }

  const res = await shopFetch<ShopPaymentResult>(event, '/api/tariffs/change-payment', {
    method: 'POST',
    body: { tariff_key: tariffKey, method: body?.method || 'yookassa' },
  })
  return {
    ok: Boolean(res.ok),
    orderId: res.payment_id ? `P-${res.payment_id}` : null,
    paymentUrl: res.payment_url || res.confirmation_url || null,
    status: res.status,
    paid: Boolean(res.paid),
    action: res.action,
  }
})
