import { getQuery } from 'h3'
import { requireUser } from '../../utils/session'
import { hasShopBackend, shopFetch, type ShopTopupOptions } from '../../utils/backend'

// Докупаемые пакеты трафика текущего тарифа (обычные + premium).
// Требует активной тарифной подписки на бэкенде; kind=all|regular|premium.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const kind = String(getQuery(event).kind || 'all')
  return await shopFetch<ShopTopupOptions>(
    event,
    `/api/tariffs/topup-options?kind=${encodeURIComponent(kind)}`,
  )
})
