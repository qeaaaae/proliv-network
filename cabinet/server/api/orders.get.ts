import { requireUser } from '../utils/session'
import { hasShopBackend, shopFetch, type ShopPaymentItem } from '../utils/backend'
import type { Order } from '../utils/store'

// upstream history_state: awaiting_payment | processing | crediting | review
// | completed | refunded | failed
function mapStatus(state: string): Order['status'] {
  if (state === 'completed' || state === 'paid' || state === 'success') return 'paid'
  if (state === 'refunded' || state === 'partially_refunded' || state === 'reversed') return 'refunded'
  if (state === 'failed' || state === 'canceled' || state === 'expired') return 'failed'
  return 'pending'
}

// История покупок - из платёжной истории бэкенда. checkout_url есть у
// платежей, ожидающих оплаты - по нему можно вернуться к оплате.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }

  const res = await shopFetch<{ items?: ShopPaymentItem[] }>(event, '/api/payments/history?limit=100')
  const orders = (res.items ?? []).map<Order>((p) => ({
    id: `P-${p.payment_id}`,
    title: p.description || 'Оплата',
    amount: p.amount ?? 0,
    method: p.provider || '',
    status: mapStatus(p.history_state || ''),
    at: p.created_at || '',
    checkoutUrl: p.checkout_url || null,
  }))
  return { orders }
})
