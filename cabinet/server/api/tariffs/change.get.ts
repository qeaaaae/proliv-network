import { requireUser } from '../../utils/session'
import { hasShopBackend, shopFetch } from '../../utils/backend'

// Варианты смены тарифа: current + targets[] с actions (mode, price, ...).
// Пасsthrough upstream GET /api/tariffs/change-options.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  return await shopFetch<Record<string, unknown>>(event, '/api/tariffs/change-options')
})
