import { requireUser } from '../utils/session'
import { hasShopBackend, mapSettings, shopFetch, type ShopMe } from '../utils/backend'

export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const me = await shopFetch<ShopMe>(event, '/api/me')
  return { settings: mapSettings(me.user?.notification_preferences) }
})
