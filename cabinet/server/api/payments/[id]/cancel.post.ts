import { getRouterParam } from 'h3'
import { requireUser } from '../../../utils/session'
import { hasShopBackend, shopFetch } from '../../../utils/backend'

// Отмена ожидающего оплаты платежа (id вида P-123 или 123).
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const id = (getRouterParam(event, 'id') || '').replace(/^P-/i, '')
  if (!/^\d+$/.test(id)) throw createError({ statusCode: 400, statusMessage: 'Bad payment id' })

  const res = await shopFetch<{ ok?: boolean; payment_id?: number; status?: string }>(
    event,
    `/api/payments/${encodeURIComponent(id)}/cancel`,
    { method: 'POST', body: {} },
  )
  return { ok: Boolean(res.ok), paymentId: res.payment_id ? `P-${res.payment_id}` : `P-${id}`, status: res.status }
})
