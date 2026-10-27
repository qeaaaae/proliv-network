import { requireUser } from '../utils/session'
import { hasShopBackend, shopFetch } from '../utils/backend'

// Мои подарочные подписки: купленные (link для передачи) и полученные.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  return await shopFetch<Record<string, unknown>>(event, '/api/gifts')
})
